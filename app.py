from flask import Flask, render_template, request
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import random
import re

app = Flask(__name__)

# ===== LOAD FLAN-T5-LARGE =====
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")

# ===== CHAT HISTORY =====
chat_history = []

# ===== CITY LISTS =====
UAE_CITIES = ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"]
INTL_CITIES = ["New York", "London", "Paris", "Tokyo", "Sydney", "Mumbai", "Singapore", "Seoul", "Shanghai", "Beijing", "Berlin", "Budapest", "Milan", "Moscow"]
ALL_CITIES = UAE_CITIES + INTL_CITIES

# ===== WEATHER FUNCTION (Optional, still works locally) =====
import requests
def get_weather(city="Dubai"):
    try:
        # Replace with your OpenWeather API key
        API_KEY = "9ed9b6938cc15732cc89f8e8bbcb3a65"
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        data = requests.get(url).json()
        if data.get("cod") != 200:
            return f"Could not find weather info for {city}."
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"].capitalize()
        return f"{desc}, Temp: {temp}°C"
    except:
        return "Weather data not available."

# ===== MAIN ROUTE =====
@app.route("/", methods=["GET", "POST"])
def home():
    global chat_history
    if request.method == "POST":
        user_input = request.form.get("prompt", "").strip()
        if not user_input:
            chat_history.append(("Solar Buddy", "Please type something ☀️"))
            return render_template("index.html", chat_history=chat_history)

        sentences = [s for s in re.split(r"[.!?;\n]+", user_input) if s.strip()]
        if len(sentences) > 1:
            chat_history.append(("Solar Buddy", "Please ask only one question at a time ☀️"))
            return render_template("index.html", chat_history=chat_history)

        chat_history.append(("You", user_input))
        lower_input = user_input.lower()

        # ===== WEATHER =====
        if any(word in lower_input for word in ["weather", "temperature", "humidity"]):
            city = next((c for c in ALL_CITIES if c.lower() in lower_input), "Dubai")
            weather_report = get_weather(city)
            chat_history.append(("Solar Buddy", f"Weather in {city}: {weather_report}"))

        # ===== GREETINGS =====
        elif any(g in lower_input for g in ["hi", "hello", "hey"]):
            chat_history.append(("Solar Buddy", random.choice([
                "Hello! ☀️ How can I brighten your solar knowledge today?",
                "Hey! Ready to learn something about solar energy?",
                "Hi there! 🌞 Ask me anything about solar power."
            ])))

        # ===== SOLAR QUESTIONS =====
        elif any(word in lower_input for word in ["solar", "energy", "sun", "panel"]):
            prompt = f"You are Solar Buddy, answer clearly and politely about solar energy: {user_input}"
            inputs = tokenizer(prompt, return_tensors="pt")
            outputs = model.generate(**inputs, max_length=200)
            answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
            chat_history.append(("Solar Buddy", answer))

        # ===== OFF-TOPIC =====
        else:
            chat_history.append(("Solar Buddy", "I mainly talk about solar energy or weather ☀️ Please ask about those topics."))

    return render_template("index.html", chat_history=chat_history)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
