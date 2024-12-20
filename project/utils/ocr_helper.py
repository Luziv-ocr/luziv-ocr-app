# Standard library imports
import logging
import re
import subprocess
import sys
import os
import platform
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

# Third-party library imports
import cv2
import numpy as np
import pytesseract
from PIL import Image


class LoggerConfig:
    """Advanced logging configuration"""

    @staticmethod
    def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
        """Create a configured logger with console and file handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Clear any existing handlers to prevent duplicate logs
        if logger.hasHandlers():
            logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # Ensure log directory exists
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # File handler
        log_file = log_dir / f'{name}.log'
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger


class OCRConfig:
    """Enhanced OCR configuration with more flexible settings"""
    TESSERACT_CONFIG = {
        'oem': 3,  # LSTM OCR Engine Mode
        'psm': 6,  # Assume uniform block of text
        'langs': ['ara', 'fra', 'eng'],  # Multilingual support
        'dpi': 300,
        'preserve_interword_spaces': 1,
        'whitelist': {
            'ara': r'[\u0600-\u06FF\s]',
            'fra': r'[A-Za-zÀ-ÿ\s]',
            'eng': r'[A-Za-z\s]'
        }
    }

    IMAGE_PROCESSING = {
        'max_dimension': 2000,
        'clahe_clip_limit': 2.0,
        'clahe_grid_size': (8, 8),
        'denoise_parameters': {
            'h': 10,
            'hColor': 10,
            'templateWindowSize': 7,
            'searchWindowSize': 21
        },
        'adaptive_thresholding': {
            'block_size': 11,
            'c_value': 2
        }
    }


class ImagePreprocessor:
    """Advanced image preprocessing with multiple techniques"""

    @classmethod
    def preprocess(cls, image: Union[Image.Image, np.ndarray],
                   techniques: Optional[List[str]] = None) -> Image.Image:
        """
        Advanced image preprocessing with selectable techniques

        Args:
            image: Input image
            techniques: List of preprocessing techniques to apply
        """
        # Default techniques if none specified
        default_techniques = [
            'to_grayscale',
            'clahe',
            'denoise',
            'adaptive_threshold',
            'skew_correction'
        ]
        techniques = techniques or default_techniques

        # Convert to numpy array if PIL Image
        img_array = np.array(image) if isinstance(image, Image.Image) else image

        # Grayscale conversion
        if 'to_grayscale' in techniques and len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # CLAHE
        if 'clahe' in techniques:
            clahe = cv2.createCLAHE(
                clipLimit=OCRConfig.IMAGE_PROCESSING['clahe_clip_limit'],
                tileGridSize=OCRConfig.IMAGE_PROCESSING['clahe_grid_size']
            )
            img_array = clahe.apply(img_array)

        # Denoising
        if 'denoise' in techniques:
            params = OCRConfig.IMAGE_PROCESSING['denoise_parameters']
            img_array = cv2.fastNlMeansDenoisingColored(
                img_array,
                h=params['h'],
                hColor=params['hColor'],
                templateWindowSize=params['templateWindowSize'],
                searchWindowSize=params['searchWindowSize']
            )

        # Adaptive Thresholding
        if 'adaptive_threshold' in techniques:
            params = OCRConfig.IMAGE_PROCESSING['adaptive_thresholding']
            img_array = cv2.adaptiveThreshold(
                img_array,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                params['block_size'],
                params['c_value']
            )

        # Skew Correction
        if 'skew_correction' in techniques:
            img_array = cls._correct_skew(img_array)

        return Image.fromarray(img_array)

    @staticmethod
    def _correct_skew(image: np.ndarray) -> np.ndarray:
        """
        Correct image skew using Hough Transform
        """
        # Detect lines
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]

        # Adjust for horizontal/vertical orientation
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated


class TextCleaner:
    """Advanced text cleaning and post-processing"""

    @staticmethod
    def clean_text(text: str, language: str = 'eng') -> str:
        """
        Clean and normalize extracted text

        Args:
            text: Raw extracted text
            language: Language of the text

        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""

        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()

        # Language-specific cleaning
        if language == 'eng':
            # Remove non-printable characters
            text = re.sub(r'[^\x20-\x7E]', '', text)
        elif language == 'ara':
            # Arabic-specific cleaning
            text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
        elif language == 'fra':
            # French-specific cleaning
            text = re.sub(r'[^A-Za-zÀ-ÿ\s]', '', text)

        return text


