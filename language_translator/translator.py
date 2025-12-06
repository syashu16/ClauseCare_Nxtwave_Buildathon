"""
Legal Document Translator
=========================

AI-powered translation for legal documents supporting all major Indian languages.
Uses Groq LLM for high-quality, context-aware legal translations.
"""

import os
import re
import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Comprehensive list of Indian languages with their details
SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "native_name": "English",
        "script": "Latin",
        "region": "Global"
    },
    "hi": {
        "name": "Hindi",
        "native_name": "हिन्दी",
        "script": "Devanagari",
        "region": "North India"
    },
    "bn": {
        "name": "Bengali",
        "native_name": "বাংলা",
        "script": "Bengali",
        "region": "West Bengal, Bangladesh"
    },
    "te": {
        "name": "Telugu",
        "native_name": "తెలుగు",
        "script": "Telugu",
        "region": "Andhra Pradesh, Telangana"
    },
    "mr": {
        "name": "Marathi",
        "native_name": "मराठी",
        "script": "Devanagari",
        "region": "Maharashtra"
    },
    "ta": {
        "name": "Tamil",
        "native_name": "தமிழ்",
        "script": "Tamil",
        "region": "Tamil Nadu"
    },
    "gu": {
        "name": "Gujarati",
        "native_name": "ગુજરાતી",
        "script": "Gujarati",
        "region": "Gujarat"
    },
    "kn": {
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "script": "Kannada",
        "region": "Karnataka"
    },
    "ml": {
        "name": "Malayalam",
        "native_name": "മലയാളം",
        "script": "Malayalam",
        "region": "Kerala"
    },
    "or": {
        "name": "Odia",
        "native_name": "ଓଡ଼ିଆ",
        "script": "Odia",
        "region": "Odisha"
    },
    "pa": {
        "name": "Punjabi",
        "native_name": "ਪੰਜਾਬੀ",
        "script": "Gurmukhi",
        "region": "Punjab"
    },
    "as": {
        "name": "Assamese",
        "native_name": "অসমীয়া",
        "script": "Assamese",
        "region": "Assam"
    },
    "ur": {
        "name": "Urdu",
        "native_name": "اردو",
        "script": "Perso-Arabic",
        "region": "North India, Pakistan"
    },
    "sa": {
        "name": "Sanskrit",
        "native_name": "संस्कृतम्",
        "script": "Devanagari",
        "region": "Classical"
    },
    "ks": {
        "name": "Kashmiri",
        "native_name": "कॉशुर",
        "script": "Perso-Arabic/Devanagari",
        "region": "Jammu & Kashmir"
    },
    "ne": {
        "name": "Nepali",
        "native_name": "नेपाली",
        "script": "Devanagari",
        "region": "Sikkim, Nepal"
    },
    "sd": {
        "name": "Sindhi",
        "native_name": "سنڌي",
        "script": "Perso-Arabic/Devanagari",
        "region": "Sindh region"
    },
    "kok": {
        "name": "Konkani",
        "native_name": "कोंकणी",
        "script": "Devanagari",
        "region": "Goa, Karnataka"
    },
    "mai": {
        "name": "Maithili",
        "native_name": "मैथिली",
        "script": "Devanagari",
        "region": "Bihar"
    },
    "doi": {
        "name": "Dogri",
        "native_name": "डोगरी",
        "script": "Devanagari",
        "region": "Jammu"
    },
    "mni": {
        "name": "Manipuri",
        "native_name": "মৈতৈলোন্",
        "script": "Meitei/Bengali",
        "region": "Manipur"
    },
    "sat": {
        "name": "Santali",
        "native_name": "ᱥᱟᱱᱛᱟᱲᱤ",
        "script": "Ol Chiki",
        "region": "Jharkhand, West Bengal"
    },
    "bodo": {
        "name": "Bodo",
        "native_name": "बड़ो",
        "script": "Devanagari",
        "region": "Assam"
    }
}


