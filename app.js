import init, { readParquet } from "https://cdn.jsdelivr.net/npm/parquet-wasm@latest/+esm";

await init();

// 🔴 UPDATE THIS
const username = "YOUR_USERNAME";
const repo = "Weather-Dashboard";

let extractedData = [];

// 🔷 Resolution (same as your Streamlit logic)
function getResolution(param) {
    return param === "rain" ? 0.25 : 1.0;
}

// 🔷 Snap to nearest grid (replaces KDTree)
function snap(value, resolution) {
    return Math.round(value / resolution) * resolution;
}

// 🔷 Get years from date range
function getYears(start, end) {
    let years = [];
    for (let y = start; y <= end; y++) years.push(y);
    return years;
}

// 🔷 MAIN FUNCTION
window.fetchData = async function () {

    const param = document.getElementById("param").value;
    const lat = parseFloat(document.getElementById("lat").value);
    const lon = parseFloat(document.getElementById("lon").value);

    const startDate = new Date(document.getElementById("startDate").value);
    const endDate = new Date(document.getElementById("endDate").value);

    // 🔴 Validation
    if (isNaN(lat) || isNaN(lon)) {
        alert("Please enter valid latitude and longitude");
        return;
    }

    if (!document.getElementById("startDate").value || !document.getElementById("endDate").value) {
        alert("Please select start and end dates");
        return;
    }

    if (startDate > endDate) {
        alert("Start date cannot be after end date");
        return;
    }

    const resolution = getResolution(param);

    const nearestLat = snap(lat, resolution);
    const nearestLon = snap(lon, resolution);

    const years = getYears(startDate.getFullYear(), endDate.getFullYear());

    extractedData = [];

    document.getElementById("output").innerText = "Loading data...";

    for (let year of years) {

        const url = `https://raw.githubusercontent.com/${username}/${repo}/main/data/${param}/${year}_${param}.parquet`;

        try {
            const response = await fetch(url);

            if (!response.ok) {
                console.log(`Skipping ${year} (file not found)`);
                continue;
            }

            const buffer = await response.arrayBuffer();

            const table = readParquet(new Uint8Array(buffer));
            const data = table.toArray();

            data.forEach(row => {

                const rowDate = new Date(row.date);

                if (
                    rowDate >= startDate &&
                    rowDate <= endDate &&
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
            console.log(`Error loading ${year}:`, err.message);
        }
    }

    if (extractedData.length === 0) {
        document.getElementById("output").innerText = "No data found for selected inputs.";
        return;
    }

    // 🔷 Sort by date (important for time series)
    extractedData.sort((a, b) => new Date(a.date) - new Date(b.date));

    document.getElementById("output").innerText =
        JSON.stringify(extractedData.slice(0, 20), null, 2);
};

// 🔷 CSV DOWNLOAD
window.downloadCSV = function () {

    if (extractedData.length === 0) {
        alert("No data available to download");
        return;
    }

    let csv = "date,lat,lon,value\n";

    extractedData.forEach(row => {
        csv += `${row.date},${row.lat},${row.lon},${row.value}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "weather_data.csv";
    a.click();
};

// 🔷 RESET FUNCTION
window.resetForm = function () {
    document.getElementById("lat").value = "";
    document.getElementById("lon").value = "";
    document.getElementById("startDate").value = "";
    document.getElementById("endDate").value = "";
    document.getElementById("output").innerText = "";
    extractedData = [];
};
