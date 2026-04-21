console.log("JS Loaded ✅");
let extractedData = [];
let chartInstance = null;

const username = "Ishku170209";
const repo = "Weather-Dashboard";

// 🔷 Load parquet dynamically
async function loadParquet(url) {
    const response = await fetch(url);
    const buffer = await response.arrayBuffer();

    const parquet = await import("https://cdn.jsdelivr.net/npm/parquet-wasm@latest/+esm");

    await parquet.default();
    return parquet.readParquet(new Uint8Array(buffer));
}

// 🔷 Sidebar toggle
function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("hidden");
}
window.toggleSidebar = toggleSidebar;

// 🔷 Resolution
function getResolution(param) {
    return param === "rain" ? 0.25 : 1.0;
}

// 🔷 Snap
function snap(val, res) {
    return Math.round(val / res) * res;
}

// 🔷 Fetch Data
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

    const res = getResolution(param);
    const nearestLat = snap(lat, res);
    const nearestLon = snap(lon, res);

    extractedData = [];

    const years = [];
    for (let y = startDate.getFullYear(); y <= endDate.getFullYear(); y++) {
        years.push(y);
    }

    for (let year of years) {

        const url = `https://raw.githubusercontent.com/${username}/${repo}/main/data/${param}/${year}_${param}.parquet`;

        try {
            const table = await loadParquet(url);
            const data = table.toArray();

            data.forEach(row => {
                const d = new Date(row.date);

                if (
                    d >= startDate &&
                    d <= endDate &&
                    Math.abs(row.lat - nearestLat) < 0.001 &&
                    Math.abs(row.lon - nearestLon) < 0.001
                ) {
                    extractedData.push({
                        date: row.date,
                        value: row[param]
                    });
                }
            });

        } catch (e) {
            console.log("Error:", e);
        }
    }

    if (extractedData.length === 0) {
        status.innerText = "No data found";
        return;
    }

    extractedData.sort((a, b) => new Date(a.date) - new Date(b.date));

    status.innerText = "Data Loaded";

    renderTable();
    renderChart();
}
window.fetchData = fetchData;

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

    const ctx = document.getElementById("chart").getContext("2d");

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
}
window.downloadCSV = downloadCSV;

// 🔷 RESET
function resetForm() {

    document.getElementById("lat").value = "";
    document.getElementById("lon").value = "";
    document.getElementById("startDate").value = "";
    document.getElementById("endDate").value = "";

    document.getElementById("table").innerHTML = "";
    document.getElementById("status").innerText = "";

    if (chartInstance) chartInstance.destroy();

    extractedData = [];
}
window.resetForm = resetForm;
