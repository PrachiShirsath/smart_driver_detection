import requests
import webbrowser
import json
import os
import tkinter as tk
from tkinter import messagebox, Listbox

# ================= CONFIGURATION =================
BG_COLOR = "#121212"
ACCENT_COLOR = "#007BFF"
INPUT_BG = "#1E1E1E"
TEXT_COLOR = "#FFFFFF"
SIMULATION_SPEED_MS = 120

# ================= GET COORDINATES =================
def get_coords(location_name):

    url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"

    headers = {
        'User-Agent': 'AI_Navigation_App'
    }

    try:
        response = requests.get(url, headers=headers)

        data = response.json()

        if data:
            return (
                float(data[0]['lon']),
                float(data[0]['lat'])
            )

        return None

    except:
        return None

# ================= SEARCH PLACE SUGGESTIONS =================
def search_places(query):

    if not query:
        return []

    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=5"

    headers = {
        'User-Agent': 'AI_Navigation_App'
    }

    try:
        response = requests.get(url, headers=headers)

        data = response.json()

        return [
            place['display_name']
            for place in data
        ]

    except:
        return []

# ================= GET ROUTE =================
def get_route(start_coords, end_coords):

    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{start_coords[0]},{start_coords[1]};"
        f"{end_coords[0]},{end_coords[1]}"
        f"?overview=full&geometries=geojson&steps=true"
    )

    try:
        response = requests.get(url)

        data = response.json()

        return data['routes'][0]['geometry']['coordinates']

    except:
        return None

# ================= GENERATE MAP =================
def generate_map(route, start_name, end_name):

    route_latlng = [[y, x] for x, y in route]

    html = f"""
<!DOCTYPE html>
<html>

<head>

<link rel="stylesheet"
href="https://unpkg.com/leaflet/dist/leaflet.css"/>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<style>

body {{
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: #121212;
    font-family: Arial, sans-serif;
}}

#map {{
    width: 100vw;
    height: 100vh;
}}

.nav-arrow {{
    width: 0;
    height: 0;

    border-left: 15px solid transparent;
    border-right: 15px solid transparent;

    border-bottom: 30px solid {ACCENT_COLOR};

    filter: drop-shadow(0 0 5px rgba(0,123,255,0.8));
}}

#alert {{
    position: fixed;

    top: 40px;
    left: 50%;

    transform: translateX(-50%);

    background: rgba(220,53,69,0.95);

    color: white;

    padding: 15px 40px;

    font-size: 22px;
    font-weight: bold;

    border-radius: 50px;

    display: none;

    z-index: 9999;
}}

#dashboard-ui {{

    position: fixed;

    bottom: 30px;
    left: 30px;

    background: rgba(30,30,30,0.95);

    color: white;

    padding: 20px;

    border-radius: 15px;

    border-left: 8px solid {ACCENT_COLOR};

    min-width: 250px;

    z-index: 9999;
}}

</style>

</head>

<body>

<div id="alert">
⚠️ SHARP CURVE AHEAD
</div>

<div id="dashboard-ui">

<div style="font-size:11px;color:#aaa;">
NAVIGATING TO
</div>

<div style="font-size:22px;font-weight:bold;margin-top:5px;">
{end_name}
</div>

<div id="status"
style="margin-top:10px;color:{ACCENT_COLOR};">
● GPS SIGNAL STABLE
</div>

</div>

<div id="map"></div>

<script>

var routeData = {json.dumps(route_latlng)};

var map = L.map('map', {{
    zoomControl: false,
    attributionControl: false
}}).setView(routeData[0], 16);

L.tileLayer(
'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png'
).addTo(map);

var pathLine = L.polyline(routeData, {{
    color: '{ACCENT_COLOR}',
    weight: 6,
    opacity: 0.7
}}).addTo(map);

var carIcon = L.divIcon({{
    className: 'car-container',

    html: '<div class="nav-arrow" id="car-img"></div>',

    iconSize: [30, 30],
    iconAnchor: [15, 15]
}});

var marker = L.marker(routeData[0], {{
    icon: carIcon
}}).addTo(map);

function speak(text) {{

    window.speechSynthesis.cancel();

    let msg = new SpeechSynthesisUtterance(text);

    window.speechSynthesis.speak(msg);
}}

function getBearing(p1, p2) {{

    let lat1 = p1[0] * Math.PI / 180;
    let lat2 = p2[0] * Math.PI / 180;

    let lon1 = p1[1] * Math.PI / 180;
    let lon2 = p2[1] * Math.PI / 180;

    let y = Math.sin(lon2 - lon1) * Math.cos(lat2);

    let x =
        Math.cos(lat1) * Math.sin(lat2) -
        Math.sin(lat1) * Math.cos(lat2) *
        Math.cos(lon2 - lon1);

    return Math.atan2(y, x) * 180 / Math.PI;
}}

async function startNavigation() {{

    speak("Starting navigation to {end_name}");

    let lastBearing = getBearing(
        routeData[0],
        routeData[1]
    );

    for (let i = 0; i < routeData.length - 1; i++) {{

        let p1 = routeData[i];
        let p2 = routeData[i + 1];

        let bearing = getBearing(p1, p2);

        let diff = Math.abs(bearing - lastBearing);

        if (diff > 180)
            diff = 360 - diff;

        if (diff > 22) {{

            document.getElementById('alert').style.display = 'block';

            speak("Sharp curve ahead");

            setTimeout(() => {{

                document.getElementById('alert').style.display = 'none';

            }}, 2000);
        }}

        let steps = 10;

        for (let s = 1; s <= steps; s++) {{

            let lat =
                p1[0] + (p2[0] - p1[0]) * (s / steps);

            let lng =
                p1[1] + (p2[1] - p1[1]) * (s / steps);

            marker.setLatLng([lat, lng]);

            map.panTo([lat, lng], {{
                animate: false
            }});

            document.getElementById('car-img')
            .style.transform = `rotate(${{bearing}}deg)`;

            await new Promise(resolve =>
                setTimeout(resolve, {SIMULATION_SPEED_MS} / steps)
            );
        }}

        lastBearing = bearing;
    }}

    document.getElementById('status').innerText =
    "● DESTINATION REACHED";

    speak("Destination reached");
}}

setTimeout(startNavigation, 3000);

</script>

</body>
</html>
"""

    file_path = os.path.abspath("car_navigation.html")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html)

    return file_path