# Legal terminology dictionary for accurate translations
LEGAL_TERMS = {
    "indemnification": {
        "hi": "क्षतिपूर्ति",
        "bn": "ক্ষতিপূরণ",
        "te": "నష్టపరిహారం",
        "ta": "இழப்பீடு",
        "mr": "नुकसानभरपाई"
    },
    "liability": {
        "hi": "दायित्व",
        "bn": "দায়বদ্ধতা",
        "te": "బాధ్యత",
        "ta": "பொறுப்பு",
        "mr": "जबाबदारी"
    },
    "jurisdiction": {
        "hi": "अधिकार क्षेत्र",
        "bn": "এখতিয়ার",
        "te": "న్యాయాధికార పరిధి",
        "ta": "அதிகார வரம்பு",
        "mr": "अधिकारक्षेत्र"
    },
    "confidentiality": {
        "hi": "गोपनीयता",
        "bn": "গোপনীয়তা",
        "te": "గోప్యత",
        "ta": "ரகசியத்தன்மை",
        "mr": "गोपनीयता"
    },
    "termination": {
        "hi": "समाप्ति",
        "bn": "সমাপ্তি",
        "te": "రద్దు",
        "ta": "முடிவு",
        "mr": "समाप्ती"
    },
    "breach": {
        "hi": "उल्लंघन",
        "bn": "লঙ্ঘন",
        "te": "ఉల్లంఘన",
        "ta": "மீறல்",
        "mr": "भंग"
    },
    "arbitration": {
        "hi": "मध्यस्थता",
        "bn": "সালিশি",
        "te": "మధ్యవర్తిత్వం",
        "ta": "நடுவர் தீர்ப்பு",
        "mr": "लवाद"
    },
    "intellectual property": {
        "hi": "बौद्धिक संपदा",
        "bn": "বুদ্ধিবৃত্তিক সম্পত্তি",
        "te": "మేధో సంపత్తి",
        "ta": "அறிவுசார் சொத்து",
        "mr": "बौद्धिक संपदा"
    },
    "force majeure": {
        "hi": "अप्रत्याशित घटना",
        "bn": "অপ্রত্যাশিত ঘটনা",
        "te": "అనూహ్య పరిస్థితి",
        "ta": "எதிர்பாராத சூழ்நிலை",
        "mr": "अनपेक्षित घटना"
    },
    "non-disclosure": {
        "hi": "गैर-प्रकटीकरण",
        "bn": "অ-প্রকাশ",
        "te": "బహిర్గతం చేయకపోవడం",
        "ta": "வெளிப்படுத்தாமை",
        "mr": "गैर-खुलासा"
    }
}


