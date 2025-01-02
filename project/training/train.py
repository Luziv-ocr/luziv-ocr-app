import cv2
import numpy as np
from PIL import Image


class LimitedDataOCRPreprocessor:
    @staticmethod
    def preprocess_image(image_path):
        """
        Advanced image preprocessing for clearer text detection (especially black text).
        """
        # Read image
        img = cv2.imread(image_path)

        # Ensure the image is valid
        if img is None:
            raise ValueError(f"Image not found or invalid path provided: {image_path}")

        # Convert to grayscale for simplification
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Multiple preprocessing techniques for clearer text detection
        preprocessed_variants = [
            # 1. Grayscale conversion
            gray_img,

            # 2. Adaptive thresholding to enhance text regions
            cv2.adaptiveThreshold(
                gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            ),

            # 3. Histogram equalization to enhance contrast and highlight text
            cv2.equalizeHist(gray_img),

            # 4. Noise reduction to reduce unnecessary noise around text
            cv2.fastNlMeansDenoising(gray_img, h=10, templateWindowSize=7, searchWindowSize=21),

            # 5. Sharpening to make the text edges more defined
            cv2.filter2D(gray_img, -1, kernel=np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])),

            # 6. CLAHE (Contrast Limited Adaptive Histogram Equalization)
            cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray_img)
        ]

        return preprocessed_variants

    @staticmethod
    def data_augmentation(image_path):
        """
        Generate synthetic training samples with better visibility of text.
        """
        img = cv2.imread(image_path)

        # Ensure the image is valid
        if img is None:
            raise ValueError(f"Image not found or invalid path provided: {image_path}")

        augmented_images = []

        # Augmentation techniques to make text more visible
        try:
            # 1. Rotation
            augmented_images.extend([
                cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
                cv2.rotate(img, cv2.ROTATE_180),
                cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            ])

            # 2. Brightness variations to enhance text visibility
            augmented_images.extend([
                cv2.convertScaleAbs(img, alpha=1.5, beta=30),  # Brighter for better contrast
                cv2.convertScaleAbs(img, alpha=0.5, beta=-30)  # Darker to make text stand out
            ])

            # 3. Perspective transform to simulate text angle variations
            rows, cols, _ = img.shape
            src_points = np.float32([[0, 0], [cols - 1, 0], [0, rows - 1], [cols - 1, rows - 1]])
            dst_points = np.float32([[50, 50], [cols - 50, 30], [30, rows - 50], [cols - 30, rows - 30]])
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            perspective_transform = cv2.warpPerspective(img, matrix, (cols, rows))
            augmented_images.append(perspective_transform)

        except Exception as e:
            print(f"Error during data augmentation: {e}")

        return augmented_images


def prepare_training_data(image_paths):
    """
    Comprehensive data preparation strategy for clearer text detection.
    """
    training_images = []

    for path in image_paths:
        try:
            # Preprocess
            preprocessed_variants = LimitedDataOCRPreprocessor.preprocess_image(path)
            training_images.extend(preprocessed_variants)

            # Augment
            augmented_variants = LimitedDataOCRPreprocessor.data_augmentation(path)
            training_images.extend(augmented_variants)

        except Exception as e:
            print(f"Error processing image {path}: {e}")

    return training_images


# Example usage
image_paths = [
    r"C:\Users\PC\Desktop\5976675309006735097_121.jpg",
    r"C:\Users\PC\Desktop\5974108864183912068_121.jpg"
]
training_images = prepare_training_data(image_paths)