class OCRHelper:
    def __init__(self, logger_level: int = logging.INFO):
        """
        Initialize OCR Helper with robust Tesseract installation

        Args:
            logger_level: Logging level for the logger
        """
        self.logger = LoggerConfig.setup_logger(level=logger_level)
        self._install_tesseract()
        self._verify_tesseract()
        self.preprocessor = ImagePreprocessor()
        self.text_cleaner = TextCleaner()

    def _install_tesseract(self) -> None:
        """
        Cross-platform Tesseract installation attempt
        """
        try:
            # Check current system
            system = platform.system().lower()

            if system == 'linux':
                # For Linux (including Streamlit Cloud)
                try:
                    # Preferred methods for Linux
                    installation_commands = [
                        ['sudo', 'apt-get', 'update'],
                        ['sudo', 'apt-get', 'install', '-y', 'tesseract-ocr'],
                        ['sudo', 'apt-get', 'install', '-y',
                         'tesseract-ocr-eng',
                         'tesseract-ocr-ara',
                         'tesseract-ocr-fra']
                    ]

                    for cmd in installation_commands:
                        try:
                            subprocess.run(cmd, check=True, capture_output=True, text=True)
                        except subprocess.CalledProcessError as e:
                            self.logger.warning(f"Command {cmd} failed: {e.stderr}")

                    # Try to locate Tesseract binary
                    tesseract_path = shutil.which('tesseract')
                    if tesseract_path:
                        pytesseract.pytesseract.tesseract_cmd = tesseract_path
                        self.logger.info(f"Tesseract installed at: {tesseract_path}")
                except Exception as apt_error:
                    self.logger.warning(f"Linux Tesseract installation attempt failed: {apt_error}")

            elif system == 'darwin':
                # For macOS
                subprocess.run(['brew', 'install', 'tesseract'], check=True)

            elif system == 'windows':
                # For Windows
                subprocess.run(['choco', 'install', 'tesseract'], check=True)

        except Exception as e:
            self.logger.error(f"Tesseract installation globally failed: {e}")

    def _verify_tesseract(self) -> None:
        """Enhanced Tesseract verification with multiple fallback methods"""
        tesseract_path = shutil.which('tesseract')
        if tesseract_path:
            self.logger.info(f"Tesseract found at: {tesseract_path}")
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            self.logger.error("Tesseract not found! Ensure it is installed and available in the system PATH.")
            raise EnvironmentError("Tesseract OCR not found.")

    def extract_text(self, image_path: Union[str, Path],
                     language: str = 'eng',
                     custom_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Extract text from document image with advanced configuration
        """
        try:
            # Validate image path
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            # Process image
            with Image.open(path) as img:
                # Check if the image is empty
                if img.size == (0, 0):
                    self.logger.error(f"Image at {image_path} is empty.")
                    return None

                # Convert image to RGB if it is in RGBA mode
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                    self.logger.info(f"Converted image from RGBA to RGB.")
                else:
                    self.logger.info(f"Image mode is {img.mode}, no conversion needed.")

                # Resize if needed
                img = self._resize_if_needed(img)

                # Preprocess
                processed_img = self.preprocessor.preprocess(img)

                # Configure OCR
                config = self._build_tesseract_config(language, custom_config)

                # Perform OCR
                raw_text = pytesseract.image_to_string(
                    processed_img,
                    config=config
                )

                # Clean text
                cleaned_text = self.text_cleaner.clean_text(raw_text, language)

                if cleaned_text:
                    self.logger.info("OCR successful.")
                    return cleaned_text

                self.logger.warning("OCR produced empty result.")
                return None

        except Exception as e:
            # More detailed error logging
            self.logger.error(f"Comprehensive OCR Error: {str(e)}")
            return None

    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """
        Resize image if its dimension is greater than max allowed
        """
        max_dimension = OCRConfig.IMAGE_PROCESSING['max_dimension']
        width, height = image.size
        if width > max_dimension or height > max_dimension:
            scale_factor = max_dimension / max(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.ANTIALIAS)
            self.logger.info(f"Resized image to: {new_width}x{new_height}")
        return image
