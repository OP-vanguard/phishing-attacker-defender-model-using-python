#!/usr/bin/env python3
"""
master_sender.py
Advanced Adversary Simulation Console
--------------------------------------------------------------------------------
Capabilities:
    - CustomTkinter GUI for scenario selection and mass injection.
    - [OFFLINE] Template Engine: High-variety mutation pool for dynamic payloads.
    - [ONLINE] Generative AI Engine: Gemini API for polymorphic payloads.
    - Mass Packet Injector: Burst fire with configurable quantity and delay.
    - Network Jitter Simulation: Elastic timing for realistic packet delivery.
    - Simulated Routing Headers: Dynamic IP and User-Agent spoofing.
    - Real-time JSON inspector and robust thread-safe UI updates.
"""

import os
import re
import json
import socket
import threading
import time
import random
import string
import datetime
from typing import Dict, Any

import customtkinter as ctk

# Attempt to load the new Google GenAI SDK.
try:
    from google import genai
    from google.genai import types
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# ============================================================================
# SYSTEM PARAMETERS & CONFIGURATION
# ============================================================================
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Custom Colors
CLR_BG = "#0d1117"
CLR_PNL = "#161b22"
CLR_ACCENT = "#58a6ff"
CLR_SAFE = "#238636"
CLR_WARN = "#d29922"
CLR_CRIT = "#da3633"
CLR_TEXT = "#c9d1d9"

# ============================================================================
# UTILITIES & EVASION MATRIX
# ============================================================================
def rand_id(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def rand_ip():
    """Generates a realistic, randomized external IPv4 address."""
    return f"{random.randint(11,240)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", # Chromium Enterprise
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0", # Mozilla Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15", # Apple Mail / Safari
    "Microsoft Office/16.0 (Windows NT 10.0; Microsoft Outlook 16.0.17126; Pro)" # Microsoft Outlook Corporate Client
]

class EvasionMatrix:
    HOMO_MAP = {
        'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х', 'y': 'у',
        'A': 'А', 'C': 'С', 'E': 'Е', 'O': 'О', 'P': 'Р'
    }
    HIGH_RISK_KEYWORDS = ["invoice", "password", "urgent", "security", "login", "suspend", "action required", "verify", "authentication"]

    @staticmethod
    def apply_homoglyph(text: str, density: float = 0.5) -> str:
        return "".join([EvasionMatrix.HOMO_MAP[c] if c in EvasionMatrix.HOMO_MAP and random.random() < density else c for c in text])

    @staticmethod
    def apply_zero_width_spacing(text: str) -> str:
        zwsp = "\u200B"
        for kw in EvasionMatrix.HIGH_RISK_KEYWORDS:
            if kw in text.lower():
                mangled_kw = zwsp.join(list(kw))
                text = re.sub(f"(?i){kw}", mangled_kw, text)
        return text

    @staticmethod
    def apply_space_padding(text: str) -> str:
        for kw in EvasionMatrix.HIGH_RISK_KEYWORDS:
            if kw in text.lower():
                spaced = " ".join(list(kw))
                text = re.sub(f"(?i){kw}", spaced, text)
        return text

