# streamlit_qr_ui.py
import os
# Disable connectivity check + force CPU
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


import streamlit as st
import cv2
import pandas as pd
import re
import tempfile
from qreader import QReader
from paddleocr import PaddleOCR 
 # Use OS temp directory (e.g. /tmp on Linux) which Streamlit Cloud allows writing to.
_TEMP_WEIGHTS_DIR = tempfile.gettempdir()

# Instantiate detector once (loads / downloads weights into _TEMP_WEIGHTS_DIR).
# This prevents repeated downloads and avoids permission problems trying to create system dirs.
detector = QReader(weights_folder=_TEMP_WEIGHTS_DIR)

# Instantiate PaddleOCR once to avoid repeated heavy initialisation.
# Wrap in try/except so import-time errors are surfaced cleanly.
try:
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
except Exception as _e:
    # If OCR fails to initialize at import, keep 'ocr' as None and handle later.
    ocr = None
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
#import jwt
import streamlit as st

#JWT_SECRET = "kantaka_secret"

#query = st.query_params
#token = query.get("token")

#if not token:
 #   st.error("Unauthorized Access")
  #  st.stop()

#try:
 #   jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
#except jwt.ExpiredSignatureError:
 #   st.error("Token expired")
  #  st.stop()
#except:
 #   st.error("Invalid token")
  #  st.stop()
# ---------------- page config ----------------
#st.set_page_config(
   # page_title="Kantaka Sodhana : QR Verification", 
  #  layout="wide", 
 #   initial_sidebar_state="collapsed",
#   page_icon="🛡️"
#)

# ---------------- CSS (Enhanced Glassmorphism & Theme) ----------------
st.markdown("""
<style>
:root {
    --bg: #070a12;
    --text: #eaf0ff;
    --muted: #a9b6dd;
    --accent: #6ee7ff;
    --accent2: #8b5cf6;
    --accent3: #00f23a;
    --danger: #ff0017;
    --glass-bg: rgba(30, 35, 55, 0.4);
    --glass-border: rgba(255, 255, 255, 0.08);
    --glow-cyan: rgba(110, 231, 255, 0.3);
    --glow-purple: rgba(139, 92, 246, 0.3);
}

/* Base App Background - Animated Space Theme */
.stApp {
    background-color: var(--bg);
    background-image: 
        radial-gradient(circle at 15% 50%, rgba(139, 92, 246, 0.2) 0%, transparent 50%),
        radial-gradient(circle at 85% 30%, rgba(110, 231, 255, 0.2) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.02) 0%, transparent 100%);
    color: var(--text);
    background-attachment: fixed;
    animation: bg-shift 20s ease-in-out infinite;
}

@keyframes bg-shift {
    0% { background-position: 0% 0%; }
    50% { background-position: 100% 100%; }
    100% { background-position: 0% 0%; }
}

/* Hide Streamlit elements */
#MainMenu, header, footer {visibility: hidden;}

/* Navbar styling with enhanced glow */
.navbar {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: rgba(10, 15, 25, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--glass-border);
    padding: 15px 0;
    margin-bottom: 2rem;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
}
.logo {
    width: 48px; height: 48px; border-radius: 14px;
    display: grid; place-items: center;
    background: linear-gradient(135deg, rgba(110,231,255,.2), rgba(139,92,246,.2));
    border: 1px solid rgba(255,255,255,.15);
    box-shadow: 0 0 25px rgba(139,92,246,.4), inset 0 0 10px rgba(110,231,255,.2);
    transition: all 0.3s ease;
}
.logo:hover {
    transform: scale(1.05);
    box-shadow: 0 0 35px rgba(139,92,246,.6), inset 0 0 15px rgba(110,231,255,.3);
}
.brand-name { 
    font-weight: 900; 
    font-size: 20px; 
    color: var(--text); 
    line-height: 1.2;
    background: linear-gradient(to right, #fff, var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 0.5px;
}
.brand-sub { 
    color: var(--muted); 
    font-size: 13px; 
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Streamlit Container Glassmorphism Overrides */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 20px !important;
    box-shadow: 0 10px 40px 0 rgba(0, 0, 0, 0.4) !important;
    padding: 15px !important;
    transition: all 0.3s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--accent) !important;
    box-shadow: 0 10px 40px 0 rgba(110, 231, 255, 0.15) !important;
}

/* Button Styling with enhanced effects */
div.stButton > button {
    width: 100%;
    border-radius: 16px;
    padding: 14px 20px;
    font-weight: 800;
    font-size: 15px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #000;
    border: none;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 0 6px 20px rgba(139,92,246,0.3);
    position: relative;
    overflow: hidden;
}
div.stButton > button::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    transition: 0.5s;
}
div.stButton > button:hover::before {
    left: 100%;
}
div.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(110,231,255,0.5);
    color: #000;
}

/* File Uploader override with glow */
[data-testid="stFileUploadDropzone"] {
    background-color: rgba(0, 0, 0, 0.3);
    border: 2px dashed rgba(110, 231, 255, 0.3);
    border-radius: 16px;
    transition: all 0.3s ease;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: var(--accent);
    background-color: rgba(110, 231, 255, 0.05);
    box-shadow: 0 0 20px rgba(110, 231, 255, 0.2);
}

/* Glass Table Styles (Rendered via HTML) */
.glass-table-container {
    width: 100%;
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid var(--glass-border);
    background: rgba(10, 15, 25, 0.5);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    margin-top: 20px;
}
.glass-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}
.glass-table th {
    background: linear-gradient(135deg, rgba(110, 231, 255, 0.1), rgba(139, 92, 246, 0.1));
    color: var(--accent);
    padding: 16px 20px;
    text-align: left;
    font-weight: 700;
    border-bottom: 2px solid var(--glass-border);
    box-shadow: inset 0 -10px 20px -10px rgba(110, 231, 255, 0.2);
    text-transform: uppercase;
    letter-spacing: 1px;
}
.glass-table td {
    padding: 14px 20px;
    color: var(--text);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.3s ease;
}
.glass-table tr:hover td {
    background: rgba(110, 231, 255, 0.08);
    transform: scale(1.01);
}
.glass-table tr:last-child td {
    border-bottom: none;
}

/* Pill Badges with glow */
.badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 24px;
    font-size: 12px;
    font-weight: 800;
    text-align: center;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
.badge-match {
    background: rgba(0, 242, 58, 0.15);
    color: #00f23a;
    border: 1px solid rgba(0, 242, 58, 0.5);
    box-shadow: 0 0 15px rgba(0, 242, 58, 0.3);
}
.badge-nomatch {
    background: rgba(255, 0, 23, 0.15);
    color: #ff0017;
    border: 1px solid rgba(255, 0, 23, 0.5);
    box-shadow: 0 0 15px rgba(255, 0, 23, 0.3);
}

/* Alert Boxes Override */
[data-testid="stAlert"] {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(16px);
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

/* Container Border Styling */
[data-testid="stContainer"] {
    border-radius: 16px;
    background: rgba(10, 15, 25, 0.3);
    border: 1px solid var(--glass-border);
    padding: 15px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

/* Status Indicators */
.status-icon {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(110, 231, 255, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(110, 231, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(110, 231, 255, 0); }
}

.block-container { max-width: 1200px; padding-top: 0px; }

/* QR Link Styling */
.qr-link {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
    display: inline-block;
}
.qr-link:hover {
    color: var(--accent2);
    text-shadow: 0 0 10px var(--glow-cyan);
}

/* Empty State Styling */
.empty-state {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    opacity: 0.6;
    margin-top: 80px;
    transition: all 0.3s ease;
}
.empty-state:hover {
    opacity: 1;
}
.empty-state i {
    font-size: 56px;
    margin-bottom: 24px;
    color: var(--accent);
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
</style>
""", unsafe_allow_html=True)

