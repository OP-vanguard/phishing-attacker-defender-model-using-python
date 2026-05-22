# 🛰️ Hybrid AI Cyber-Range Sandbox

A standalone, multi-threaded local cyber range modeling a complete adversary emulation and incident response lifecycle. This project features an automated polymorphic traffic injector communicating over local network sockets with a custom blue-team monitoring command center.

## 📡 Core System Architecture
* **Red-Team Controller (`email_sender.py`):** Simulates a multi-scenario attack matrix, introducing dynamic payload variations and handling real-time delivery channels.
* **Blue-Team Command HUD (`gui_app.py`):** Runs a continuous asynchronous background listener on UDP port 5005 to capture incoming network telemetry payloads instantly.
* **Hybrid Core Logic:** Employs an offline heuristics engine to parse byte streams, calculate risk severity metrics, map threats to the MITRE ATT&CK framework, and falls back to localized evaluations under API rate constraints.

## 🔬 Heuristics Engine Detection Matrix
1. **Defense Evasion:** Identifies multi-consecutive hidden zero-width spaces (`\u200b`).
2. **Identity Spoofing:** Sifts lookalike Cyrillic homoglyph characters used in forged sender domains.
3. **Keyword Spacing Padding:** Catches exploded character spacing tricks inside high-velocity administrative text strings.
4. **Behavioral Mismatches:** Dynamically cross-verifies high-urgency operational text context against automated script-based User-Agent strings (`python-requests`, `curl`).

## 🛠️ Installation & Setup
1. Clone the repository to your environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Launch the monitoring engine console: `python gui_app.py`
4. Fire traffic bursts from the adversary controller: `python email_sender.py`
