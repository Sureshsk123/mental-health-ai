from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"
CORS(app)

# SQLAlchemy engine (Postgres via DATABASE_URL)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var is not set")

engine = create_engine(DATABASE_URL)


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

    # scoring logic
    score = 0
    if mood == "sad":
        score += 30
    elif mood == "very_sad":
        score += 50
    elif mood == "happy":
        score -= 10

    if sleep_hours < 5:
        score += 30
    elif sleep_hours < 7:
        score += 10

    if screen_time_hours > 8:
        score += 30
    elif screen_time_hours > 5:
        score += 15

    score = max(0, min(100, score))
    if score < 30:
        level = "Low"
    elif score < 70:
        level = "Medium"
    else:
        level = "High"

    # Save to Postgres via SQLAlchemy
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO history
                (username, timestamp, mood, sleep_hours, screen_time_hours, risk_score, risk_level)
                VALUES (:username, :timestamp, :mood, :sleep_hours, :screen_time_hours, :risk_score, :risk_level)
                """
            ),
            {
                "username": get_current_user(),
                "timestamp": datetime.now().isoformat(),
                "mood": mood,
                "sleep_hours": sleep_hours,
                "screen_time_hours": screen_time_hours,
                "risk_score": score,
                "risk_level": level,
            },
        )

    return jsonify(
        {
            "risk_score": score,
            "risk_level": level,
            "explanation": f"mood={mood}, sleep={sleep_hours}h, screen={screen_time_hours}h",
        }
    )


@app.route("/api/speech-mood", methods=["POST"])
def speech_mood():
    data = request.get_json() or {}
    audio_text = data.get("text", "")

    sad_keywords = {
        "sad": 3,
        "depressed": 5,
        "tired": 2,
        "stress": 4,
        "cry": 4,
        "hurt": 3,
        "bad": 2,
        "down": 3,
        "anxious": 4,
        "lonely": 4,
    }
    happy_keywords = {
        "happy": 3,
        "good": 2,
        "great": 3,
        "love": 3,
        "excited": 4,
        "amazing": 4,
        "fun": 2,
        "awesome": 3,
        "perfect": 3,
    }

    text_lower = audio_text.lower()
    sad_score = sum(weight for word, weight in sad_keywords.items() if word in text_lower)
    happy_score = sum(
        weight for word, weight in happy_keywords.items() if word in text_lower
    )

    total_words = len(text_lower.split())
    confidence = min(95, max(20, (sad_score + happy_score) * 15))

    if sad_score > happy_score * 1.2:
        mood = "very_sad"
    elif sad_score > happy_score:
        mood = "sad"
    elif happy_score > sad_score * 1.2:
        mood = "happy"
    else:
        mood = "neutral"

    return jsonify(
        {
            "mood": mood,
            "confidence": confidence,
            "detected_keywords": {
                "sad": sad_score,
                "happy": happy_score,
                "text_length": total_words,
            },
        }
    )


@app.route("/api/clear-history", methods=["POST"])
def clear_history():
    username = get_current_user()
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM history WHERE username = :username"),
            {"username": username},
        )
    return jsonify({"status": "success"})


@app.route("/api/history")
def get_history():
    username = get_current_user()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, username, timestamp, mood, sleep_hours, screen_time_hours, risk_score, risk_level
                FROM history
                WHERE username = :username
                ORDER BY timestamp DESC
                LIMIT 10
                """
            ),
            {"username": username},
        ).fetchall()

    history = []
    for row in rows:
        history.append(
            {
                "id": row.id,
                "username": row.username,
                "timestamp": row.timestamp,
                "mood": row.mood,
                "sleep": row.sleep_hours,
                "screen": row.screen_time_hours,
                "score": row.risk_score,
                "level": row.risk_level,
            }
        )
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
