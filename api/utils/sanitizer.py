"""Utilitaires de nettoyage et sécurité"""

import re
from html import unescape


def strip_html(text: str) -> str:
    """
    Supprime les balises HTML et décode les entités HTML.
    
    Exemples:
    - "<p>Hello</p>" → "Hello"
    - "<strong>Bold</strong> text" → "Bold text"
    - "Test &amp; Demo" → "Test & Demo"
    
    Args:
        text: Texte contenant du HTML
        
    Returns:
        Texte nettoyé sans balises HTML
    """
    if not text or not isinstance(text, str):
        return text
    
    # Supprime les balises HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Décode les entités HTML (&amp; → &, &lt; → <, etc)
    text = unescape(text)
    
    # Supprime les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
