import streamlit as st
import os
import re
import logging
from io import BytesIO
from PIL import Image

# Configuration initiale de la page
st.set_page_config(
    page_title="Moroccan ID OCR",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://github.com/yourusername/moroccan-id-ocr/wiki',
        'Report a bug': 'https://github.com/yourusername/moroccan-id-ocr/issues',
        'About': """
        ## Moroccan ID OCR Application

        **Version:** 1.0.3  
        **Purpose:** Intelligent Document Processing for Moroccan ID Cards

        Developed with advanced OCR technologies.

        ### Features
        - Advanced Text Extraction
        - Multilingual Support (Arabic & French)
        - Intelligent Data Parsing

        Created with ❤️ using Streamlit
        """
    }
)

# Configuration de pytesseract et vérification de Tesseract OCR
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # Pour Streamlit Cloud
except ImportError:
    st.error("Pytesseract n'est pas installé. Ajoutez-le dans `requirements.txt`.")
    pytesseract = None


class OCRHelper:
    def __init__(self):
        self.logger = logging.getLogger('OCRHelper')
        self.tesseract_installed = self.check_tesseract()

    def check_tesseract(self):
        """
        Vérifie si Tesseract est installé et disponible.
        """
        if pytesseract is None:
            st.error("Pytesseract n'est pas configuré correctement.")
            return False

        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract Version: {version}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur de vérification Tesseract : {e}")
            st.error("Tesseract OCR n'est pas installé ou mal configuré.")
            return False

    def extract_text(self, image, language='ara+fra'):
        """
        Extraction du texte à partir d'une image via Tesseract.
        """
        if not self.tesseract_installed:
            st.error("Tesseract OCR n'est pas configuré.")
            return None

        try:
            extracted_text = pytesseract.image_to_string(image, lang=language)
            return extracted_text
        except Exception as e:
            self.logger.error(f"Erreur d'extraction OCR : {e}")
            st.error(f"Erreur lors de l'extraction : {e}")
            return None


class EnhancedStreamlitOCR:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('StreamlitOCR')
        self.ocr_helper = OCRHelper()

    def preprocess_uploaded_image(self, uploaded_file):
        """
        Pré-traitement de l'image téléchargée.
        """
        try:
            image = Image.open(uploaded_file)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            return image
        except Exception as e:
            self.logger.error(f"Erreur de traitement de l'image : {e}")
            st.error(f"Erreur de traitement de l'image : {e}")
            return None

    def parse_extracted_data(self, text):
        """
        Analyse des données extraites via OCR.
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

        patterns = {
            'cin_number': r'\b[A-Z]{1,2}\d{6}\b',
            'date_of_birth': r'\d{2}/\d{2}/\d{4}',
            'latin_name': r'[A-Z][a-z]+ [A-Z][a-z]+',
            'arabic_name': r'[\u0600-\u06FF\s]+',
        }

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

    def render_application(self):
        """
        Rendu de l'interface utilisateur Streamlit.
        """
        st.title("🆔 Moroccan ID Card OCR")
        st.write("Téléchargez une carte d'identité marocaine pour extraire les informations.")

        if not self.ocr_helper.tesseract_installed:
            st.error("Tesseract OCR n'est pas configuré. Vérifiez votre configuration.")
            return

        uploaded_file = st.file_uploader(
            "Choisissez une image",
            type=['png', 'jpg', 'jpeg'],
            help="Téléchargez une image claire et de haute résolution."
        )

        if uploaded_file:
            image = self.preprocess_uploaded_image(uploaded_file)
            if image:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Image téléchargée")
                    st.image(image, use_column_width=True)

                with col2:
                    st.subheader("Informations extraites")
                    if st.button("Extraire le texte"):
                        with st.spinner("Traitement de l'image..."):
                            extracted_text = self.ocr_helper.extract_text(image)
                            if extracted_text:
                                st.text_area("Texte brut extrait :", extracted_text, height=200)

                                parsed_data = self.parse_extracted_data(extracted_text)
                                st.subheader("Données analysées :")
                                st.json(parsed_data)


# Démarrage de l'application
if __name__ == "__main__":
    app = EnhancedStreamlitOCR()
    app.render_application()
