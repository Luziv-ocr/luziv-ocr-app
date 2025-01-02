import cv2
import numpy as np
from PIL import Image
import logging
import os
from typing import Optional, Union
from pathlib import Path
import platform
import shutil
import pytesseract
from .api_ocr_helper import APIOCRHelper


class OCRHelper:
    def __init__(self, api_key: str = None):
        self.setup_logging()
        self.api_key = api_key
        self.api_helper = APIOCRHelper(api_key) if api_key else None
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
        try:
            if platform.system().lower() == 'windows':
                tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    self.logger.info(f"Tesseract found at: {tesseract_path}")
                    return True
            else:
                tesseract_path = shutil.which('tesseract')
                if tesseract_path:
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    self.logger.info(f"Tesseract found at: {tesseract_path}")
                    return True

            self.logger.warning("Tesseract not found or not properly configured")
            return False
        except Exception as e:
            self.logger.error(f"Tesseract check failed: {e}")
            return False

    def extract_text(self, image_path: Union[str, Path], method: str = 'api',
                     language: str = 'ara+fra') -> Optional[str]:
        """
        Extract text from image using specified method
        """
        try:
            # if method == 'api' and self.api_helper:
            return self.api_helper.extract_text(image_path, language)
            # elif method == 'tesseract' and self.tesseract_available:
            #     return self._extract_text_tesseract(image_path, language)
            # elif method == 'auto':
            #     # Try API first, then fall back to Tesseract
            #     if self.api_helper:
            #         result = self.api_helper.extract_text(image_path, language)
            #         if result:
            #             return result
            #     if self.tesseract_available:
            #         return self._extract_text_tesseract(image_path, language)

            self.logger.error("No valid OCR method available")
            return None

        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return None

    def _extract_text_tesseract(self, image_path: Union[str, Path], language: str) -> Optional[str]:
        """
        Extract text using Tesseract OCR
        """
        try:
            # Map language codes to Tesseract format
            lang_mapping = {
                'ara': 'ara',
                'fra': 'fra',
                'eng': 'eng',
                'ara+fra': 'ara+fra'
            }
            tesseract_lang = lang_mapping.get(language, 'ara+fra')

            # Read image using PIL
            image = Image.open(image_path)

            # Extract text
            text = pytesseract.image_to_string(image, lang=tesseract_lang)

            if text.strip():
                self.logger.info("Tesseract OCR extraction successful")
                return text.strip()
            else:
                self.logger.warning("Tesseract OCR returned empty text")
                return None

        except Exception as e:
            self.logger.error(f"Tesseract OCR extraction failed: {e}")
            return None