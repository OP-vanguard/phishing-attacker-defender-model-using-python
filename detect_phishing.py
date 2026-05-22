import pandas as pd
import joblib
import numpy as np
import sys
import re
import os
import xgboost as xgb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from scipy.sparse import hstack, csr_matrix

MODEL_FILE = 'phishing_xgboost_model.pkl'
VECTORIZER_FILE = 'vectorizer.pkl'
DATA_FILE = 'phishing_lab_data.csv'

RISK_TLDS = ['.xyz', '.top', '.click', '.su', '.link']
INTERNAL_DOMAINS = ['company.com', 'hr-portal.internal', 'it-service.local']
BRAND_NAMES = ['Microsoft', 'CEO', 'HR', 'Finance', 'Payroll', 'DocuSign', 'Office 365']
GLOBAL_TRUSTED_DOMAINS = ['github.com', 'aws.amazon.com', 'amazon.com', 'linkedin.com', 'microsoft.com', 'google.com', 'atlassian.com']

def extract_manual_features(df):
    senders = df['sender'].fillna('').astype(str).str.lower()
    subjects = df['subject'].fillna('').astype(str)
    bodies = df['body'].fillna('').astype(str)
    full_text = senders + " " + subjects + " " + bodies

    has_ip_link = full_text.apply(lambda x: bool(re.search(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', x)))
    has_risk_tld = full_text.apply(lambda x: any(tld in x.lower() for tld in RISK_TLDS))

    def check_mismatch(row):
        sender = row['sender'].lower()
        if any(dom in sender for dom in INTERNAL_DOMAINS + GLOBAL_TRUSTED_DOMAINS): return 0
        text = (row['subject'] + " " + row['body']).lower()
        if any(brand.lower() in text for brand in BRAND_NAMES): return 1
        return 0
    mismatches = df.apply(check_mismatch, axis=1)

    def target_referencing(row):
        sender = row['sender'].lower()
        if any(dom in sender for dom in INTERNAL_DOMAINS + GLOBAL_TRUSTED_DOMAINS): 
            return 0 
        text = (row['subject'] + " " + row['body']).lower()
        if any(dom in text for dom in INTERNAL_DOMAINS): 
            return 1 
        return 0
    targeted_refs = df.apply(target_referencing, axis=1)

    return np.stack([
        has_ip_link.astype(int),
        has_risk_tld.astype(int),
        mismatches.astype(int),
        targeted_refs.astype(int)
    ], axis=1)

def train_and_save():
    if not os.path.exists(DATA_FILE):
        return

    df = pd.read_csv(DATA_FILE).fillna('')
    y_str = df['label'].astype(str).str.lower()
    y = (y_str == 'phishing').astype(int) 
    
    df['text'] = df['sender'] + " " + df['subject'] + " " + df['body']

    X_manual = csr_matrix(extract_manual_features(df))
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=10000, stop_words='english')
    X_text = vectorizer.fit_transform(df['text'])
    
    X = hstack([X_manual, X_text])
    
    num_manual_features = X_manual.shape[1]
    num_text_features = X_text.shape[1]
    feature_weights = np.concatenate([
        np.full(num_manual_features, 0.90),
        np.full(num_text_features, 0.10)
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
    
    model = xgb.XGBClassifier(
        n_estimators=100, 
        max_depth=6, 
        learning_rate=0.1, 
        random_state=42, 
        n_jobs=-1,
        eval_metric='logloss'
    )
    model.fit(X_train, y_train, feature_weights=feature_weights)

    predictions = model.predict(X_test)
    print(classification_report(y_test, predictions, target_names=['Legit', 'Phishing']))

    joblib.dump(model, MODEL_FILE)
    joblib.dump(vectorizer, VECTORIZER_FILE)

def manual_test():
    if not os.path.exists(MODEL_FILE): 
        train_and_save()
        
    model = joblib.load(MODEL_FILE)
    vectorizer = joblib.load(VECTORIZER_FILE)
    
    print("\n================ PHISHGUARD PRO: UNIFIED PIPELINE ================")
    print("PASTE THE EMAIL BELOW (Ctrl+D to analyze):")
    try:
        user_input = sys.stdin.read().strip()
    except EOFError:
        user_input = ""

    if not user_input: return

    # SENDER & DOMAIN EXTRACTION
    sender_match = re.search(r'From:\s*(.*)', user_input, re.I)
    sender_raw = sender_match.group(1).strip() if sender_match else ""
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender_raw)
    sender_email = email_match.group(0).lower() if email_match else sender_raw.lower()
    sender_domain = sender_email.split('@')[-1] if '@' in sender_email else ""
    
    links = re.findall(r'https?://([^\s/<>"]+)', user_input)
    body_lower = user_input.lower()

    # -------------------------------------------------------------------------
    # STEP 1: THE WHITELIST GATE
    # -------------------------------------------------------------------------
    is_internal_sender = any(sender_email.endswith('@' + d) for d in INTERNAL_DOMAINS)
    all_internal_links = all((any(d in link.lower() for d in INTERNAL_DOMAINS) for link in links))

    if is_internal_sender and (all_internal_links or len(links) == 0):
        print_results("LEGIT (Internal Short-Circuit)", 1.05)
        return  

    # -------------------------------------------------------------------------
    # STEP 2: GLOBAL TRUSTED DOMAINS GAP
    # -------------------------------------------------------------------------
    is_trusted_sender = any(sender_domain.endswith(td) for td in GLOBAL_TRUSTED_DOMAINS)
    links_have_trusted_routes = any(any(td in link.lower() for td in GLOBAL_TRUSTED_DOMAINS) for link in links)
    
    has_global_trust = is_trusted_sender or links_have_trusted_routes

    # -------------------------------------------------------------------------
    # STEP 3: DETERMINISTIC BLACKLIST (HARD KILL-SWITCH)
    # -------------------------------------------------------------------------
    ipv4_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    is_hard_phish = False
    for link in links:
        link_lower = link.lower()
        if ipv4_pattern.search(link_lower) or any(tld in link_lower for tld in RISK_TLDS):
            is_hard_phish = True
            break

    if is_hard_phish:
        print_results("CRITICAL PHISH (Deterministic Hard-Kill)", 99.99)
        return  

    # -------------------------------------------------------------------------
    # STEP 4: TARGETED SPOOFING TRAP (GHOST PHISH)
    # -------------------------------------------------------------------------
    references_internal_assets = any(dom in body_lower for dom in INTERNAL_DOMAINS)
    has_untrusted_ext_links = not all((any(idom in link.lower() for idom in INTERNAL_DOMAINS) or any(tdom in link.lower() for tdom in GLOBAL_TRUSTED_DOMAINS)) for link in links)
    
    if not is_internal_sender and not has_global_trust:
        if references_internal_assets and has_untrusted_ext_links:
            print_results("SUSPICIOUS / SPEAR-PHISHING (Untrusted Cloud Trap)", 75.00)
            return

    # -------------------------------------------------------------------------
    # STEP 5: ML FALLBACK CLASSIFIER
    # -------------------------------------------------------------------------
    test_df = pd.DataFrame([{'sender': sender_email, 'subject': '', 'body': user_input}])
    X_man = csr_matrix(extract_manual_features(test_df))
    X_txt = vectorizer.transform([sender_email + " " + user_input])
    final_input = hstack([X_man, X_txt])
    
    confidence = model.predict_proba(final_input)[0][1] * 100

    if confidence >= 80.0:
        verdict = "CRITICAL PHISHING"
    elif confidence >= 50.0:
        verdict = "WARNING / SUSPICIOUS"
    else:
        verdict = "SAFE"

    print_results(f"{verdict} (Analyzed by XGBoost Model)", confidence)

def print_results(verdict, confidence):
    print("\n" + "=" * 80)
    print(f"VERDICT:             {verdict}")
    print(f"PHISHING CONFIDENCE: {confidence:.2f}%")
    print(f"STRICT THRESHOLD:    80.0%")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    if '--train' in sys.argv: 
        train_and_save()
    else: 
        manual_test()
