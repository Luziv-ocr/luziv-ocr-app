import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import cv2
import numpy as np
from PIL import Image
import pytesseract
import concurrent.futures
import re


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

        # File handler
        file_handler = logging.FileHandler(f'{name}.log', mode='a')
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
                   techniques: List[str] = None) -> Image.Image:
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
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image

        # Grayscale conversion
        if 'to_grayscale' in techniques:
            if len(img_array.shape) == 3:
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
    def __init__(self):
        self.logger = LoggerConfig.setup_logger()
        self._verify_tesseract()
        self.preprocessor = ImagePreprocessor()
        self.text_cleaner = TextCleaner()

    def _verify_tesseract(self) -> None:
        """Verify Tesseract installation"""
        try:
            pytesseract.get_tesseract_version()
            self.logger.info("Tesseract successfully verified")
        except pytesseract.TesseractNotFoundError:
            self.logger.error("Tesseract not found in system PATH")
            raise RuntimeError("Tesseract is not installed or not in system PATH")

    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """Resize image if it exceeds maximum dimensions"""
        max_dim = OCRConfig.IMAGE_PROCESSING['max_dimension']
        if max(image.size) > max_dim:
            ratio = max_dim / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            self.logger.debug(f"Resizing image from {image.size} to {new_size}.")
            return image.resize(new_size, Image.Resampling.LANCZOS)
        return image

    def extract_text(self,
                     image_path: str,
                     language: str = 'eng',
                     custom_config: Dict[str, Any] = None) -> Optional[str]:
        """
        Extract text from document image with advanced configuration

        Args:
            image_path: Path to the image file
            language: Primary language for OCR
            custom_config: Custom Tesseract configuration

        Returns:
            Extracted and cleaned text or None
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
            self.logger.error(f"Error during OCR: {str(e)}")
            return None

    def _build_tesseract_config(self,
                                language: str,
                                custom_config: Dict[str, Any] = None) -> str:
        """
        Build Tesseract configuration

        Args:
            language: OCR language
            custom_config: Additional configuration

        Returns:
            Formatted Tesseract configuration string
        """
        # Base configuration
        base_config = OCRConfig.TESSERACT_CONFIG.copy()

        # Apply custom configuration if provided
        if custom_config:
            base_config.update(custom_config)

        # Create configuration string
        config = (
            f'--oem {base_config["oem"]} '
            f'--psm {base_config["psm"]} '
            f'-l {language} '
            f'--dpi {base_config["dpi"]} '
            f'-c preserve_interword_spaces='
            f'{base_config["preserve_interword_spaces"]}'
        )

        return config

    def batch_ocr_processing(self,
                             image_paths: List[str],
                             max_workers: int = None) -> Dict[str, Optional[str]]:
        """
        Batch OCR processing with concurrent execution

        Args:
            image_paths: List of image file paths
            max_workers: Maximum number of concurrent workers

        Returns:
            Dictionary of results with image paths as keys
        """
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.extract_text, path): path
                for path in image_paths
            }

            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results[path] = result
                except Exception as exc:
                    self.logger.error(f'{path} generated an exception: {exc}')

        return results


def main():
    # Initialize OCR Helper
    ocr_helper = OCRHelper()

    # Single image processing
    try:
        text = ocr_helper.extract_text('document.jpg', language='eng')
        print("Extracted Text:", text)
    except Exception as e:
        print(f"Error processing single image: {e}")

    # Batch processing
    try:
        batch_results = ocr_helper.batch_ocr_processing([
            'doc1.jpg', 'doc2.jpg', 'doc3.jpg'
        ])
        for path, text in batch_results.items():
            print(f"{path}: {text}")
    except Exception as e:
        print(f"Error in batch processing: {e}")


if __name__ == "__main__":
    main()