# ============================================================================
# ATTACK & BASELINE MATRIX DEFINITIONS (GUI & ONLINE PROMPTS)
# ============================================================================
SCENARIOS = {
    1: {"cat": "Baseline", "name": "Internal IT Maintenance Notice", "type": "SAFE", "prompt": "Write a 0% risk internal corporate email announcing scheduled hardware maintenance. Sender must end in '@company.internal'."},
    2: {"cat": "Baseline", "name": "Corporate HR Newsletter", "type": "SAFE", "prompt": "Write a polite HR community email regarding cafeteria updates or holiday schedules. Originates from hr-ops@company.internal."},
    3: {"cat": "Baseline", "name": "Trusted SaaS Automated Alert", "type": "SAFE", "prompt": "Generate a benign automatic email from a trusted SaaS (e.g., GitHub, Jira) notifying of a ticket update."},
    4: {"cat": "Sector A", "name": "Executive Wire Request (Whaling)", "type": "THREAT", "prompt": "Create an email from the CEO demanding a highly confidential, urgent wire transfer to an external firm."},
    5: {"cat": "Sector A", "name": "Cloud Service Revocation", "type": "THREAT", "prompt": "Impersonate Google Workspace or Office 365 Admin. Warn the user of anomalous activity and threaten immediate session revocation."},
    6: {"cat": "Sector A", "name": "Urgent Compensation Portal", "type": "THREAT", "prompt": "Draft a highly confidential HR email regarding Q4 merit increases and bonuses. Provide an external link."},
    7: {"cat": "Sector A", "name": "MFA Sync Outage", "type": "THREAT", "prompt": "Mask as an Okta or Duo portal. State the user's physical token has sync drift. Force re-authentication."},
    8: {"cat": "Sector A", "name": "Overdue Vendor Invoice", "type": "THREAT", "prompt": "B2B social engineering. Create a convincing vendor email seeking overdue remittance for mapped milestones."},
    9: {"cat": "Sector A", "name": "Legal Subpoena Notice", "type": "THREAT", "prompt": "Instill panic by impersonating federal litigation or legal counsel. Demand immediate review of a subpoena document."},
    10: {"cat": "Sector B", "name": "Homoglyph Lookalike Domain", "type": "EVASION", "prompt": "Formulate a threat advisory about network suspension. Use aggressive terms: Security, Verification, Suspension."},
    11: {"cat": "Sector B", "name": "Zero-Width Space Obfuscation", "type": "EVASION", "prompt": "Produce an administrative alert urging payment account revalidation. Focus on compromised credentials."},
    12: {"cat": "Sector B", "name": "Character Padding Evasion", "type": "EVASION", "prompt": "Create an urgent password reset prompt."},
    13: {"cat": "Sector B", "name": "Embedded @ Router Trick", "type": "EVASION", "prompt": "Structure a URL masking parameter boundary. Use semantic '@' to hide hostile endpoint arrays."},
    14: {"cat": "Sector B", "name": "Brand Squatter Typos", "type": "EVASION", "prompt": "Phishing utilizing aggressive brand typo routing. Use misspellings intentionally natively, for example 'Amz0n.com'."},
    15: {"cat": "Sector C", "name": "Honey-Token Leak Probe", "type": "THREAT", "prompt": "Pretend to be an automated SIEM daemon dropping crashed network environment dumps. Include SECRET_AWS_KEY mappings."},
}

