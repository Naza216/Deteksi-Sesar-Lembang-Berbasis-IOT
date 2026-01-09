const API_BASE_URL = "http://localhost:5000";

// ---- CHART MAGNITUDE & DEVIATION (REALTIME) ----
const ctx = document.getElementById("magnitudeChart").getContext("2d");
const magnitudeChart = new Chart(ctx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Magnitude (g)",
        data: [],
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59,130,246,0.3)",
        tension: 0.25,
        pointRadius: 2,
        yAxisID: "y",
      },
      {
        label: "Deviation |g - 1|",
        data: [],
        borderColor: "#f97316",
        backgroundColor: "rgba(249,115,22,0.25)",
        tension: 0.25,
        pointRadius: 2,
        yAxisID: "y1",
      },
    ],
  },
  options: {
    plugins: {
      legend: {
        labels: { usePointStyle: true, boxWidth: 10 },
      },
    },
    scales: {
      x: { display: true },
      y: {
        position: "left",
        beginAtZero: false,
        min: 0.6,
        max: 1.4,
        grid: { color: "rgba(55,65,81,0.6)" },
      },
      y1: {
        position: "right",
        beginAtZero: true,
        min: 0.0,
        max: 0.6,
        grid: { drawOnChartArea: false },
        ticks: { color: "#f97316" },
      },
    },
  },
});

// ---- CHART DISTRIBUSI STATUS & DEVIASI (DARI HISTORY) ----
const statusCtx = document.getElementById("statusBarChart")?.getContext("2d");
const deviationCtx = document.getElementById("deviationChart")?.getContext("2d");

let statusBarChart = null;
let deviationChart = null;

if (statusCtx) {
  statusBarChart = new Chart(statusCtx, {
    type: "bar",
    data: {
      labels: ["NORMAL", "WARNING", "ALERT"],
      datasets: [
        {
          label: "Jumlah kejadian (1 jam)",
          data: [0, 0, 0],
          backgroundColor: ["#22c55e", "#fb923c", "#f97373"],
          borderRadius: 6,
          maxBarThickness: 40,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(55,65,81,0.6)" },
          ticks: { precision: 0 },
        },
      },
    },
  });
}

if (deviationCtx) {
  deviationChart = new Chart(deviationCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "|g - 1|",
          data: [],
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56,189,248,0.25)",
          tension: 0.25,
          pointRadius: 2,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: {
          display: true,
          grid: { color: "rgba(31,41,55,0.6)" },
        },
        y: {
          beginAtZero: true,
          max: 0.6,
          grid: { color: "rgba(55,65,81,0.6)" },
        },
      },
    },
  });
}

// ---- PETA SIMULASI LOKASI SENSOR (ITENAS) ----
let map = L.map("map", { zoomControl: false }).setView(
  [-6.9033, 107.6425],
  16
); // ITENAS Bandung

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

let espMarker = L.circleMarker([-6.9033, 107.6425], {
  radius: 10,
  color: "#3b82f6",
  weight: 2,
  fillColor: "#22c55e",
  fillOpacity: 0.9,
}).addTo(map);

espMarker.bindPopup(
  "<b>Sensor Gempa - ITENAS</b><br>Simulasi lokasi pemasangan."
);

// ---- FUNGSI AMBIL DATA TERBARU (REALTIME) ----
async function fetchData() {
  try {
    const responseLatest = await fetch(`${API_BASE_URL}/api/latest`, {
      headers: { "ngrok-skip-browser-warning": "true" },
    });

    if (!responseLatest.ok) {
      throw new Error(`HTTP error! status: ${responseLatest.status}`);
    }

    const data = await responseLatest.json();

    if (data) {
      const mag = data.magnitude_g || 0;
      const dev = data.deviation || 0;

      document.getElementById("magnitude").innerText = mag.toFixed(4);

      const statusElem = document.getElementById("statusTitle");
      statusElem.innerText = data.status || "NORMAL";

      const statusCard = statusElem.parentElement.parentElement;
      if (data.status === "WARNING") {
        statusElem.style.color = "#ef4444";
        statusCard.style.borderColor = "#ef4444";
      } else if (data.status === "ALERT") {
        statusElem.style.color = "#f97316";
        statusCard.style.borderColor = "#f97316";
      } else {
        statusElem.style.color = "#10b981";
        statusCard.style.borderColor = "#374151";
      }

      document.getElementById("kedalaman").innerText = `${
        data.kedalaman || "0"
      } km`;
      document.getElementById("koordinat").innerText =
        data.koordinat || "-";

      document.getElementById("deskripsiKekuatan").innerText =
        data.kekuatan_goncangan || getKekuatanDeskripsi(mag);
      document.getElementById("deskripsiPergerakan").innerText =
        data.jenis_pergerakan || (mag > 1.1 ? "Getaran Terdeteksi" : "Stabil");

      document.getElementById("time").innerText =
        "Terakhir diperbarui: " +
        (data.waktu || new Date().toLocaleTimeString());

      const connBadge = document.getElementById("conn-badge");
      connBadge.style.color = "#10b981";
      connBadge.style.background = "rgba(16, 185, 129, 0.1)";
      connBadge.innerHTML =
        '<i class="fas fa-circle" style="font-size:8px;"></i> Connected';

      // update grafik realtime
      updateChart(mag, dev);
    }
  } catch (error) {
    console.error("Gagal mengambil data:", error);
    const statusElem = document.getElementById("statusTitle");
    statusElem.innerText = "OFFLINE";
    statusElem.style.color = "#9ca3af";

    const connBadge = document.getElementById("conn-badge");
    connBadge.style.color = "#ef4444";
    connBadge.style.background = "rgba(239, 68, 68, 0.1)";
    connBadge.innerHTML =
      '<i class="fas fa-circle" style="font-size:8px;"></i> Disconnected';
  }
}

