import streamlit as st
from supabase import create_client, Client
import os
import logging
from PIL import Image
from utils.ocr_helper import OCRHelper
from utils.text_parser import MoroccanIDExtractor
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StreamlitOCR")

# Configure Streamlit page
st.set_page_config(
    page_title="Moroccan ID OCR",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="auto",
)


def init_supabase():
    """Initialize Supabase client with fallback options"""
    try:
        # Try to get from st.secrets first
        supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
        supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]
    except KeyError:
        # Fallback to environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        # If still not found, use default values (not recommended for production)
        if not supabase_url or not supabase_key:
            logger.warning("Using default Supabase credentials. This is not recommended for production.")
            supabase_url = "https://zonxlcgvjzibarsduajd.supabase.co"
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvbnhsY2d2anppYmFyc2R1YWpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4MTgyMjgsImV4cCI6MjA1MTM5NDIyOH0.MQO_j-JgWfbmZ_4s9Cndwc4ldmHl5uC9AgPwtdolnKo"

    return create_client(supabase_url, supabase_key)


# Initialize Supabase client
supabase: Client = init_supabase()


def verify_jwt(token):
    """Verify JWT token with Supabase"""
    try:
        response = supabase.auth.get_user(token)
        return response
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        return None


class StreamlitWithAuth:
    def __init__(self):
        self.setup_session_state()

    def setup_session_state(self):
        """Initialize session state variables"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user" not in st.session_state:
            st.session_state.user = None

    def check_authentication(self):
        """Check if user is authenticated"""
        try:
            # Get token from URL query params
            params = st.experimental_get_query_params()
            token = params.get('token', [None])[0]

            if not token:
                st.warning("Please log in to access this application.")
                st.markdown("If you don't have an account, please sign up [here](your-signup-url)")
                st.stop()

            # Verify the JWT with Supabase
            user = verify_jwt(token)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
            else:
                st.warning("Invalid or expired token. Please log in again.")
                st.stop()

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            st.error("An error occurred during authentication. Please try again.")
            st.stop()

    def render_application(self):
        """Main application render method"""
        # Check authentication before proceeding
        self.check_authentication()

        # If authenticated, render the OCR application
        app = EnhancedStreamlitOCR()
        app.render_application()


class EnhancedStreamlitOCR:
    def __init__(self):
        self.setup_logging()
        self.initialize_components()
        self.setup_session_state()

    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("StreamlitOCR")
        self.logger.info("Application initialized successfully")

    def initialize_components(self):
        """Initialize OCR components"""
        try:
            # Try to get API key from different sources
            api_key = (
                    os.getenv("OCR_SPACE_API_KEY") or
                    st.secrets.get("ocr", {}).get("OCR_SPACE_API_KEY") or
                    "K88544333088957"  # fallback value
            )
            self.ocr_helper = OCRHelper(api_key=api_key)
            self.id_extractor = MoroccanIDExtractor()
            self.logger.info("Components initialized successfully")
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            st.error("Failed to initialize application components. Please try again.")

    def setup_session_state(self):
        """Initialize session state variables"""
        if "processing_history" not in st.session_state:
            st.session_state.processing_history = []

    def preprocess_uploaded_image(self, uploaded_file):
        """Preprocess uploaded image"""
        try:
            image = Image.open(uploaded_file)
            if image.mode == "RGBA":
                image = image.convert("RGB")
            return image
        except Exception as e:
            self.logger.error(f"Image preprocessing error: {e}")
            st.error("Error processing image. Please try a different image.")
            return None

    def preprocess_camera_image(self, camera_image):
        """Preprocess camera captured image"""
        try:
            if camera_image:
                image = Image.open(camera_image)
                if image.mode == "RGBA":
                    image = image.convert("RGB")
                return image
            return None
        except Exception as e:
            self.logger.error(f"Camera image preprocessing error: {e}")
            st.error("Error processing camera image. Please try again.")
            return None

    def extract_and_parse_text(self, image):
        """Extract and parse text from image"""
        if not image:
            st.error("No image provided for processing")
            return None

        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Save temporary image
            temp_path = "temp_uploaded_image.jpg"
            image.save(temp_path, "JPEG", quality=100, optimize=True)

            status_text.text("Extracting text from image...")
            progress_bar.progress(40)

            # Extract text
            extracted_text = self.ocr_helper.extract_text(temp_path, method="api", language="ara+fra")

            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if not extracted_text:
                st.error("Failed to extract text from the image. Please try again.")
                return None

            status_text.text("Parsing extracted text...")
            progress_bar.progress(70)

            # Parse extracted text
            parsed_data = self.id_extractor.extract(extracted_text)

            status_text.text("Processing complete!")
            progress_bar.progress(100)
            time.sleep(1)

            # Store in history
            st.session_state.processing_history.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "result": parsed_data
            })

            return {"full_text": extracted_text, "parsed_data": parsed_data}

        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
            st.error(f"An error occurred during processing: {str(e)}")
            return None

    def render_application(self):
        """Render the main application interface"""
        st.title("🆔 Moroccan ID Card OCR")
        st.write("Upload a Moroccan ID card image for intelligent text extraction.")

        # User information
        if st.session_state.user:
            st.sidebar.write(f"Welcome, {st.session_state.user.user.email}")

        # File upload and camera input
        uploaded_file = st.file_uploader(
            "Choose an image",
            type=["png", "jpg", "jpeg"],
            help="Upload a clear, high-resolution image of a Moroccan ID card."
        )

        camera_image = st.camera_input("Or capture image using your camera")

        image = None
        if uploaded_file:
            image = self.preprocess_uploaded_image(uploaded_file)
        elif camera_image:
            image = self.preprocess_camera_image(camera_image)

        if image:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Uploaded/Camera Image")
                st.image(image, use_container_width=True)

            with col2:
                if st.button("Extract Text", type="primary"):
                    with st.spinner("Processing image..."):
                        extraction_result = self.extract_and_parse_text(image)

                        if extraction_result:
                            tab1, tab2 = st.tabs(["📜 Full Text", "🔍 Parsed Info"])

                            with tab1:
                                st.text_area(
                                    "Extracted Text",
                                    value=extraction_result["full_text"],
                                    height=200,
                                    key="full_text_tab"
                                )

                            with tab2:
                                st.json(extraction_result["parsed_data"])

        # Processing History
        if st.session_state.processing_history:
            with st.expander("Processing History"):
                for entry in reversed(st.session_state.processing_history):
                    st.write(f"**Processed at:** {entry['timestamp']}")
                    st.json(entry['result'])
                    st.markdown("---")


if __name__ == "__main__":
    try:
        app = StreamlitWithAuth()
        app.render_application()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page and try again.")