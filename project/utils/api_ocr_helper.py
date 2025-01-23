import logging
from io import BytesIO
from typing import Optional

import requests
from PIL import Image


class APIOCRHelper:
    def __init__(self, api_key: str):
        self.logger = logging.getLogger('APIOCRHelper')
        self.api_key = api_key
        self.api_url = "https://api.ocr.space/parse/image"

        # Updated language mapping
        self.language_mapping = {
            'ara': 'ara',
            'fra': 'fre',
            'eng': 'eng',
            'ara+fra': 'ara,fre'

        }

    def extract_text(self, image_path: str, language: str = 'ara') -> Optional[str]:
        try:
            # Map the language parameter to API
            api_language = self.language_mapping.get(language, 'ara')

            # Prepare the image
            image = Image.open(image_path)
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            # Optimize image for API
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG', quality=98)
            img_byte_arr = img_byte_arr.getvalue()

            # Prepare API request
            payload = {
                'apikey': self.api_key,
                'language': "auto",
                'OCREngine': 2,
                'detectOrientation': True,
                'scale': True,
                'isTable': False,
            }
            self.logger.info(payload)
            files = {
                'image': ('image.png', img_byte_arr, 'image/png')
            }

            # Make API request
            response = requests.post(
                self.api_url,
                files=files,
                data=payload,
                timeout=30
            )
            self.logger.info(response)

            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"API Response: {result}")

                if result.get('ParsedResults'):
                    text = result['ParsedResults'][0]['ParsedText']
                    self.logger.info("API OCR extraction successful")
                    return text
                else:
                    error_msg = result.get('ErrorMessage', 'Unknown error')
                    self.logger.error(f"API OCR Error: {error_msg}")
                    return None
            else:
                self.logger.error(f"API request failed with status code: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error in API OCR extraction: {str(e)}")
            return None

    def validate_api_key(self) -> bool:
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
                    return False
                return True
            return False

        except Exception as e:
            self.logger.error(f"API key validation failed: {str(e)}")
            return False
