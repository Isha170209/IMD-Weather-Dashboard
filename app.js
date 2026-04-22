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

    // TABLE
    let html = "<table><tr><th>Date</th><th>Value</th></tr>";
    data.forEach(d=>{
        html += `<tr><td>${d.date}</td><td>${d[param]}</td></tr>`;
    });
    html += "</table>";
    document.getElementById("table").innerHTML = html;

    // CHART
    if(chartInstance) chartInstance.destroy();

    chartInstance = new Chart(document.getElementById("chart"), {
        type:"line",
        data:{
            labels: data.map(d=>d.date),
            datasets:[{
                label:param,
                data:data.map(d=>d[param])
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
