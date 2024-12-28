import streamlit as st
import os
import logging
from PIL import Image
from utils.ocr_helper import OCRHelper
from utils.text_parser import MoroccanIDExtractor
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Moroccan ID OCR",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="auto",
)


class EnhancedStreamlitOCR:
    def __init__(self):
        self.setup_logging()
        self.initialize_components()
        self.setup_session_state()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('StreamlitOCR')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.info("Application initialized successfully")

    def initialize_components(self):
        try:
            # Get API key from environment or secrets
            api_key = os.getenv("OCR_SPACE_API_KEY", st.secrets.get("OCR_SPACE_API_KEY", "K88544333088957"))

            self.ocr_helper = OCRHelper(api_key=api_key)
            self.id_extractor = MoroccanIDExtractor()
            self.logger.info("Components initialized successfully")

        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            st.error("Failed to initialize application components. Please check the logs.")

    def setup_session_state(self):
        if 'processing_history' not in st.session_state:
            st.session_state.processing_history = []
        if 'last_processed_image' not in st.session_state:
            st.session_state.last_processed_image = None

    def preprocess_uploaded_image(self, uploaded_file):
        try:
            image = Image.open(uploaded_file)
            self.logger.info(f"Image uploaded: {uploaded_file.name}")
            self.logger.info(f"Image size: {image.size}")
            self.logger.info(f"Image mode: {image.mode}")

            if image.mode == 'RGBA':
                image = image.convert('RGB')
                self.logger.info("Converted image from RGBA to RGB")

            st.session_state.last_processed_image = image
            return image

        except Exception as e:
            self.logger.error(f"Image preprocessing error: {e}")
            st.error(f"Error processing image: {str(e)}")
            return None

    def extract_and_parse_text(self, image, ocr_method='auto', language='ara+fra'):
        if not image:
            st.error("No image provided for processing")
            return None

        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Saving image for processing...")
            progress_bar.progress(20)

            temp_path = 'temp_uploaded_image.jpg'
            image.save(temp_path, 'JPEG', quality=95)

            status_text.text("Extracting text from image...")
            progress_bar.progress(40)

            try:
                if ocr_method == 'tesseract' and not self.ocr_helper.tesseract_available:
                    st.warning("Tesseract is not available. Falling back to API method.")
                    ocr_method = 'api'

                extracted_text = self.ocr_helper.extract_text(
                    temp_path,
                    method=ocr_method,
                    language=language
                )

                if extracted_text is None:
                    st.error("Failed to extract text from the image. Please try again or use a different image.")
                    self.logger.error("Text extraction failed")
                    return None

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            status_text.text("Parsing extracted text...")
            progress_bar.progress(70)

            parsed_data = self.id_extractor.extract(extracted_text)

            status_text.text("Processing complete!")
            progress_bar.progress(100)
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()

            st.session_state.processing_history.append({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'method': ocr_method,
                'language': language,
                'result': parsed_data
            })

            return {
                'full_text': extracted_text,
                'parsed_data': parsed_data
            }

        except Exception as e:
            self.logger.error(f"Text extraction error: {e}")
            st.error(f"Error extracting text: {str(e)}")
            if 'progress_bar' in locals():
                progress_bar.empty()
            if 'status_text' in locals():
                status_text.empty()
            return None

    def render_application(self):
        st.title("🆔 Moroccan ID Card OCR")
        st.write("Upload a Moroccan ID card image for intelligent text extraction")

        col1, col2 = st.columns(2)

        with col1:
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

        with col2:
            ocr_method = st.radio(
                "Select OCR Method",
                options=['auto', 'api', 'tesseract'],
                format_func=lambda x: {
                    'auto': "Automatic (Recommended)",
                    'tesseract': "Tesseract (Local)" + (
                        " - Not Available" if not self.ocr_helper.tesseract_available else ""),
                    'api': "OCR.space API"
                }[x],
                help="Choose OCR method or let the system decide automatically"
            )

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

        if st.session_state.processing_history:
            with st.expander("Processing History", expanded=False):
                for entry in reversed(st.session_state.processing_history):
                    st.write(f"**Processed at:** {entry['timestamp']}")
                    st.write(f"**Method:** {entry['method']}")
                    st.write(f"**Language:** {entry['language']}")
                    st.json(entry['result'])
                    st.markdown("---")


if __name__ == "__main__":
    app = EnhancedStreamlitOCR()
    app.render_application()