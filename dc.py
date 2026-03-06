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
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException


# ============================
# Utility Functions
# ============================

def clean_text(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower())


def generate_clean_exact_match_df(ocr_df, app_df):
    if app_df is None or app_df.empty or ocr_df is None or ocr_df.empty:
        return None

    cleaned_ocr_text = clean_text(ocr_df['recognized_text'].iloc[0])

    def match_row(val):
        original_val = str(val).strip()
        cleaned_val = clean_text(original_val)

        if cleaned_val in cleaned_ocr_text:
            return pd.Series(['matched', original_val])
        else:
            return pd.Series(['not matched', ''])

    result_df = app_df.copy()
    result_df[['result', 'matched_text']] = result_df['Value'].apply(match_row)
    return result_df


# ============================
# QR Code Extraction (OpenCV)
# ============================

def decode_qr(image):
    detector = QReader()
    decoded_qrs, _ = detector.detect_and_decode(image=image, return_detections=True)
    return decoded_qrs[0] if decoded_qrs else None


# ============================
# Certificate Data Scraping
# ============================

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
                val = cells[1].text.strip()
                data.append((key, val))

        driver.quit()

        return pd.DataFrame(data, columns=["Field", "Value"]) if data else None

    except (WebDriverException, TimeoutException):
        return None


# ============================
# Streamlit UI
# ============================

st.set_page_config(
    page_title="Kotak Life QR Based Document Verification",
    layout="wide"
)

st.title("📝 Kotak Life QR Based Document Verification")

uploaded_file = st.file_uploader(
    "📤 Upload a Death Certificate Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_image_path = temp_file.name

    # ================= OCR =================
    st.info("🔍 Running OCR...")

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        results = ocr.ocr(temp_image_path, cls=True)

        texts = [line[1][0] for line in results[0]]
        joined_text = ' '.join(texts)

        ocr_df = pd.DataFrame({'recognized_text': [joined_text]})

    except Exception as e:
        st.error(f"OCR Failed: {e}")
        st.stop()

    # ================= QR =================
    st.info("📦 Decoding QR Code...")

    img = cv2.imread(temp_image_path)
    url = decode_qr(img)

    if not url:
        st.error("❌ No QR code found in the image.")
        st.stop()

    st.success(f"✅ QR URL Detected: {url}")

    # ================= Extract Data =================
    st.info("📄 Extracting certificate data...")

    app_df = extract_with_requests(url)

    if app_df is None or app_df.empty:
        app_df = extract_with_selenium(url)

    if app_df is None or app_df.empty:
        st.error("❌ Failed to extract data from the QR page.")
        st.stop()

    # Clean specific field example
    if "Place of Death" in app_df["Field"].values:
        app_df.loc[app_df["Field"] == "Place of Death", "Value"] = (
            app_df.loc[app_df["Field"] == "Place of Death", "Value"]
            .str.split("/")
            .str[0]
            .str.strip()
        )

    # ================= Matching =================
    st.info("🧠 Matching certificate data with OCR...")

    resultant_df = generate_clean_exact_match_df(ocr_df, app_df)

    if resultant_df is not None:
        st.success("✅ Matching Complete!")

        styled_df = resultant_df.style.applymap(
            lambda x: (
                'background-color: #00f23a; color: black; font-weight: bold;'
                if x == 'matched'
                else 'background-color: #ff0017; color: black; font-weight: bold;'
            ),
            subset=['result']
        )

        st.dataframe(styled_df)

        if all(resultant_df['result'] == 'matched'):
            st.success("✔️ The death certificate data matches the portal data.")
        else:
            st.warning("⚠️ The certificate data does not fully match.")