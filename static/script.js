let chart;
let recognition;
let isRecording = false;

// -------- USER SWITCHING --------
async function setUser() {
  const name = document.getElementById("usernameInput").value || "guest";
  try {
    const res = await fetch("/set-user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: name })
    });
    const data = await res.json();
    loadHistory();
    updateChart();
    const label = document.getElementById("currentUserLabel");
    if (label) {
      label.innerHTML = 'Viewing data for: <strong>' + data.username + '</strong>';
    }
  } catch (e) {
    alert("Could not switch user");
  }
}


// -------- SPEECH RECOGNITION SETUP --------
if ("webkitSpeechRecognition" in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";
}

// -------- SPEAK MOOD --------
async function startSpeech(event) {
  const speechBtn = event.target;
  const speechDiv = document.getElementById("speechText");

  if (!recognition) {
    speechDiv.innerHTML = "❌ Speech not supported";
    speechDiv.style.display = "block";
    return;
  }

  if (isRecording) {
    recognition.stop();
    speechBtn.textContent = "🎤 Speak Mood";
    speechBtn.classList.remove("recording");
    isRecording = false;
    return;
  }

  isRecording = true;
  speechBtn.textContent = "⏹️ Stop";
  speechBtn.classList.add("recording");
  speechDiv.style.display = "block";
  speechDiv.innerHTML = "🎤 Listening... Speak now!";

  recognition.onresult = async function (e) {
    const transcript = e.results[0][0].transcript;
    speechDiv.innerHTML = `You said: "${transcript}"`;

    try {
      const res = await fetch("/api/speech-mood", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: transcript })
      });
      const data = await res.json();

      document.getElementById("mood").value = data.mood;
      speechDiv.innerHTML += `<br><strong>🎯 AI Detected: ${data.mood.toUpperCase()} (${data.confidence}% confidence)</strong>`;
    } catch (err) {
      speechDiv.innerHTML += "<br>❌ AI analysis failed";
    }
  };

  recognition.onerror = function () {
    speechDiv.innerHTML = "❌ Speech error";
  };

  recognition.onend = function () {
    speechBtn.textContent = "🎤 Speak Mood";
    speechBtn.classList.remove("recording");
    isRecording = false;
  };

  recognition.start();
}

// -------- CHECK RISK --------
async function checkRisk(event) {
  event.preventDefault();

  const mood = document.getElementById("mood").value;
  const sleep = Number(document.getElementById("sleep").value);
  const screen = Number(document.getElementById("screen").value);
  const resultDiv = document.getElementById("result");

  resultDiv.innerHTML = "Checking...";
  resultDiv.className = "";

  try {
    const res = await fetch("/api/risk-score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mood,
        sleep_hours: sleep,
        screen_time_hours: screen
      })
    });

    const data = await res.json();

    // remove old classes
    resultDiv.classList.remove("low", "medium", "high");

    // set text
    resultDiv.innerHTML = `Risk: <strong>${data.risk_level}</strong> (${data.risk_score}/100)<br>${data.explanation}`;

    // add class based on level
    if (data.risk_level === "Low") {
      resultDiv.classList.add("low");
    } else if (data.risk_level === "Medium") {
      resultDiv.classList.add("medium");
    } else {
      resultDiv.classList.add("high");
    }

    loadHistory();
    updateChart();
  } catch (err) {
    resultDiv.innerHTML = "❌ Server not running? Start: python3 app.py";
    resultDiv.className = "high";
  }
}

// -------- LOAD HISTORY --------
async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const history = await res.json();
    const tbody = document.querySelector("#historyTable tbody");
    tbody.innerHTML = "";

    history.forEach((entry) => {
      const row = tbody.insertRow();
      row.innerHTML = `
        <td>${new Date(entry.timestamp).toLocaleString()}</td>
        <td>${entry.mood}</td>
        <td>${entry.sleep}h</td>
        <td>${entry.screen}h</td>
        <td class="${entry.level.toLowerCase()}">${entry.level} (${entry.score})</td>
      `;
    });
  } catch (e) {
    // ignore errors in history load (e.g. first deploy)
  }
}

// -------- UPDATE CHART --------
function updateChart() {
  const ctx = document.getElementById("riskChart").getContext("2d");
  if (chart) chart.destroy();

  fetch("/api/history")
    .then((res) => res.json())
    .then((history) => {
      if (history.length === 0) {
        chart = new Chart(ctx, {
          type: "line",
          data: {
            labels: ["No data yet"],
            datasets: [
              {
                label: "Risk Score",
                data: [0],
                borderColor: "#007bff"
              }
            ]
          }
        });
        return;
      }

      const recent = history.slice(0, 10);
      const labels = recent.map((h) =>
        new Date(h.timestamp).toLocaleDateString()
      );
      const scores = recent.map((h) => h.score);

      chart = new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Your Risk Trend",
              data: scores,
              borderColor: "#dc3545",
              backgroundColor: "rgba(220,53,69,0.1)",
              tension: 0.4,
              fill: true,
              pointRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          scales: {
            y: { min: 0, max: 100 }
          }
        }
      });
    })
    .catch(() => {
      chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: ["Demo"],
          datasets: [
            {
              label: "Demo",
              data: [50],
              borderColor: "#007bff"
            }
          ]
        }
      });
    });
}

// initial load
loadHistory();
updateChart();
