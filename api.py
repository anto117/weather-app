from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, pickle, pandas as pd, os, math
from datetime import datetime, timedelta
import openrouteservice # You will need to run: pip install openrouteservice

# --- CONFIGURATION ---
# 🔒 SECURITY WARNING: Storing API keys directly in code is risky.
#    It's better to use environment variables. For example: os.environ.get('WAQI_TOKEN')
WAQI_TOKEN = "863296fb81e839b073505ca569860cdf03f1ce80"
WEATHER_API_KEY = "8724fb5e1424446a9f0152514250110"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjliYjU2NGQxNzJiMzQwYWU5ZGI3ZTI5NTQ3ZDVhZTBlIiwiaCI6Im11cm11cjY0In0=" # Your existing ORS key
TEMPO_API_KEY = "YOUR_TEMPO_API_KEY"  # This is a placeholder, this feature branch will fail.

MODELS_DIR = 'models'
forecast_feature_available = os.path.exists(MODELS_DIR) and len(os.listdir(MODELS_DIR)) > 0
if forecast_feature_available:
    print(f"✅ {len(os.listdir(MODELS_DIR))} prediction models found. Forecast feature is enabled.")
else:
    print("⚠️ Warning: 'models' directory is empty or not found. Forecast feature will be disabled.")

app = Flask(__name__)
CORS(app)

# --- HELPER FUNCTIONS ---
def get_coords_from_name(location_name):
    url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"
    try:
        r = requests.get(url, headers={"User-Agent": "React-AQI-App-Search"})
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None
    except requests.RequestException:
        return None, None

def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    try:
        r = requests.get(url, headers={"User-Agent": "React-AQI-App-v3"})
        r.raise_for_status()
        data = r.json()
        address = data.get("address", {})
        city = (address.get("suburb") or address.get("hamlet") or
                address.get("village") or address.get("town") or address.get("city") or "Unknown Area")
        state = address.get("state") or address.get("county") or "Unknown"
        return city, state
    except requests.RequestException:
        return "Unknown Area", "Unknown"

