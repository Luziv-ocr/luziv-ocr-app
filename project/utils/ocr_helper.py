import logging
import re
import subprocess
import os
import platform
import shutil
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Union
from io import BytesIO

import cv2
import numpy as np
import pytesseract
from PIL import Image


class OCRConfig:
    TESSERACT_CONFIG = {
        'oem': 3,
        'psm': 3,
        'langs': ['ara', 'fra', 'eng'],
        'dpi': 300,
        'preserve_interword_spaces': 1,
        'language_mapping': {
            'ara': 'ara',
            'fra': 'fra',
            'eng': 'eng',
            'ara+fra': 'ara+fra'
        }
    }

    IMAGE_PROCESSING = {
        'max_dimension': 3000,
        'clahe_clip_limit': 3.0,
        'clahe_grid_size': (8, 8),
        'denoise_parameters': {
            'h': 10,
            'templateWindowSize': 7,
            'searchWindowSize': 21
        },
        'adaptive_thresholding': {
            'block_size': 11,
            'c_value': 2
        }
    }

    API_CONFIG = {
        'url': 'https://api.ocr.space/parse/image',
        'engine': 2,
        'language_mapping': {
            'ara': 'ara',
            'fra': 'fre',
            'eng': 'eng',
            'ara+fra': 'ara,fre'  # Updated language codes for API
        }
    }


class ImagePreprocessor:
    @staticmethod
    def preprocess(image: Union[Image.Image, np.ndarray]) -> Image.Image:
        # Convert PIL Image to OpenCV format if needed
        if isinstance(image, Image.Image):
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_array = image

        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(
            clipLimit=OCRConfig.IMAGE_PROCESSING['clahe_clip_limit'],
            tileGridSize=OCRConfig.IMAGE_PROCESSING['clahe_grid_size']
        )
        img_array = clahe.apply(img_array)

        # Denoise
        img_array = cv2.fastNlMeansDenoising(
            img_array,
            None,
            h=OCRConfig.IMAGE_PROCESSING['denoise_parameters']['h']
        )

        # Adaptive thresholding
        img_array = cv2.adaptiveThreshold(
            img_array,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            OCRConfig.IMAGE_PROCESSING['adaptive_thresholding']['block_size'],
            OCRConfig.IMAGE_PROCESSING['adaptive_thresholding']['c_value']
        )

        return Image.fromarray(img_array)


class OCRHelper:
    def __init__(self, api_key: str = None, logger_level: int = logging.INFO):
        """
        Initialize OCRHelper with API key and logging configuration

        Args:
            api_key: OCR.space API key
            logger_level: Logging level (default: logging.INFO)
        """
        self.setup_logging(logger_level)
        self.api_key = api_key
        self._configure_tesseract()
        self.preprocessor = ImagePreprocessor()

    def setup_logging(self, level: int):
        """Setup logging configuration"""
        self.logger = logging.getLogger('OCRHelper')
        self.logger.setLevel(level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _configure_tesseract(self):
        """Configure Tesseract OCR path based on operating system"""
        try:
            if platform.system().lower() == 'windows':
                tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
                    self.logger.info(f"Using Tesseract from: {tesseract_path}")
                    return
            else:
                tesseract_path = shutil.which('tesseract')
                if tesseract_path:
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    self.logger.info(f"Found Tesseract at: {tesseract_path}")
                    return

            raise EnvironmentError("Tesseract not found")

        except Exception as e:
            self.logger.error(f"Failed to configure Tesseract: {e}")
            raise

    def extract_text(self, image_path: Union[str, Path], method: str = 'tesseract',
                     language: str = 'ara+fra') -> Optional[str]:
        """
        Extract text from image using specified OCR method

        Args:
            image_path: Path to image file
            method: OCR method ('tesseract' or 'api')
            language: Language code(s) for OCR

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            # Preprocess image
            processed_image = self.preprocessor.preprocess(image)

            # Extract text using selected method
            if method == 'tesseract':
                return self._extract_with_tesseract(processed_image, language)
            elif method == 'api':
                return self._extract_with_api(processed_image, language)
            else:
                raise ValueError(f"Unsupported OCR method: {method}")

        except Exception as e:
            self.logger.error(f"Error in text extraction: {str(e)}")
            return None

    def _extract_with_tesseract(self, image: Image.Image, language: str) -> Optional[str]:
        """Extract text using Tesseract OCR"""
        try:
            # Handle multiple languages
            if language == 'ara+fra':
                tesseract_lang = 'ara+fra'
            else:
                tesseract_lang = OCRConfig.TESSERACT_CONFIG['language_mapping'].get(language, language)

            config = f'--oem {OCRConfig.TESSERACT_CONFIG["oem"]} --psm {OCRConfig.TESSERACT_CONFIG["psm"]}'

            text = pytesseract.image_to_string(
                image,
                lang=tesseract_lang,
                config=config
            )

            if text.strip():
                self.logger.info("Tesseract OCR extraction successful")
                return text.strip()
            else:
                self.logger.warning("Tesseract OCR produced empty result")
                return None

        except Exception as e:
            self.logger.error(f"Tesseract OCR Error: {str(e)}")
            return None

    def _extract_with_api(self, image: Image.Image, language: str) -> Optional[str]:
        """Extract text using OCR.space API"""
        try:
            if not self.api_key:
                raise ValueError("API key is required for OCR.space API method")

            # Convert image to bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG', optimize=True, quality=95)
            img_byte_arr = img_byte_arr.getvalue()

            # Get correct language code for API
            api_language = OCRConfig.API_CONFIG['language_mapping'].get(language, 'eng')

            # Prepare API request
            payload = {
                'apikey': self.api_key,
                'language': api_language,
                'OCREngine': OCRConfig.API_CONFIG['engine'],
                'detectOrientation': True,
                'scale': True,
                'isTable': False,
                'filetype': 'PNG',
            }

            files = {
                'image': ('image.png', img_byte_arr, 'image/png')
            }

            # Make API request with timeout
            response = requests.post(
                OCRConfig.API_CONFIG['url'],
                files=files,
                data=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # Check for API errors
                if 'ErrorMessage' in result and result['ErrorMessage']:
                    error_msg = result['ErrorMessage']
                    self.logger.error(f"API Error: {error_msg}")
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
            self.logger.error(f"API OCR Error: {str(e)}")
            return None

    def validate_api_key(self) -> bool:
        """
        Validate the OCR.space API key

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            if not self.api_key:
                return False

            # Create a small test image
            test_image = Image.new('RGB', (100, 30), color='white')
            img_byte_arr = BytesIO()
            test_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Make test request
            response = requests.post(
                OCRConfig.API_CONFIG['url'],
                files={'image': ('test.png', img_byte_arr, 'image/png')},
                data={
                    'apikey': self.api_key,
                    'language': 'eng',
                    'OCREngine': OCRConfig.API_CONFIG['engine']
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

            return False

        except Exception as e:
            self.logger.error(f"API key validation failed: {str(e)}")
            return False


def main():
    """Test function for OCRHelper"""
    # Replace with your actual API key
    api_key = "YOUR_API_KEY"

    # Initialize helper
    ocr_helper = OCRHelper(api_key)

    # Test API key validation
    if ocr_helper.validate_api_key():
        print("API key is valid")
    else:
        print("API key is invalid")


if __name__ == "__main__":
    main()