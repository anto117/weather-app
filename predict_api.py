from flask import Flask, request, jsonify
import pandas as pd
import joblib

app = Flask(__name__)

# Load trained model
model = joblib.load(r"C:\Users\NITRO\Documents\linear_air_quality_lag.pkl")

# List of Kerala cities in your dataset
KERALA_CITIES = ["Thiruvananthapuram", "Kochi", "Kozhikode", "Kollam", "Kottayam", "Alappuzha", "Thrissur", "Palakkad", "Malappuram", "Kannur", "Wayanad", "Pathanamthitta", "Idukki"]

@app.route('/api/predict_kerala', methods=['GET'])
def predict_kerala():
    predictions = []
    for city in KERALA_CITIES:
        # Example dummy lag values (you can fetch actual previous day data if available)
        data = {
            'City': city,
            'Day': 4,
            'Month': 10,
            'Year': 2025,
            'PM10_lag1': 180,
            'NO2_lag1': 40,
            'CO_lag1': 1.2,
            'SO2_lag1': 12,
            'O3_lag1': 30,
            'AQI_lag1': 250,
            'PM2.5_lag1': 120
        }

        df = pd.DataFrame([data])
        df = pd.get_dummies(df)
        df = df.reindex(columns=model.feature_names_in_, fill_value=0)
        prediction = model.predict(df)[0]
        predictions.append({'City': city, 'PM2.5': round(float(prediction), 2)})

    return jsonify(predictions)

if __name__ == '__main__':
    app.run(debug=True)
