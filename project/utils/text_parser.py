import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict, Any, List


class MoroccanIDExtractor:
    def __init__(self):
        self.patterns = {
            'full_name': r'(?:NOM\s*(?:ET\s*)?PRENOM\s*[:]*\s*)([A-ZÀ-Ÿ\s-]+)',
            'arabic_name': r'[\u0600-\u06FF\s\-\']+',
            'cin_number': r'[A-Z]\d{6}',
            'date_of_birth': r'(?:Né\s*(?:le)?|Date\s*de\s*naissance)\s*[:]*\s*(\d{2}[./]\d{2}[./]\d{4})',
            'birth_place': r'(?:à|Lieu\s*de\s*naissance)\s*[:]*\s*([A-ZÀ-Ÿa-z\s-]+)',
            'gender': r'(?:Sexe\s*[:]*\s*)(HOMME|FEMME|M|F)',
            'nationality': r'(?:Nationalité\s*[:]*\s*)([A-ZÀ-Ÿa-z\s]+)',
            'expiry_date': r'(?:Valable\s*jusqu\'au|Valid\s*until)\s*[:]*\s*(\d{2}[./]\d{2}[./]\d{4})'
        }

    def normalize_text(self, text: str) -> str:
        """
        Normalize text by removing extra spaces and converting to standard form
        """
        # Normalize unicode and remove extra whitespaces
        normalized = unicodedata.normalize('NFKD', text)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def parse_date(self, date_str: str) -> Optional[datetime.date]:
        """
        Parse date with multiple format support
        """
        if not date_str:
            return None

        # Standardize date separators
        date_str = date_str.replace('.', '/').replace('-', '/')
        date_formats = [
            '%d/%m/%Y',  # 10/06/2002
            '%m/%d/%Y',  # 06/10/2002
            '%Y/%m/%d',  # 2002/06/10
            '%d/%m/%y',  # 10/06/02
            '%m/%d/%y'  # 06/10/02
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def extract_moroccan_id(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive extraction of Moroccan ID details
        """
        # Normalize input text
        normalized_text = self.normalize_text(text)

        # Initialize result dictionary
        result = {
            'document_type': 'Carte Nationale d\'Identité',
            'full_name': None,
            'cin_number': None,
            'date_of_birth': None,
            'birth_place': None,
            'gender': None,
            'nationality': None,
            'expiry_date': None
        }

        # Extract full name
        name_match = re.search(self.patterns['full_name'], normalized_text, re.IGNORECASE)
        if name_match:
            result['full_name'] = name_match.group(1).strip()

        # Extract CIN number
        cin_match = re.search(self.patterns['cin_number'], normalized_text)
        if cin_match:
            result['cin_number'] = cin_match.group()

        # Extract date of birth
        dob_match = re.search(self.patterns['date_of_birth'], normalized_text, re.IGNORECASE)
        if dob_match:
            result['date_of_birth'] = self.parse_date(dob_match.group(1))

        # Extract birth place
        birth_place_match = re.search(self.patterns['birth_place'], normalized_text, re.IGNORECASE)
        if birth_place_match:
            result['birth_place'] = birth_place_match.group(1).strip()

        # Extract gender
        gender_match = re.search(self.patterns['gender'], normalized_text, re.IGNORECASE)
        if gender_match:
            result['gender'] = gender_match.group(1).upper()

        # Extract nationality
        nationality_match = re.search(self.patterns['nationality'], normalized_text, re.IGNORECASE)
        if nationality_match:
            result['nationality'] = nationality_match.group(1).strip()

        # Extract expiry date
        expiry_match = re.search(self.patterns['expiry_date'], normalized_text, re.IGNORECASE)
        if expiry_match:
            result['expiry_date'] = self.parse_date(expiry_match.group(1))

        return result

    def validate_extracted_data(self, extracted_data: Dict[str, Any]) -> List[str]:
        """
        Validate extracted data for completeness
        """
        warnings = []

        mandatory_fields = ['full_name', 'cin_number', 'date_of_birth']
        for field in mandatory_fields:
            if not extracted_data[field]:
                warnings.append(f"{field.replace('_', ' ').title()} not detected")

        return warnings


def main():
    # Sample ID text (replace with actual OCR output)
    sample_text = """
    ROYAUME DU MAROC
    CARTE NATIONALE D'IDENTITE
    NOM ET PRENOM: JAMAL DIAE-EDDINE
    Né le 10.06.2002 à KHENIFRA
    CIN: Y510850
    Nationalité: Marocaine
    Sexe: HOMME
    Valable jusqu'au 17.10.2032
    """

    extractor = MoroccanIDExtractor()

    # Extract ID details
    extracted_details = extractor.extract_moroccan_id(sample_text)

    # Print extracted details
    print("🔍 Moroccan ID Details:")
    for key, value in extracted_details.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    # Validate extracted data
    warnings = extractor.validate_extracted_data(extracted_details)
    if warnings:
        print("\n⚠️ Warnings:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()