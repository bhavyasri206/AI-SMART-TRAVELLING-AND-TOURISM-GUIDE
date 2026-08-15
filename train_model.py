import os
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PLACES_FILE = os.path.join(BASE_DIR, "datasets", "places.csv")
HOTELS_FILE = os.path.join(BASE_DIR, "datasets", "hotels.csv")
FOOD_FILE = os.path.join(BASE_DIR, "datasets", "food.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")

os.makedirs(MODEL_DIR, exist_ok=True)

print("Loading datasets...")

places = pd.read_csv(PLACES_FILE)
hotels = pd.read_csv(HOTELS_FILE)
food = pd.read_csv(FOOD_FILE)

for df in (places, hotels, food):
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

cities = sorted(
    set(places["city"].dropna().astype(str).str.strip())
    | set(hotels["city"].dropna().astype(str).str.strip())
    | set(food["city"].dropna().astype(str).str.strip())
)

model = {
    "model_name": "Tourism Recommendation Model",
    "version": "1.1",
    "purpose": "Tourism place, hotel and food recommendation",
    "data_sources": ["places.csv", "hotels.csv", "food.csv"],
    "cities": cities,
    "places": places.to_dict(orient="records"),
    "hotels": hotels.to_dict(orient="records"),
    "food": food.to_dict(orient="records"),
}

model_file = os.path.join(MODEL_DIR, "tourism_model.pkl")
joblib.dump(model, model_file)

print()
print("----------------------------------------")
print("TOURISM MODEL TRAINING COMPLETED")
print("----------------------------------------")
print("Cities :", len(cities))
print("Places :", len(places))
print("Hotels :", len(hotels))
print("Food   :", len(food))
print("Model  :", model_file)
print("----------------------------------------")
