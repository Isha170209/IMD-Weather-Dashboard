import init, { readParquet } from "https://cdn.jsdelivr.net/npm/parquet-wasm@latest/+esm";

await init();

// 🔴 IMPORTANT: Replace these
const username = "YOUR_USERNAME";
const repo = "Weather-Dashboard";
const token = "YOUR_GITHUB_TOKEN";  // ⚠ exposed in browser

let extractedData = [];

// 🔷 Resolution
function getResolution(param) {
    return param === "rain" ? 0.25 : 1.0;
}

// 🔷 Snap to nearest grid (replacement of KDTree)
function snap(value, resolution) {
    return Math.round(value / resolution) * resolution;
}

// 🔷 Get list of years between dates
function getYears(start, end) {
    let years = [];
    for (let y = start; y <= end; y++) years.push(y);
    return years;
}

// 🔷 Fetch parquet from PRIVATE GitHub repo
async function fetchParquetFromGitHub(path) {

    const url = `https://api.github.com/repos/${username}/${repo}/contents/${path}`;

    const response = await fetch(url, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status}`);
    }

    const data = await response.json();

    // 🔷 Decode base64 → Uint8Array
    const binary = atob(data.content);
    const bytes = new Uint8Array(binary.length);

    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }

    return bytes;
}

// 🔷 MAIN FUNCTION
window.fetchData = async function () {

    const param = document.getElementById("param").value;
    const lat = parseFloat(document.getElementById("lat").value);
    const lon = parseFloat(document.getElementById("lon").value);

    const startDate = new Date(document.getElementById("startDate").value);
    const endDate = new Date(document.getElementById("endDate").value);

    if (isNaN(lat) || isNaN(lon)) {
        alert("Please enter valid latitude and longitude");
        return;
    }

    if (!startDate || !endDate) {
        alert("Please select valid dates");
        return;
    }

    const resolution = getResolution(param);

    const nearestLat = snap(lat, resolution);
    const nearestLon = snap(lon, resolution);

    const years = getYears(startDate.getFullYear(), endDate.getFullYear());

    extractedData = [];

    document.getElementById("output").innerText = "Loading...";

    for (let year of years) {

        const path = `data/${param}/${year}_${param}.parquet`;

        try {
            const bytes = await fetchParquetFromGitHub(path);

            const table = readParquet(bytes);
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
            console.log(`Skipping ${year}:`, err.message);
        }
    }

    if (extractedData.length === 0) {
        document.getElementById("output").innerText = "No data found.";
        return;
    }

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
