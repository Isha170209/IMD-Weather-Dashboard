console.log("App started ✅");

const API_BASE = "https://weather-dashboard-9dn4.onrender.com";

let extractedData = [];
let chartInstance = null;
let map;
let markersLayer;

// ================= PAGE NAVIGATION =================
window.openDashboard = function () {
    document.getElementById("homePage").style.display = "none";
    document.getElementById("dashboardPage").style.display = "block";

    setTimeout(() => {
        map.invalidateSize();
    }, 200);
};

window.goHome = function () {
    document.getElementById("dashboardPage").style.display = "none";
    document.getElementById("homePage").style.display = "block";
};

// ================= INIT =================
window.addEventListener("DOMContentLoaded", () => {

    map = L.map('map').setView([22, 78], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);

    document.getElementById("submitBtn").addEventListener("click", fetchData);
    document.getElementById("resetBtn").addEventListener("click", resetForm);
    document.getElementById("downloadBtn").addEventListener("click", downloadCSV);

    console.log("Buttons working ✅");
});

// ================= FETCH =================
async function fetchData() {

    const status = document.getElementById("status");
    status.innerText = "Loading...";

    const param = document.getElementById("param").value;
    const lat = parseFloat(document.getElementById("lat").value);
    const lon = parseFloat(document.getElementById("lon").value);

    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;

    const monthly = document.getElementById("monthlyToggle").checked;

    if (isNaN(lat) || isNaN(lon)) {
        alert("Enter valid lat/lon");
        return;
    }

    try {

        const url = `${API_BASE}/weather?param=${param}&lat=${lat}&lon=${lon}&start=${startDate}&end=${endDate}&monthly=${monthly}`;

        console.log("Calling API:", url);

        const res = await fetch(url);

        if (!res.ok) throw new Error("API error");

        const data = await res.json();

        console.log("API Response:", data);

        if (!Array.isArray(data) || data.length === 0) {
            status.innerText = "No data found";
            return;
        }

        extractedData = data.map(d => ({
            date: d.date,
            value: d[param]
        }));

        status.innerText = `Loaded ${extractedData.length} records`;

        renderTable();
        renderChart(param);

        markersLayer.clearLayers();
        L.marker([lat, lon]).addTo(markersLayer);

    } catch (err) {
        console.error(err);
        status.innerText = "Error loading data";
    }
}

// ================= TABLE =================
function renderTable() {

    let html = "<table><tr><th>Date</th><th>Value</th></tr>";

    extractedData.forEach(r => {
        html += `<tr><td>${r.date}</td><td>${r.value}</td></tr>`;
    });

    html += "</table>";

    document.getElementById("table").innerHTML = html;
}

// ================= CHART =================
function renderChart(param) {

    const ctx = document.getElementById("chart");

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: extractedData.map(d => d.date),
            datasets: [{
                label: param.toUpperCase(),
                data: extractedData.map(d => d.value),
                borderWidth: 2
            }]
        }
    });
}

// ================= DOWNLOAD =================
function downloadCSV() {

    if (extractedData.length === 0) {
        alert("No data");
        return;
    }

    let csv = "date,value\n";

    extractedData.forEach(r => {
        csv += `${r.date},${r.value}\n`;
    });

    const blob = new Blob([csv]);
    const a = document.createElement("a");

    a.href = URL.createObjectURL(blob);
    a.download = "weather.csv";
    a.click();
}

// ================= RESET =================
function resetForm() {

    document.getElementById("lat").value = "";
    document.getElementById("lon").value = "";
    document.getElementById("startDate").value = "";
    document.getElementById("endDate").value = "";

    document.getElementById("table").innerHTML = "";
    document.getElementById("status").innerText = "";

    if (chartInstance) chartInstance.destroy();

    markersLayer.clearLayers();
    extractedData = [];
}
