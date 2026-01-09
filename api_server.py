from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import mysql.connector
import paho.mqtt.client as mqtt_client
import uuid
from datetime import datetime, timedelta

# =======================================================
# 1. KONFIGURASI
# =======================================================
app = Flask(__name__)
CORS(app)

@app.route("/")
def dashboard():
    return render_template("index.html")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",        # sesuaikan dengan Laragon
    "database": "iot_sesar"
}

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_CONTROL = "/lembang/control/actuator"
CLIENT_ID_PUBLISHER = f"Lembang_Publisher_{uuid.uuid4().hex[:6]}"

# posisi tetap sensor (ganti dengan koordinat lokasi sensor-mu)
DEFAULT_COORD = "-6.8320, 107.6170"

# =======================================================
# 2. FUNGSI INFERENSI + ESTIMASI
# =======================================================
def estimate_depth_km(magnitude_g, deviation):
    mag = magnitude_g or 0.0
    dev = deviation or 0.0

    if dev >= 0.4:
        return 5     # dangkal
    elif dev >= 0.25:
        return 10    # menengah
    elif dev >= 0.15:
        return 20    # agak dalam
    else:
        return 30    # dalam

def infer_descriptions(reading):
    """Menambahkan deskripsi inferensi dengan pengamanan data NULL."""
    if reading is None:
        return {}

    deviation = reading.get("deviation") if reading.get("deviation") is not None else 0.0
    acx = reading.get("acx_g") if reading.get("acx_g") is not None else 0.0
    acy = reading.get("acy_g") if reading.get("acy_g") is not None else 0.0
    acz = reading.get("acz_g") if reading.get("acz_g") is not None else 1.0  # gravitasi

    status_db = "NORMAL"
    if deviation >= 0.20:
        status_db = "ALERT"
    if deviation >= 0.35:
        status_db = "WARNING"

    # 1. Kekuatan Goncangan
    if deviation >= 0.40:
        kekuatan = "Goncangan Keras (Berpotensi merusak)."
    elif deviation >= 0.15:
        kekuatan = "Goncangan Sedang (Perlu waspada)."
    else:
        kekuatan = "Goncangan Lemah (Kondisi aman)."

    # 2. Jenis Pergerakan
    horizontal_component = abs(acx) + abs(acy)
    vertical_component = abs(acz - 1.0)

    if horizontal_component > (vertical_component * 1.5) and deviation > 0.1:
        pergerakan = "Dominan Horizontal (Sesar Geser)."
    else:
        pergerakan = "Dominan Vertikal (Sesar Naik/Turun)."

    reading["status"] = status_db

    return {
        "kekuatan_goncangan": kekuatan,
        "jenis_pergerakan": pergerakan
    }

# =======================================================
# 3. KONEKSI UTILITAS
# =======================================================
mqttc = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, CLIENT_ID_PUBLISHER)

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ API MQTT Publisher terhubung.")
        else:
            print(f"❌ Gagal MQTT, rc={rc}")

    mqttc.on_connect = on_connect
    try:
        mqttc.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqttc.loop_start()
    except Exception as e:
        print(f"❌ Gagal MQTT: {e}")

connect_mqtt()

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# =======================================================
# 4. ENDPOINTS API
# =======================================================
@app.route("/api/latest", methods=["GET"])
def get_latest_reading():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM gempa ORDER BY waktu DESC LIMIT 1")
        record = cursor.fetchone()

        if record:
            # isi kedalaman: pakai nilai DB kalau ada, kalau NULL pakai estimasi
            if record.get("kedalaman") is None:
                est_depth = estimate_depth_km(
                    record.get("magnitude_g"),
                    record.get("deviation")
                )
                record["kedalaman"] = str(est_depth)
            else:
                record["kedalaman"] = str(record.get("kedalaman"))

            # isi koordinat: pakai DB kalau ada, kalau NULL pakai posisi tetap sensor
            record["koordinat"] = record.get("koordinat") if record.get("koordinat") is not None else DEFAULT_COORD

            # tambahkan deskripsi inferensi
            descriptions = infer_descriptions(record)
            final_data = {**record, **descriptions}
            return jsonify(final_data)
        else:
            return jsonify({"message": "No data available"}), 404

    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route("/api/history", methods=["GET"])
