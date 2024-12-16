import cv2
import numpy as np
import pytesseract
from PIL import Image


class LimitedDataOCRPreprocessor:
    @staticmethod
    def preprocess_image(image_path):
        """
        Advanced image preprocessing for limited data"""
        # Read image
        img = cv2.imread(image_path)

        # Multiple preprocessing techniques
        preprocessed_variants = [
            # 1. Grayscale conversion
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),

            # 2. Adaptive thresholding
            cv2.adaptiveThreshold(
                cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            ),

            # 3. Enhanced contrast
            cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)),

            # 4. Noise reduction
            cv2.fastNlMeansDenoising(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        ]

        return preprocessed_variants

    @staticmethod
    def data_augmentation(image_path):
        """
        Generate synthetic training samples"""
        img = cv2.imread(image_path)
        augmented_images = []

        # Augmentation techniques
        augmentations = [
            # 1. Rotation
            cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
            cv2.rotate(img, cv2.ROTATE_180),

            # 2. Brightness variations
            cv2.convertScaleAbs(img, alpha=1.5, beta=30),
            cv2.convertScaleAbs(img, alpha=0.5, beta=-30),

            # 3. Perspective transforms
            lambda img: cv2.warpPerspective(
                img,
                cv2.getPerspectiveTransform(
                    np.float32([[0, 0], [img.shape[1], 0], [0, img.shape[0]], [img.shape[1], img.shape[0]]]),
                    np.float32([[50, 50], [img.shape[1] - 50, 30], [30, img.shape[0] - 50],
                                [img.shape[1] - 30, img.shape[0] - 30]])
                ),
                (img.shape[1], img.shape[0])
            )
        ]

        return augmentations


def prepare_training_data(image_paths):
    """
    Comprehensive data preparation strategy"""
    training_images = []

    for path in image_paths:
        # Preprocess
        preprocessed_variants = LimitedDataOCRPreprocessor.preprocess_image(path)
        training_images.extend(preprocessed_variants)

        # Augment
        augmented_variants = LimitedDataOCRPreprocessor.data_augmentation(path)
        training_images.extend(augmented_variants)

    return training_images


# Example usage
image_paths = [
    r"C:\Users\PC\Desktop\5976675309006735097_121.jpg",
    r"C:\Users\PC\Desktop\5974108864183912068_121.jpg"
]
training_images = prepare_training_data(image_paths)