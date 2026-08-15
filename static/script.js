/* Smart AI Tourism Guide - corrected frontend */

const API_URL = ""; // Same Flask server. No localhost/CORS mismatch.

let currentCity = "";
let currentLatitude = null;
let currentLongitude = null;

document.addEventListener("DOMContentLoaded", () => {
    loadPopularPlaces();
});

async function fetchJSON(url, options = {}) {
    const response = await fetch(`${API_URL}${url}`, options);
    let data = null;

    try {
        data = await response.json();
    } catch {
        throw new Error(`Server returned HTTP ${response.status}`);
    }

    if (!response.ok || data.success === false) {
        throw new Error(data.message || `Request failed: HTTP ${response.status}`);
    }

    return data;
}

async function searchDestination() {
    const input = document.getElementById("searchInput");
    const city = input.value.trim();

    if (!city) {
        alert("Please enter a city or destination.");
        return;
    }

    currentCity = city;

    const resultSection = document.getElementById("searchResult");
    const resultContent = document.getElementById("searchResultContent");

    resultSection.classList.remove("hidden");
    resultContent.innerHTML = `<div class="loading">🔎 Searching for ${escapeHTML(city)}...</div>`;

    try {
        const data = await fetchJSON(`/api/search?city=${encodeURIComponent(city)}`);

        displaySearchResults(data);
        document.getElementById("hotelsContainer").innerHTML =
            createHotelCards(data.hotels || []);
        document.getElementById("foodContainer").innerHTML =
            createFoodCards(data.food || []);

        resultSection.scrollIntoView({ behavior: "smooth" });
    } catch (error) {
        console.error(error);
        resultContent.innerHTML = `
            <div class="loading">
                ❌ ${escapeHTML(error.message)}
                <br>Please make sure app.py is running.
            </div>
        `;
    }
}