# ============================================================================
# OFFLINE MUTATION POOL
# ============================================================================
OFFLINE_MUTATION_POOL = {
    1: { # IT Maintenance
        "senders": ["sysadmin@company.internal", "it-ops@company.internal", "network-team@company.internal", "infrastructure@company.internal"],
        "subjects": ["Notice: Core Switch Patching", "Scheduled Maintenance Window", "Network Downtime Advisory", "Routine Server Upgrades"],
        "bodies": ["Engineers will commence structural database patches tonight. No user action is requested.", "Please be advised that the VPN will be down for 15 minutes at 2 AM for firmware updates.", "Routine maintenance will be performed on the intranet portal this weekend.", "We are upgrading the core switches. Expect brief intermittent connectivity drops."],
        "paths": ["/status", "/it-schedule", "/maintenance-logs", "/network-health"]
    },
    2: { # HR Newsletter
        "senders": ["hr-ops@company.internal", "communications@company.internal", "culture@company.internal", "benefits@company.internal"],
        "subjects": ["Cafeteria Menu Update", "Weekly Corporate Newsletter", "Upcoming Holiday Schedule", "Employee Wellness Program Updates"],
        "bodies": ["The new weekly menu is up! Enjoy the new salad bar options.", "Please review the attached newsletter for updates on our Q3 town hall.", "A quick reminder about the upcoming long weekend and office closure.", "Join us this Friday for the employee wellness seminar in the main lobby."],
        "paths": ["/menu", "/newsletter-q3", "/holiday-calendar", "/wellness-events"]
    },
    3: { # Trusted SaaS
        "senders": ["notifications@github.com", "jira@atlassian.net", "alerts@pagerduty.com", "no-reply@slack.com"],
        "subjects": ["Successful Build #404", "Jira Ticket Updated: PROJ-102", "PagerDuty: Incident Resolved", "New Login from Unknown Device"],
        "bodies": ["Your recent commit has successfully passed all CI/CD pipeline checks.", "User 'admin' has updated the status of your assigned Jira ticket to 'Done'.", "The database latency incident has been marked as resolved by the on-call engineer.", "A new sign-in was detected. If this was you, no further action is required."],
        "paths": ["/builds/404", "/browse/PROJ-102", "/incidents/view", "/account/security"]
    },
    4: { # CEO Whaling
        "senders": ["ceo.office@executive-relay", "board.director@confidential-exec", "president@corporate-advisory", "founder@stealth-acquisition"],
        "subjects": ["URGENT: Confidential Acquisition Wire", "Immediate Action: Project Titan", "Confidential: Escrow Funding Required", "Time Sensitive: Board Directive"],
        "bodies": ["Process this wire transfer immediately for the Project Titan acquisition. Keep this discrete.", "I am in a meeting and cannot be reached. Wire the funds to the attached escrow account immediately.", "We need to finalize the vendor payment before EOD. Process the attached invoice ASAP.", "This is a highly confidential board matter. Execute the transfer instructions via the secure portal."],
        "paths": ["/wire-auth", "/secure-escrow", "/titan-docs", "/board-portal"]
    },
    5: { # Cloud Revocation
        "senders": ["admin@workspace-alert", "security@o365-protection", "no-reply@cloud-compliance", "alerts@azure-security-net"],
        "subjects": ["Action Required: Account Suspension", "Security Alert: Anomalous Login", "Immediate Action: Session Revocation", "Warning: Unauthorized Access Blocked"],
        "bodies": ["Unusual activity detected. Verify your account immediately or face suspension.", "Your Office 365 session has been flagged for anomalous routing. Re-authenticate to prevent lockout.", "Multiple failed login attempts detected from a foreign IP. Secure your account now.", "Your cloud storage access will be revoked in 2 hours unless you verify your identity."],
        "paths": ["/verify-session", "/account-recovery", "/secure-login", "/auth-challenge"]
    },
    6: { # Q4 Merit
        "senders": ["hr-comp@workday-secure", "payroll@compensation-review", "benefits@hr-portal-auth", "rewards@merit-matrix"],
        "subjects": ["Q4 Merit Increase Document", "Confidential: Your Compensation Review", "Action Required: Bonus Allocation", "New Document: Salary Adjustment"],
        "bodies": ["Your annual compensation adjustment is available for review. Please authenticate to view.", "The Q4 merit matrix has been finalized. Review your updated salary and bonus structure.", "Please sign the attached compensation addendum before the end of the pay period.", "Your performance review and subsequent salary adjustment document requires your signature."],
        "paths": ["/merit-review", "/comp-portal", "/salary-doc", "/bonus-allocation"]
    },
    7: { # MFA Sync
        "senders": ["no-reply@okta-sync", "auth@duo-security-portal", "mfa-admin@token-verify", "security@authenticator-update"],
        "subjects": ["MFA Token Sync Drift Detected", "Action Required: Re-sync Authenticator", "Warning: 2FA Device Unlinked", "Urgent: Security Token Expiration"],
        "bodies": ["Your physical MFA token is experiencing sync drift. Re-authenticate to prevent lockout.", "We detected an error with your Duo push notifications. Please re-sync your device.", "Your two-factor authentication session has expired. Log in to restore access.", "Mandatory security update: Please verify your MFA token via the secure portal."],
        "paths": ["/sync-token", "/mfa-verify", "/duo-restore", "/okta-auth"]
    },
    8: { # Overdue Invoice
        "senders": ["billing@vendor-remittance", "accounts.payable@supplier-portal", "finance@contractor-invoicing", "collections@b2b-payments"],
        "subjects": ["OVERDUE: Invoice #88392", "Action Required: Unpaid Remittance", "Final Notice: Outstanding Balance", "Payment Required: Q3 Services"],
        "bodies": ["Your account is past due. Please remit payment for Invoice #88392 immediately to avoid service interruption.", "We have not received payment for the Q3 consulting services. Review the attached statement.", "This is our final notice regarding your outstanding balance. Access the payment portal below.", "Please process the attached invoice for the recent hardware delivery ASAP."],
        "paths": ["/invoice-view", "/pay-portal", "/remittance-doc", "/statement-88392"]
    },
    9: { # Legal Subpoena
        "senders": ["compliance@legal-summons", "counsel@federal-litigation", "notices@court-docket", "admin@legal-discovery"],
        "subjects": ["Subpoena Duces Tecum: Action Required", "Confidential: Federal Litigation Notice", "Urgent: Court Summons Attached", "Mandatory Legal Discovery Request"],
        "bodies": ["You have been named in a federal subpoena. Review the attached docket immediately.", "This email serves as official notice of pending litigation. Access the secure discovery portal.", "A court summons requires your immediate attention. Failure to respond may result in a default judgment.", "Please review the attached legal hold notice regarding the ongoing compliance investigation."],
        "paths": ["/docket-view", "/subpoena-doc", "/legal-hold", "/summons-auth"]
    },
    10: { # Homoglyph
        "senders": ["alert@network-suspension", "admin@security-verify", "support@account-review", "ops@system-halt"],
        "subjects": ["Security Alert: Network Suspension", "Urgent: Account Verification Required", "Warning: System Halt Imminent", "Action Required: Security Audit"],
        "bodies": ["Your network access will be suspended due to a security violation. Verify your identity.", "An unauthorized device has accessed your account. Immediate verification is required.", "System halt initiated. Please review the security audit logs to cancel the operation.", "Your credentials have been flagged in a recent breach. Secure your account immediately."],
        "paths": ["/verify", "/secure", "/audit-log", "/halt-override"]
    },
    11: { # ZWSP
        "senders": ["admin@account-revalidation", "billing@payment-update", "support@credential-check", "security@auth-revalidate"],
        "subjects": ["Action Required: Payment Revalidation", "Urgent: Update Your Credentials", "Notice: Account Revalidation", "Security: Payment Method Declined"],
        "bodies": ["Your payment method requires revalidation. Please update your billing information.", "We detected an issue with your credentials. Please revalidate your account.", "Your recent transaction was declined. Update your payment details to restore service.", "Mandatory account revalidation is required to maintain your current subscription tier."],
        "paths": ["/revalidate", "/billing-update", "/credential-check", "/payment-auth"]
    },
    12: { # Keyword Padding
        "senders": ["support@password-reset", "helpdesk@credential-recovery", "admin@auth-reset", "it@password-policy"],
        "subjects": ["Urgent: Password Reset Required", "Action Required: Credential Recovery", "Notice: Mandatory Password Update", "Security: Password Policy Change"],
        "bodies": ["Your password has expired. Please initiate a password reset immediately.", "A password reset request was initiated from a new device. If this wasn't you, secure your account.", "Due to a recent policy change, a mandatory password update is required.", "Your account has been locked. Follow the link to complete the credential recovery process."],
        "paths": ["/reset-pw", "/recovery", "/update-auth", "/policy-accept"]
    },
    13: { # Embedded @ Router
        "senders": ["routing@github.com", "redirect@microsoft.com", "auth@google.com", "login@salesforce.com"],
        "subjects": ["Authentication Redirect", "Secure Login Portal", "Single Sign-On Access", "Identity Verification"],
        "bodies": ["Please follow the secure redirect to access your enterprise dashboard.", "Your session requires re-authentication via the single sign-on portal.", "Access the secure identity verification router to continue.", "Click the link below to be routed to the secure login environment."],
        "paths": ["/login", "/sso-auth", "/verify", "/dashboard"]
    },
    14: { # Brand Squatter
        "senders": ["support@amz0n", "billing@microsof", "help@paypa1", "admin@netf1ix"],
        "subjects": ["Your Order Has Been Suspended", "Microsoft Subscription Expired", "PayPal: Unusual Activity", "Netflix: Update Payment Details"],
        "bodies": ["Your recent Amazon order has been suspended due to a billing error. Update your details.", "Your Microsoft 365 subscription has expired. Renew now to avoid data loss.", "We detected unusual activity on your PayPal account. Please verify your identity.", "Your Netflix payment method was declined. Update your billing information to continue watching."],
        "paths": ["/order-issue", "/renew-sub", "/verify-activity", "/update-billing"]
    },
    15: { # Honey-Token
        "senders": ["daemon@infra-logs", "syslog@aws-collector", "root@server-dump", "admin@k8s-cluster"],
        "subjects": ["CRASH DUMP: Auth Server", "Syslog: Kernel Panic Detected", "Alert: Kubernetes Pod Evicted", "Automated Report: Environment Variables"],
        "bodies": ["Memory dump recorded. Env variables exposed:\nSECRET_AWS_KEY=AKIA{aws_key}", "Kernel panic on node-04. Core dump attached. AWS_ACCESS_KEY_ID=AKIA{aws_key}", "Pod eviction triggered due to OOM. Environment state saved: AWS_SECRET=AKIA{aws_key}", "Automated infrastructure report. Sensitive variables detected in plaintext: AKIA{aws_key}"],
        "paths": ["/dump-view", "/syslog-archive", "/k8s-logs", "/env-report"]
    }
}

