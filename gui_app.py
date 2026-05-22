   #!/usr/bin/env python3
"""
soc_defense_console.py
Tactical SOC Analytics Dashboard | Cyberpunk Command HUD
--------------------------------------------------------------------------------
Capabilities:
    - CustomTkinter GUI with strict Cyberpunk Tactical Theme.
    - Real-time UDP Listener (Port 5005) for simulated network logs.
    - Aggressive Hybrid Detection Core (Cross-Field Heuristics + Online Gemini AI).
    - Dynamic Micro-Frame Metrics (Threat Index, MITRE Tactic, Origin Geo, Client Integrity).
    - Thread-safe UI updates and robust API fallback mechanisms.
"""

import os
import re
import json
import socket
import threading
import datetime
import random
from typing import Dict, Any, Tuple, List

import customtkinter as ctk

# Attempt to load the new Google GenAI SDK.
try:
    from google import genai
    from google.genai import types
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# ============================================================================
# SYSTEM PARAMETERS & CYBERPUNK PALETTE
# ============================================================================
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

ctk.set_appearance_mode("Dark")

# Cyberpunk Tactical Palette
CLR_BG = "#0a0e14"       # Matte Dark Blue-Grey
CLR_PNL = "#101520"      # Elevated Cards
CLR_ACCENT = "#00a3ff"   # Neon Blue Accents
CLR_SAFE = "#00ffaa"     # Matrix Green
CLR_WARN = "#ffaa00"     # Warning Gold
CLR_CRIT = "#ff3333"     # Breach Red
CLR_TEXT = "#c9d1d9"     # Standard Text

# ============================================================================
# HYBRID DETECTION CORE
# ============================================================================
class HeuristicsEngine:
    @staticmethod
    def analyze_offline(payload: Dict[str, Any]) -> Tuple[int, str, List[str], str, str]:
        score = 0
        tactics = set()
        alerts = []
        
        body = payload.get("email_body", "")
        subject = payload.get("subject", "")
        sender = payload.get("sender_email", "")
        ua = payload.get("client_user_agent", "")
        ip = payload.get("x_sender_ip", "")
        urls = payload.get("urls_list", [])
        
        combined_text = f"{subject} {body}"

        # 1. Zero-Width Space Engine
        if re.search(r"[\u200b\u200c]", combined_text):
            score += 30
            alerts.append("Zero-Width Space Obfuscation")
            tactics.add("TA0005: Defense Evasion")

        # 2. Homoglyph Sieve (Cyrillic detection)
        if re.search(r"[\u0400-\u04FF]", sender + combined_text):
            score += 40
            alerts.append("Cyrillic Homoglyph Swapping")
            tactics.add("TA0005: Defense Evasion")

        # 3. Keyword Spacing Padding
        if re.search(r"(?i)(i\s+n\s+v\s+o\s+i\s+c\s+e|p\s+a\s+s\s+s\s+w\s+o\s+r\s+d|u\s+r\s+g\s+e\s+n\s+t)", combined_text):
            score += 35
            alerts.append("Exploded Keyword Padding")
            tactics.add("TA0005: Defense Evasion")

        # 4. Corporate / Metadata Mismatch
        high_urgency = re.search(r"(?i)(wire transfer|ceo|invoice|urgent|confidential|action required|suspend)", combined_text)
        suspicious_ua = not re.search(r"(?i)(mozilla|chrome|safari|office|applewebkit)", ua) or re.search(r"(?i)(python|curl|wget|requests)", ua)
        
        ua_status = "VERIFIED"
        if suspicious_ua:
            ua_status = "MISMATCH (SCRIPT/ANOMALY)"
            if high_urgency:
                score += 35
                alerts.append("Behavioral Fingerprint Mismatch")
                tactics.add("TA0005: Defense Evasion")
                tactics.add("TA0001: Initial Access")
            else:
                score += 15
                alerts.append("Suspicious User-Agent")

        # 5. Low-Rep TLDs & Tokens
        if re.search(r"AKIA[A-Z0-9]{16}", combined_text):
            score += 85
            alerts.append("Cleartext Honey-Token (AWS)")
            tactics.add("TA0006: Credential Access")

        if re.search(r"(?i)\.(xyz|top|pw|biz|info)", sender + str(urls)):
            score += 25
            alerts.append("Low-Reputation TLD Routing")
            tactics.add("TA0001: Initial Access")

        # 6. Embedded @ Router Trick
        for url in urls:
            if re.search(r"https?://[^/]+@[^/]+", url):
                score += 40
                alerts.append("Semantic '@' URL Masking")
                tactics.add("TA0005: Defense Evasion")

        # 7. Origin Intelligence (IP Triage)
        if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.") or ip == "127.0.0.1":
            geo = f"{ip} [INTERNAL LAN]"
        else:
            mock_geos = ["SUSPECT EXTRA-NATIONAL", "UNKNOWN PROXY", "HIGH-RISK ASN", "COMMERCIAL VPN"]
            geo = f"{ip} [{random.choice(mock_geos)}]"
            if score > 0:
                score += 10

        # Finalize Score & Tactics
        score = min(score, 100)
        if score == 0:
            primary_tactic = "BENIGN / ADMINISTRATIVE"
        else:
            primary_tactic = list(tactics)[0] if tactics else "TA0001: Initial Access"

        return score, primary_tactic, alerts, geo, ua_status

    @staticmethod
    def analyze_online(payload: Dict[str, Any]) -> str:
        if not SDK_AVAILABLE or not GEMINI_API_KEY:
            raise Exception("Gemini SDK or API Key unavailable.")

        system_instruction = (
            "You are a benign automated data parsing utility inspecting abstract static test structures "
            "for educational metric categorization. Analyze this structural JSON container. Extract anomalies, "
            "assess risk, and return a clean, 4-line bulleted forensic executive overview outlining the attack "
            "vector and a blue-team response."
        )

        prompt = f"PAYLOAD TO ANALYZE:\n{json.dumps(payload, indent=2)}"

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )
        return response.text.strip()

