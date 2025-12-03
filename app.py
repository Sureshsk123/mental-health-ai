from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
from flask import send_from_directory
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"  # required for sessions
CORS(app)

# Initialize database
def init_db():
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, username TEXT, timestamp TEXT, 
                  mood TEXT, sleep_hours REAL, screen_time_hours REAL,
                  risk_score INTEGER, risk_level TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_current_user():
    return session.get("username", "guest")



@app.route("/api/health-check")
def health_check():
    return jsonify({"status": "ok", "message": "Mental health AI backend running!"})

@app.route("/api/risk-score", methods=["POST"])
def risk_score():
    data = request.get_json(force=True, silent=True) or {}
    
    mood = data.get("mood", "neutral")
    sleep_hours = data.get("sleep_hours", 7)
    screen_time_hours = data.get("screen_time_hours", 4)

    score = 0
    if mood == "sad": score += 30
    elif mood == "very_sad": score += 50
    elif mood == "happy": score -= 10
    if sleep_hours < 5: score += 30
    elif sleep_hours < 7: score += 10
    if screen_time_hours > 8: score += 30
    elif screen_time_hours > 5: score += 15
    
    score = max(0, min(100, score))
    if score < 30: level = "Low"
    elif score < 70: level = "Medium"
    else: level = "High"

    # Save to database
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    username = get_current_user()
    c.execute(
    "INSERT INTO history (username, timestamp, mood, sleep_hours, screen_time_hours, risk_score, risk_level) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)",
    (username, datetime.now().isoformat(), mood, sleep_hours, screen_time_hours, score, level)
)

    conn.commit()
    conn.close()

    return jsonify({
        "risk_score": score,
        "risk_level": level,
        "explanation": f"mood={mood}, sleep={sleep_hours}h, screen={screen_time_hours}h"
    })

@app.route("/api/speech-mood", methods=["POST"])
def speech_mood():
    data = request.get_json() or {}
    audio_text = data.get("text", "")
    
    # BETTER keyword analysis with weights
    sad_keywords = {"sad": 3, "depressed": 5, "tired": 2, "stress": 4, "cry": 4, "hurt": 3, "bad": 2, "down": 3, "anxious": 4, "lonely": 4}
    happy_keywords = {"happy": 3, "good": 2, "great": 3, "love": 3, "excited": 4, "amazing": 4, "fun": 2, "awesome": 3, "perfect": 3}
    
    text_lower = audio_text.lower()
    sad_score = sum(sad_keywords[word] for word in sad_keywords if word in text_lower)
    happy_score = sum(happy_keywords[word] for word in happy_keywords if word in text_lower)
    
    total_words = len(text_lower.split())
    confidence = min(95, max(20, (sad_score + happy_score) * 15))  # Better confidence
    
    if sad_score > happy_score * 1.2:  # More sensitive to sadness
        mood = "very_sad"
    elif sad_score > happy_score:
        mood = "sad"
    elif happy_score > sad_score * 1.2:
        mood = "happy"
    else:
        mood = "neutral"
    
    return jsonify({
        "mood": mood, 
        "confidence": confidence,
        "detected_keywords": {
            "sad": sad_score,
            "happy": happy_score,
            "text_length": total_words
        }
    })

@app.route("/api/clear-history", methods=["POST"])
def clear_history():
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route("/api/history")
def get_history():
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    username = get_current_user()
    c.execute(
        "SELECT * FROM history WHERE username = ? ORDER BY timestamp DESC LIMIT 10",
        (username,)
    )
    rows = c.fetchall()
    conn.close()
    
    history = []  # ✅ list, not set
    for row in rows:
        history.append({
            "id": row[0],
            "username": row[1],
            "timestamp": row[2],
            "mood": row[3],
            "sleep": row[4],
            "screen": row[5],
            "score": row[6],
            "level": row[7]
        })
    return jsonify(history)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/set-user", methods=["POST"])
def set_user():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip() or "guest"
    session["username"] = username
    return jsonify({"username": username})

    
if __name__ == "__main__":
    app.run(debug=True)
