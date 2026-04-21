import * as arrow from "https://cdn.jsdelivr.net/npm/apache-arrow@latest/+esm";

console.log("App started ✅");

const username = "Isha170209";
const repo = "Weather-Dashboard";

let extractedData = [];
let chartInstance = null;
let map;
let markersLayer;

// 🔷 INIT
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

// 🔷 FETCH DATA (PARQUET via Apache Arrow)
async function fetchData() {

    const status = document.getElementById("status");
    status.innerText = "Loading...";

    const param = document.getElementById("param").value;
    const lat = parseFloat(document.getElementById("lat").value);
    const lon = parseFloat(document.getElementById("lon").value);

    const startDate = new Date(document.getElementById("startDate").value);
    const endDate = new Date(document.getElementById("endDate").value);

    if (isNaN(lat) || isNaN(lon)) {
        alert("Enter valid lat/lon");
        return;
    }

    extractedData = [];
    markersLayer.clearLayers();

    for (let year = startDate.getFullYear(); year <= endDate.getFullYear(); year++) {

        const url = `https://raw.githubusercontent.com/${username}/${repo}/main/data/${param}/${year}_${param}.parquet`;

        console.log("Fetching:", url);

        try {
            const res = await fetch(url);

            if (!res.ok) {
                console.log("File not found:", url);
                continue;
            }

            const buffer = await res.arrayBuffer();

            // 🔥 Read parquet (Arrow-compatible)
            const table = await arrow.tableFromIPC(buffer);

            console.log("Rows:", table.numRows);

            const dateCol = table.getChild("date");
            const latCol = table.getChild("lat");
            const lonCol = table.getChild("lon");
            const valCol = table.getChild(param);

            const grouped = {};

            for (let i = 0; i < table.numRows; i++) {

                const date = dateCol.get(i);
                const lat2 = latCol.get(i);
                const lon2 = lonCol.get(i);
                const value = valCol.get(i);

                if (!date || value == null) continue;

                const d = new Date(date);
                if (d < startDate || d > endDate) continue;

                const dist = Math.sqrt(
                    (lat2 - lat) ** 2 +
                    (lon2 - lon) ** 2
                );

                if (!grouped[date] || dist < grouped[date].dist) {
                    grouped[date] = {
                        date,
                        value,
                        dist
                    };
                }
            }

            Object.values(grouped).forEach(v => extractedData.push(v));

        } catch (err) {
            console.error("Error reading:", url, err);
        }
    }

    if (extractedData.length === 0) {
        status.innerText = "No data found";
        return;
    }

    extractedData.sort((a, b) => new Date(a.date) - new Date(b.date));

    status.innerText = `Loaded ${extractedData.length} records`;

    renderTable();
    renderChart();

    L.marker([lat, lon]).addTo(markersLayer);
}

// 🔷 TABLE
function renderTable() {

    let html = "<table><tr><th>Date</th><th>Value</th></tr>";

    extractedData.forEach(r => {
        html += `<tr><td>${r.date}</td><td>${r.value}</td></tr>`;
    });

    html += "</table>";

    document.getElementById("table").innerHTML = html;
}

// 🔷 CHART
function renderChart() {

    const ctx = document.getElementById("chart");

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: extractedData.map(d => d.date),
            datasets: [{
                label: "Value",
                data: extractedData.map(d => d.value),
                borderWidth: 2
            }]
        }
    });
}

// 🔷 CSV DOWNLOAD
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

// 🔷 RESET
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
