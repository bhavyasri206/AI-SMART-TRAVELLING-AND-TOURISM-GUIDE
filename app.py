from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import math

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PLACES_FILE = os.path.join(BASE_DIR, "datasets", "places.csv")
HOTELS_FILE = os.path.join(BASE_DIR, "datasets", "hotels.csv")
FOOD_FILE = os.path.join(BASE_DIR, "datasets", "food.csv")


def load_csv(file_path):
    try:
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        print(f"Dataset not found: {file_path}")
    except Exception as exc:
        print(f"Dataset loading error ({file_path}): {exc}")
    return pd.DataFrame()


def clean_dataframe(df):
    if df.empty:
        return df

    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = df[column].fillna("").astype(str).str.strip()

    return df


places_df = clean_dataframe(load_csv(PLACES_FILE))
hotels_df = clean_dataframe(load_csv(HOTELS_FILE))
food_df = clean_dataframe(load_csv(FOOD_FILE))


@app.route("/")
def home():
    return render_template("index.html")


def filter_by_city(df, city):
    if df.empty or "city" not in df.columns:
        return df.iloc[0:0].copy()

    wanted = str(city).strip().casefold()
    values = df["city"].astype(str).str.strip().str.casefold()
    return df[values == wanted].copy()


def records(df):
    if df.empty:
        return []
    # Convert NaN values so JSON never contains invalid NaN values.
    return df.where(pd.notna(df), None).to_dict(orient="records")


@app.route("/api/status", methods=["GET"])
def dataset_status():
    return jsonify({
        "success": True,
        "places_dataset": {"loaded": not places_df.empty, "records": len(places_df)},
        "hotels_dataset": {"loaded": not hotels_df.empty, "records": len(hotels_df)},
        "food_dataset": {"loaded": not food_df.empty, "records": len(food_df)},
    })


@app.route("/api/popular-places", methods=["GET"])
def popular_places():
    if places_df.empty:
        return jsonify({"success": False, "message": "Places dataset not found.", "places": []})

    # Prefer highest-rated places when a rating column exists; otherwise use first 12.
    data = places_df.copy()
    if "rating" in data.columns:
        data["__rating"] = pd.to_numeric(data["rating"], errors="coerce")
        data = data.sort_values("__rating", ascending=False, na_position="last").drop(columns="__rating")

    data = data.head(12)
    return jsonify({"success": True, "count": len(data), "places": records(data)})


@app.route("/api/search", methods=["GET"])
def search():
    # Frontend uses ?city=. Keep ?query= as a backward-compatible alias.
    city = request.args.get("city", request.args.get("query", "")).strip()

    if not city:
        return jsonify({
            "success": False,
            "message": "Please enter a city or destination.",
            "places": [],
            "hotels": [],
            "food": [],
        }), 400

    places = filter_by_city(places_df, city)
    hotels = filter_by_city(hotels_df, city)
    food = filter_by_city(food_df, city)

    return jsonify({
        "success": True,
        "city": city.title(),
        "places": records(places),
        "hotels": records(hotels),
        "food": records(food),
    })


@app.route("/api/destination", methods=["GET"])
def destination():
    city = request.args.get("city", "").strip()

    if not city:
        return jsonify({"success": False, "message": "Please enter a destination."}), 400

    places = filter_by_city(places_df, city)
    hotels = filter_by_city(hotels_df, city)
    food = filter_by_city(food_df, city)

    return jsonify({
        "success": True,
        "city": city.title(),
        "places": records(places),
        "hotels": records(hotels),
        "food": records(food),
    })


@app.route("/api/places", methods=["GET"])
def all_places():
    return jsonify({"success": True, "count": len(places_df), "data": records(places_df)})


@app.route("/api/hotels", methods=["GET"])
def all_hotels():
    city = request.args.get("city", "").strip()
    result = filter_by_city(hotels_df, city) if city else hotels_df
    return jsonify({"success": True, "count": len(result), "data": records(result)})


@app.route("/api/food", methods=["GET"])
def all_food():
    city = request.args.get("city", "").strip()
    result = filter_by_city(food_df, city) if city else food_df
    return jsonify({"success": True, "count": len(result), "data": records(result)})


def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        earth_radius = 6371.0

        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )

        return round(
            earth_radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)),
            2,
        )
    except (TypeError, ValueError, ZeroDivisionError):
        return None


@app.route("/api/nearby", methods=["GET"])
def nearby():
    latitude = request.args.get("lat")
    longitude = request.args.get("lon")

    if latitude is None or longitude is None:
        return jsonify({
            "success": False,
            "message": "Location coordinates are required.",
            "places": [],
        }), 400

    if places_df.empty:
        return jsonify({
            "success": False,
            "message": "Places dataset not found.",
            "places": [],
        }), 500

    if "latitude" not in places_df.columns or "longitude" not in places_df.columns:
        return jsonify({
            "success": False,
            "message": "Latitude and longitude are not available in places dataset.",
            "places": [],
        }), 500

    nearby_places = []

    for _, row in places_df.iterrows():
        distance = calculate_distance(
            latitude,
            longitude,
            row.get("latitude"),
            row.get("longitude"),
        )

        if distance is not None and distance <= 70:
            place = row.to_dict()
            place["distance_km"] = distance
            nearby_places.append(place)

    nearby_places.sort(key=lambda item: item.get("distance_km", float("inf")))

    # The browser already knows the coordinates, so we do not pretend to reverse-geocode
    # a city here. Both "places" and "data" are returned for compatibility.
    return jsonify({
        "success": True,
        "radius_km": 70,
        "count": len(nearby_places),
        "places": nearby_places,
        "data": nearby_places,
    })