# ============================================================================
# OFFLINE GENERATOR LOGIC
# ============================================================================
def generate_offline_payload(index: int) -> Dict[str, Any]:
    pool = OFFLINE_MUTATION_POOL[index]
    scenario_type = SCENARIOS[index]["type"]
    
    # 1. Randomly select components
    sender_base = random.choice(pool["senders"])
    subject = random.choice(pool["subjects"])
    body = random.choice(pool["bodies"])
    path = random.choice(pool["paths"])
    
    # 2. Dynamic TLD Application for Threats/Evasion
    if scenario_type in ["THREAT", "EVASION"]:
        bad_tlds = ['.xyz', '.top', '.pw', '.biz', '.info']
        if "." not in sender_base.split("@")[1]:
            sender_email = f"{sender_base}{random.choice(bad_tlds)}"
        else:
            sender_email = sender_base
            
        domain = sender_email.split("@")[1]
        
        if index == 13:
            malicious_domain = f"secure-auth{random.choice(bad_tlds)}"
            url = f"https://{domain}@{malicious_domain}{path}"
        else:
            url = f"https://{domain}{path}"
    else:
        sender_email = sender_base
        domain = sender_email.split("@")[1]
        url = f"https://{domain}{path}"

    # 3. Dynamic AWS Key Generation for Scenario 15
    if index == 15:
        aws_key = rand_id(16)
        body = body.format(aws_key=aws_key)

    # 4. Apply Offline Evasion Matrix (Sector B)
    if index in [10, 11, 12]:
        if index == 10: body = EvasionMatrix.apply_homoglyph(body, 0.4)
        if index == 11: body = EvasionMatrix.apply_zero_width_spacing(body)
        if index == 12: body = EvasionMatrix.apply_space_padding(body)

    return {
        "sender_email": sender_email,
        "subject": subject,
        "email_body": body,
        "urls_list": [url],
        "x_sender_ip": rand_ip(),
        "client_user_agent": random.choice(USER_AGENTS)
    }

