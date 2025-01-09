import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict


class MoroccanIDExtractor:
    def __init__(self):
        """
        Initialize patterns for extracting specific fields from Moroccan ID text.
        Supports both Arabic and French text formats.
        """
        self.patterns = {
            'cin_number': r'\b[A-Z]{1,2}\d{6}\b',  # CIN: 1-2 letters followed by 6 digits
            'name': {
                'fr': r'NOM\s*ET\s*PRENOM\s*[:]*\s*([A-Z\s\-]+)',
                'ar': r'الاسم\s*الكامل\s*[:]*\s*([\u0600-\u06FF\s]+)'
            },
            'birth_date': {
                'fr': r'N[eé]\s*le\s*(\d{2}[./-]\d{2}[./-]\d{4})',
                'ar': r'تاريخ\s*الازدياد\s*[:]*\s*(\d{2}[./-]\d{2}[./-]\d{4})'
            },
            'birth_place': {
                'fr': r'\b(?:\u00e0|a)\s*([A-Z\s\-]+)',
                'ar': r'مكان\s*الازدياد\s*[:]*\s*([\u0600-\u06FF\s]+)'
            },
            'expiry_date': {
                'fr': r'Valable\s*jusqu\'au\s*(\d{2}[./-]\d{2}[./-]\d{4})',
                'ar': r'صالحة\s*إلى\s*غاية\s*(\d{2}[./-]\d{2}[./-]\d{4})'
            },
            'gender': {
                'fr': r'Sexe\s*[:]*\s*([MF])',
                'ar': r'الجنس\s*[:]*\s*([ذأ])'
            },
            'address': {
                'fr': r'Adresse\s*[:]*\s*([A-Z0-9\s\-\.,]+)',
                'ar': r'العنوان\s*[:]*\s*([\u0600-\u06FF0-9\s\-\.,]+)'
                "ss"
            }
        }

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text by removing accents, extra spaces, and unifying format.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text string
        """
        # Remove accents
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))

        # Remove multiple spaces and trim
        text = re.sub(r'\s+', ' ', text).strip()

        # Standardize Arabic characters
        arabic_chars = {
            'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
            'ة': 'ه',
            'ى': 'ي',
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
        }
        for ar_char, replacement in arabic_chars.items():
            text = text.replace(ar_char, replacement)

        return text

    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """
        Convert date string to standard format (YYYY-MM-DD).

        Args:
            date_str: Date string in various formats

        Returns:
            Standardized date string or None if parsing fails
        """
        if not date_str:
            return None

        # Standardize separators
        date_str = date_str.replace('.', '/').replace('-', '/')

        try:
            # Try different date formats
            for fmt in ['%d/%m/%Y', '%Y/%m/%d', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def clean_irrelevant_lines(self, text: str) -> str:
        """
        Remove irrelevant lines and text patterns.

        Args:
            text: Input text to clean

        Returns:
            Cleaned text
        """
        # Remove lines with no useful information (French and Arabic headers)
        patterns_to_remove = [
            r'(ROYAUME DU MAROC|CARTE NATIONALE D\'IDENTITE)',
            r'(المملكة المغربية|البطاقة الوطنية للتعريف)'
        ]
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text.strip()

    def extract(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract relevant fields from Moroccan ID card text.
        Handles both Arabic and French text.

        Args:
            text: OCR extracted text from ID card

        Returns:
            Dictionary containing extracted information
        """
        # Normalize and clean text
        text = self.normalize_text(text)
        text = self.clean_irrelevant_lines(text)

        # Initialize results dictionary
        extracted = {
            'CIN Number': None,
            'Full Name': None,
            'Date of Birth': None,
            'Place of Birth': None,
            'Gender': None,
            'Address': None,
            'Expiry Date': None
        }

        # Extract fields
        for key, patterns in self.patterns.items():
            if isinstance(patterns, dict):  # Handle language-specific patterns
                for lang, pattern in patterns.items():
                    if match := re.search(pattern, text):
                        if key == 'birth_date' or key == 'expiry_date':
                            extracted[key.replace('_', ' ').title()] = self.parse_date(match.group(1))
                        else:
                            extracted[key.replace('_', ' ').title()] = match.group(1).strip()
                        break
            else:
                if match := re.search(patterns, text):
                    extracted[key.replace('_', ' ').title()] = match.group()

        return extracted


def main():
    """Test function for the Moroccan ID Extractor"""
    # Sample text (both French and Arabic)
    test_texts = [
        """
        ROYAUME DU MAROC
        CARTE NATIONALE D'IDENTITE
        NOM ET PRENOM: MOHAMMED ALAMI
        Né le 15.06.1990 à RABAT
        CIN: A123456
        Sexe: M
        Adresse: 123 RUE HASSAN II, RABAT
        Valable jusqu'au 20.10.2030
        """,
        """
        المملكة المغربية
        البطاقة الوطنية للتعريف
        الاسم الكامل: محمد علمي
        تاريخ الازدياد: 15/06/1990
        مكان الازدياد: الرباط
        رقم البطاقة: A123456
        الجنس: ذ
        العنوان: 123 شارع الحسن الثاني، الرباط
        صالحة إلى غاية 20/10/2030
        """
    ]

    extractor = MoroccanIDExtractor()

    for i, test_text in enumerate(test_texts, 1):
        print(f"\nTest {i} Results:")
        results = extractor.extract(test_text)
        for field, value in results.items():
            print(f"{field}: {value}")
        print("-" * 50)


if __name__ == "__main__":
    main()
