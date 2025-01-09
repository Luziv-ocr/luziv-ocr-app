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
        self.logger.info("Application initialized successfully")

    def initialize_components(self):
        try:
            api_key = os.getenv("OCR_SPACE_API_KEY", st.secrets.get("OCR_SPACE_API_KEY", "18cebf81cc88957"))
            self.ocr_helper = OCRHelper(api_key=api_key)
            self.id_extractor = MoroccanIDExtractor()
            self.logger.info("Components initialized successfully")
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            st.error("Failed to initialize application components. Please check the logs.")

    def setup_session_state(self):
        if 'processing_history' not in st.session_state:
            st.session_state.processing_history = []

    def preprocess_uploaded_image(self, uploaded_file):
        try:
            image = Image.open(uploaded_file)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            return image
        except Exception as e:
            self.logger.error(f"Image preprocessing error: {e}")
            st.error(f"Error processing image: {str(e)}")
            return None

    def extract_and_parse_text(self, image):
        if not image:
            st.error("No image provided for processing")
            return None

        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            temp_path = 'temp_uploaded_image.jpg'
            image.save(temp_path, 'JPEG', quality=95)

            status_text.text("Extracting text from image...")
            progress_bar.progress(40)

            extracted_text = self.ocr_helper.extract_text(temp_path, method='auto', language='ara+fra')
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if not extracted_text:
                st.error("Failed to extract text from the image. Please try again or use a different image.")
                return None

            status_text.text("Parsing extracted text...")
            progress_bar.progress(70)

            parsed_data = self.id_extractor.extract(extracted_text)

            status_text.text("Processing complete!")
            progress_bar.progress(100)
            time.sleep(1)

            st.session_state.processing_history.append({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'result': parsed_data
            })

            return {
                'full_text': extracted_text,
                'parsed_data': parsed_data
            }

        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
            st.error(f"Error: {str(e)}")
            return None

    def render_application(self):
        st.title("🆔 Moroccan ID Card OCR")
        st.write("Upload a Moroccan ID card image or use your camera for intelligent text extraction.")

        # Toggle for selecting input method
        input_method = st.radio("Choose Input Method:", ("Upload File", "Use Camera"))

        image = None

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Choose an image",
                type=['png', 'jpg', 'jpeg'],
                help="Upload a clear, high-resolution image of a Moroccan ID card."
            )
            if uploaded_file:
                image = self.preprocess_uploaded_image(uploaded_file)

        elif input_method == "Use Camera":
            camera_image = st.camera_input("Take a picture")
            if camera_image:
                image = self.preprocess_uploaded_image(camera_image)

        if image:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Captured/Uploaded Image")
                st.image(image, use_container_width=True)

            with col2:
                if st.button("Extract Text"):
                    extraction_result = self.extract_and_parse_text(image)

                    if extraction_result:
                        tab1, tab2 = st.tabs(["📜 Full Text", "🔍 Parsed Info"])

                        with tab1:
                            st.text_area(
                                "Extracted Text",
                                value=extraction_result['full_text'],
                                height=200,
                                key="full_text_tab"
                            )

                        with tab2:
                            st.json(extraction_result['parsed_data'], expanded=True)

        if st.session_state.processing_history:
            with st.expander("Processing History"):
                for entry in reversed(st.session_state.processing_history):
                    st.write(f"**Processed at:** {entry['timestamp']}")
                    st.json(entry['result'])
                    st.markdown("---")

if __name__ == "__main__":
    app = EnhancedStreamlitOCR()
    app.render_application()
