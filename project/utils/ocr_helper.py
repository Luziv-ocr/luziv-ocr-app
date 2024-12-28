import logging
import os
import platform
import shutil
from pathlib import Path
from typing import Optional, Union
from PIL import Image
import cv2
import numpy as np
import pytesseract
import requests
from io import BytesIO


class OCRHelper:
    def __init__(self, api_key: str = None):
        self.setup_logging()
        self.api_key = api_key
        self.tesseract_available = self._check_tesseract()

    def setup_logging(self):
        self.logger = logging.getLogger('OCRHelper')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available and properly configured"""
        try:
            if platform.system().lower() == 'windows':
                tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    return True
            else:
                tesseract_path = shutil.which('tesseract')
                if tesseract_path:
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    return True

            # Try to set TESSDATA_PREFIX if not set
            if not os.getenv('TESSDATA_PREFIX'):
                possible_paths = [
                    '/usr/share/tesseract-ocr/4.00/tessdata',
                    '/usr/share/tessdata',
                    '/usr/local/share/tessdata'
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        os.environ['TESSDATA_PREFIX'] = path
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Tesseract check failed: {e}")
            return False

    def extract_text(self, image_path: Union[str, Path], method: str = 'auto',
                     language: str = 'ara+fra') -> Optional[str]:
        """
        Extract text from image using specified OCR method

        Args:
            image_path: Path to image file
            method: OCR method ('auto', 'tesseract', or 'api')
            language: Language code(s) for OCR
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            # Try Tesseract first if available and method is 'auto' or 'tesseract'
            if method in ['auto', 'tesseract'] and self.tesseract_available:
                text = self._extract_with_tesseract(image, language)
                if text:
                    return text
                elif method == 'tesseract':
                    return None

            # Fallback to API or if API method specifically requested
            if method in ['auto', 'api'] and self.api_key:
                return self._extract_with_api(image, language)

            raise ValueError("No available OCR method")

        except Exception as e:
            self.logger.error(f"Text extraction error: {str(e)}")
            return None

    def _extract_with_tesseract(self, image: Image.Image, language: str) -> Optional[str]:
        """Extract text using Tesseract OCR"""
        try:
            # Convert language code
            lang_map = {'ara+fra': 'ara+fra', 'ara': 'ara', 'fra': 'fra', 'eng': 'eng'}
            tesseract_lang = lang_map.get(language, 'eng')

            # Configure Tesseract
            config = '--oem 3 --psm 3'

            # Extract text
            text = pytesseract.image_to_string(image, lang=tesseract_lang, config=config)

            return text.strip() if text.strip() else None

        except Exception as e:
            self.logger.error(f"Tesseract extraction failed: {e}")
            return None

    def _extract_with_api(self, image: Image.Image, language: str) -> Optional[str]:
        """Extract text using OCR.space API"""
        try:
            if not self.api_key:
                raise ValueError("API key required for OCR.space API")

            # Prepare image
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Configure API request
            lang_map = {
                'ara+fra': 'ara,fre',
                'ara': 'ara',
                'fra': 'fre',
                'eng': 'eng'
            }
            api_lang = lang_map.get(language, 'eng')

            payload = {
                'apikey': self.api_key,
                'language': api_lang,
                'OCREngine': 2,
                'scale': True,
                'isTable': False
            }

            files = {
                'image': ('image.png', img_byte_arr, 'image/png')
            }

            # Make API request
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files=files,
                data=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('ParsedResults'):
                    return result['ParsedResults'][0]['ParsedText'].strip()

            return None

        except Exception as e:
            self.logger.error(f"API extraction failed: {e}")
            return None

