
import pandas as pd
import numpy as np
import os
import pickle
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.model_selection import train_test_split

DATA_FILE = "city_day.csv"  
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)


df = pd.read_csv(DATA_FILE)

target_city = "Kanjirappally"
if 'City' not in df.columns:
    raise ValueError("CSV must contain a 'City' column.")

available_cities = df['City'].str.strip().unique()
if target_city not in available_cities:
    print(f"⚠️ '{target_city}' not found in CSV. Using '{available_cities[0]}' instead.")
    target_city = available_cities[0]

city_df = df[df['City'].str.strip() == target_city].copy()
if city_df.empty:
    raise ValueError(f"No data found for city '{target_city}' in CSV. Cannot train model.")


if 'Date' not in city_df.columns or 'AQI' not in city_df.columns:
    raise ValueError("CSV must contain 'Date' and 'AQI' columns.")

city_df.sort_values("Date", inplace=True)
city_df.reset_index(drop=True, inplace=True)

y = city_df['AQI'].astype(float)


X = pd.DataFrame()
X['AQI_lag1'] = y.shift(1)
X = X.dropna()
y = y.iloc[1:]  

if len(X) < 2:
    raise ValueError("Not enough data after creating lag features to train the model.")


test_size = max(1, int(len(X) * 0.2)) 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)
print(f"Training samples: {len(X_train)}, Testing samples: {len(X_test)}")


model = SARIMAX(y_train, order=(1, 0, 0), seasonal_order=(0, 0, 0, 0))
model_fit = model.fit(disp=False)
print("✅ Model training completed.")


model_file = os.path.join(MODELS_DIR, f"{target_city.lower().replace(' ', '')}_model.pkl")
with open(model_file, "wb") as f:
    pickle.dump(model_fit, f)

print(f"✅ Model saved for city '{target_city}' at '{model_file}'")
