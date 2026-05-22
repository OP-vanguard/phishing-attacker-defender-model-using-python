import csv
import random
import string
from faker import Faker

fake = Faker()

INTERNAL_DOMAIN = "company.com"
INTERNAL_DOMAINS_LIST = [INTERNAL_DOMAIN, 'hr-portal.internal', 'it-service.local']
RISK_TLDS = ['.xyz', '.top', '.click', '.su', '.link']
FREE_EMAIL_PROVIDERS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'mail.ru']
BRANDS = ['Microsoft Office 365', 'DocuSign', 'HR Department', 'IT Security', 'Zoom', 'Salesforce']

def get_typosquat(domain):
    """Generates realistic typo-squatted domains (e.g., company.com -> compnay.com)"""
    if len(domain) < 5: return domain
    char_idx = random.randint(1, len(domain) - 5)
    chars = list(domain)
    # Swap two letters
    chars[char_idx], chars[char_idx+1] = chars[char_idx+1], chars[char_idx]
    return "".join(chars)

def generate_legit_email():
    """Generates legitimate internal traffic"""
    email_type = random.choice(["mundane", "automated", "urgent"])
    sender = f"{fake.first_name().lower()}.{fake.last_name().lower()}@{random.choice(INTERNAL_DOMAINS_LIST)}"
    
    if email_type == "mundane":
        subject = fake.sentence(nb_words=4).strip('.')
        body = f"Hey,\n\n{fake.paragraph(nb_sentences=3)}\n\nTalk soon,\n{fake.first_name()}"
    
    elif email_type == "automated":
        subject = "Jira Ticket Status: " + fake.catch_phrase()
        sender = f"jira-system@{INTERNAL_DOMAIN}"
        body = f"An update has been posted to your ticket.\n\nDetails: {fake.sentence()}\nView ticket: https://{INTERNAL_DOMAIN}/jira/{fake.uuid4()}"
    
    else:  # Urgent Internal
        subject = f"ACTION REQUIRED: {random.choice(['Q3', 'Q4', 'Annual'])} Update"
        body = f"Team,\n\nPlease make sure to complete your compliance tasks at the link below by Friday.\nhttps://portal.{INTERNAL_DOMAIN}/auth/{fake.uuid4()}\n\n{fake.paragraph()}"
    
    return [sender, subject, body, "legit"]

def generate_phishing_email():
    """Generates highly evasive adversarial traffic"""
    attack_vector = random.choice(["ip_payload", "risky_tld", "typo_squat", "freemail_impersonator", "brand_impersonation"])
    
    if attack_vector == "ip_payload":
        sender = f"system@{fake.domain_name()}"
        subject = "Urgent: System Compromise Warning"
        ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        body = f"Warning!\n\nYour machine has an overdue patch. To avoid network lockout, navigate here: http://{ip}/updates\n\nIT Support"
        
    elif attack_vector == "risky_tld":
        sender = f"admin@{fake.domain_word()}{random.choice(RISK_TLDS)}"
        subject = "Invoice OVERDUE"
        body = f"Your invoice for ${random.randint(50, 2000)} is past due. Review it now: https://billing-secure{random.choice(RISK_TLDS)}/auth\n\nThanks,\nFinance"
        
    elif attack_vector == "typo_squat":
        squatted = get_typosquat(INTERNAL_DOMAIN)
        sender = f"admin@{squatted}"
        subject = "Updated Company Policy (Read immediately)"
        body = f"Please read the attached employee handbook adjustments here: https://portal.{squatted}/policy-update.\n\n- HR Team"
        
    elif attack_vector == "freemail_impersonator":
        sender = f"ceo.{fake.first_name().lower()}_{fake.last_name().lower()}@{random.choice(FREE_EMAIL_PROVIDERS)}"
        subject = "Are you available?"
        body = f"I am in a meeting right now and need you to handle a quick request. Can you buy some gift cards for a vendor? I will reimburse you.\nLet me know ASAP.\n\nSent from my iPhone"
        
    else:  # Brand Impersonation (Domain Mismatch)
        brand = random.choice(BRANDS)
        sender = f"noreply-notification@{fake.domain_name()}" # Sender doesn't match the brand
        subject = f"{brand}: Signature Required"
        body = f"Hello, you have 1 pending secure document waiting on {brand}.\nReview here: https://{fake.domain_word()}.co/review\n\n{fake.paragraph()}"

    return [sender, subject, body, "phishing"]

def build_adversarial_dataset(count=100000):
    print("Initializing Advanced Data Generator...")
    data = []
    data.append(["sender", "subject", "body", "label"]) # Header
    
    # 50,000 Legit / 50,000 Phishing
    for i in range(count):
        if i % 10000 == 0:
            print(f"Synthesizing... {i}/{count} complete")
            
        is_legit = i < (count // 2)
        if is_legit:
            data.append(generate_legit_email())
        else:
            data.append(generate_phishing_email())

    # Randomly shuffle data (ignoring header)
    header = data.pop(0)
    random.shuffle(data)
    data.insert(0, header)

    with open('phishing_lab_data.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
        
    print(f"\nSUCCESS: Successfully packed {count} highly-variant, randomized emails into phishing_lab_data.csv.")
    print("Next step: Retrain your machine learning pipeline with the new data!")

if __name__ == "__main__":
    build_adversarial_dataset(100000)
