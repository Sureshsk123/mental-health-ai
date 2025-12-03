Mental Health Risk Predictor

A simple web app that estimates daily mental health risk using mood, sleep, and screen time, plus optional speech‑based mood detection. Built with Flask, SQLite, Bootstrap, and Chart.js.

Features

- Daily risk prediction based on:
  - Self‑reported mood (happy / neutral / sad / very sad)  
  - Sleep hours  
  - Screen time hours  
- Color‑coded risk levels (Low / Medium / High)  
- Trend chart of risk over recent days  
- Recent history table  
- Simple “Switch User” support using sessions so each user sees their own data  
- Lightweight SQLite storage for demo use

Tech Stack

- Backend: Python, Flask, Flask‑CORS, SQLite  
- Frontend: HTML, CSS, Bootstrap 5, Vanilla JS, Chart.js  
- Deployment: (fill when you deploy, e.g. Vercel)



How It Works

- The frontend collects mood, sleep, and screen time and sends them to a `/api/risk-score` endpoint.  
- The backend applies simple rule‑based scoring to compute a risk score (0–100) and a risk level.  
- Each prediction is stored in a `history` table (SQLite) along with the current username from the session.  
- The `/api/history` endpoint returns the last 10 entries for the current user, which are displayed in the table and chart.  
- A `/api/speech-mood` endpoint analyzes transcribed speech text and infers mood from positive/negative keywords.

Future Improvements

- Replace rule‑based scoring with an ML model trained on real data  
- Add authentication and secure user accounts  
- Connect to wearable / phone APIs for automatic sleep and usage data  
- Counselor dashboard to monitor high‑risk users