function displaySearchResults(data) {
    const container = document.getElementById("searchResultContent");
    const places = data.places || [];

    if (!places.length) {
        container.innerHTML = `
            <div class="loading">
                😕 No tourism data found for
                <strong>${escapeHTML(currentCity)}</strong>.
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="card-grid">
            ${places.map(createPlaceCard).join("")}
        </div>
    `;
}

async function loadPopularPlaces() {
    const container = document.getElementById("placesContainer");

    try {
        const data = await fetchJSON("/api/popular-places");
        const places = data.places || [];

        container.innerHTML = places.length
            ? places.map(createPlaceCard).join("")
            : `<div class="loading">No places available.</div>`;
    } catch (error) {
        console.error(error);
        container.innerHTML = `
            <div class="loading">
                ⚠️ ${escapeHTML(error.message)}
                <br>Start app.py and refresh the page.
            </div>
        `;
    }
}

function createPlaceCard(place) {
    const name = place.name || place.place || "Tourist Place";
    const city = place.city || "";
    const state = place.state || "";
    const category = place.category || "Tourist Attraction";
    const description = place.description || "Beautiful destination to explore.";
    const bestTime = place.best_time || place.bestTime || "Check local conditions";
    const image = place.image || getCategoryImage(category);

    return `
        <div class="card">
            <img
                class="card-image"
                src="${escapeAttribute(image)}"
                alt="${escapeAttribute(name)}"
                loading="lazy"
                onerror="this.src='${escapeAttribute(getFallbackImage())}'"
            >
            <div class="card-content">
                <h3>${escapeHTML(name)}</h3>
                <p>📍 ${escapeHTML(city)}${state ? ", " + escapeHTML(state) : ""}</p>
                <p>${escapeHTML(description)}</p>
                <div class="card-info">
                    <span class="badge">${escapeHTML(category)}</span>
                    <span class="badge">⏰ ${escapeHTML(bestTime)}</span>
                    ${place.distance_km !== undefined
                        ? `<span class="badge">📏 ${escapeHTML(String(place.distance_km))} km</span>`
                        : ""}
                </div>
            </div>
        </div>
    `;
}

function createHotelCards(hotels) {
    if (!hotels.length) {
        return `<div class="loading">🏨 No hotels found for this destination.</div>`;
    }

    return hotels.map(hotel => {
        const name = hotel.hotel || hotel.name || "Hotel";
        const city = hotel.city || "";
        const state = hotel.state || "";
        const price = hotel.price_per_night ?? hotel.price ?? "N/A";
        const rating = hotel.rating ?? "N/A";
        const type = hotel.type || "Hotel";
        const description = hotel.description || "Comfortable stay for travellers.";

        return `
            <div class="card">
                <img class="card-image"
                     src="${escapeAttribute(getHotelImage())}"
                     alt="${escapeAttribute(name)}"
                     loading="lazy">
                <div class="card-content">
                    <h3>🏨 ${escapeHTML(name)}</h3>
                    <p>📍 ${escapeHTML(city)}${state ? ", " + escapeHTML(state) : ""}</p>
                    <p>${escapeHTML(description)}</p>
                    <div class="card-info">
                        <span class="badge price">₹${escapeHTML(String(price))}/night</span>
                        <span class="badge rating">⭐ ${escapeHTML(String(rating))}</span>
                        <span class="badge">${escapeHTML(type)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

function createFoodCards(foodList) {
    if (!foodList.length) {
        return `<div class="loading">🍛 No food information found.</div>`;
    }

    return foodList.map(food => {
        const foodName = food.food || food.name || "Local Food";
        const city = food.city || "";
        const state = food.state || "";
        const type = food.type || "Local Speciality";
        const price = food.avg_price ?? food.price ?? "N/A";
        const description = food.description || "Try this local speciality.";
        const meal = food.meal_type || food.meal || "Anytime";

        return `
            <div class="card">
                <img class="card-image"
                     src="${escapeAttribute(getFoodImage())}"
                     alt="${escapeAttribute(foodName)}"
                     loading="lazy">
                <div class="card-content">
                    <h3>🍛 ${escapeHTML(foodName)}</h3>
                    <p>📍 ${escapeHTML(city)}${state ? ", " + escapeHTML(state) : ""}</p>
                    <p>${escapeHTML(description)}</p>
                    <div class="card-info">
                        <span class="badge price">₹${escapeHTML(String(price))}</span>
                        <span class="badge">${escapeHTML(type)}</span>
                        <span class="badge">🍽️ ${escapeHTML(meal)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

function findMyLocation() {
    const status = document.getElementById("locationStatus");

    if (!navigator.geolocation) {
        status.textContent = "❌ Geolocation is not supported by your browser.";
        return;
    }

    status.textContent = "📍 Finding your location...";

    navigator.geolocation.getCurrentPosition(
        async position => {
            currentLatitude = position.coords.latitude;
            currentLongitude = position.coords.longitude;
            status.textContent = "📍 Location found. Finding nearby destinations...";

            try {
                const data = await fetchJSON(
                    `/api/nearby?lat=${encodeURIComponent(currentLatitude)}&lon=${encodeURIComponent(currentLongitude)}`
                );

                displayNearbyPlaces(data.places || data.data || []);

                status.textContent =
                    `✅ Nearby places loaded (${data.count || 0} found).`;
            } catch (error) {
                console.error(error);
                status.textContent =
                    `⚠️ ${error.message}`;
            }
        },
        error => {
            console.error(error);
            status.textContent =
                error.code === 1
                    ? "❌ Location permission was denied."
                    : "❌ Unable to find your location.";
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }
    );
}

function displayNearbyPlaces(places) {
    const container = document.getElementById("placesContainer");

    if (!places.length) {
        container.innerHTML =
            `<div class="loading">😕 No nearby tourism places found within 70 km.</div>`;
        return;
    }

    container.innerHTML = places.map(createPlaceCard).join("");

    document.getElementById("places").scrollIntoView({
        behavior: "smooth"
    });
}

async function generateTripPlan() {
    const city = document.getElementById("plannerCity").value.trim();
    const days = parseInt(document.getElementById("plannerDays").value, 10);
    const budget = parseFloat(document.getElementById("plannerBudget").value);
    const result = document.getElementById("planResult");

    if (!city) {
        alert("Please enter your destination.");
        return;
    }

    if (!Number.isInteger(days) || days < 1) {
        alert("Please enter a valid number of days.");
        return;
    }

    if (!Number.isFinite(budget) || budget <= 0) {
        alert("Please enter a valid budget.");
        return;
    }

    result.classList.remove("hidden");
    result.innerHTML = `
        <div class="loading">
            🤖 Preparing your ${days}-day trip plan...
        </div>
    `;

    try {
        const data = await fetchJSON("/api/plan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ city, days, budget })
        });

        displayTripPlan(data);
    } catch (error) {
        console.error(error);
        result.innerHTML = `
            <div class="plan-day">
                <h3>❌ Unable to generate plan</h3>
                <p>${escapeHTML(error.message)}</p>
            </div>
        `;
    }
}

function displayTripPlan(data) {
    const result = document.getElementById("planResult");

    let html = `
        <h3>🤖 AI Trip Plan for ${escapeHTML(data.destination || data.city || currentCity)}</h3>
        <p>📅 Days: <strong>${escapeHTML(String(data.days ?? ""))}</strong></p>
        <p>💰 Budget: <strong>₹${escapeHTML(String(data.budget ?? ""))}</strong></p>
    `;

    if (data.budget_status) {
        html += `<p style="margin-top:15px;">${escapeHTML(data.budget_status)}</p>`;
    }

    if (data.estimated_total !== undefined) {
        html += `
            <p style="margin-top:10px;">
                Estimated total:
                <strong>₹${escapeHTML(String(data.estimated_total))}</strong>
            </p>
        `;
    }

    if (data.recommended_hotel) {
        const hotel = data.recommended_hotel;
        html += `
            <hr style="margin:20px 0;">
            <h3>🏨 Recommended Hotel</h3>
            <p>${escapeHTML(hotel.hotel || hotel.name || "Hotel")}</p>
        `;
    }

    if (Array.isArray(data.food) && data.food.length) {
        html += `
            <h3 style="margin-top:20px;">🍛 Food Suggestions</h3>
            <p>${escapeHTML(data.food.map(item => item.food || item.name || "Food").join(", "))}</p>
        `;
    }

    if (Array.isArray(data.daily_plan)) {
        data.daily_plan.forEach(day => {
            const names = (day.places || [])
                .map(place => place.name || place.place || "Place")
                .join(", ");

            html += `
                <div class="plan-day">
                    <h3>📅 Day ${escapeHTML(String(day.day ?? ""))}</h3>
                    <p>🏞️ ${escapeHTML(names || "Explore local attractions")}</p>
                </div>
            `;
        });
    }

    result.innerHTML = html;
}

function getCategoryImage(category) {
    const value = String(category || "").toLowerCase();

    if (value.includes("temple") || value.includes("spiritual") || value.includes("worship")) {
        return "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=900&q=80";
    }

    if (value.includes("beach") || value.includes("coast")) {
        return "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80";
    }

    if (value.includes("nature") || value.includes("waterfall") || value.includes("hill") || value.includes("mountain")) {
        return "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80";
    }

    if (value.includes("historic") || value.includes("historical") || value.includes("fort") || value.includes("palace")) {
        return "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=900&q=80";
    }

    return "https://images.unsplash.com/photo-1477587458883-47145ed94245?auto=format&fit=crop&w=900&q=80";
}

function getHotelImage() {
    return "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80";
}

function getFoodImage() {
    return "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80";
}

function getFallbackImage() {
    return "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80";
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    }[char]));
}

function escapeAttribute(value) {
    return escapeHTML(value);
}