# ================= RUN APPLICATION =================
def run_app():

    start_city = ent_from.get()
    end_city = ent_to.get()

    if not start_city or not end_city:

        messagebox.showerror(
            "Error",
            "Please enter locations"
        )

        return

    start_coords = get_coords(start_city)
    end_coords = get_coords(end_city)

    if start_coords and end_coords:

        route = get_route(
            start_coords,
            end_coords
        )

        if route:

            map_file = generate_map(
                route,
                start_city,
                end_city
            )

            # OPEN IN DEFAULT BROWSER
            webbrowser.open(
                "file://" + map_file
            )

        else:

            messagebox.showerror(
                "Error",
                "No route found"
            )

    else:

        messagebox.showerror(
            "Error",
            "Invalid locations"
        )

# ================= AUTOCOMPLETE FIELD =================
def styled_field(label, default):

    frame = tk.Frame(
        root,
        bg=BG_COLOR
    )

    frame.pack(
        fill="x",
        padx=40,
        pady=10
    )

    tk.Label(
        frame,
        text=label,
        font=("Arial", 9, "bold"),
        fg=ACCENT_COLOR,
        bg=BG_COLOR
    ).pack(anchor="w")

    entry = tk.Entry(
        frame,
        bg=INPUT_BG,
        fg=TEXT_COLOR,
        font=("Arial", 14),
        relief="flat",
        insertbackground="white"
    )

    entry.insert(0, default)

    entry.pack(
        fill="x",
        ipady=8,
        pady=5
    )

    suggestion_box = Listbox(
        frame,
        bg=INPUT_BG,
        fg=TEXT_COLOR,
        font=("Arial", 11),
        relief="flat",
        height=5
    )

    suggestion_box.pack(fill="x")

    suggestion_box.pack_forget()

    # ===== UPDATE SUGGESTIONS =====
    def update_suggestions(event):

        query = entry.get()

        suggestions = search_places(query)

        suggestion_box.delete(0, tk.END)

        if suggestions:

            suggestion_box.pack(fill="x")

            for place in suggestions:
                suggestion_box.insert(
                    tk.END,
                    place
                )

        else:

            suggestion_box.pack_forget()

    # ===== SELECT PLACE =====
    def select_place(event):

        if not suggestion_box.curselection():
            return

        index = suggestion_box.curselection()[0]

        selected = suggestion_box.get(index)

        entry.delete(0, tk.END)

        entry.insert(0, selected)

        suggestion_box.pack_forget()

    entry.bind(
        "<KeyRelease>",
        update_suggestions
    )

    suggestion_box.bind(
        "<<ListboxSelect>>",
        select_place
    )

    return entry

# ================= MAIN WINDOW =================
root = tk.Tk()

root.title("AI Navigation Dashboard")

root.geometry("450x500")

root.configure(bg=BG_COLOR)

# ================= HEADER =================
header = tk.Frame(
    root,
    bg=BG_COLOR
)

header.pack(
    fill="x",
    pady=30,
    padx=40
)

tk.Label(
    header,
    text="N A V I G A T I O N",
    font=("Impact", 28),
    fg=TEXT_COLOR,
    bg=BG_COLOR
).pack(side="left")

# ================= INPUT FIELDS =================
ent_from = styled_field(
    "CURRENT POSITION",
    "Mumbai"
)

ent_to = styled_field(
    "DESTINATION",
    "Pune"
)

# ================= BUTTON =================
btn_start = tk.Button(
    root,
    text="START ROUTE",
    command=run_app,
    bg=ACCENT_COLOR,
    fg="white",
    font=("Arial", 12, "bold"),
    relief="flat",
    cursor="hand2"
)

btn_start.pack(
    fill="x",
    padx=40,
    pady=40,
    ipady=12
)

# ================= START APP =================
root.mainloop()