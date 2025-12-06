"""
GenLegalAI Language Translation Module
======================================

Supports translation of legal documents and analysis into all major Indian languages.

Supported Languages:
- Hindi (हिन्दी)
- Bengali (বাংলা)
- Telugu (తెలుగు)
- Marathi (मराठी)
- Tamil (தமிழ்)
- Gujarati (ગુજરાતી)
- Kannada (ಕನ್ನಡ)
- Malayalam (മലയാളം)
- Odia (ଓଡ଼ିଆ)
- Punjabi (ਪੰਜਾਬੀ)
- Assamese (অসমীয়া)
- Urdu (اردو)
- Sanskrit (संस्कृतम्)
- English
"""

from .translator import LegalTranslator, SUPPORTED_LANGUAGES

__all__ = ['LegalTranslator', 'SUPPORTED_LANGUAGES']