st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">', unsafe_allow_html=True)

# ---------------- Utility functions ----------------
def clean_text(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def generate_clean_exact_match_df(ocr_df, app_df):
    if app_df is None or app_df.empty or ocr_df is None or ocr_df.empty:
        return None

    cleaned_ocr_text = clean_text(ocr_df['recognized_text'].iloc[0])

    def match_row(val):
        original_val = str(val).strip()
        cleaned_val = clean_text(original_val)

        if cleaned_val and cleaned_val in cleaned_ocr_text:
            return pd.Series(['matched', original_val])
        else:
            return pd.Series(['not matched', ''])

    result_df = app_df.copy()
    result_df[['result', 'matched_text']] = result_df['Value'].apply(match_row)
    return result_df

def decode_qr(image):
    """
    Use the module-level 'detector' (QReader) which was created using
    tempfile.gettempdir() for weights_folder to avoid permission issues.
    """
    # Use the pre-created detector (no re-instantiation here)
    decoded_qrs, _ = detector.detect_and_decode(image=image, return_detections=True)
    return decoded_qrs[0] if decoded_qrs else None


def extract_with_requests(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.select("table tr")

        data = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                val = cells[1].get_text(strip=True)
                data.append((key, val))

        return pd.DataFrame(data, columns=["Field", "Value"]) if data else None
    except requests.RequestException:
        return None

def extract_with_selenium(url):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//table//tr"))
        )

        rows = driver.find_elements(By.XPATH, "//table//tr")

        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == 2:
                key = cells[0].text.strip()
                val = cells[1].text.strip()  # Fixed: was 'text.strip()'
                data.append((key, val))

        driver.quit()

        return pd.DataFrame(data, columns=["Field", "Value"]) if data else None
    except (WebDriverException, TimeoutException):
        return None

# ---------------- HTML Table Generator ----------------
def generate_html_table(df):
    """Generates a beautiful glassmorphism HTML table from the matched dataframe"""
    html = '<div class="glass-table-container"><table class="glass-table">'
    html += '<tr><th>Field</th><th>OCR Value</th><th>Portal Value</th><th>Status</th></tr>'
    
    for _, row in df.iterrows():
        field = row['Field']
        ocr_val = row['matched_text'] if row['matched_text'] else "<span style='color:#666'>Not Found</span>"
        portal_val = row['Value']
        status = str(row['result']).strip().lower()
        
        if status == 'matched':
            badge = '<span class="badge badge-match">matched</span>'
        else:
            badge = '<span class="badge badge-nomatch">not matched</span>'
            
        html += f'<tr><td>{field}</td><td>{ocr_val}</td><td>{portal_val}</td><td>{badge}</td></tr>'
        
    html += '</table></div>'
    return html

# ---------------- Top navbar ----------------
st.markdown(f"""
<div class="navbar">
  <div style="max-width:1200px;margin:auto;display:flex;align-items:center;justify-content:space-between;padding:0 20px;">
    <div style="display:flex;align-items:center;gap:15px">
      <div class="logo"><i class="fa-solid fa-user-shield" style="font-size: 18px; color: #fff;"></i></div>
      <div>
        <div class="brand-name">Kantaka Sodhana</div>
        <div class="brand-sub">Automated QR Verification</div>
      </div>
    </div>
    <a href="/usecases" style="padding:8px 20px;border-radius:999px;border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.05);text-decoration:none;color:var(--text);font-weight:600;font-size:14px;transition:all 0.3s ease;">
      <i class="fa-solid fa-arrow-left"></i> Back
    </a>
  </div>
</div>
""", unsafe_allow_html=True)


# ---------------- Layout ----------------
col_left, col_right = st.columns([1, 1.8], gap="large")

with col_left:
    st.markdown("### Upload Document")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload JPG / PNG certificate",
            type=["jpg", "jpeg", "png"],
            key="certificate_upload",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            st.image(uploaded_file, caption="Document Preview", use_container_width=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        verify_btn = st.button("🔍 Verify Document", key="verify_btn")

# ---------------- Temporary file handling ----------------
temp_image_path = None
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_image_path = temp_file.name

# ---------------- Processing & Right Column ----------------
with col_right:
    st.markdown("### Verification Results")
    
    if verify_btn:
        if not uploaded_file:
            st.error("⚠️ Please upload a certificate image first.")
        else:
            with st.status("Analyzing Document...", expanded=True) as status:
                
                st.write("🔍 Running Optical Character Recognition (OCR)...")
                try:
                    ocr = PaddleOCR(use_angle_cls=True, lang='en')
                    results = ocr.ocr(temp_image_path, cls=True)
                    texts = [line[1][0] for line in results[0]] if results and len(results) > 0 else []
                    joined_text = ' '.join(texts)
                    ocr_df = pd.DataFrame({'recognized_text': [joined_text]})
                except Exception as e:
                    status.update(label="OCR Failed", state="error", expanded=True)
                    st.error(f"OCR Exception: {e}")
                    st.stop()

                st.write("📦 Decoding QR Code...")
                img = cv2.imread(temp_image_path)
                url = decode_qr(img)
                if not url:
                    status.update(label="No QR Code Found", state="error", expanded=True)
                    st.error("No valid QR code was detected in the uploaded image.")
                    st.stop()

                st.write("📄 Extracting Portal Data...")
                app_df = extract_with_requests(url)
                if app_df is None or app_df.empty:
                    app_df = extract_with_selenium(url)

                if app_df is None or app_df.empty:
                    status.update(label="Extraction Failed", state="error", expanded=True)
                    st.error("Failed to extract data from the QR destination page.")
                    st.stop()

                # Clean Place of Death
                if "Place of Death" in app_df["Field"].values:
                    app_df.loc[app_df["Field"] == "Place of Death", "Value"] = (
                        app_df.loc[app_df["Field"] == "Place of Death", "Value"]
                        .str.split("/").str[0].str.strip()
                    )

                st.write("🧠 Cross-Referencing Data...")
                resultant_df = generate_clean_exact_match_df(ocr_df, app_df)
                if resultant_df is None:
                    status.update(label="Matching Failed", state="error", expanded=True)
                    st.error("No data available to perform matching.")
                    st.stop()
                
                status.update(label="Verification Complete!", state="complete", expanded=False)

            # Display QR Link in a container
            with st.container(border=True):
                st.markdown(f"🔗 **QR Destination:** <a href='{url}' class='qr-link' target='_blank'>{url}</a>", unsafe_allow_html=True)

            # Display custom HTML Glassmorphism Table
            st.markdown(generate_html_table(resultant_df), unsafe_allow_html=True)

            # Final Summary Badge
            all_matched = (resultant_df['result'] == 'matched').all()
            st.markdown("<br>", unsafe_allow_html=True)
            if all_matched:
                st.success("✅ **SUCCESS:** All certificate details match the official portal data.", icon="🛡️")
            else:
                st.error("⚠️ **WARNING:** Discrepancies found between the physical document and portal data.", icon="🚨")

    else:
        # Empty state prompt
        if not uploaded_file:
            st.markdown("""
            <div class="empty-state">
                <i class="fa-solid fa-file-shield"></i>
                <h4 style="margin:0;">Awaiting Document</h4>
                <p style="font-size: 14px;">Upload a certificate to begin automated verification.</p>
            </div>
            """, unsafe_allow_html=True)