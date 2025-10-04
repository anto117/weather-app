from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pickle
import pandas as pd
import os
import math

MODELS_DIR = 'models'
AVAILABLE_MODELS = []  


def load_available_models_locations():
    global AVAILABLE_MODELS
    try:
        df = pd.read_csv('city_day.csv', usecols=['City', 'Latitude', 'Longitude']).drop_duplicates(subset=['City']).dropna()
        model_files = os.listdir(MODELS_DIR)
        for model_file in model_files:
            city_name = model_file.replace('_model.pkl', '')
            city_data = df[df['City'] == city_name]
            if not city_data.empty:
                AVAILABLE_MODELS.append({
                    "city": city_name,
                    "lat": city_data.iloc[0]['Latitude'],
                    "lon": city_data.iloc[0]['Longitude']
                })
        if AVAILABLE_MODELS:
            print(f"✅ Successfully loaded locations for {len(AVAILABLE_MODELS)} prediction models.")
        else:
            print("⚠️ No model locations loaded. Ensure city names in CSV match model files.")
    except Exception as e:
        print(f"❌ Error loading model locations: {e}")



def find_closest_city_with_model(user_lat, user_lon):
    if not AVAILABLE_MODELS:
        return None

    def distance(lat1, lon1, lat2, lon2):
        return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

    closest_city = min(
        AVAILABLE_MODELS,
        key=lambda city: distance(user_lat, user_lon, city['lat'], city['lon'])
    )
    return closest_city['city']


def reverse_geocode(lat, lon): 
    return "Kottayam", "Kerala"

def fetch_waqi(lat, lon): 
    return {"aqi": 88, "station": "Sample", "pollutants": {}, "advice": "Moderate"}

def fetch_weather(lat, lon): 
    return {"current": {"temp": 29, "description": "Partly cloudy"}, "astro": {}, "hourly": []}



app = Flask(__name__)
CORS(app)



@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({"features": {"forecast": len(AVAILABLE_MODELS) > 0}})


@app.route("/api/forecast", methods=["GET"])
def get_aqi_forecast():
    lat_str = request.args.get("lat")
    lon_str = request.args.get("lon")
    if not lat_str or not lon_str:
        return jsonify({"error": "Latitude and longitude parameters are required."}), 400

    user_lat, user_lon = float(lat_str), float(lon_str)

   
    closest_city = find_closest_city_with_model(user_lat, user_lon)
    if not closest_city:
        return jsonify({"error": "No forecast models available"}), 503

    model_path = f"{MODELS_DIR}/{closest_city}_model.pkl"

    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        
        steps = 7
        forecast_result = model.get_forecast(steps=steps)
        forecast_values = forecast_result.predicted_mean  

        forecast_list = []
        for date, val in forecast_values.items():
            forecast_list.append({
                "date": date.strftime("%Y-%m-%d"),
                "predicted_aqi": max(0, round(val)) 
            })

        return jsonify({
            "city_used_for_forecast": closest_city,
            "forecast": forecast_list
        })

    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route("/api/live-data", methods=["GET"])
def get_live_data():
   
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    return jsonify({
        "location": {"town": "Kottayam", "district": "Kerala"},
        "aqiData": fetch_waqi(float(lat), float(lon)),
        "weatherData": fetch_weather(float(lat), float(lon))
    })


if __name__ == "__main__":
    load_available_models_locations()
    app.run(debug=True, port=5000)
