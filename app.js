const API = "https://weather-dashboard-9dn4.onrender.com";

let chartInstance;
let map, rectangle;

// ================= SECTION SWITCH =================
function showSection(id){
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
    document.getElementById(id).classList.add("active");

    // Fix map rendering issue
    if(id === "mapSection" && map){
        setTimeout(()=>map.invalidateSize(), 200);
    }
}

// ================= SINGLE LOCATION =================
async function fetchSingle(){

    let param = document.getElementById("param").value;
    let lat = document.getElementById("lat").value;
    let lon = document.getElementById("lon").value;
    let start = document.getElementById("start").value;
    let end = document.getElementById("end").value;

    let url = `${API}/weather?param=${param}&lat=${lat}&lon=${lon}&start=${start}&end=${end}`;

    let res = await fetch(url);
    let data = await res.json();

    if(!data.length) return alert("No data");

    // ================= UNIT =================
    let unit = "";
    if(param === "rain") unit = "mm";
    if(param === "tmin" || param === "tmax") unit = "°C";

    // ================= FORMAT DATE =================
    function formatDate(d){
        let dt = new Date(d);
        return `${dt.getFullYear()}/${String(dt.getMonth()+1).padStart(2,'0')}/${String(dt.getDate()).padStart(2,'0')}`;
    }

    // ================= VALUES =================
    let values = data.map(d => d[param]);

    let avg = (values.reduce((a,b)=>a+b,0) / values.length).toFixed(2);
    let min = Math.min(...values).toFixed(2);
    let max = Math.max(...values).toFixed(2);
    let sum = values.reduce((a,b)=>a+b,0).toFixed(2);

    // ================= METRICS TABLE =================
    let metricsHTML = `
    <h3>Summary Metrics</h3>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Average</td><td>${avg} ${unit}</td></tr>
        <tr><td>Minimum</td><td>${min} ${unit}</td></tr>
        <tr><td>Maximum</td><td>${max} ${unit}</td></tr>
        ${param === "rain" ? `<tr><td>Sum</td><td>${sum} ${unit}</td></tr>` : ""}
    </table>
    `;

    document.getElementById("metrics").innerHTML = metricsHTML;

    // ================= DAILY TABLE =================
    let html = "<table><tr><th>Date</th><th>Value</th></tr>";

    data.forEach(d=>{
        html += `<tr><td>${formatDate(d.date)}</td><td>${d[param]} ${unit}</td></tr>`;
    });

    html += "</table>";
    document.getElementById("table").innerHTML = html;

    // ================= CHART =================
    if(chartInstance) chartInstance.destroy();

    chartInstance = new Chart(document.getElementById("chart"), {
        type:"line",
        data:{
            labels: data.map(d => formatDate(d.date)),
            datasets:[{
                label: `${param} (${unit})`,
                data: values,
                borderWidth: 2
            }]
        }
    });
}

// ================= MAP =================
function initMap(){
    map = L.map('map').setView([22,78],5);

    L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
    ).addTo(map);
}

async function loadMap(){

    if(!map) initMap();

    let lat = parseFloat(document.getElementById("mapLat").value);
    let lon = parseFloat(document.getElementById("mapLon").value);
    let date = document.getElementById("mapDate").value;
    let param = document.getElementById("mapParam").value;

    let url = `${API}/weather?param=${param}&lat=${lat}&lon=${lon}&start=${date}&end=${date}`;

    let res = await fetch(url);
    let data = await res.json();

    if(!data.length) return alert("No data");

    let val = data[0][param];

    map.setView([lat, lon], 8);

    if(rectangle) map.removeLayer(rectangle);

    let bounds = [
        [lat-0.125, lon-0.125],
        [lat+0.125, lon+0.125]
    ];

    rectangle = L.rectangle(bounds, {color:'red'}).addTo(map);
    rectangle.bindPopup(`${param}: ${val}`).openPopup();
}

// ================= CSV =================
async function processCSV(){

    let file = document.getElementById("csvFile").files[0];
    let text = await file.text();

    let rows = text.split("\n");

    for(let r of rows){
        let [lat, lon] = r.split(",");
        if(!lat) continue;

        let url = `${API}/weather?param=rain&lat=${lat}&lon=${lon}&start=2003-01-01&end=2003-01-03`;

        await fetch(url);
    }

    alert("Done processing CSV");
}
