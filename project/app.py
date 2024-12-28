import streamlit as st
import os
import logging
from PIL import Image
from utils.ocr_helper import OCRHelper
from utils.text_parser import MoroccanIDExtractor

# Configure Streamlit page
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
        **Version:** 1.0.4  
        **Purpose:** Intelligent Document Processing for Moroccan ID Cards
        """
    }
)


class EnhancedStreamlitOCR:
    def __init__(self):
        self.setup_logging()
        self.initialize_ocr()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('StreamlitOCR')
        self.logger.info("Application initialized successfully")

    def initialize_ocr(self):
        try:
            self.ocr_helper = OCRHelper(api_key="K88544333088957")
            self.id_extractor = MoroccanIDExtractor()
            self.logger.info("OCR Helper initialized successfully")
        except Exception as e:
            self.logger.error(f"OCR Helper initialization failed: {e}")
            st.error(f"OCR Helper initialization failed: {e}")
            self.ocr_helper = None

    def preprocess_uploaded_image(self, uploaded_file):
        try:
            image = Image.open(uploaded_file)

            self.logger.info(f"Image uploaded: {uploaded_file.name}")
            self.logger.info(f"Image size: {image.size}")
            self.logger.info(f"Image mode: {image.mode}")

            if image.mode == 'RGBA':
                image = image.convert('RGB')
                self.logger.info("Converted image from RGBA to RGB")

            return image
        except Exception as e:
            self.logger.error(f"Image preprocessing error: {e}")
            st.error(f"Error processing image: {e}")
            return None

    def extract_and_parse_text(self, image, ocr_method='tesseract', language='ara+fra'):
        if self.ocr_helper is None:
            st.error("OCR Helper not initialized.")
            return None

        try:
            # Save image to temporary file
            temp_path = 'temp_uploaded_image.jpg'
            image.save(temp_path, 'JPEG', quality=95)

            # Extract text using selected method
            extracted_text = self.ocr_helper.extract_text(
                temp_path,
                method=ocr_method,
                language=language
            )

            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if not extracted_text:
                st.warning("No text could be extracted from the image.")
                return None

            # Parse extracted data
            parsed_data = self.id_extractor.extract(extracted_text)

            return {
                'full_text': extracted_text,
                'parsed_data': parsed_data
            }

        except Exception as e:
            self.logger.error(f"Text extraction error: {e}")
            st.error(f"Error extracting text: {e}")
            return None

    def render_application(self):
        st.title("🆔 Moroccan ID Card OCR")
        st.write("Upload a Moroccan ID card image for intelligent text extraction")

        # Language selection
        language = st.selectbox(
            "Select Language",
            options=['ara+fra', 'ara', 'fra', 'eng'],
            format_func=lambda x: {
                'ara+fra': 'Arabic + French',
                'ara': 'Arabic',
                'fra': 'French',
                'eng': 'English'
            }[x],
            help="Choose the language(s) for OCR"
        )

        # OCR method selection
        ocr_method = st.radio(
            "Select OCR Method",
            options=['tesseract', 'api'],
            format_func=lambda x: "Tesseract (Local)" if x == 'tesseract' else "OCR.space API",
            help="Choose between local Tesseract OCR or cloud-based OCR.space API"
        )

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear, high-resolution image of a Moroccan ID card"
        )

        if uploaded_file is not None:
            image = self.preprocess_uploaded_image(uploaded_file)

            if image:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Uploaded Image")
                    st.image(image, use_container_width=True)

                with col2:
                    st.subheader("Extracted Information")

                    if st.button("Extract Text", type="primary"):
                        with st.spinner(f"Processing image using {ocr_method.capitalize()}..."):
                            extraction_result = self.extract_and_parse_text(
                                image,
                                ocr_method=ocr_method,
                                language=language
                            )

                            if extraction_result:
                                tab1, tab2 = st.tabs(["📜 Full Text", "🔍 Parsed Info"])

                                with tab1:
                                    st.text_area(
                                        "Extracted Text",
                                        value=extraction_result['full_text'],
                                        height=200
                                    )

                                with tab2:
                                    st.json(extraction_result['parsed_data'])


if __name__ == "__main__":
    app = EnhancedStreamlitOCR()
    app.render_application()