// ---- DESKRIPSI KEKUATAN (CADANGAN) ----
function getKekuatanDeskripsi(mag) {
  if (mag > 1.5) return "Sangat Kuat";
  if (mag > 1.2) return "Sedang";
  return "Lemah/Normal";
}

// ---- UPDATE CHART REALTIME ----
function updateChart(magValue, devValue) {
  const now = new Date().toLocaleTimeString();

  magnitudeChart.data.labels.push(now);
  magnitudeChart.data.datasets[0].data.push(magValue);
  magnitudeChart.data.datasets[1].data.push(devValue || 0);

  if (magnitudeChart.data.labels.length > 30) {
    magnitudeChart.data.labels.shift();
    magnitudeChart.data.datasets[0].data.shift();
    magnitudeChart.data.datasets[1].data.shift();
  }

  magnitudeChart.update();
}

// ---- FUNGSI KONTROL ESP32 ----
async function sendControlCommand(command) {
  if (command === "SHUTDOWN") {
    if (!confirm("ESP32 akan mati total. Lanjutkan?")) return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: command }),
    });

    const result = await response.json();
    if (result.status === "success") {
      console.log("Perintah berhasil dikirim:", command);
    } else {
      alert("Gagal kirim perintah: " + result.message);
    }
  } catch (error) {
    console.error("Error Kontrol:", error);
    alert("Gagal tersambung ke API Flask.");
  }
}

// ---- LOAD EVENTS (RIWAYAT) + UPDATE 2 CHART ANALISIS ----
async function loadEvents() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/history`);
    if (!res.ok) throw new Error(res.status);
    const rows = await res.json();

    const container = document.getElementById("eventsContainer");
    container.innerHTML = rows
      .map(
        (r) => `
      <tr>
        <td>${r.waktu}</td>
        <td>${r.magnitude_g.toFixed(3)}</td>
        <td>${r.deviation.toFixed(3)}</td>
        <td style="color:${
          r.status === "WARNING"
            ? "#ef4444"
            : r.status === "ALERT"
            ? "#f97316"
            : "#10b981"
        };">
          ${r.status}
        </td>
        <td>${r.kedalaman || "0"} km</td>
        <td>${r.koordinat || "-"}</td>
      </tr>
    `
      )
      .join("");

    // update chart distribusi status
    if (statusBarChart) {
      let normal = 0,
        warning = 0,
        alert = 0;
      rows.forEach((r) => {
        if (r.status === "WARNING") warning++;
        else if (r.status === "ALERT") alert++;
        else normal++;
      });
      statusBarChart.data.datasets[0].data = [normal, warning, alert];
      statusBarChart.update();
    }

    // update chart deviation |g - 1|
    if (deviationChart) {
      const labels = rows.map((r) =>
        r.waktu ? r.waktu.split(" ")[1] : ""
      );
      const deviations = rows.map((r) => r.deviation);

      deviationChart.data.labels = labels.slice(-30);
      deviationChart.data.datasets[0].data = deviations.slice(-30);
      deviationChart.update();
    }
  } catch (e) {
    console.error(e);
  }
}

// ---- NAVIGASI TAB (Overview / Events / Maps) ----
const navItems = document.querySelectorAll(".nav-item");
const overviewSection = document.getElementById("overviewSection");
const eventsSection = document.getElementById("eventsSection");
const mapsSection = document.getElementById("mapsSection");

navItems.forEach((item, index) => {
  item.addEventListener("click", () => {
    navItems.forEach((n) => n.classList.remove("active"));
    item.classList.add("active");

    overviewSection.style.display = index === 0 ? "block" : "none";
    eventsSection.style.display = index === 1 ? "block" : "none";
    mapsSection.style.display = index === 2 ? "block" : "none";

    if (index === 1) {
      loadEvents();
    }

    if (index === 2) {
      setTimeout(() => {
        map.invalidateSize();
      }, 100);
    }
  });
});

// ---- PREDIKSI GEMPA SUSULAN ----
async function fetchAftershockPrediction() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/aftershock`);
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();

    const levelElem = document.getElementById("aftershockLevel");
    const textElem = document.getElementById("aftershockText");
    const box = document.getElementById("aftershockBox");

    const level = data.level || "RENDAH";
    levelElem.innerText = level;
    textElem.innerText = data.pesan || "";

    if (level === "TINGGI") {
      box.style.borderLeftColor = "#ef4444";
      levelElem.style.color = "#ef4444";
    } else if (level === "SEDANG") {
      box.style.borderLeftColor = "#f97316";
      levelElem.style.color = "#f97316";
    } else {
      box.style.borderLeftColor = "#10b981";
      levelElem.style.color = "#10b981";
    }
  } catch (e) {
    console.error("Aftershock error:", e);
  }
}

// ---- AUTO REFRESH ----
setInterval(fetchData, 3000);
fetchData();
