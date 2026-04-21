import init, { readParquet } from "https://cdn.jsdelivr.net/npm/parquet-wasm@latest/+esm";

await init();

const username = "Ishku170209";
const repo = "Weather-Dashboard";

let extractedData = [];

// 🔹 Resolution
function getResolution(param) {
    return param === "rain" ? 0.25 : 1.0;
}

// 🔹 Snap to nearest grid
function snap(val, res) {
    return Math.round(val / res) * res;
}

// 🔹 Get years
function getYears(start, end) {
    let years = [];
    for (let y = start; y <= end; y++) years.push(y);
    return years;
}

// 🔹 FETCH DATA
window.fetchData = async function () {

    const param = document.getElementById("param").value;
    const lat = parseFloat(document.getElementById("lat").value);
    const lon = parseFloat(document.getElementById("lon").value);

    const startDate = new Date(document.getElementById("startDate").value);
    const endDate = new Date(document.getElementById("endDate").value);

    const res = getResolution(param);

    const nearestLat = snap(lat, res);
    const nearestLon = snap(lon, res);

    const years = getYears(startDate.getFullYear(), endDate.getFullYear());

    extractedData = [];

    for (let year of years) {

        const url = `https://raw.githubusercontent.com/${username}/${repo}/main/data/${param}/${year}_${param}.parquet`;

        try {
            const response = await fetch(url);
            const buffer = await response.arrayBuffer();

            const table = readParquet(new Uint8Array(buffer));
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
                        lat: row.lat,
                        lon: row.lon,
                        value: row[param] ?? row.value
                    });
                }
            });

        } catch (err) {
            console.log("Missing year:", year);
        }
    }

    document.getElementById("output").innerText =
        JSON.stringify(extractedData.slice(0, 20), null, 2);
};

// 🔹 CSV DOWNLOAD
window.downloadCSV = function () {

    if (extractedData.length === 0) {
        alert("No data available");
        return;
    }

    let csv = "date,lat,lon,value\n";

    extractedData.forEach(r => {
        csv += `${r.date},${r.lat},${r.lon},${r.value}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "weather_data.csv";
    a.click();
};

// 🔹 RESET
window.resetForm = function () {
    document.getElementById("lat").value = "";
    document.getElementById("lon").value = "";
    document.getElementById("startDate").value = "";
    document.getElementById("endDate").value = "";
    document.getElementById("output").innerText = "";
    extractedData = [];
};