def get_historical_readings():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                id,
                waktu,
                magnitude_g,
                deviation,
                status,
                kedalaman,
                koordinat
            FROM gempa
            ORDER BY waktu DESC
            LIMIT 100
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        cleaned = []
        for r in rows:
            mag = r.get("magnitude_g")
            dev = r.get("deviation")

            # kalau NULL → pakai estimasi + koordinat default
            if r.get("kedalaman") is None:
                r["kedalaman"] = estimate_depth_km(mag, dev)
            if r.get("koordinat") is None:
                r["koordinat"] = DEFAULT_COORD

            cleaned.append(r)
        return jsonify(cleaned)
    except Exception as e:
        print("HISTORY ERROR:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()
# ====== Statistik per jam / 2 jam ======
@app.route("/api/stats", methods=["GET"])
def get_stats():
    """
    Statistik gempa untuk window waktu tertentu.
    query param: window_h (jam), default 1 jam.
    """
    window_h = request.args.get("window_h", default=1, type=int)
    if window_h <= 0:
        window_h = 1

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                COUNT(*) AS total_event,
                SUM(status = 'WARNING') AS total_warning,
                SUM(status = 'ALERT')   AS total_alert,
                MAX(magnitude_g) AS max_magnitude,
                AVG(deviation)   AS avg_deviation
            FROM gempa
            WHERE waktu >= NOW() - INTERVAL %s HOUR
        """
        cursor.execute(query, (window_h,))
        stats = cursor.fetchone()
        # pastikan tidak None
        for k in stats:
            stats[k] = stats[k] if stats[k] is not None else 0
        stats["window_h"] = window_h
        return jsonify(stats)
    except Exception as e:
        print("STATS ERROR:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route("/api/aftershock", methods=["GET"])
def predict_aftershock():
    """
    Analisis sederhana potensi gempa susulan berdasarkan
    tren deviation dan frekuensi WARNING dalam 30 menit terakhir.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 30 menit terakhir
        query = """
            SELECT
                waktu,
                magnitude_g,
                deviation,
                status
            FROM gempa
            WHERE waktu >= NOW() - INTERVAL 30 MINUTE
            ORDER BY waktu ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            return jsonify({
                "level": "RENDAH",
                "pesan": "Belum ada data 30 menit terakhir.",
                "detail": {}
            })

        # hitung indikator
        total = len(rows)
        warning_count = sum(1 for r in rows if r.get("status") == "WARNING")
        alert_count   = sum(1 for r in rows if r.get("status") == "ALERT")
        max_dev = max(r.get("deviation") or 0 for r in rows)
        avg_dev = sum((r.get("deviation") or 0) for r in rows) / total

        # heuristik sederhana
        if warning_count >= 5 or max_dev >= 0.45:
            level = "TINGGI"
            pesan = "Aktivitas getaran cukup sering dan kuat. Potensi gempa susulan relatif tinggi, tetap waspada."
        elif warning_count >= 2 or alert_count >= 4 or avg_dev >= 0.20:
            level = "SEDANG"
            pesan = "Terjadi beberapa getaran signifikan. Potensi gempa susulan sedang."
        else:
            level = "RENDAH"
            pesan = "Aktivitas getaran relatif tenang. Potensi gempa susulan rendah."

        detail = {
            "total_event": total,
            "warning_count": warning_count,
            "alert_count": alert_count,
            "max_deviation": round(max_dev, 3),
            "avg_deviation": round(avg_dev, 3),
            "window_menit": 30
        }

        return jsonify({
            "level": level,
            "pesan": pesan,
            "detail": detail
        })
    except Exception as e:
        print("AFTERSHOCK ERROR:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route("/api/control", methods=["POST"])
def control_actuator():
    data = request.get_json(silent=True) or {}
    command = data.get("command")
    if not command:
        return jsonify({"status": "error", "message": "No command provided"}), 400

    try:
        mqttc.publish(MQTT_TOPIC_CONTROL, command)
        return jsonify({"status": "success", "message": f"Command {command} sent"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
