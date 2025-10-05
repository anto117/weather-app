from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pickle
import pandas as pd
import os
import math
from datetime import datetime, timedelta
import openrouteservice


MODELS_DIR = 'models'
DATA_FILE = "city_day.csv"

forecast_feature_available = os.path.exists(MODELS_DIR) and len(os.listdir(MODELS_DIR)) > 0
if forecast_feature_available:
    print(f"✅ {len(os.listdir(MODELS_DIR))} prediction models found. Forecast feature is enabled.")
else:
    print("⚠️ Warning: 'models' directory is empty or not found. Forecast feature will be disabled.")
    print("➡️ To enable, run 'python train_all_models.py' to create the models.")

WAQI_TOKEN = "863296fb81e839b073505ca569860cdf03f1ce80"
WEATHER_API_KEY = "8724fb5e1424446a9f0152514250110"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjliYjU2NGQxNzJiMzQwYWU5ZGI3ZTI5NTQ3ZDVhZTBlIiwiaCI6Im11cm11cjY0In0="
TEMPO_API_KEY = "YOUR_TEMPO_API_KEY"  # 🔹 Replace with your real Tempo API key


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
        city = address.get("city") or address.get("town") or address.get("village") or "Unknown Area"
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
        if data.get("status") != "ok": 
            return None
        if not isinstance(data["data"].get("aqi"), (int, float)): 
            return None
        iaqi = data["data"].get("iaqi", {})
        pollutants = {p: iaqi.get(p, {}).get("v", "N/A") for p in ["pm25", "pm10", "o3", "so2", "no2"]}
        return {
            "aqi": data["data"]["aqi"], 
            "station": data["data"].get("city", {}).get("name", "Unknown Station"), 
            "pollutants": pollutants,
            "advice": health_advice(data["data"]["aqi"])
        }
    except (requests.RequestException, KeyError):
        return None


def fetch_weather(lat, lon):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={lat},{lon}&days=1&aqi=no&alerts=no"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if 'error' in data: 
            return None
        current = data["current"]
        forecast = data["forecast"]["forecastday"][0]
        return {
            "current": {
                "temp": current["temp_c"], 
                "is_day": current["is_day"], 
                "description": current["condition"]["text"], 
                "condition_code": current["condition"]["code"]
            }, 
            "astro": forecast["astro"], 
            "hourly": [{"time": h["time_epoch"], "temp": h["temp_c"], "icon": h["condition"]["icon"]} for h in forecast["hour"]]
        }
    except requests.RequestException:
        return None


def health_advice(aqi):
    if not isinstance(aqi, (int, float)): 
        return "Data not available."
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Moderate"
    if aqi <= 150: return "Unhealthy for Sensitive Groups Please wear a mask outdoors."
    return "Unhealthy"


def get_stations_in_bounds(lat, lon):
    lat_margin, lon_margin = 0.5, 0.5
    bounds = f"{lat-lat_margin},{lon-lon_margin},{lat+lat_margin},{lon+lon_margin}"
    url = f"https://api.waqi.info/map/bounds/?latlng={bounds}&token={WAQI_TOKEN}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "ok": 
            return []
        return [{"lat": float(s["lat"]), "lon": float(s["lon"]), "aqi": int(s["aqi"])} for s in data["data"] if s["aqi"].replace('.', '', 1).isdigit()]
    except requests.RequestException: 
        return []


def calculate_interpolated_aqi(user_lat, user_lon):
    stations = get_stations_in_bounds(user_lat, user_lon)
    if not stations: 
        return None, {}
    for station in stations:
        station['dist'] = math.sqrt((station['lat'] - user_lat)**2 + (station['lon'] - user_lon)**2)
    nearby_stations = sorted(stations, key=lambda s: s['dist'])[:4]
    weighted_sum, weight_sum = 0, 0
    for station in nearby_stations:
        if station['dist'] == 0: 
            return station['aqi'], {}
        weight = 1 / station['dist']
        weighted_sum += station['aqi'] * weight
        weight_sum += weight
    if weight_sum == 0: 
        return None, {}
    interpolated_aqi = round(weighted_sum / weight_sum)
    closest_station_data = fetch_waqi(user_lat, user_lon)
    pollutants = closest_station_data.get('pollutants', {}) if closest_station_data else {}
    return interpolated_aqi, pollutants


app = Flask(__name__)
CORS(app)


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({"features": {"forecast": forecast_feature_available}})


