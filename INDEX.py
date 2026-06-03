import customtkinter as ctk
import tkinter as tk
from tkinter import *
import threading
import requests
import speech_recognition as sr
import time
import os
import webbrowser

# =========================================
# CONFIG
# =========================================
WEATHER_API_KEY = "c8558652c35dd3188649b9785b3e446b"

OLLAMA_URL = "http://localhost:11434/api/generate"

# =========================================
# CUSTOM TKINTER
# =========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =========================================
# MAIN WINDOW
# =========================================
root = ctk.CTk()

root.title("🚗 AI Driver Assistant")

root.geometry("1400x850")

# =========================================
# VARIABLES
# =========================================
voice_enabled = True
is_listening = False
continuous_mode = False
conversation_history = []

# =========================================
# STATUS UPDATE
# =========================================
def update_status(text, color):

    status_label.configure(
        text=text,
        text_color=color
    )

# =========================================
# SPEAK
# =========================================
def speak(text):

    if not voice_enabled:
        return

    update_status("🔊 Speaking...", "#ff00ff")

    try:

        safe_text = text.replace('"', '')

        os.system(f'say "{safe_text}" &')

    except:
        pass

    update_status("✅ Ready", "#00ff99")

# =========================================
# WEATHER
# =========================================
def get_weather():

    try:

        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": "Pune",
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }

        data = requests.get(
            url,
            params=params
        ).json()

        temp = data["main"]["temp"]

        cond = data["weather"][0]["main"]

        return f"{temp}°C | {cond}"

    except:

        return "Weather unavailable"

# =========================================
# CHAT DISPLAY
# =========================================
def user_print(text):

    chatbox.insert(
        END,
        f"\n🧑 YOU:\n{text}\n",
        "user"
    )

    chatbox.see(END)

# =========================================
# AI DISPLAY
# =========================================
def ai_print(text):

    chatbox.insert(
        END,
        "\n🤖 AI:\n",
        "ai"
    )

    for char in text:

        chatbox.insert(END, char)

        chatbox.update()

        time.sleep(0.005)

    chatbox.insert(END, "\n")

    chatbox.see(END)

# =========================================
# AI CHATBOT
# =========================================
def ask_ai(prompt):

    try:

        conversation_history.append(
            f"User: {prompt}"
        )

        history = "\n".join(
            conversation_history[-6:]
        )

        system_prompt = f"""
You are futuristic AI Driver Assistant.

Rules:
- Give short replies
- Prioritize driver safety
- Sound like Tesla AI
- Be smart and helpful

Conversation:
{history}

AI:
"""

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3",
                "prompt": system_prompt,
                "stream": False
            },
            timeout=120
        )

        reply = response.json()["response"]

        conversation_history.append(
            f"AI: {reply}"
        )

        return reply

    except Exception as e:

        return f"AI Error: {e}"

# =========================================
# COMMAND ROUTER
# =========================================
def handle_command(user):

    user = user.lower()

    # =====================================
    # WEATHER
    # =====================================
    if "weather" in user:

        weather = get_weather()

        return f"Weather is {weather}"

    # =====================================
    # OPEN MAPS
    # =====================================
    elif "open maps" in user:

        webbrowser.open(
            "https://maps.google.com"
        )

        return "Opening Google Maps."

    # =====================================
    # DRIVER SAFETY
    # =====================================
    elif "sleepy" in user or "tired" in user:

        return "Driver fatigue detected. Please take a short break."

    # =====================================
    # EXIT
    # =====================================
    elif "exit" in user:

        root.destroy()

    # =====================================
    # DEFAULT AI
    # =====================================
    else:

        return ask_ai(user)

# =========================================
# SEND MESSAGE
# =========================================
def send_message():

    user = entry.get()

    if user == "":
        return

    user_print(user)

    entry.delete(0, END)

    update_status(
        "🧠 Thinking...",
        "#ffaa00"
    )

    def process():

        reply = handle_command(user)

        root.after(
            0,
            lambda: finish(reply)
        )

    threading.Thread(
        target=process,
        daemon=True
    ).start()

# =========================================
# FINISH
# =========================================
def finish(reply):

    ai_print(reply)

    speak(reply)