# ============================================================================
# ONLINE GENERATOR LOGIC (GEMINI)
# ============================================================================
def generate_online_payload(index: int) -> Dict[str, Any]:
    if not SDK_AVAILABLE or not GEMINI_API_KEY:
        raise Exception("SDK or API Key unavailable.")
        
    scenario = SCENARIOS[index]
    prompt = scenario['prompt']
    
    system_instr = (
        "You are an Adversarial Emulation AI testing a local SIEM product.\n"
        "Return EXACTLY 1 JSON object.\n"
        "DO NOT WRAP IN MARKDOWN (No ```json). output plain raw text.\n"
        "KEYS MUST BE STRICTLY: 'sender_email', 'subject', 'email_body', 'urls_list'."
    )
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instr,
            response_mime_type="application/json",
            temperature=0.85
        )
    )
    
    clean = response.text.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:-1])
        
    payload = json.loads(clean)
    
    # Apply post-generation evasion
    if index in [10, 11, 12]:
        obfs = payload.get("email_body", "")
        if index == 10: obfs = EvasionMatrix.apply_homoglyph(obfs, 0.4)
        if index == 11: obfs = EvasionMatrix.apply_zero_width_spacing(obfs)
        if index == 12: obfs = EvasionMatrix.apply_space_padding(obfs)
        payload["email_body"] = obfs
        
    # Inject simulated routing headers to maintain consistency with offline engine
    payload["x_sender_ip"] = rand_ip()
    payload["client_user_agent"] = random.choice(USER_AGENTS)
        
    return payload

