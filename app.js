import init, { readParquet } from "https://cdn.jsdelivr.net/npm/parquet-wasm@latest/+esm";
window.addEventListener("DOMContentLoaded", () => {
    console.log("DOM Ready ✅");
});

await init();

console.log("JS Loaded ✅");

const username = "Isha170209";   // your github username
const repo = "Weather-Dashboard";

let extractedData = [];
let chartInstance = null;

// 🔷 MAP
let map = L.map('map').setView([22, 78], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

let markersLayer = L.layerGroup().addTo(map);

// 🔷 SIDEBAR
window.toggleSidebar = function () {
    document.getElementById("sidebar").classList.toggle("hidden");
};

// 🔷 SINGLE LOCATION
window.fetchData = async function () {

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

        try {
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

        } catch (e) {}
    }

    if (extractedData.length === 0) {
        status.innerText = "No data found";
        return;
    }

    extractedData.sort((a, b) => new Date(a.date) - new Date(b.date));

    status.innerText = `Loaded ${extractedData.length} records`;

    renderTable(extractedData);
    renderChart(extractedData);

    // map marker
    L.marker([lat, lon]).addTo(markersLayer)
        .bindPopup("Selected Location");
};

// 🔷 MULTI LOCATION
window.processCSV = async function () {

    const file = document.getElementById("csvFile").files[0];
    if (!file) {
        alert("Upload CSV");
        return;
    }

    const text = await file.text();
    const rows = text.split("\n").slice(1);

    const param = document.getElementById("param").value;
    const startDate = new Date(document.getElementById("startDate").value);
    const endDate = new Date(document.getElementById("endDate").value);

    let finalData = [];
    markersLayer.clearLayers();

    for (let row of rows) {

        const [name, latStr, lonStr] = row.split(",");
        const lat = parseFloat(latStr);
        const lon = parseFloat(lonStr);

        if (isNaN(lat) || isNaN(lon)) continue;

        let locData = [];

        for (let year = startDate.getFullYear(); year <= endDate.getFullYear(); year++) {

            const url = `https://raw.githubusercontent.com/${username}/${repo}/main/data/${param}/${year}_${param}.parquet`;

            try {
                const response = await fetch(url);
                if (!response.ok) continue;

                const buffer = await response.arrayBuffer();
                const table = readParquet(new Uint8Array(buffer));
                const data = table.toArray();

                const grouped = {};

                data.forEach(r => {

                    const d = new Date(r.date);
                    if (d < startDate || d > endDate) return;
                    if (r[param] === null || isNaN(r[param])) return;

                    const dist = Math.sqrt(
                        (r.lat - lat) ** 2 +
                        (r.lon - lon) ** 2
                    );

                    if (!grouped[r.date] || dist < grouped[r.date].dist) {
                        grouped[r.date] = {
                            date: r.date,
                            value: r[param],
                            dist: dist
                        };
                    }
                });

                Object.values(grouped).forEach(v => {
                    locData.push({
                        location: name,
                        date: v.date,
                        value: v.value
                    });
                });

            } catch (e) {}
        }

        finalData.push(...locData);

        L.marker([lat, lon]).addTo(markersLayer)
            .bindPopup(`<b>${name}</b>`);
    }

    renderTable(finalData);
};

// 🔷 TABLE
function renderTable(data) {

    let html = "<table><tr>";

    if (data[0].location) {
        html += "<th>Location</th>";
    }

    html += "<th>Date</th><th>Value</th></tr>";

    data.forEach(r => {
        html += "<tr>";
        if (r.location) html += `<td>${r.location}</td>`;
        html += `<td>${r.date}</td><td>${r.value}</td></tr>`;
    });

    html += "</table>";

    document.getElementById("table").innerHTML = html;
}

// 🔷 CHART
function renderChart(data) {

    const ctx = document.getElementById("chart");

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: "Value",
                data: data.map(d => d.value),
                borderWidth: 2
            }]
        }
    });
}

// 🔷 CSV
window.downloadCSV = function () {

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
};

// 🔷 RESET
window.resetForm = function () {

    document.getElementById("lat").value = "";
    document.getElementById("lon").value = "";
    document.getElementById("startDate").value = "";
    document.getElementById("endDate").value = "";

    document.getElementById("table").innerHTML = "";
    document.getElementById("status").innerText = "";

    if (chartInstance) chartInstance.destroy();

    markersLayer.clearLayers();

    extractedData = [];
};
document.getElementById("submitBtn").addEventListener("click", fetchData);
document.getElementById("resetBtn").addEventListener("click", resetForm);
document.getElementById("downloadBtn").addEventListener("click", downloadCSV);
document.getElementById("csvBtn").addEventListener("click", processCSV);
document.getElementById("toggleBtn").addEventListener("click", toggleSidebar);
