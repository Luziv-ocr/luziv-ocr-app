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
            'birth_date': r'(\d{2}[./-]\d{2}[./-]\d{4})',  # Matches dates in DD.MM.YYYY format
            'place_of_birth': r'\bب\s*([\u0600-\u06FF\s]+)',  # Arabic: Match "ب خنيفره"
            'expiry_date': r'Valable\s*jusqu\'au\s*(\d{2}[./-]\d{2}[./-]\d{4})|صالحة\s*إلى\s*غاية\s*(\d{2}[./-]\d{2}[./-]\d{4})'
        }

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text by removing accents, extra spaces, and unifying format.
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
        """
        if not date_str:
            return None

        # Standardize separators
        date_str = date_str.replace('.', '/').replace('-', '/')

        try:
            return datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            return None

    def clean_irrelevant_lines(self, text: str) -> str:
        """
        Remove irrelevant lines and text patterns.
        """
        # Remove lines with no useful information (French and Arabic headers)
        patterns_to_remove = [
            r'(ROYAUME DU MAROC|CARTE NATIONALE D\'IDENTITE)',
            r'(المملكة المغربية|البطاقة الوطنية للتعريف)',
            r'المدير العام للامن الوطني|Way'
        ]
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text.strip()

    def extract(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract relevant fields from Moroccan ID card text.
        """
        # Normalize and clean text
        text = self.normalize_text(text)

        # Clean irrelevant headers
        cleaned_text = self.clean_irrelevant_lines(text)

        # Initialize results dictionary
        extracted = {
            'CIN Number': None,
            'Full Name': None,
            'Date of Birth': None,
            'Place of Birth': None,
            'Expiry Date': None
        }

        # Extract CIN number
        if match := re.search(self.patterns['cin_number'], cleaned_text):
            extracted['CIN Number'] = match.group()

        # Extract full name (first major line)
        match_name = re.search(r'\b([A-Z][A-Z-]+ [A-Z][A-Z-]+)\b', cleaned_text)
        if match_name:
            extracted['Full Name'] = match_name.group(1)

        # Extract date of birth
        if match := re.search(self.patterns['birth_date'], cleaned_text):
            extracted['Date of Birth'] = self.parse_date(match.group(1))

        # Extract place of birth
        if match := re.search(self.patterns['place_of_birth'], cleaned_text):
            place = match.group(1).strip()
            # Remove leading or irrelevant words like "تاريخ"
            place = re.sub(r'^تاريخ\s*', '', place)
            extracted['Place of Birth'] = place

        # Extract expiry date
        if match := re.search(self.patterns['expiry_date'], cleaned_text):
            extracted['Expiry Date'] = self.parse_date(match.group(1) or match.group(2))

        return extracted


def main():
    """Test function for the Moroccan ID Extractor"""
    test_text = """
    ROYAUME DU MAROC
    CARTE NATIONALE D'IDENTITE
    DIAE-EDDINE JAMAL Ne le à KHENIFRA المملكه المغربيه البطاقه الوطنيه للتعريف ضياء الدين جمال مزداد بتاريخ تاريخ ب خنيفره 10.06.2002 المدير العام للامن الوطني Way, عبد اللطيف شي CAN 217945 N° Y510850 ES2 Valable jusqu'au 17.10.2032 صالحة إلى غاية
    """

    extractor = MoroccanIDExtractor()
    results = extractor.extract(test_text)
    for field, value in results.items():
        print(f"{field}: {value}")


if __name__ == "__main__":
    main()
