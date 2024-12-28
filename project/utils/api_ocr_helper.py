import requests
import logging
from pathlib import Path
from typing import Optional, Dict
from PIL import Image
from io import BytesIO


class APIOCRHelper:
    """
    Dedicated OCR.space API helper class with improved error handling and response processing
    """

    def __init__(self, api_key: str):
        self.setup_logging()
        self.api_key = api_key
        self.api_url = "https://api.ocr.space/parse/image"

        # Language mapping for OCR.space API
        self.language_mapping = {
            'ara': 'Arabic',
            'fra': 'French',
            'eng': 'English',
            'ara+fra': 'Arabic,French'
        }

    def setup_logging(self):
        """Initialize logging configuration"""
        self.logger = logging.getLogger('APIOCRHelper')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _prepare_image(self, image_path: str) -> Optional[bytes]:
        """
        Prepare image for API submission by optimizing and converting to proper format

        Args:
            image_path: Path to the image file

        Returns:
            Bytes of the processed image or None if processing fails
        """
        try:
            image = Image.open(image_path)

            # Convert RGBA to RGB if needed
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            # Optimize image for API
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG', optimize=True, quality=95)
            return img_byte_arr.getvalue()

        except Exception as e:
            self.logger.error(f"Image preparation failed: {str(e)}")
            return None

    def extract_text(self, image_path: str, language: str = 'ara+fra') -> Optional[str]:
        """
        Extract text from image using OCR.space API

        Args:
            image_path: Path to the image file
            language: OCR language configuration (default: 'ara+fra')

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Map the language parameter to API format
            api_language = self.language_mapping.get(language, 'English')

            # Prepare the image
            img_bytes = self._prepare_image(image_path)
            if not img_bytes:
                return None

            # Prepare API request
            payload = {
                'apikey': self.api_key,
                'language': api_language,
                'OCREngine': 2,  # More accurate engine
                'detectOrientation': True,
                'scale': True,
                'isTable': False,
                'filetype': 'PNG',
                'forceCreateSession': True,
                'detectCheckbox': False,
                'checkboxTemplate': 0,
            }

            files = {
                'image': ('image.png', img_bytes, 'image/png')
            }

            # Make API request with timeout
            response = requests.post(
                self.api_url,
                files=files,
                data=payload,
                timeout=30
            )

            # Process response
            if response.status_code == 200:
                result = response.json()

                # Check for API errors
                if 'ErrorMessage' in result and result['ErrorMessage']:
                    self.logger.error(f"API Error: {result['ErrorMessage']}")
                    return None

                # Extract text from results
                if result.get('ParsedResults'):
                    text = result['ParsedResults'][0]['ParsedText']
                    self.logger.info("API OCR extraction successful")
                    return text.strip()
                else:
                    self.logger.error("No parsed results in API response")
                    return None
            else:
                self.logger.error(f"API request failed with status code: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            self.logger.error("API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in API OCR extraction: {str(e)}")
            return None

    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test request

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            # Create a small test image
            test_image = Image.new('RGB', (100, 30), color='white')
            img_byte_arr = BytesIO()
            test_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Make a test request
            response = requests.post(
                self.api_url,
                files={'image': ('test.png', img_byte_arr, 'image/png')},
                data={
                    'apikey': self.api_key,
                    'language': 'eng',
                    'OCREngine': 2
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if 'ErrorMessage' in result and 'Invalid API key' in result['ErrorMessage']:
                    self.logger.error("Invalid API key")
                    return False
                self.logger.info("API key validation successful")
                return True

            self.logger.error(f"API key validation failed with status code: {response.status_code}")
            return False

        except Exception as e:
            self.logger.error(f"API key validation failed: {str(e)}")
            return False


def main():
    """Test function for the API OCR Helper"""
    # Replace with your actual API key
    api_key = "K88544333088957"

    # Initialize helper
    helper = APIOCRHelper(api_key)

