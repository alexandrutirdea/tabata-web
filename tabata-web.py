#!/usr/bin/python3

from flask import Flask, request, jsonify, render_template_string, send_from_directory
import threading
import time
import subprocess
from ipaddress import ip_address, ip_network
import os
import yaml

app = Flask(__name__)

# Load config from YAML
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

ACCESS_KEY = config["access_key"]
SCRIPT_PATH = config["script_path"]
PRESETS = config["presets"]

# Track workout state
tabata_state = {
    "status": "Idle",
    "phase": "",
    "phase_time_left": 0,
    "total_time_left": 0
}

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), filename)

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>🏋️ Tabata Workout</title>
    <style>
        body {
            font-family: sans-serif;
            text-align: center;
            padding-top: 40px;
            transition: background-color 0.5s ease;
        }
        h1 {
            font-size: 2em;
        }
        .timer {
            font-size: 2em;
            margin-top: 20px;
        }
        button {
            padding: 12px 20px;
            font-size: 16px;
            margin: 5px;
        }
    </style>
</head>
<body>
    <h1>Tabata Workout Timer</h1>
    <div class="timer">
        <p><strong>Status:</strong> <span id="status">Idle</span></p>
        <p><strong>Phase:</strong> <span id="phase">--</span></p>
        <p><strong>Phase Time Left:</strong> <span id="phaseTime">--</span></p>
        <p><strong>Total Time Left:</strong> <span id="totalTime">--</span></p>
    </div>
    <div>
        <button onclick="startPreset('gentle')">Gentle</button>
        <button onclick="startPreset('standard')">Standard</button>
        <button onclick="startPreset('brutal')">Brutal</button>
    </div>
    <br>
    <button onclick="startWorkout()">Custom Start</button>

    <audio id="silence" loop autoplay>
        <source src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA=" type="audio/wav">
    </audio>

    <audio id="beep-prepare"><source src="/static/prepare.mp3" type="audio/mpeg"></audio>
    <audio id="beep-work"><source src="/static/work.mp3" type="audio/mpeg"></audio>
    <audio id="beep-rest"><source src="/static/rest.mp3" type="audio/mpeg"></audio>

    <script>
        let lastPhase = "";

        function setBackgroundColor(phaseLabel) {
            const body = document.body;
            const label = phaseLabel.toLowerCase();

            if (label.includes("work")) {
                body.style.backgroundColor = "#ff4d4d";
            } else if (label.includes("rest")) {
                body.style.backgroundColor = "#4dff88";
            } else if (label.includes("prepare")) {
                body.style.backgroundColor = "#4da6ff";
            } else if (label.includes("complete")) {
                body.style.backgroundColor = "#dddddd";
            } else {
                body.style.backgroundColor = "#ffffff";
            }
        }

        function playPhaseSound(phase) {
            if (phase.includes("prepare")) {
                document.getElementById("beep-prepare").play().catch(() => {});
            } else if (phase.includes("work")) {
                document.getElementById("beep-work").play().catch(() => {});
            } else if (phase.includes("rest")) {
                document.getElementById("beep-rest").play().catch(() => {});
            }
        }

        async function fetchStatus() {
            const res = await fetch("/status");
            const data = await res.json();

            document.getElementById("status").innerText = data.status;
            document.getElementById("phase").innerText = data.phase;
            document.getElementById("phaseTime").innerText = data.phase_time_left + "s";
            document.getElementById("totalTime").innerText = data.total_time_left + "s";
            setBackgroundColor(data.phase);

            if (data.phase !== lastPhase) {
                lastPhase = data.phase;
                playPhaseSound(data.phase.toLowerCase());
            }
        }

        async function startWorkout() {
            await fetch("/start?k=8xnUr", { method: "POST" });
        }

        async function startPreset(key) {
            await fetch(`/start?k=8xnUr&p=${key}`, { method: "POST" });
        }

        document.addEventListener("click", function enableAudio() {
            const audio = document.getElementById("silence");
            if (audio && audio.paused) {
                audio.play().catch(() => {});
            }
            document.removeEventListener("click", enableAudio);
        });

        setInterval(fetchStatus, 1000);
        fetchStatus();
    </script>
</body>
</html>
"""

def is_lan_ip(ip):
    try:
        ip_obj = ip_address(ip)
        return ip_obj in ip_network("192.168.0.0/16") or ip_obj.is_loopback
    except:
        return False

def run_tabata_timer(work, rest, rounds, prepare):
    total_time = prepare + (work + rest) * rounds - rest
    total_remaining = total_time
    tabata_state["status"] = "Running"

    def phase(label, duration):
        nonlocal total_remaining
        tabata_state["phase"] = label
        for t in range(duration, 0, -1):
            tabata_state["phase_time_left"] = t
            tabata_state["total_time_left"] = total_remaining
            time.sleep(1)
            total_remaining -= 1

    phase("Prepare", prepare)
    for i in range(1, rounds + 1):
        phase(f"Round {i} - Work", work)
        if i < rounds:
            phase(f"Round {i} - Rest", rest)

    tabata_state.update({
        "status": "Idle",
        "phase": "Complete",
        "phase_time_left": 0,
        "total_time_left": 0
    })

@app.route("/")
def index():
    return render_template_string(HTML_UI)

@app.route("/start", methods=["POST"])
def start_tabata():
    key = request.args.get("k")
    if key != ACCESS_KEY:
        return "Unauthorized", 403

    preset_key = request.args.get("p")
    if preset_key in PRESETS:
        params = PRESETS[preset_key]
    else:
        params = {
            "work": int(request.args.get("work", "30")),
            "rest": int(request.args.get("rest", "10")),
            "rounds": int(request.args.get("rounds", "10")),
            "prepare": int(request.args.get("prepare", "20"))
        }

    if request.remote_addr.startswith("192.168."):
    	client_ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    else:
    	client_ip = request.remote_addr

    if is_lan_ip(client_ip):
        subprocess.Popen([
            "python3", "/app/workoutmusic.py",
            "Workout music",
            str((params["prepare"] + (params["work"] + params["rest"]) * params["rounds"] - params["rest"] + 59) // 60),
            "31", "YOUR_PLEX_PLAYER"
        ])
    else:
        print(f"🌐 Remote request from {client_ip} — skipping music")

    threading.Thread(
        target=run_tabata_timer,
        args=(params["work"], params["rest"], params["rounds"], params["prepare"]),
        daemon=True
    ).start()

    subprocess.Popen([
        SCRIPT_PATH,
        str(params["work"]),
        str(params["rest"]),
        str(params["rounds"]),
        str(params["prepare"])
    ])

    return "🏁 Tabata started", 200

@app.route("/status")
def status():
    return jsonify(tabata_state)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011)
