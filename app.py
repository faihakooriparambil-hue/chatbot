from flask import Flask, render_template, request
import requests
import random
import re
import os

app = Flask(__name__)

# ===== CHAT HISTORY =====
chat_history = []

# ===== API KEYS =====
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")  # set this in Render
HF_API_KEY = os.environ.get("HF_API_KEY")                    # set this in Render

# ===== HUGGING FACE MODEL =====
MODEL_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# ===== CITY LISTS =====
UAE_CITIES = [
    "Abu Dhabi,AE", "Dubai,AE", "Sharjah,AE", "Ajman,AE",
    "Ras Al Khaimah,AE", "Fujairah,AE", "Umm Al Quwain,AE"
]

INTERNATIONAL_CITIES = [
    "New York,US", "London,GB", "Paris,FR", "Tokyo,JP", "Sydney,AU",
    "Mumbai,IN", "Singapore,SG", "Seoul,KR", "Shanghai,CN", "Beijing,CN",
    "Berlin,DE", "Budapest,HU", "Milan,IT", "Moscow,RU"
]

ALL_CITIES = UAE_CITIES + INTERNATIONAL_CITIES

# ===== WEATHER FUNCTION =====
def get_weather(city="Dubai,AE"):
    if not OPENWEATHER_API_KEY:
        return "Weather API key not set 🌥️"

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        data = requests.get(url, timeout=10).json()
        if data.get("cod") != 200:
            return f"Sorry, I couldn't find weather info for '{city.split(',')[0]}'"

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["description"].capitalize()

        if "rain" in desc.lower():
            air_status = "It looks rainy 🌧️ — stay cozy!"
        elif "clear" in desc.lower():
            air_status = "The sky’s clear ☀️ — perfect for solar panels!"
        elif "cloud" in desc.lower():
            air_status = "A bit cloudy ☁️ but still good for solar energy."
        else:
            air_status = "Moderate conditions outside 🌤️."

        return f"{desc}. Temp: {temp}°C (feels like {feels_like}°C). Humidity: {humidity}%. {air_status}"
    except:
        return "Weather info couldn’t be fetched right now 🌥️"

# ===== CITY DETECTION =====
def extract_city(user_input):
    user_input = user_input.lower()
    for city in ALL_CITIES:
        if city.split(',')[0].lower() in user_input:
            return city
    return "Dubai,AE"

# ===== MAIN ROUTE =====
@app.route("/", methods=["GET", "POST"])
def home():
    global chat_history
    if request.method == "POST":
        user_input = request.form.get("prompt", "").strip()
        if not user_input:
            chat_history.append(("Solar Buddy", "Please type something ☀️"))
            return render_template("index.html", chat_history=chat_history)

        sentences = [s for s in re.split(r'[.!?;\n]+', user_input) if s.strip()]
        if len(sentences) > 1:
            chat_history.append(("Solar Buddy", "Please ask only one question at a time ☀️"))
            return render_template("index.html", chat_history=chat_history)

        chat_history.append(("You", user_input))
        lower_input = user_input.lower()

        # ===== WEATHER =====
        if any(word in lower_input for word in ["weather", "temperature", "humidity"]):
            city = extract_city(user_input)
            weather_report = get_weather(city)
            chat_history.append(("Solar Buddy", f"Here’s the weather in {city.split(',')[0]}: {weather_report}"))

        # ===== GREETINGS =====
        elif any(g in lower_input for g in ["hi", "hello", "hey"]):
            chat_history.append(("Solar Buddy", random.choice([
                "Hello! ☀️ How can I brighten your solar knowledge today?",
                "Hey! Ready to learn something about solar energy?",
                "Hi there! 🌞 Ask me anything about solar power."
            ])))

        # ===== SOLAR QUESTIONS =====
        elif any(word in lower_input for word in ["solar", "energy", "sun", "panel"]):
            if not HF_API_KEY:
                chat_history.append(("Solar Buddy", "Model API key not set 🔐"))
            else:
                payload = {"inputs": f"You are Solar Buddy. Answer politely about solar energy: {user_input}"}
                try:
                    res = requests.post(MODEL_URL, headers=HEADERS, json=payload, timeout=60)
                    data = res.json()
                    if isinstance(data, list) and "generated_text" in data[0]:
                        answer = data[0]["generated_text"]
                    else:
                        answer = "Sorry, I couldn’t generate an answer right now."
                except:
                    answer = "Sorry, I couldn’t generate an answer right now."
                chat_history.append(("Solar Buddy", answer))

        # ===== OFF-TOPIC =====
        else:
            chat_history.append(("Solar Buddy", "I mainly talk about solar energy or weather ☀️ Please ask about those topics."))

    return render_template("index.html", chat_history=chat_history)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