@app.route("/api/plan", methods=["POST"])
def plan_trip():
    data = request.get_json(silent=True) or {}

    city = str(data.get("city", "")).strip()
    try:
        days = int(data.get("days", 1))
    except (TypeError, ValueError):
        days = 0

    try:
        budget = float(data.get("budget", 0))
    except (TypeError, ValueError):
        budget = 0

    if not city:
        return jsonify({"success": False, "message": "Please enter a destination."}), 400

    if days < 1:
        return jsonify({"success": False, "message": "Days must be at least 1."}), 400

    if budget <= 0:
        return jsonify({"success": False, "message": "Budget must be greater than 0."}), 400

    city_places = filter_by_city(places_df, city)
    city_hotels = filter_by_city(hotels_df, city)
    city_food = filter_by_city(food_df, city)

    # -----------------------------
    # Hotel recommendation
    # -----------------------------
    selected_hotel = None
    hotel_cost = 0.0

    if not city_hotels.empty and "price_per_night" in city_hotels.columns:
        city_hotels["price_per_night"] = pd.to_numeric(
            city_hotels["price_per_night"], errors="coerce"
        )
        city_hotels = city_hotels.dropna(subset=["price_per_night"])

        if not city_hotels.empty:
            affordable = city_hotels[
                city_hotels["price_per_night"] * days <= budget * 0.45
            ]

            candidates = affordable if not affordable.empty else city_hotels
            selected_hotel = candidates.sort_values("price_per_night").iloc[0].to_dict()
            hotel_cost = float(selected_hotel["price_per_night"]) * days

    # -----------------------------
    # Food recommendation
    # -----------------------------
    selected_food = []
    food_cost_per_day = 0.0

    if not city_food.empty and "avg_price" in city_food.columns:
        city_food["avg_price"] = pd.to_numeric(
            city_food["avg_price"], errors="coerce"
        )
        city_food = city_food.dropna(subset=["avg_price"])

        if not city_food.empty:
            selected_food = records(
                city_food.sort_values("avg_price").head(3)
            )
            food_cost_per_day = float(city_food["avg_price"].mean())

    total_food_cost = food_cost_per_day * days

    # -----------------------------
    # Place recommendation
    # -----------------------------
    selected_places = []

    if not city_places.empty:
        if "rating" in city_places.columns:
            city_places["rating"] = pd.to_numeric(
                city_places["rating"], errors="coerce"
            )
            city_places = city_places.sort_values(
                "rating", ascending=False, na_position="last"
            )

        selected_places = records(
            city_places.head(min(days * 3, len(city_places)))
        )

    # -----------------------------
    # Local travel estimate
    # -----------------------------
    travel_cost_per_day = 350 if days >= 5 else 400
    local_travel_cost = travel_cost_per_day * days

    estimated_total = hotel_cost + total_food_cost + local_travel_cost

    budget_status = (
        "Your trip is within the budget."
        if estimated_total <= budget
        else "Estimated cost is above your budget. Consider a lower-cost hotel or fewer activities."
    )

    # -----------------------------
    # Daily plan
    # -----------------------------
    daily_plan = []
    for day in range(1, days + 1):
        day_places = selected_places[(day - 1) * 3 : day * 3]
        daily_plan.append({
            "day": day,
            "places": day_places,
        })

    return jsonify({
        "success": True,
        "destination": city.title(),
        "city": city.title(),  # backward compatibility
        "days": days,
        "budget": budget,
        "recommended_hotel": selected_hotel,
        "hotel_cost": round(hotel_cost, 2),
        "food": selected_food,
        "food_cost_per_day": round(food_cost_per_day, 2),
        "total_food_cost": round(total_food_cost, 2),
        "local_travel_cost": round(local_travel_cost, 2),
        "estimated_total": round(estimated_total, 2),
        "remaining_budget": round(budget - estimated_total, 2),
        "budget_status": budget_status,
        "places": selected_places,
        "daily_plan": daily_plan,
        "summary": budget_status,  # frontend compatibility
        "budget_breakdown": {
            "hotel": round(hotel_cost, 2),
            "food": round(total_food_cost, 2),
            "travel": round(local_travel_cost, 2),
            "activities": 0,
        },
        "days_plan": daily_plan,  # frontend compatibility
    })


if __name__ == "__main__":
    print("=" * 60)
    print("TRAVELLING & TOURISM GUIDE MANAGEMENT SYSTEM")
    print("=" * 60)
    print(f"Places loaded : {len(places_df)} records")
    print(f"Hotels loaded : {len(hotels_df)} records")
    print(f"Food loaded   : {len(food_df)} records")
    print("Server: http://127.0.0.1:5000")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
