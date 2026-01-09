const mqtt = require('mqtt');
const mysql = require('mysql');

const db = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'root',
    database: 'iot_sesar'
});

const client = mqtt.connect('mqtt://broker.emqx.io');

client.on('connect', () => {
    client.subscribe('/lembang/sensor/data');
    console.log("✅ Terhubung ke MQTT & Database");
});

client.on('message', (topic, message) => {
    const data = JSON.parse(message.toString());
    const query = "INSERT INTO gempa (sensor_id, magnitude_g, status, waktu) VALUES (?, ?, ?, NOW())";
    db.query(query, [data.sensor_id, data.magnitude_g, data.status], (err) => {
        if (err) console.error(err);
        else console.log("Data tersimpan dari: " + data.sensor_id);
    });
});