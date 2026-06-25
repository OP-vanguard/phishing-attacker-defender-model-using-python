🎣 Hybrid AI Cyber-Range Sandbox — Phishing Attacker & Defender Model

A full-stack adversary emulation and incident response simulation built entirely in Python. Models a complete attack/defense lifecycle: a red-team controller generates realistic polymorphic phishing scenarios, while a blue-team SOC command center detects, classifies, and triages them in real time. Designed to mirror how real SOC analysts handle phishing at scale.


🎯 Why I Built This

Phishing is consistently one of the top attack vectors in real-world breaches. SOC analysts need to distinguish legitimate emails from suspicious or malicious ones — fast, and at volume. I wanted to understand both sides: how attackers craft convincing phishing emails using evasion techniques, and how defenders build detection logic to catch them. This project simulates the full cycle in a controlled local environment.


🚀 What It Does

Red-Team Controller (email_sender.py)


Simulates a multi-scenario phishing attack matrix with dynamic payload variations
Supports online mode (real delivery channels) and offline mode (local simulation for safe lab use)
Injects evasion techniques including zero-width space padding, Cyrillic homoglyph spoofing, and keyword spacing tricks
Transmits attack telemetry over UDP port 5005 to the blue-team listener in real time


Email Generator (generate_emails.py)


Produces synthetic phishing and benign emails with randomized content, sender spoofing, and urgency language
Varies payload structure to simulate polymorphic attack patterns


SOC Command Center / Blue-Team HUD (gui_app.py)


Runs a continuous asynchronous UDP listener on port 5005, capturing attack telemetry instantly
Classifies every incoming email as Safe / Suspicious / Phishing using a layered detection pipeline
Features a real-time GUI dashboard displaying live alert feeds, classification results, and risk metrics


Detection Engine (detect_phishing.py)


Offline heuristics engine handles detection without API dependency
Falls back to localized evaluation under rate constraints — always operational
Maps detected techniques to the MITRE ATT&CK framework automatically



🔬 Heuristics Detection Matrix

Evasion TechniqueDetection MethodZero-Width Space PaddingUnicode \u200b consecutive character detectionCyrillic Homoglyph SpoofingCharacter set analysis on sender domain stringsKeyword Spacing ObfuscationPattern matching for exploded character spacing in high-urgency textBehavioral MismatchCross-verifies urgency language against automated User-Agent strings (python-requests, curl)


🏗️ Technical Architecture

[ email_sender.py ]          [ generate_emails.py ]
  Red-Team Controller    +     Polymorphic Email Engine
         |
         | UDP Port 5005 (real-time telemetry)
         ▼
[ gui_app.py ]               [ detect_phishing.py ]
  SOC Command HUD        +     Heuristics + MITRE Mapping Engine
  (Async UDP Listener)         (Offline-capable)


Multi-threaded async listener keeps the GUI responsive during high-volume attack bursts
Hybrid detection pipeline: AI-assisted classification with offline heuristics fallback
UDP telemetry channel simulates real network traffic between attacker and defender systems



🛠️ Installation & Setup

bash# Clone the repository
git clone https://github.com/OP-vanguard/phishing-attacker-defender-model-using-python.git
cd phishing-attacker-defender-model-using-python

# Install dependencies
pip install -r requirements.txt

# Step 1: Launch the SOC monitoring interface
python gui_app.py

# Step 2: Fire phishing scenarios from the red-team controller
python email_sender.py


Note: Run gui_app.py first so the UDP listener is active before the attacker begins transmitting.




🗺️ MITRE ATT&CK Coverage

TechniqueATT&CK IDPhishingT1566Spearphishing via EmailT1566.001Masquerading (Homoglyph Spoofing)T1036Defense Evasion via ObfuscationT1027User Execution (Malicious Link/Attachment)T1204


📚 What I Learned


How phishing evasion techniques work at the character and behavioral level
Building a red-team vs blue-team simulation in a local, controlled environment
Designing detection logic that works offline without relying on external APIs
Mapping real-world attack techniques to MITRE ATT&CK framework entries
Async network communication between attacker and defender components using UDP sockets
How SOC analysts triage and classify incoming alerts under real-time pressure



⚠️ Disclaimer

This project is built strictly for educational and research purposes in a controlled local lab environment. All phishing simulations are self-contained and do not interact with real external email infrastructure unless explicitly configured. Use responsibly and only in environments you own or have permission to test.


🔧 Tech Stack

Python Tkinter UDP Sockets Threading Heuristics Engine MITRE ATT&CK Phishing Detection SOC Simulation


👤 Author

OP-vanguard — Cybersecurity student | Aspiring SOC Analyst

🔗 GitHub Profile