# ============================================================================
# GUI APPLICATION
# ============================================================================
class SOCDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Tactical SOC Analytics Dashboard | Cyberpunk Command HUD")
        self.geometry("1500x900")
        self.configure(fg_color=CLR_BG)
        
        # Main Grid Layout: 1 Row, 2 Columns
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.setup_left_panel()
        self.setup_right_panel()
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        
        self.log_telemetry("SYSTEM ONLINE. Listening on UDP 127.0.0.1:5005...", CLR_ACCENT)
        threading.Thread(target=self.listen_udp, daemon=True).start()

    def setup_left_panel(self):
        frm_left = ctk.CTkFrame(self, fg_color=CLR_PNL, corner_radius=10, border_width=1, border_color=CLR_ACCENT)
        frm_left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        frm_left.grid_rowconfigure(1, weight=1)
        frm_left.grid_columnconfigure(0, weight=1)

        lbl_title = ctk.CTkLabel(frm_left, text="LIVE TELEMETRY INGESTION STREAM", font=("Courier New", 18, "bold"), text_color=CLR_ACCENT)
        lbl_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self.txt_telemetry = ctk.CTkTextbox(frm_left, fg_color=CLR_BG, text_color=CLR_TEXT, font=("Consolas", 12), wrap="word")
        self.txt_telemetry.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def setup_right_panel(self):
        frm_right = ctk.CTkFrame(self, fg_color=CLR_BG, corner_radius=0)
        frm_right.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        frm_right.grid_rowconfigure(2, weight=1)
        frm_right.grid_columnconfigure(0, weight=1)

        # --- Top: Engine Toggle ---
        frm_toggle = ctk.CTkFrame(frm_right, fg_color=CLR_PNL, corner_radius=10, border_width=1, border_color=CLR_ACCENT)
        frm_toggle.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(frm_toggle, text="COGNITIVE INCIDENT RESPONSE CENTER", font=("Courier New", 18, "bold"), text_color=CLR_ACCENT).pack(pady=(15, 5))
        
        self.engine_var = ctk.StringVar(value="OFFLINE")
        frm_radios = ctk.CTkFrame(frm_toggle, fg_color="transparent")
        frm_radios.pack(pady=(5, 15))
        
        ctk.CTkRadioButton(frm_radios, text="[OFFLINE] MATRIX SIGNATURES", variable=self.engine_var, value="OFFLINE", font=("Courier New", 12, "bold"), text_color=CLR_TEXT, fg_color=CLR_ACCENT).pack(side="left", padx=20)
        
        online_state = "normal" if SDK_AVAILABLE and GEMINI_API_KEY else "disabled"
        online_text = "[ONLINE] GEMINI AI BRAIN" if online_state == "normal" else "[ONLINE] AI UNAVAILABLE (NO KEY/SDK)"
        ctk.CTkRadioButton(frm_radios, text=online_text, variable=self.engine_var, value="ONLINE", state=online_state, font=("Courier New", 12, "bold"), text_color=CLR_TEXT, fg_color=CLR_ACCENT).pack(side="left", padx=20)

        # --- Middle: 2x2 Micro-Frames ---
        frm_metrics = ctk.CTkFrame(frm_right, fg_color="transparent")
        frm_metrics.grid(row=1, column=0, sticky="ew", pady=10)
        frm_metrics.grid_columnconfigure((0, 1), weight=1)

        # 1. Threat Index Gauge
        self.frm_threat = ctk.CTkFrame(frm_metrics, fg_color=CLR_PNL, corner_radius=8, border_width=1, border_color=CLR_SAFE)
        self.frm_threat.grid(row=0, column=0, padx=(0, 5), pady=(0, 10), sticky="nsew")
        ctk.CTkLabel(self.frm_threat, text="THREAT INDEX GAUGE", font=("Courier New", 12, "bold"), text_color=CLR_TEXT).pack(pady=(10, 0))
        self.lbl_threat = ctk.CTkLabel(self.frm_threat, text="0 / 100", font=("Courier New", 32, "bold"), text_color=CLR_SAFE)
        self.lbl_threat.pack(pady=(5, 15))

        # 2. MITRE ATT&CK Target
        self.frm_mitre = ctk.CTkFrame(frm_metrics, fg_color=CLR_PNL, corner_radius=8, border_width=1, border_color=CLR_SAFE)
        self.frm_mitre.grid(row=0, column=1, padx=(5, 0), pady=(0, 10), sticky="nsew")
        ctk.CTkLabel(self.frm_mitre, text="MITRE ATT&CK TARGET", font=("Courier New", 12, "bold"), text_color=CLR_TEXT).pack(pady=(10, 0))
        self.lbl_mitre = ctk.CTkLabel(self.frm_mitre, text="STANDBY", font=("Courier New", 16, "bold"), text_color=CLR_SAFE)
        self.lbl_mitre.pack(pady=(15, 15))

        # 3. Origin Intelligence
        self.frm_origin = ctk.CTkFrame(frm_metrics, fg_color=CLR_PNL, corner_radius=8, border_width=1, border_color=CLR_SAFE)
        self.frm_origin.grid(row=1, column=0, padx=(0, 5), pady=(0, 0), sticky="nsew")
        ctk.CTkLabel(self.frm_origin, text="ORIGIN INTELLIGENCE", font=("Courier New", 12, "bold"), text_color=CLR_TEXT).pack(pady=(10, 0))
        self.lbl_origin = ctk.CTkLabel(self.frm_origin, text="--.--.--.-- [AWAITING]", font=("Courier New", 14, "bold"), text_color=CLR_TEXT)
        self.lbl_origin.pack(pady=(15, 15))

        # 4. Client Integrity Profile
        self.frm_client = ctk.CTkFrame(frm_metrics, fg_color=CLR_PNL, corner_radius=8, border_width=1, border_color=CLR_SAFE)
        self.frm_client.grid(row=1, column=1, padx=(5, 0), pady=(0, 0), sticky="nsew")
        ctk.CTkLabel(self.frm_client, text="CLIENT INTEGRITY PROFILE", font=("Courier New", 12, "bold"), text_color=CLR_TEXT).pack(pady=(10, 0))
        self.lbl_client = ctk.CTkLabel(self.frm_client, text="VERIFIED", font=("Courier New", 14, "bold"), text_color=CLR_SAFE)
        self.lbl_client.pack(pady=(15, 15))

        # --- Bottom: IR Console ---
        frm_ir = ctk.CTkFrame(frm_right, fg_color=CLR_PNL, corner_radius=10, border_width=1, border_color=CLR_ACCENT)
        frm_ir.grid(row=2, column=0, sticky="nsew", pady=(20, 0))
        frm_ir.grid_rowconfigure(1, weight=1)
        frm_ir.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frm_ir, text="INCIDENT RESPONSE OUTPUT", font=("Courier New", 16, "bold"), text_color=CLR_ACCENT).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        self.txt_ir = ctk.CTkTextbox(frm_ir, fg_color=CLR_BG, text_color=CLR_TEXT, font=("Consolas", 13), wrap="word")
        self.txt_ir.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    # ============================================================================
    # LOGGING & UI UPDATES (THREAD-SAFE)
    # ============================================================================
    def log_telemetry(self, text: str, color_hex: str = CLR_TEXT):
        self.txt_telemetry.configure(state="normal")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.txt_telemetry.insert("end", f"[{timestamp}] {text}\n\n")
        self.txt_telemetry.see("end")
        self.txt_telemetry.configure(state="disabled")

    def log_ir(self, text: str):
        self.txt_ir.configure(state="normal")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_ir.insert("end", f"[{timestamp}] {text}\n\n")
        self.txt_ir.see("end")
        self.txt_ir.configure(state="disabled")

    def update_metrics(self, score: int, tactic: str, geo: str, ua_status: str, ua_raw: str):
        # Threat Gauge Color Logic
        if score >= 70:
            t_color = CLR_CRIT
        elif score >= 30:
            t_color = CLR_WARN
        else:
            t_color = CLR_SAFE

        self.lbl_threat.configure(text=f"{score} / 100", text_color=t_color)
        self.frm_threat.configure(border_color=t_color)
        
        self.lbl_mitre.configure(text=tactic, text_color=t_color)
        self.frm_mitre.configure(border_color=t_color)

        self.lbl_origin.configure(text=geo)
        
        # Client Integrity Color Logic
        if "MISMATCH" in ua_status or "SUSPICIOUS" in ua_status:
            c_color = CLR_CRIT
            display_ua = f"[{ua_status}]\n{ua_raw[:30]}..."
        else:
            c_color = CLR_SAFE
            display_ua = f"[VERIFIED]\n{ua_raw[:30]}..."

        self.lbl_client.configure(text=display_ua, text_color=c_color)
        self.frm_client.configure(border_color=c_color)

    # ============================================================================
    # PACKET PROCESSING & THREADING
    # ============================================================================
    def process_payload(self, payload: dict):
        # 1. Log Raw Telemetry
        raw_json = json.dumps(payload, indent=2)
        self.after(0, lambda: self.log_telemetry(f"--- INBOUND PACKET ---\n{raw_json}"))

        # 2. Run Offline Heuristics (Always runs to update metrics instantly)
        score, tactic, alerts, geo, ua_status = HeuristicsEngine.analyze_offline(payload)
        ua_raw = payload.get("client_user_agent", "UNKNOWN")
        
        self.after(0, lambda: self.update_metrics(score, tactic, geo, ua_status, ua_raw))

        # 3. Handle IR Output based on Engine Mode
        mode = self.engine_var.get()
        
        if mode == "OFFLINE":
            ir_text = f"--- OFFLINE MATRIX REPORT ---\n"
            ir_text += f"Calculated Risk : {score}/100\n"
            ir_text += f"Primary Tactic  : {tactic}\n"
            ir_text += f"Triggered Alerts:\n"
            if alerts:
                for alert in alerts:
                    ir_text += f"  - {alert}\n"
            else:
                ir_text += "  - No anomalous signatures detected.\n"
            self.after(0, lambda: self.log_ir(ir_text))
            
        elif mode == "ONLINE":
            self.after(0, lambda: self.log_ir("[*] Transmitting payload to Gemini Cognitive Core..."))
            try:
                ai_report = HeuristicsEngine.analyze_online(payload)
                self.after(0, lambda: self.log_ir(f"--- GEMINI AI FORENSIC OVERVIEW ---\n{ai_report}"))
            except Exception as e:
                err_msg = f"[!] AI ENGINE FAILURE: {e}\nFalling back to Offline Matrix."
                self.after(0, lambda: self.log_ir(err_msg))
                # Fallback to offline logging
                self.after(0, lambda: self.engine_var.set("OFFLINE"))
                self.process_payload(payload) # Re-process as offline

    def listen_udp(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(65535)
                payload = json.loads(data.decode('utf-8'))
                # Spin off a worker thread for each packet to prevent UI blocking
                threading.Thread(target=self.process_payload, args=(payload,), daemon=True).start()
            except json.JSONDecodeError:
                self.after(0, lambda: self.log_telemetry("[!] ERROR: Malformed non-JSON packet dropped.", CLR_CRIT))
            except Exception as e:
                self.after(0, lambda err=e: self.log_telemetry(f"[!] SOCKET ERROR: {err}", CLR_CRIT))

if __name__ == "__main__":
    app = SOCDashboard()
    app.mainloop()
