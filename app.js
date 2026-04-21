import init, { readParquet } from "https://cdn.jsdelivr.net/npm/parquet-wasm@latest/+esm";

await init();

console.log("JS Loaded ✅");

const username = "Isha170209";   // 🔴 CHANGE THIS
const repo = "Weather-Dashboard";

let extractedData = [];
let chartInstance = null;

// 🔷 Sidebar toggle
window.toggleSidebar = function () {
    document.getElementById("sidebar").classList.toggle("hidden");
};

// 🔷 MAIN FUNCTION
window.fetchData = async function () {

    const status = document.getElementById("status");
    status.innerText = "Loading...";

    const param = document.getElementById("param").value;
    const lat = parseFloat(document.getElementById("lat").value);
    const lon = parseFloat(document.getElementById("lon").value);

    const startDate = new Date(document.getElementById("startDate").value);
    const endDate = new Date(document.getElementById("endDate").value);

    if (isNaN(lat) || isNaN(lon)) {
        alert("Enter valid latitude/longitude");
        return;
    }

    extractedData = [];

    // Loop through years
    for (let year = startDate.getFullYear(); year <= endDate.getFullYear(); year++) {

        const url = `https://raw.githubusercontent.com/${username}/${repo}/main/data/${param}/${year}_${param}.parquet`;

        console.log("Loading:", url);

        try {
            const response = await fetch(url);
            if (!response.ok) continue;

            const buffer = await response.arrayBuffer();
            const table = readParquet(new Uint8Array(buffer));
            const data = table.toArray();

            // 🔷 NEAREST NEIGHBOUR PER DATE
            const grouped = {};

            data.forEach(row => {

                const d = new Date(row.date);

                // Date filter
                if (d < startDate || d > endDate) return;

                // Skip NaN
                if (row[param] === null || isNaN(row[param])) return;

                const key = row.date;

                const dist = Math.sqrt(
                    Math.pow(row.lat - lat, 2) +
                    Math.pow(row.lon - lon, 2)
                );

                if (!grouped[key] || dist < grouped[key].dist) {
                    grouped[key] = {
                        dist: dist,
                        date: row.date,
                        value: row[param]
                    };
                }
            });

            // Push to final array
            Object.values(grouped).forEach(r => {
                extractedData.push({
                    date: r.date,
                    value: r.value
                });
            });

        } catch (err) {
            console.log("Error loading year:", year, err);
        }
    }

    if (extractedData.length === 0) {
        status.innerText = "No data found (check location/date)";
        return;
    }

    // Sort by date
    extractedData.sort((a, b) => new Date(a.date) - new Date(b.date));

    status.innerText = `Data Loaded (${extractedData.length} records)`;

    renderTable();
    renderChart();
};

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
window.downloadCSV = function () {

    if (extractedData.length === 0) {
        alert("No data to download");
        return;
    }

    let csv = "date,value\n";

    extractedData.forEach(r => {
        csv += `${r.date},${r.value}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv" });

    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "weather_data.csv";
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

    extractedData = [];
};
