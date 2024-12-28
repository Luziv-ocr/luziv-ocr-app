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

    def extract(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract relevant fields from Moroccan ID card text.
        Handles both Arabic and French text.

        Args:
            text: OCR extracted text from ID card

        Returns:
            Dictionary containing extracted information
        """
        # Normalize text
        text = self.normalize_text(text)

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

        # Extract CIN Number
        if cin_match := re.search(self.patterns['cin_number'], text):
            extracted['CIN Number'] = cin_match.group()

        # Extract Name (try both French and Arabic patterns)
        for lang in ['fr', 'ar']:
            if name_match := re.search(self.patterns['name'][lang], text):
                extracted['Full Name'] = name_match.group(1).strip()
                break

        # Extract Birth Date
        for lang in ['fr', 'ar']:
            if birth_date_match := re.search(self.patterns['birth_date'][lang], text):
                extracted['Date of Birth'] = self.parse_date(birth_date_match.group(1))
                break

        # Extract Birth Place
        for lang in ['fr', 'ar']:
            if birth_place_match := re.search(self.patterns['birth_place'][lang], text):
                extracted['Place of Birth'] = birth_place_match.group(1).strip()
                break

        # Extract Gender
        for lang in ['fr', 'ar']:
            if gender_match := re.search(self.patterns['gender'][lang], text):
                gender_value = gender_match.group(1)
                if lang == 'fr':
                    extracted['Gender'] = 'Male' if gender_value == 'M' else 'Female'
                else:
                    extracted['Gender'] = 'Male' if gender_value == 'ذ' else 'Female'
                break

        # Extract Address
        for lang in ['fr', 'ar']:
            if address_match := re.search(self.patterns['address'][lang], text):
                extracted['Address'] = address_match.group(1).strip()
                break

        # Extract Expiry Date
        for lang in ['fr', 'ar']:
            if expiry_match := re.search(self.patterns['expiry_date'][lang], text):
                extracted['Expiry Date'] = self.parse_date(expiry_match.group(1))
                break

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