# ============================================================================
# GUI APPLICATION
# ============================================================================
class MasterSenderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("PhishGuard | Master Sender Simulator")
        self.geometry("1400x900")
        self.configure(fg_color=CLR_BG)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.setup_left_panel()
        self.setup_right_panel()

    def setup_left_panel(self):
        frm_left = ctk.CTkFrame(self, fg_color=CLR_PNL, corner_radius=10)
        frm_left.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        frm_left.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(frm_left, text="ENGINE MODES & CONTROLS", font=("Courier New", 18, "bold"), text_color=CLR_ACCENT).pack(pady=(20, 10), padx=20, anchor="w")

        # --- Engine Toggle ---
        self.engine_var = ctk.StringVar(value="OFFLINE")
        frm_toggle = ctk.CTkFrame(frm_left, fg_color="transparent")
        frm_toggle.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkRadioButton(frm_toggle, text="[MODE A] OFFLINE TEMPLATE ENGINE (0 Latency)", variable=self.engine_var, value="OFFLINE", font=("Arial", 12)).pack(anchor="w", pady=5)
        
        online_state = "normal" if SDK_AVAILABLE and GEMINI_API_KEY else "disabled"
        online_text = "[MODE B] ONLINE GEMINI AI (Polymorphic)" if online_state == "normal" else "[MODE B] ONLINE GEMINI AI (Missing API Key/SDK)"
        ctk.CTkRadioButton(frm_toggle, text=online_text, variable=self.engine_var, value="ONLINE", state=online_state, font=("Arial", 12)).pack(anchor="w", pady=5)

        # --- Mass Packet Injector ---
        ctk.CTkLabel(frm_left, text="MASS PACKET INJECTOR", font=("Courier New", 16, "bold"), text_color=CLR_WARN).pack(pady=(20, 5), padx=20, anchor="w")
        
        frm_mass = ctk.CTkFrame(frm_left, fg_color=CLR_BG, corner_radius=8)
        frm_mass.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(frm_mass, text="Payload Quantity:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.qty_entry = ctk.CTkEntry(frm_mass, width=60)
        self.qty_entry.insert(0, "5")
        self.qty_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(frm_mass, text="Base Delay (sec):").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.delay_entry = ctk.CTkEntry(frm_mass, width=60)
        self.delay_entry.insert(0, "0.5")
        self.delay_entry.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        
        self.mix_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frm_mass, text="RANDOMIZED MIX (Safe + Threat)", variable=self.mix_var).grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="w")
        
        self.btn_burst = ctk.CTkButton(frm_mass, text="🔥 FIRE ATTACK BURST", fg_color=CLR_CRIT, hover_color="#8a1818", command=self.start_burst_thread)
        self.btn_burst.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        # --- Scenario Matrix ---
        ctk.CTkLabel(frm_left, text="SCENARIO MATRIX (Single Fire)", font=("Courier New", 16, "bold"), text_color=CLR_ACCENT).pack(pady=(20, 5), padx=20, anchor="w")
        
        self.scenario_scroll = ctk.CTkScrollableFrame(frm_left, fg_color="transparent")
        self.scenario_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        current_cat = ""
        for idx, data in SCENARIOS.items():
            if data['cat'] != current_cat:
                ctk.CTkLabel(self.scenario_scroll, text=data['cat'].upper(), font=("Arial", 12, "bold"), text_color=CLR_TEXT).pack(anchor="w", pady=(10, 2))
                current_cat = data['cat']
            
            btn_color = CLR_SAFE if data['type'] == "SAFE" else CLR_CRIT if data['type'] == "THREAT" else CLR_WARN
            btn = ctk.CTkButton(self.scenario_scroll, text=f"{idx}. {data['name']}", fg_color=btn_color, anchor="w", command=lambda i=idx: self.start_single_fire_thread(i))
            btn.pack(fill="x", padx=10, pady=2)

    def setup_right_panel(self):
        frm_right = ctk.CTkFrame(self, fg_color=CLR_PNL, corner_radius=10)
        frm_right.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        frm_right.grid_rowconfigure(1, weight=1)
        frm_right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frm_right, text="REAL-TIME INSPECTOR (UDP: 127.0.0.1:5005)", font=("Courier New", 18, "bold"), text_color=CLR_ACCENT).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self.txt_inspector = ctk.CTkTextbox(frm_right, fg_color=CLR_BG, text_color="#A9BACD", font=("Consolas", 13), wrap="word")
        self.txt_inspector.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.log_inspector("System initialized. Awaiting payload generation...")

    def log_inspector(self, text: str):
        self.txt_inspector.configure(state="normal")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.txt_inspector.insert("end", f"[{timestamp}] {text}\n\n")
        self.txt_inspector.see("end")
        self.txt_inspector.configure(state="disabled")

    def log_payload(self, payload: dict, engine: str):
        log_str = f"--- {engine} PAYLOAD GENERATED ---\n"
        log_str += f"Sender IP  : {payload.get('x_sender_ip', 'N/A')}\n"
        log_str += f"User Agent : {payload.get('client_user_agent', 'N/A')}\n"
        log_str += f"Sender     : {payload.get('sender_email')}\n"
        log_str += f"Subject    : {payload.get('subject')}\n"
        log_str += f"URLs       : {', '.join(payload.get('urls_list', []))}\n"
        log_str += f"Body       :\n{payload.get('email_body')}\n"
        log_str += f"--- RAW JSON DISPATCHED TO {UDP_IP}:{UDP_PORT} ---\n"
        log_str += json.dumps(payload, indent=2)
        self.log_inspector(log_str)

    def send_packet(self, payload: dict):
        try:
            packet = json.dumps(payload).encode('utf-8')
            self.sock.sendto(packet, (UDP_IP, UDP_PORT))
        except Exception as e:
            self.after(0, lambda: self.log_inspector(f"SOCKET ERROR: {e}"))

    # ============================================================================
    # THREADING & EXECUTION (Safely wrapped with lambdas)
    # ============================================================================
    def start_single_fire_thread(self, index: int):
        threading.Thread(target=self._single_fire_worker, args=(index,), daemon=True).start()

    def _single_fire_worker(self, index: int):
        engine_mode = self.engine_var.get()
        self.after(0, lambda: self.log_inspector(f"[*] Generating payload {index} via {engine_mode} engine..."))
        
        try:
            if engine_mode == "ONLINE":
                payload = generate_online_payload(index)
            else:
                payload = generate_offline_payload(index)
                
            self.send_packet(payload)
            self.after(0, lambda p=payload, e=engine_mode: self.log_payload(p, e))
            
        except Exception as e:
            self.after(0, lambda err=e: self.log_inspector(f"[!] GENERATION ERROR: {err}. Falling back to OFFLINE mode."))
            try:
                payload = generate_offline_payload(index)
                self.send_packet(payload)
                self.after(0, lambda p=payload: self.log_payload(p, "OFFLINE FALLBACK"))
            except Exception as e2:
                 self.after(0, lambda err=e2: self.log_inspector(f"[!] FATAL FALLBACK ERROR: {err}"))

    def start_burst_thread(self):
        try:
            qty = int(self.qty_entry.get())
            delay = float(self.delay_entry.get())
        except ValueError:
            self.log_inspector("[!] Invalid quantity or delay value.")
            return
            
        is_mixed = self.mix_var.get()
        threading.Thread(target=self._burst_worker, args=(qty, delay, is_mixed), daemon=True).start()

    def _burst_worker(self, qty: int, base_delay: float, is_mixed: bool):
        engine_mode = self.engine_var.get()
        self.after(0, lambda: self.log_inspector(f"[*] INITIATING BURST: {qty} packets, ~{base_delay}s avg delay, Engine: {engine_mode}, Mixed: {is_mixed}"))
        self.after(0, lambda: self.btn_burst.configure(state="disabled", text="FIRING..."))
        
        for i in range(qty):
            if is_mixed:
                idx = random.choice(list(SCENARIOS.keys()))
            else:
                idx = random.choice([k for k, v in SCENARIOS.items() if v["type"] != "SAFE"])
                
            self.after(0, lambda current=i+1, total=qty, s_idx=idx: self.log_inspector(f"[-] Burst {current}/{total} - Generating Scenario {s_idx}..."))
            
            try:
                if engine_mode == "ONLINE":
                    payload = generate_online_payload(idx)
                else:
                    payload = generate_offline_payload(idx)
                    
                self.send_packet(payload)
                self.after(0, lambda p=payload, e=engine_mode: self.log_payload(p, f"{e} BURST"))
                
            except Exception as e:
                self.after(0, lambda err=e: self.log_inspector(f"[!] BURST GENERATION ERROR (Falling back to offline): {err}"))
                payload = generate_offline_payload(idx)
                self.send_packet(payload)
                self.after(0, lambda p=payload: self.log_payload(p, "OFFLINE BURST FALLBACK"))
                
            # Logical Timing Jitter Engine
            actual_delay = base_delay * random.uniform(0.6, 1.4)
            time.sleep(actual_delay)
            
        self.after(0, lambda: self.log_inspector("[*] BURST COMPLETE."))
        self.after(0, lambda: self.btn_burst.configure(state="normal", text="🔥 FIRE ATTACK BURST"))

if __name__ == "__main__":
    app = MasterSenderApp()
    app.mainloop()
