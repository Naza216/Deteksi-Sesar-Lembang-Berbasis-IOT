const API_BASE_URL = 'https://unclamped-unsublimated-tamie.ngrok-free.dev/ ';

// Inisialisasi Chart (Mengambil instance yang sudah dibuat di HTML)
// Note: Kode Chart sudah ada di HTML Anda, kita tinggal menggunakannya.

async function fetchData() {
    try {
        // 1. Ambil data terbaru
        const responseLatest = await fetch(`${API_BASE_URL}/api/latest`);
        const data = await responseLatest.json();

        if (data) {
            // Update Angka Magnitude
            document.getElementById('magnitude').innerText = data.magnitude_g.toFixed(4);
            
            // Update Status Sistem
            const statusElem = document.getElementById('statusTitle');
            statusElem.innerText = data.status;
            
            // Update Warna Status
            if (data.status === 'WARNING') {
                statusElem.style.color = '#ef4444'; // Merah (Danger)
            } else {
                statusElem.style.color = '#10b981'; // Hijau (Success)
            }

            // Update Deskripsi (Inference)
            document.getElementById('deskripsiKekuatan').innerText = getKekuatanDeskripsi(data.magnitude_g);
            document.getElementById('deskripsiPergerakan').innerText = data.magnitude_g > 1.1 ? "Getaran Terdeteksi" : "Stabil";
            
            // Update Waktu
            document.getElementById('time').innerText = "Terakhir diperbarui: " + new Date().toLocaleTimeString();

            // Update Chart
            updateChart(data.magnitude_g);
        }

    } catch (error) {
        console.error("Gagal mengambil data:", error);
        document.getElementById('statusTitle').innerText = "OFFLINE";
        document.getElementById('statusTitle').style.color = '#9ca3af';
    }
}

// Fungsi bantu deskripsi kekuatan
function getKekuatanDeskripsi(mag) {
    if (mag > 1.5) return "Sangat Kuat";
    if (mag > 1.2) return "Sedang";
    return "Lemah/Normal";
}

// Fungsi Update Chart
function updateChart(newValue) {
    const now = new Date().toLocaleTimeString();
    
    magnitudeChart.data.labels.push(now);
    magnitudeChart.data.datasets[0].data.push(newValue);

    // Batasi 15 data saja di grafik agar tidak penuh
    if (magnitudeChart.data.labels.length > 15) {
        magnitudeChart.data.labels.shift();
        magnitudeChart.data.datasets[0].data.shift();
    }
    
    magnitudeChart.update();
}

// --- FUNGSI KONTROL (PENTING) ---
async function sendControlCommand(command) {
    // Tambah konfirmasi jika tombol Shutdown ditekan
    if (command === 'SHUTDOWN') {
        if (!confirm("ESP32 akan mati total. Lanjutkan?")) return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/control`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command })
        });

        const result = await response.json();
        if (result.status === 'success') {
            console.log("Perintah berhasil dikirim:", command);
        } else {
            alert("Gagal kirim perintah: " + result.message);
        }
    } catch (error) {
        console.error("Error Kontrol:", error);
        alert("Gagal tersambung ke API Flask.");
    }
}

// Jalankan pengambilan data setiap 3 detik
setInterval(fetchData, 3000);
fetchData(); // Jalankan sekali saat start