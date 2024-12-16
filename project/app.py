import streamlit as st
import os
import re
import base64
from io import BytesIO
from PIL import Image
import pytesseract
import cv2
import numpy as np


class EnhancedTextExtractor:
    @staticmethod
    def preprocess_image(image):
        """Advanced image preprocessing for better OCR"""
        # Convert to grayscale
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

        # Apply thresholding
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)

        return denoised

    @staticmethod
    def extract_text_multilingual(image):
        """
        Extract text using Tesseract with multiple languages
        """
        preprocessed = EnhancedTextExtractor.preprocess_image(image)

        # Tesseract configuration for Arabic and French
        custom_config = r'--oem 3 --psm 6 -l ara+fra'

        # Extract text
        text = pytesseract.image_to_string(preprocessed, config=custom_config)
        return text

    @staticmethod
    def separate_languages(text):
        """Separate Arabic and French texts"""
        # Regex for Arabic and Latin characters
        arabic_pattern = re.compile(r'[\u0600-\u06FF]+')
        latin_pattern = re.compile(r'[a-zA-Z]+')

        # Separate lines
        lines = text.split('\n')

        arabic_lines = []
        french_lines = []

        for line in lines:
            if arabic_pattern.search(line):
                arabic_lines.append(line)
            elif latin_pattern.search(line):
                french_lines.append(line)

        return {
            'arabic_text': '\n'.join(arabic_lines),
            'french_text': '\n'.join(french_lines)
        }

    @staticmethod
    def parse_extracted_data(text):
        """
        Basic parsing of extracted text
        """
        parsed_data = {
            'names': {
                'arabic': None,
                'latin': None
            },
            'cin_number': None,
            'date_of_birth': None,
            'place_of_birth': None,
            'expiry_date': None
        }

        # Simple regex patterns for extraction
        patterns = {
            'cin_number': r'\b[A-Z]{1,2}\d{6}\b',
            'date_of_birth': r'\d{2}/\d{2}/\d{4}',
            'latin_name': r'[A-Z][a-z]+ [A-Z][a-z]+',
            'arabic_name': r'[\u0600-\u06FF\s]+',
        }

        # Extract information using regex
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                if key == 'latin_name':
                    parsed_data['names']['latin'] = match.group(0)
                elif key == 'arabic_name':
                    parsed_data['names']['arabic'] = match.group(0)
                elif key == 'cin_number':
                    parsed_data['cin_number'] = match.group(0)
                elif key == 'date_of_birth':
                    parsed_data['date_of_birth'] = match.group(0)

        return parsed_data


def main():
    st.set_page_config(page_title="Moroccan ID OCR", layout="wide")

    st.title("🆔 Moroccan ID Card OCR")
    st.write("Upload a Moroccan ID card image for text extraction")

    # File uploader
    uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        # Read the image
        image = Image.open(uploaded_file)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Uploaded Image")
            st.image(image, use_container_width=True)

        with col2:
            st.subheader("Extracted Information")

            if st.button("Extract Text"):
                with st.spinner("Processing..."):
                    # Extract text
                    extracted_text = EnhancedTextExtractor.extract_text_multilingual(image)

                    # Separate languages
                    language_texts = EnhancedTextExtractor.separate_languages(extracted_text)

                    # Parse extracted data
                    parsed_data = EnhancedTextExtractor.parse_extracted_data(extracted_text)

                    # Create tabs
                    tab1, tab2, tab3 = st.tabs(["📜 Full Text", "🇲🇦 Arabic", "🇫🇷 French"])

                    with tab1:
                        st.text(extracted_text)

                    with tab2:
                        st.markdown("#### Arabic Text")
                        st.text(language_texts['arabic_text'])
                        if parsed_data['names']['arabic']:
                            st.markdown(f"**Arabic Name:** {parsed_data['names']['arabic']}")

                    with tab3:
                        st.markdown("#### French Text")
                        st.text(language_texts['french_text'])

                        st.markdown("##### Parsed Information")
                        if parsed_data['names']['latin']:
                            st.markdown(f"**Name:** {parsed_data['names']['latin']}")
                        if parsed_data['cin_number']:
                            st.markdown(f"**CIN Number:** {parsed_data['cin_number']}")
                        if parsed_data['date_of_birth']:
                            st.markdown(f"**Date of Birth:** {parsed_data['date_of_birth']}")


if __name__ == "__main__":
    main()