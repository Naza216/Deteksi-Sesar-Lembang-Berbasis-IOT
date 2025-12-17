from flask import Flask, jsonify
from flask import request, jsonify
from flask_cors import CORS
import mysql.connector
import paho.mqtt.client as mqtt_client
from datetime import datetime, timedelta
import time # Diperlukan untuk fungsi reconnect DB

# =======================================================
# 1. KONFIGURASI FLASK & CORS
# =======================================================
app = Flask(__name__)
CORS(app) # Mengizinkan frontend di domain lain untuk mengakses API ini

# =======================================================
# 2. KONFIGURASI DATABASE & MQTT
# =======================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': 'root', 
    'database': 'iot_sesar' 
}

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_CONTROL = "/lembang/control/actuator"
CLIENT_ID_PUBLISHER = "Frontend_API_Publisher"

# =======================================================
# 3. FUNGSI INFERENSI (Menambahkan Deskripsi Deskriptif)
# =======================================================

def infer_descriptions(reading):
    """Menambahkan deskripsi inferensi berdasarkan data percepatan (g)."""
    if reading is None:
        return {}

    deviation = reading.get('deviation', 0.0)
    acx = reading.get('acx_g', 0.0)
    acy = reading.get('acy_g', 0.0)
    acz = reading.get('acz_g', 0.0)
    
    # --- Penentuan Status Akhir (Hanya NORMAL atau WARNING) ---
    status_db = "NORMAL"
    if deviation >= 0.15:
        status_db = "WARNING"
        
    # --- 1. Kekuatan Goncangan (Deskriptif) ---
    if deviation >= 0.40:
        kekuatan = "Goncangan Keras (Kuat dan Jelas Terasa, Berpotensi merusak)."
    elif deviation >= 0.15:
        kekuatan = "Goncangan Sedang (Terasa, perabotan bergetar, perlu waspada)."
    else:
        kekuatan = "Goncangan Lemah (Tidak terasa atau sangat halus, kondisi aman)."

    # --- 2. Kedalaman (Inferensi Kualitatif dari Kualitas Getaran) ---
    if deviation > 0.35:
        kedalaman = "Diduga Dangkal (Dekat dengan lokasi sensor, reaksi cepat diperlukan)."
    else:
        kedalaman = "Diduga Sedang/Jauh (Dampak melemah, mungkin lokasi jauh atau kedalaman besar)."

    # --- 3. Jenis Pergerakan (Inferensi dari Rasio Sumbu) ---
    horizontal_component = abs(acx) + abs(acy)
    vertical_component = abs(acz - 1.0) 
    
    if horizontal_component > (vertical_component * 1.5) and deviation > 0.1:
        pergerakan = "Dominan Horizontal (Sesar Geser/Mendatar terdeteksi)."
    else:
        pergerakan = "Dominan Vertikal (Sesar Naik/Turun atau Guncangan Jarak Jauh terdeteksi)."

    reading['status'] = status_db
    
    return {
        "kekuatan_goncangan": kekuatan,
        "kedalaman_inferensi": kedalaman,
        "jenis_pergerakan": pergerakan
    }

# =======================================================
# 4. FUNGSI KONEKSI UTILITAS
# =======================================================

# Inisialisasi MQTT Publisher Client
mqttc = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, CLIENT_ID_PUBLISHER)

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ API MQTT Publisher terhubung.")
        else:
            print(f"❌ API MQTT Publisher gagal terhubung, kode {rc}. Mencoba lagi...")
            time.sleep(5)
            # Tidak perlu auto-reconnect di sini, loop_start sudah menangani
    
    mqttc.on_connect = on_connect
    try:
        mqttc.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqttc.loop_start() # Jalankan loop di background thread
    except Exception as e:
        print(f"❌ Gagal koneksi MQTT Publisher awal: {e}")
        
connect_mqtt()

def get_db_connection():
    """Membuat koneksi DB baru. Melakukan retry jika gagal."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except mysql.connector.Error as err:
            print(f"DB Connection Error (Attempt {attempt+1}/{max_retries}): {err}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise # Lempar error setelah semua retry gagal

# =======================================================
# 5. ENDPOINTS API (MODIFIKASI)
# =======================================================

@app.route('/api/latest', methods=['GET'])
def get_latest_reading():
    """Mengambil record dengan status terparah dalam 5 detik terakhir (dengan retry koneksi)."""
    conn = None
    try:
        conn = get_db_connection() # Menggunakan fungsi retry
        cursor = conn.cursor(dictionary=True)
        
        # 1. Query untuk mengambil record terparah (deviation terbesar) dalam 5 detik terakhir.
        query = """
        SELECT * FROM gempa 
        WHERE waktu >= DATE_SUB(NOW(), INTERVAL 5 SECOND)
        ORDER BY deviation DESC, waktu DESC
        LIMIT 1
        """
        cursor.execute(query)
        record = cursor.fetchone()
        
        # 2. Jika tidak ada record dalam 5 detik, ambil record terakhir yang ada.
        if not record:
            cursor.execute("SELECT * FROM gempa ORDER BY waktu DESC LIMIT 1")
            record = cursor.fetchone()

        # 3. Tambahkan deskripsi inferensi sebelum dikirim
        if record:
            descriptions = infer_descriptions(record) 
            final_data = {**record, **descriptions}
            return jsonify(final_data)
        else:
            return jsonify({"message": "No data available"}), 404
            
    except mysql.connector.Error as err:
        print(f"DB Error: {err}")
        return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/control', methods=['POST'])
def control_actuator():
    """
    Mengontrol aktuator atau mematikan ESP32.
    Perintah yang diterima: TEST_ON, TEST_OFF, SHUTDOWN.
    """
    data = request.json
    command = data.get('command', '').upper()
    
    # Tambahkan perintah SHUTDOWN ke list valid
    VALID_COMMANDS = ["TEST_ON", "TEST_OFF", "SHUTDOWN"]

    if command in VALID_COMMANDS:
        if mqttc.is_connected():
            # Terbitkan perintah ke topik yang di-subscribe oleh ESP32
            result = mqttc.publish(MQTT_TOPIC_CONTROL, command)
            
            if result[0] == mqtt_client.MQTT_ERR_SUCCESS:
                print(f"[MQTT PUB] Perintah '{command}' berhasil dikirim ke {MQTT_TOPIC_CONTROL}")
                
                # Respon khusus untuk SHUTDOWN
                if command == "SHUTDOWN":
                    message = "Perintah SHUTDOWN (Deep Sleep) berhasil dikirim. Sensor akan mati total."
                else:
                    message = f"Perintah {command} dikirim."
                    
                return jsonify({"status": "SUCCESS", "message": message}), 200
            else:
                return jsonify({"status": "ERROR", "message": "Gagal menerbitkan pesan MQTT."}), 500
        else:
            print("❌ API Publisher tidak terhubung ke MQTT Broker.")
            return jsonify({"status": "ERROR", "message": "API Publisher offline. Cek koneksi internet/broker."}), 503
    else:
        return jsonify({"status": "ERROR", "message": "Perintah tidak valid."}), 400
    
@app.route('/api/history', methods=['GET'])
def get_historical_readings():
    """Mengembalikan 100 record historis untuk grafik."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, waktu, magnitude_g, deviation, status FROM gempa ORDER BY waktu DESC LIMIT 100"
        cursor.execute(query)
        records = cursor.fetchall()
        
        return jsonify(records)
            
    except mysql.connector.Error as err:
        print(f"DB Error: {err}")
        return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    # Jalankan server API di port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)