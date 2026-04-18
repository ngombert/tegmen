import pytest
from common.privacy import sanitize_message

def test_sanitize_no_pii():
    text = "Bonjour, j'ai besoin d'une recette de pâtes."
    assert sanitize_message(text) == text

def test_sanitize_email():
    text = "Mon email est contact@exemple.com pour plus d'infos."
    expected = "Mon email est [EMAIL] pour plus d'infos."
    assert sanitize_message(text) == expected

def test_sanitize_phone():
    texts = [
        "Appelez-moi au 0612345678",
        "Appelez-moi au 06 12 34 56 78",
        "Appelez-moi au +33612345678",
        "Appelez-moi au 01.23.45.67.89",
    ]
    for text in texts:
        assert "[PHONE]" in sanitize_message(text)

def test_sanitize_mixed_pii():
    text = "Email: jean.philippe@work.fr, Tel: 01 22 33 44 55"
    expected = "Email: [EMAIL], Tel: [PHONE]"
    assert sanitize_message(text) == expected

def test_sanitize_empty():
    assert sanitize_message("") == ""
    assert sanitize_message(None) is None
