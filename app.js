import init, { readParquet } from "https://cdn.jsdelivr.net/npm/parquet-wasm@latest/+esm";

console.log("Script starting...");

// GLOBALS
const username = "Isha170209";
const repo = "Weather-Dashboard";

let extractedData = [];
let chartInstance = null;
let map;
let markersLayer;

// 🔷 INIT APP
async function initApp() {

    try {
        console.log("Initializing parquet...");
        await init();
        console.log("Parquet initialized ✅");

        // 🔷 MAP INIT
        map = L.map('map').setView([22, 78], 5);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        markersLayer = L.layerGroup().addTo(map);

        // 🔷 BUTTON EVENTS
        document.getElementById("submitBtn").addEventListener("click", fetchData);
        document.getElementById("resetBtn").addEventListener("click", resetForm);
        document.getElementById("downloadBtn").addEventListener("click", downloadCSV);

        console.log("Buttons connected ✅");

    } catch (err) {
        console.error("INIT ERROR ❌", err);
    }
}

// 🔷 FETCH DATA
async function fetchData() {

    try {
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

            const response = await fetch(url);
            if (!response.ok) continue;

            const buffer = await response.arrayBuffer();
            const table = readParquet(new Uint8Array(buffer));
            const data = table.toArray();

            const grouped = {};

            data.forEach(row => {

                const d = new Date(row.date);
                if (d < startDate || d > endDate) return;
                if (row[param] === null || isNaN(row[param])) return;

                const dist = Math.sqrt(
                    (row.lat - lat) ** 2 +
                    (row.lon - lon) ** 2
                );

                if (!grouped[row.date] || dist < grouped[row.date].dist) {
                    grouped[row.date] = {
                        date: row.date,
                        value: row[param],
                        dist: dist
                    };
                }
            });

            Object.values(grouped).forEach(v => extractedData.push(v));
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

    } catch (err) {
        console.error("FETCH ERROR ❌", err);
    }
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

// 🔷 CSV
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

// 🔷 START APP
window.addEventListener("DOMContentLoaded", initApp);