# =========================================
# VOICE LISTEN
# =========================================
def listen():

    global is_listening

    if is_listening:
        return

    is_listening = True

    recognizer = sr.Recognizer()

    try:

        with sr.Microphone() as source:

            update_status(
                "🎤 Listening...",
                "#00ffff"
            )

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

            text = recognizer.recognize_google(
                audio
            )

            entry.delete(0, END)

            entry.insert(0, text)

            send_message()

    except:

        update_status(
            "Voice Error",
            "red"
        )

    is_listening = False

# =========================================
# CONTINUOUS MODE
# =========================================
def toggle_continuous():

    global continuous_mode

    continuous_mode = not continuous_mode

    if continuous_mode:

        ai_print(
            "Continuous listening activated."
        )

        threading.Thread(
            target=continuous_loop,
            daemon=True
        ).start()

    else:

        ai_print(
            "Continuous listening stopped."
        )

# =========================================
# CONTINUOUS LOOP
# =========================================
def continuous_loop():

    while continuous_mode:

        listen()

        time.sleep(1)

# =========================================
# SIDEBAR
# =========================================
sidebar = ctk.CTkFrame(
    root,
    width=300,
    corner_radius=0
)

sidebar.pack(
    side=LEFT,
    fill=Y
)

# =========================================
# TITLE
# =========================================
title = ctk.CTkLabel(
    sidebar,
    text="🚗 DRIVER AI",
    font=("Arial", 32, "bold")
)

title.pack(pady=30)

# =========================================
# WEATHER
# =========================================
weather_label = ctk.CTkLabel(
    sidebar,
    text=f"🌦 {get_weather()}",
    font=("Arial", 18)
)

weather_label.pack(pady=10)

# =========================================
# STATUS
# =========================================
status_label = ctk.CTkLabel(
    sidebar,
    text="✅ Ready",
    text_color="#00ff99",
    font=("Arial", 18, "bold")
)

status_label.pack(pady=20)

# =========================================
# BUTTONS
# =========================================

ctk.CTkButton(
    sidebar,
    text="🗺 Open Maps",
    width=240,
    height=50,
    command=lambda: webbrowser.open(
        "https://maps.google.com"
    )
).pack(pady=10)

ctk.CTkButton(
    sidebar,
    text="🎤 Voice Command",
    width=240,
    height=50,
    command=lambda: threading.Thread(
        target=listen,
        daemon=True
    ).start()
).pack(pady=10)

ctk.CTkButton(
    sidebar,
    text="🧠 Continuous Mode",
    width=240,
    height=50,
    command=toggle_continuous
).pack(pady=10)

# =========================================
# MAIN PANEL
# =========================================
main_frame = ctk.CTkFrame(root)

main_frame.pack(
    side=RIGHT,
    expand=True,
    fill=BOTH
)

# =========================================
# CHATBOX
# =========================================
chatbox = tk.Text(
    main_frame,
    bg="#0b0f19",
    fg="#00ffe7",
    font=("Consolas", 14),
    padx=20,
    pady=20,
    insertbackground="white",
    relief="flat"
)

chatbox.pack(
    expand=True,
    fill=BOTH,
    padx=20,
    pady=20
)

chatbox.tag_config(
    "user",
    foreground="#00ffff"
)

chatbox.tag_config(
    "ai",
    foreground="#ff00ff"
)

# =========================================
# BOTTOM BAR
# =========================================
bottom = ctk.CTkFrame(
    main_frame,
    height=100
)

bottom.pack(fill=X)

# =========================================
# ENTRY
# =========================================
entry = ctk.CTkEntry(
    bottom,
    placeholder_text="Ask your AI Driver Assistant...",
    height=55,
    font=("Arial", 16)
)

entry.pack(
    side=LEFT,
    expand=True,
    fill=X,
    padx=20,
    pady=20
)

# =========================================
# SEND BUTTON
# =========================================
send_btn = ctk.CTkButton(
    bottom,
    text="Send",
    width=120,
    height=55,
    command=send_message
)

send_btn.pack(
    side=RIGHT,
    padx=20
)

# =========================================
# ENTER SUPPORT
# =========================================
root.bind(
    "<Return>",
    lambda event: send_message()
)

# =========================================
# STARTUP
# =========================================
ai_print(
    "Welcome back driver. Systems online."
)

speak(
    "Welcome back driver"
)

# =========================================
# RUN
# =========================================
root.mainloop()