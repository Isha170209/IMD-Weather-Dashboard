console.log("App started ✅");

const API_BASE = "https://weather-dashboard-9dn4.onrender.com";

let extractedData = [];
let chartInstance = null;

// ================= DOM ELEMENTS =================
const paramEl = document.getElementById("param");
const latEl = document.getElementById("lat");
const lonEl = document.getElementById("lon");
const startDateEl = document.getElementById("startDate");
const endDateEl = document.getElementById("endDate");

const submitBtn = document.getElementById("submitBtn");
const resetBtn = document.getElementById("resetBtn");
const downloadBtn = document.getElementById("downloadBtn");

const dailyTable = document.getElementById("dailyTable");
const summaryTable = document.getElementById("summaryTable");

// ================= PAGE =================
window.openDashboard = function () {
    document.getElementById("homePage").style.display = "none";
    document.getElementById("dashboardPage").style.display = "block";
};

window.goHome = function () {
    document.getElementById("dashboardPage").style.display = "none";
    document.getElementById("homePage").style.display = "block";
};

// ================= INIT =================
window.addEventListener("DOMContentLoaded", () => {
    submitBtn.addEventListener("click", fetchData);
    resetBtn.addEventListener("click", resetForm);
    downloadBtn.addEventListener("click", downloadCSV);

    console.log("Buttons working ✅");
});

// ================= FETCH =================
async function fetchData() {

    const param = paramEl.value;
    const lat = parseFloat(latEl.value);
    const lon = parseFloat(lonEl.value);

    const start = startDateEl.value;
    const end = endDateEl.value;

    if (isNaN(lat) || isNaN(lon)) {
        alert("Enter valid lat/lon");
        return;
    }

    const url = `${API_BASE}/weather?param=${param}&lat=${lat}&lon=${lon}&start=${start}&end=${end}`;

    console.log("Calling API:", url);

    try {
        const res = await fetch(url);

        if (!res.ok) throw new Error("API error");

        const data = await res.json();

        console.log("API Response:", data);

        if (!Array.isArray(data) || data.length === 0) {
            alert("No data");
            return;
        }

        extractedData = data.map(d => ({
            date: d.date,
            value: d[param]
        }));

        renderChart(param);
        renderDailyTable(param);
        renderSummary(param);

    } catch (err) {
        console.error(err);
        alert("Error loading data");
    }
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
                label: getUnitLabel(param),
                data: extractedData.map(d => d.value),
                borderWidth: 2
            }]
        }
    });
}

// ================= DAILY TABLE =================
function renderDailyTable(param) {

    let html = `<table>
    <tr><th>Date</th><th>${getUnitLabel(param)}</th></tr>`;

    extractedData.forEach(r => {
        html += `<tr><td>${r.date}</td><td>${r.value}</td></tr>`;
    });

    html += "</table>";

    dailyTable.innerHTML = html;
}

// ================= SUMMARY =================
function renderSummary(param) {

    const values = extractedData.map(d => d.value);

    const avg = (values.reduce((a,b)=>a+b,0) / values.length).toFixed(2);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const sum = values.reduce((a,b)=>a+b,0);

    let html = `<table>
    <tr><th>Metric</th><th>${getUnitLabel(param)}</th></tr>
    <tr><td>Average</td><td>${avg}</td></tr>
    <tr><td>Max</td><td>${max}</td></tr>
    <tr><td>Min</td><td>${min}</td></tr>`;

    if (param === "rain") {
        html += `<tr><td>Total Rainfall</td><td>${sum}</td></tr>`;
    }

    html += "</table>";

    summaryTable.innerHTML = html;
}

// ================= UTIL =================
function getUnitLabel(param) {
    if (param === "rain") return "Rainfall (mm)";
    if (param === "tmin" || param === "tmax") return "Temperature (°C)";
}

// ================= CSV =================
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
    extractedData = [];

    if (chartInstance) chartInstance.destroy();

    dailyTable.innerHTML = "";
    summaryTable.innerHTML = "";

    latEl.value = "";
    lonEl.value = "";
    startDateEl.value = "";
    endDateEl.value = "";
}
