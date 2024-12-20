import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict


class MoroccanIDExtractor:
    def __init__(self):
        """
        Define patterns for extracting specific fields from Moroccan ID text.
        """
        self.patterns = {
            'cin_number': r'\b[A-Z]{1,2}\d{6}\b',  # CIN: 1-2 letters followed by 6 digits
            'name': r'NOM\s*ET\s*PRENOM\s*[:]*\s*([A-Z\s\-]+)',
            'birth_date': r'N[eé]\s*le\s*(\d{2}[./-]\d{2}[./-]\d{4})',
            'birth_place': r'\b(?:\u00e0|a)\s*([A-Z\s\-]+)',
            'expiry_date': r'Valable\s*jusqu\'au\s*(\d{2}[./-]\d{2}[./-]\d{4})'
        }

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text: remove accents, extra spaces, and unify format.
        """
        text = unicodedata.normalize('NFKD', text)  # Remove accents
        text = re.sub(r'\s+', ' ', text).strip()  # Remove multiple spaces
        return text

    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """
        Convert date string to standard format (YYYY-MM-DD).
        """
        if not date_str:
            return None
        date_str = date_str.replace('.', '/').replace('-', '/')
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            return None

    def extract(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract relevant fields from Moroccan ID card text.
        """
        # Normalize and remove headers
        text = self.normalize_text(text)

        # Ignore known header terms
        headers_to_ignore = ["ROYAUME DU MAROC", "CARTE NATIONALE D'IDENTITE"]
        for header in headers_to_ignore:
            text = text.replace(header, "")

        extracted = {
            'CIN Number': None,
            'Full Name': None,
            'Date of Birth': None,
            'Birth Place': None,
            'Expiry Date': None
        }

        # CIN Number
        if cin_match := re.search(self.patterns['cin_number'], text):
            extracted['CIN Number'] = cin_match.group()

        # Full Name
        if name_match := re.search(self.patterns['name'], text):
            extracted['Full Name'] = name_match.group(1).strip()

        # Date of Birth
        if birth_date_match := re.search(self.patterns['birth_date'], text):
            extracted['Date of Birth'] = self.parse_date(birth_date_match.group(1))

        # Birth Place
        if birth_place_match := re.search(self.patterns['birth_place'], text):
            extracted['Birth Place'] = birth_place_match.group(1).strip()

        # Expiry Date
        if expiry_date_match := re.search(self.patterns['expiry_date'], text):
            extracted['Expiry Date'] = self.parse_date(expiry_date_match.group(1))

        return extracted


def main():
    """
    Simulate OCR output and test Moroccan ID extraction.
    """
    ocr_output = """
    ROYAUME DU MAROC
    CARTE NATIONALE D'IDENTITE
    NOM ET PRENOM: JAMAL DIAE-EDDINE
    Né le 10.06.2002 à KHENIFRA
    CIN: Y510850
    Valable jusqu'au 17.10.2032
    """

    # Initialize extractor
    extractor = MoroccanIDExtractor()

    # Extract information
    result = extractor.extract(ocr_output)

    # Display results
    print("\nExtracted Moroccan ID Information:")
    for field, value in result.items():
        print(f"{field}: {value}")


if __name__ == "__main__":
    main()
