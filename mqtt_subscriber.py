import paho.mqtt.client as mqtt
import mysql.connector
import json
import time

# =======================================================
# 1. KONFIGURASI MQTT
# =======================================================
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "/lembang/sensor/data"
CLIENT_ID = "Backend_DB_Subscriber"

# =======================================================
# 2. KONFIGURASI DATABASE (Sesuaikan dengan setup Anda)
# =======================================================
DB_HOST = "localhost"
DB_USER = "root"  
DB_PASSWORD = "root" 
DB_NAME = "iot_sesar" 

# Objek koneksi DB
mydb = None

# =======================================================
# FUNGSI DATABASE
# =======================================================

def connect_db():
    """Mencoba koneksi ke database."""
    global mydb
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("✅ Koneksi Database berhasil.")
        return mydb
    except mysql.connector.Error as err:
        print(f"❌ Error koneksi DB: {err}")
        time.sleep(5)
        return connect_db()

def insert_reading(data):
    """Memasukkan data JSON dari MQTT ke tabel 'gempa'."""
    global mydb
    if not mydb or not mydb.is_connected():
        print("Koneksi DB terputus, mencoba menyambung ulang...")
        mydb = connect_db()
        if not mydb:
            return

    cursor = mydb.cursor()
    
    # 1. LOGIKA PENGAMAN STATUS (Menghapus 'ALERT' dari data yang akan dimasukkan)
    # Jika status dari ESP32 adalah ALERT, ubah menjadi WARNING sebelum dimasukkan ke DB.
    # Ini memastikan DB hanya menerima NORMAL atau WARNING.
    input_status = data.get('status', 'NORMAL').upper()
    if input_status == "ALERT":
        final_status = "WARNING"
    else:
        final_status = input_status

    # 2. QUERY INSERT
    # Pastikan urutan kolom sesuai dengan tabel 'gempa' Anda!
    sql = """INSERT INTO gempa 
             (acx_g, acy_g, acz_g, magnitude_g, deviation, status, temperature)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    
    val = (
        data.get('AcX_g'),
        data.get('AcY_g'),
        data.get('AcZ_g'),
        data.get('magnitude_g'),
        data.get('deviation'),
        final_status, # Menggunakan status yang sudah difilter
        data.get('temperature', None)
    )
    
    try:
        cursor.execute(sql, val)
        mydb.commit()
        print(f"   [DB] Data berhasil disimpan. Status: {final_status}, Mag: {data.get('magnitude_g')}")
    except mysql.connector.Error as err:
        print(f"❌ Error saat INSERT data: {err}")
        mydb.rollback()
    finally:
        cursor.close()

# Callback saat pesan MQTT diterima
def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)
        print(f"\n[MQTT] Data diterima dari ESP32.")
        insert_reading(data)

    except json.JSONDecodeError:
        print(f"❌ Error: Payload bukan format JSON yang valid.")
    except Exception as e:
        print(f"❌ Error tak terduga: {e}")

# Inisialisasi dan jalankan client MQTT
def main_subscriber():
    connect_db()
    
    # Menggunakan VERSION1 untuk kompatibilitas callback API
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, CLIENT_ID) 
    client.on_connect = lambda c, u, f, rc: print(f"✅ Terhubung ke MQTT Broker dengan kode: {rc}") or c.subscribe(MQTT_TOPIC)
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ Gagal koneksi ke MQTT Broker: {e}")
        return

    client.loop_forever()

if __name__ == "__main__":
    main_subscriber()