@app.route("/api/forecast", methods=["GET"])
def get_aqi_forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "Lat/Lon parameters are required."}), 400
    
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        return jsonify({"error": "Invalid latitude or longitude values."}), 400

    city, _ = reverse_geocode(lat, lon)
    model_name = f"{city.replace(' ', '').lower()}_model.pkl"
    model_path = os.path.join(MODELS_DIR, model_name)
    
    if not os.path.exists(model_path):
        return jsonify({"error": f"A forecast model for '{city}' is not available."}), 404

    try:
        with open(model_path, "rb") as f:
            model_fit = pickle.load(f)
        forecast_result = model_fit.get_forecast(steps=7)
        forecast_values = forecast_result.predicted_mean
        start_date = datetime.today()
        response_data = {
            "city_used_for_forecast": city,
            "forecast": [
                {"date": (start_date + timedelta(days=i+1)).strftime('%Y-%m-%d'), "predicted_aqi": round(val)}
                for i, val in enumerate(forecast_values)
            ]
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500


@app.route("/api/live-data", methods=["GET"])
def get_live_data():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon: 
        return jsonify({"error": "Lat/Lon are required"}), 400
    
    lat, lon = float(lat), float(lon)
    interpolated_aqi, pollutants = calculate_interpolated_aqi(lat, lon)
    aqi_data = {"aqi": interpolated_aqi, "advice": health_advice(interpolated_aqi), "station": "Interpolated Value", "pollutants": pollutants} if interpolated_aqi else fetch_waqi(lat, lon)
    weather_data = fetch_weather(lat, lon)

    if not aqi_data or not weather_data:
        return jsonify({"error": "Could not retrieve complete data for this location."}), 500

    city, state = reverse_geocode(lat, lon)
    return jsonify({"location": {"town": city, "district": state}, "aqiData": aqi_data, "weatherData": weather_data})


# 🔹 Updated logic: North America → Tempo API, Else → WAQI
@app.route("/api/search-aqi", methods=["GET"])
def search_aqi_by_keyword():
    keyword = request.args.get("keyword")
    if not keyword:
        return jsonify({"error": "Search keyword is required"}), 400

    lat, lon = get_coords_from_name(keyword)
    if not lat or not lon:
        return jsonify({"error": "Could not determine location coordinates"}), 404

    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
                         headers={"User-Agent": "React-AQI-App"})
        r.raise_for_status()
        country = r.json().get("address", {}).get("country", "")
    except requests.RequestException:
        country = ""

    north_america = ["United States", "USA", "Canada", "Mexico"]
    if any(c.lower() in country.lower() for c in north_america):
        # ✅ Use Tempo API
        try:
            tempo_url = f"https://api.tempo.com/v1/airquality?lat={lat}&lon={lon}&apikey={TEMPO_API_KEY}"
            res = requests.get(tempo_url)
            res.raise_for_status()
            data = res.json()
            return jsonify({
                "source": "Tempo API",
                "country": country,
                "location": keyword,
                "data": data
            })
        except requests.RequestException as e:
            return jsonify({"error": f"Tempo API error: {str(e)}"}), 500
    else:
        # 🌍 Use WAQI API
        try:
            waqi_url = f"https://api.waqi.info/search/?keyword={keyword}&token={WAQI_TOKEN}"
            res = requests.get(waqi_url)
            res.raise_for_status()
            data = res.json()
            if data.get("status") != "ok":
                return jsonify({"error": "WAQI search failed"}), 500
            return jsonify({
                "source": "WAQI API",
                "country": country,
                "data": data["data"]
            })
        except requests.RequestException as e:
            return jsonify({"error": f"WAQI API error: {str(e)}"}), 500


@app.route("/api/clean-route", methods=["GET"])
def get_clean_route():
    start_name = request.args.get("start")
    end_name = request.args.get("end")
    if not start_name or not end_name: 
        return jsonify({"error": "Start and end locations are required"}), 400
    
    start_lat, start_lon = get_coords_from_name(start_name)
    end_lat, end_lon = get_coords_from_name(end_name)
    if not start_lat or not end_lat: 
        return jsonify({"error": "Could not find coordinates for one or both locations"}), 404
    
    client = openrouteservice.Client(key=ORS_API_KEY)
    coords = ((start_lon, start_lat), (end_lon, end_lat))
    try:
        standard_route = client.directions(coordinates=coords, profile='driving-car', format='geojson')
        distance_meters = standard_route['features'][0]['properties']['summary']['distance']
        clean_route, warning, nearby_stations = standard_route, None, []
        
        if distance_meters <= 150000:
            bounds = standard_route['bbox']
            center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2
            nearby_stations = get_stations_in_bounds(center_lat, center_lon)
            avoid_polygons = []
            for station in nearby_stations:
                if station["aqi"] > 100:
                    radius = 0.01
                    poly = {
                        "type": "Polygon",
                        "coordinates": [[
                            [station['lon']-radius, station['lat']-radius],
                            [station['lon']+radius, station['lat']-radius],
                            [station['lon']+radius, station['lat']+radius],
                            [station['lon']-radius, station['lat']+radius],
                            [station['lon']-radius, station['lat']-radius]
                        ]]
                    }
                    avoid_polygons.append(poly)
            if avoid_polygons:
                options = {"avoid_polygons": {"type": "MultiPolygon", "coordinates": [p["coordinates"] for p in avoid_polygons]}}
                clean_route = client.directions(coordinates=coords, profile='driving-car', format='geojson', options=options)
        else:
            warning = "Route is over 150km. Clean Air feature is only available for shorter trips."
            
        return jsonify({"standard_route": standard_route, "clean_route": clean_route, "stations": nearby_stations, "warning": warning})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