def fetch_waqi(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "ok" or not isinstance(data["data"].get("aqi"), (int, float)):
            return None
        iaqi = data["data"].get("iaqi", {})
        pollutants = {p: iaqi.get(p, {}).get("v", "N/A") for p in ["pm25", "pm10", "o3", "so2", "no2"]}
        return {
            "aqi": data["data"]["aqi"], "station": data["data"].get("city", {}).get("name", "Unknown Station"),
            "pollutants": pollutants, "advice": health_advice(data["data"]["aqi"])
        }
    except (requests.RequestException, KeyError):
        return None

def fetch_weather(lat, lon):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={lat},{lon}&days=1&aqi=no&alerts=no"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if 'error' in data: return None
        current, forecast = data["current"], data["forecast"]["forecastday"][0]
        return {
            "current": {"temp": current["temp_c"], "is_day": current["is_day"], "description": current["condition"]["text"], "condition_code": current["condition"]["code"]},
            "astro": forecast["astro"],
            "hourly": [{"time": h["time_epoch"], "temp": h["temp_c"], "icon": h["condition"]["icon"]} for h in forecast["hour"]]
        }
    except requests.RequestException:
        return None

def health_advice(aqi):
    if not isinstance(aqi, (int, float)): return "Data not available."
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Moderate"
    if aqi <= 150: return "Unhealthy for Sensitive Groups – wear a mask outdoors."
    return "Unhealthy"

def get_stations_in_bounds(bounds_str):
    url = f"https://api.waqi.info/map/bounds/?latlng={bounds_str}&token={WAQI_TOKEN}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "ok": return []
        return [{"lat": float(s["lat"]), "lon": float(s["lon"]), "aqi": int(s["aqi"])} for s in data["data"] if str(s["aqi"]).replace('.', '', 1).isdigit()]
    except requests.RequestException:
        return []

def calculate_interpolated_aqi(user_lat, user_lon):
    bounds = f"{user_lat-0.5},{user_lon-0.5},{user_lat+0.5},{user_lon+0.5}"
    stations = get_stations_in_bounds(bounds)
    if not stations: return None, {}
    for station in stations:
        station['dist'] = math.sqrt((station['lat'] - user_lat) ** 2 + (station['lon'] - user_lon) ** 2)
    nearby = sorted(stations, key=lambda s: s['dist'])[:4]
    weighted_sum, weight_sum = 0, 0
    for st in nearby:
        if st['dist'] == 0: return st['aqi'], {} # If we are right on a station
        weight = 1 / st['dist']
        weighted_sum += st['aqi'] * weight
        weight_sum += weight
    if weight_sum == 0: return None, {}
    return round(weighted_sum / weight_sum), {}


# --- API ROUTES ---

@app.route("/api/forecast")
def get_aqi_forecast():
    lat, lon = request.args.get("lat"), request.args.get("lon")
    if not lat or not lon: return jsonify({"error": "Lat/Lon required"}), 400
    try: lat, lon = float(lat), float(lon)
    except ValueError: return jsonify({"error": "Invalid coordinates"}), 400

    city, _ = reverse_geocode(lat, lon)
    model_file = f"{city.replace(' ', '').lower()}_model.pkl"
    path = os.path.join(MODELS_DIR, model_file)

    if not os.path.exists(path):
        # ✅ FIX: Fallback to Open-Meteo and FORMAT the data for the frontend
        try:
            end_date = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
            start_date = datetime.utcnow().strftime('%Y-%m-%d')
            url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&daily=pm2_5&start_date={start_date}&end_date={end_date}"
            r = requests.get(url)
            r.raise_for_status()
            data = r.json().get('daily', {})
            
            if not data.get('time') or not data.get('pm2_5'):
                return jsonify({"error": "Fallback API returned no data"}), 404

            # Transform data to match the format expected by the frontend chart
            formatted_forecast = [
                {"date": date, "predicted_aqi": round(aqi) if aqi is not None else 0}
                for date, aqi in zip(data['time'], data['pm2_5'])
            ]
            return jsonify({
                "city_used_for_forecast": city,
                "forecast_source": "Open-Meteo (Fallback)",
                "forecast": formatted_forecast
            })
        except Exception as e:
            return jsonify({"error": f"No model for '{city}' and fallback failed: {str(e)}"}), 404

    try:
        with open(path, "rb") as f: model = pickle.load(f)
        res = model.get_forecast(steps=30)
        vals = res.predicted_mean
        start = datetime.today()
        return jsonify({
            "city_used_for_forecast": city, "forecast_source": "Trained Model",
            "forecast": [{"date": (start + timedelta(days=i + 1)).strftime('%Y-%m-%d'), "predicted_aqi": round(v)} for i, v in enumerate(vals)]
        })
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

@app.route("/api/live-data")
def get_live_data():
    lat, lon = request.args.get("lat"), request.args.get("lon")
    if not lat or not lon: return jsonify({"error": "Lat/Lon required"}), 400
    lat, lon = float(lat), float(lon)
    
    aqi_data = fetch_waqi(lat, lon)
    if not aqi_data: # If direct WAQI fails, try interpolation
        interpolated_aqi, pollutants = calculate_interpolated_aqi(lat, lon)
        if interpolated_aqi:
             aqi_data = {"aqi": interpolated_aqi, "advice": health_advice(interpolated_aqi), "station": "Interpolated from nearby stations", "pollutants": pollutants}

    weather_data = fetch_weather(lat, lon)
    if not aqi_data or not weather_data: return jsonify({"error": "Could not retrieve complete data for this location"}), 500
    
    city, state = reverse_geocode(lat, lon)
    return jsonify({"location": {"town": city, "district": state}, "aqiData": aqi_data, "weatherData": weather_data})

@app.route("/api/search-aqi")
def search_aqi_by_keyword():
    keyword = request.args.get("keyword")
    if not keyword: return jsonify({"error": "Keyword required"}), 400
    try:
        url = f"https://api.waqi.info/search/?keyword={keyword}&token={WAQI_TOKEN}"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if data.get("status") != "ok": return jsonify([]), 200 # Return empty list, not error
        return jsonify(data["data"])
    except Exception as e:
        return jsonify({"error": f"WAQI API error: {str(e)}"}), 500

# ✅ FIX: Added the missing /api/clean-route endpoint
@app.route("/api/clean-route")
def get_clean_route():
    start_loc, end_loc = request.args.get("start"), request.args.get("end")
    if not start_loc or not end_loc:
        return jsonify({"error": "Start and end locations are required."}), 400

    start_lat, start_lon = get_coords_from_name(start_loc)
    end_lat, end_lon = get_coords_from_name(end_loc)
    if not start_lat or not end_lat:
        return jsonify({"error": "Could not find coordinates for one or both locations."}), 404

    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
        coords = ((start_lon, start_lat), (end_lon, end_lat))
        route = client.directions(coordinates=coords, profile='driving-car', format='geojson')
        
        # Get bounding box of the route to find relevant AQI stations
        bbox = route['bbox']
        bounds_str = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"
        stations = get_stations_in_bounds(bounds_str)

        return jsonify({
            "standard_route": route['features'][0]['geometry'],
            "clean_route": route['features'][0]['geometry'], # Placeholder: clean route logic is complex
            "stations": stations,
            "warning": "Note: Clean route suggestion is a prototype. The standard route is shown."
        })
    except Exception as e:
        return jsonify({"error": f"Route calculation failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)