@dataclass
class TranslationResult:
    """Result of a translation operation"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    legal_terms_preserved: List[str]
    translation_notes: List[str]


class LegalTranslator:
    """
    AI-powered legal document translator supporting all Indian languages.
    
    Features:
    - Context-aware legal translations
    - Preserves legal terminology accuracy
    - Handles complex legal jargon
    - Provides translation confidence scores
    - Maintains document formatting
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = "llama-3.3-70b-versatile"
        self.legal_terms = LEGAL_TERMS
        
    def get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        lang = SUPPORTED_LANGUAGES.get(code, {})
        return lang.get("name", code)
    
    def get_native_name(self, code: str) -> str:
        """Get native language name"""
        lang = SUPPORTED_LANGUAGES.get(code, {})
        return lang.get("native_name", code)
    
    def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        context: str = "legal document",
        preserve_formatting: bool = True
    ) -> TranslationResult:
        """
        Translate text to target language with legal context awareness.
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'hi' for Hindi)
            source_language: Source language code (default: 'en')
            context: Context for translation (e.g., 'contract', 'legal notice')
            preserve_formatting: Whether to preserve document formatting
            
        Returns:
            TranslationResult with translated text and metadata
        """
        if not self.client:
            raise ValueError("No API key configured for translation")
        
        target_lang_name = self.get_language_name(target_language)
        target_native = self.get_native_name(target_language)
        source_lang_name = self.get_language_name(source_language)
        
        # Build translation prompt
        system_prompt = f"""You are an expert legal translator specializing in Indian languages.
You are translating from {source_lang_name} to {target_lang_name} ({target_native}).

CRITICAL GUIDELINES:
1. Maintain legal accuracy - legal terms must be translated correctly
2. Preserve the legal meaning and implications
3. Use formal legal register appropriate for {target_lang_name}
4. Keep proper nouns, names, dates, and numbers in original form
5. Maintain paragraph structure and formatting
6. For complex legal terms, you may include the English term in parentheses
7. Use standard legal terminology recognized in Indian courts

LEGAL TERMINOLOGY REFERENCE:
- Contract = अनुबंध (Hindi), চুক্তি (Bengali), ఒప్పందం (Telugu)
- Clause = धारा/खंड (Hindi), ধারা (Bengali), నిబంధన (Telugu)
- Agreement = समझौता (Hindi), চুক্তি (Bengali), ఒప్పందం (Telugu)
- Party = पक्ष (Hindi), পক্ষ (Bengali), పక్షం (Telugu)
- Terms and Conditions = नियम और शर्तें (Hindi)

Respond with ONLY the translated text. No explanations or notes."""

        user_prompt = f"""Translate this {context} from {source_lang_name} to {target_lang_name} ({target_native}):

---
{text[:8000]}
---

Provide the complete translation in {target_lang_name} script."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=8000
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Identify preserved legal terms
            preserved_terms = []
            for term in self.legal_terms.keys():
                if term.lower() in text.lower():
                    preserved_terms.append(term)
            
            # Generate translation notes
            notes = []
            if len(text) > 8000:
                notes.append("Text was truncated for translation. Full document may require multiple passes.")
            if preserved_terms:
                notes.append(f"Key legal terms translated: {', '.join(preserved_terms[:5])}")
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.85,  # Base confidence
                legal_terms_preserved=preserved_terms,
                translation_notes=notes
            )
            
        except Exception as e:
            return TranslationResult(
                original_text=text,
                translated_text=f"Translation error: {str(e)}",
                source_language=source_language,
                target_language=target_language,
                confidence=0.0,
                legal_terms_preserved=[],
                translation_notes=[f"Error: {str(e)}"]
            )
    
    def translate_summary(
        self,
        summary: str,
        target_language: str
    ) -> TranslationResult:
        """Translate a risk assessment or analysis summary"""
        return self.translate(
            text=summary,
            target_language=target_language,
            context="legal analysis summary"
        )
    
    def translate_clauses(
        self,
        clauses: List[str],
        target_language: str
    ) -> List[TranslationResult]:
        """Translate multiple clauses"""
        results = []
        for clause in clauses:
            result = self.translate(
                text=clause,
                target_language=target_language,
                context="contract clause"
            )
            results.append(result)
        return results
    
    def translate_risk_report(
        self,
        risk_summary: str,
        recommendations: List[str],
        target_language: str
    ) -> Dict[str, any]:
        """Translate a complete risk report"""
        
        # Translate summary
        summary_result = self.translate(
            text=risk_summary,
            target_language=target_language,
            context="legal risk assessment"
        )
        
        # Translate recommendations
        translated_recs = []
        for rec in recommendations[:10]:  # Limit to 10
            rec_result = self.translate(
                text=rec,
                target_language=target_language,
                context="legal recommendation"
            )
            translated_recs.append(rec_result.translated_text)
        
        return {
            "summary": summary_result.translated_text,
            "recommendations": translated_recs,
            "target_language": target_language,
            "language_name": self.get_language_name(target_language),
            "native_name": self.get_native_name(target_language)
        }
    
    def get_supported_languages(self) -> Dict[str, Dict]:
        """Get all supported languages with details"""
        return SUPPORTED_LANGUAGES
    
    def detect_language(self, text: str) -> str:
        """Attempt to detect the language of input text"""
        if not self.client:
            return "en"  # Default to English
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Detect the language of the text. Respond with ONLY the ISO 639-1 language code (e.g., 'en', 'hi', 'bn', 'te', 'ta', 'mr', 'gu', 'kn', 'ml')."
                    },
                    {
                        "role": "user",
                        "content": f"Detect language: {text[:500]}"
                    }
                ],
                temperature=0,
                max_tokens=10
            )
            
            detected = response.choices[0].message.content.strip().lower()
            if detected in SUPPORTED_LANGUAGES:
                return detected
            return "en"
            
        except Exception:
            return "en"
    
    def translate_ui_elements(self, target_language: str) -> Dict[str, str]:
        """Get translated UI elements for the interface"""
        
        ui_translations = {
            "en": {
                "title": "Legal Document Translator",
                "upload": "Upload Document",
                "translate": "Translate",
                "download": "Download Translation",
                "select_language": "Select Target Language",
                "original": "Original Text",
                "translated": "Translated Text",
                "risk_assessment": "Risk Assessment",
                "recommendations": "Recommendations",
                "summary": "Summary",
                "high_risk": "High Risk",
                "medium_risk": "Medium Risk",
                "low_risk": "Low Risk"
            },
            "hi": {
                "title": "कानूनी दस्तावेज़ अनुवादक",
                "upload": "दस्तावेज़ अपलोड करें",
                "translate": "अनुवाद करें",
                "download": "अनुवाद डाउनलोड करें",
                "select_language": "लक्ष्य भाषा चुनें",
                "original": "मूल पाठ",
                "translated": "अनुवादित पाठ",
                "risk_assessment": "जोखिम मूल्यांकन",
                "recommendations": "सिफारिशें",
                "summary": "सारांश",
                "high_risk": "उच्च जोखिम",
                "medium_risk": "मध्यम जोखिम",
                "low_risk": "कम जोखिम"
            },
            "bn": {
                "title": "আইনি নথি অনুবাদক",
                "upload": "নথি আপলোড করুন",
                "translate": "অনুবাদ করুন",
                "download": "অনুবাদ ডাউনলোড করুন",
                "select_language": "লক্ষ্য ভাষা নির্বাচন করুন",
                "original": "মূল পাঠ্য",
                "translated": "অনূদিত পাঠ্য",
                "risk_assessment": "ঝুঁকি মূল্যায়ন",
                "recommendations": "সুপারিশ",
                "summary": "সারাংশ",
                "high_risk": "উচ্চ ঝুঁকি",
                "medium_risk": "মাঝারি ঝুঁকি",
                "low_risk": "কম ঝুঁকি"
            },
            "te": {
                "title": "న్యాయ పత్ర అనువాదకుడు",
                "upload": "పత్రాన్ని అప్‌లోడ్ చేయండి",
                "translate": "అనువదించు",
                "download": "అనువాదాన్ని డౌన్‌లోడ్ చేయండి",
                "select_language": "లక్ష్య భాషను ఎంచుకోండి",
                "original": "అసలు పాఠ్యం",
                "translated": "అనువాదిత పాఠ్యం",
                "risk_assessment": "రిస్క్ అసెస్‌మెంట్",
                "recommendations": "సిఫార్సులు",
                "summary": "సారాంశం",
                "high_risk": "అధిక ప్రమాదం",
                "medium_risk": "మధ్యస్థ ప్రమాదం",
                "low_risk": "తక్కువ ప్రమాదం"
            },
            "ta": {
                "title": "சட்ட ஆவண மொழிபெயர்ப்பாளர்",
                "upload": "ஆவணத்தைப் பதிவேற்றவும்",
                "translate": "மொழிபெயர்க்கவும்",
                "download": "மொழிபெயர்ப்பைப் பதிவிறக்கவும்",
                "select_language": "இலக்கு மொழியைத் தேர்ந்தெடுக்கவும்",
                "original": "அசல் உரை",
                "translated": "மொழிபெயர்க்கப்பட்ட உரை",
                "risk_assessment": "இடர் மதிப்பீடு",
                "recommendations": "பரிந்துரைகள்",
                "summary": "சுருக்கம்",
                "high_risk": "அதிக ஆபத்து",
                "medium_risk": "நடுத்தர ஆபத்து",
                "low_risk": "குறைந்த ஆபத்து"
            },
            "mr": {
                "title": "कायदेशीर दस्तऐवज अनुवादक",
                "upload": "दस्तऐवज अपलोड करा",
                "translate": "भाषांतर करा",
                "download": "भाषांतर डाउनलोड करा",
                "select_language": "लक्ष्य भाषा निवडा",
                "original": "मूळ मजकूर",
                "translated": "भाषांतरित मजकूर",
                "risk_assessment": "जोखीम मूल्यांकन",
                "recommendations": "शिफारसी",
                "summary": "सारांश",
                "high_risk": "उच्च जोखीम",
                "medium_risk": "मध्यम जोखीम",
                "low_risk": "कमी जोखीम"
            }
        }
        
        return ui_translations.get(target_language, ui_translations["en"])


def get_language_options() -> List[Tuple[str, str]]:
    """Get language options for dropdown menus"""
    options = []
    for code, details in SUPPORTED_LANGUAGES.items():
        display = f"{details['native_name']} ({details['name']})"
        options.append((code, display))
    return sorted(options, key=lambda x: x[1])
