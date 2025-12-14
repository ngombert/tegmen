"""Verification script for Semantic Router."""

import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("verification")

try:
    from src.agent_maestro.router import classify_intent, warmup
except ImportError:
    print("❌ Error: Could not import router. Make sure you are running from project root.")
    exit(1)


TEST_CASES: List[Tuple[str, str]] = [
    # Gourmet
    ("Qu'est-ce qu'on mange ce soir ?", "gourmet"),
    ("Je veux une recette de pâtes carbonara", "gourmet"),
    ("Liste de courses pour la semaine", "gourmet"),
    ("Idée de repas végétarien", "gourmet"),
    
    # Acadomie
    ("J'ai besoin d'aide pour mon devoir de maths", "acadomie"),
    ("Quand sont les prochaines vacances ?", "acadomie"),
    ("Révision pour le contrôle d'histoire", "acadomie"),
    ("Exercice de grammaire difficile", "acadomie"),
    
    # Explorer
    ("On part où ce week-end ?", "explorer"),
    ("Prix des billets pour le Japon", "explorer"),
    ("Activité à faire avec les enfants dimanche", "explorer"),
    ("Meilleur hôtel à Nice", "explorer"),
    
    # Chitchat
    ("Quelle est la capitale de la France ?", "chitchat"),
    ("Raconte-moi une blague", "chitchat"),
    ("Bonjour comment ça va ?", "chitchat"),
    
    # Unknown (Truly random stuff)
    ("aksjdhkajshd", "unknown"),
    ("1283719283", "unknown"),
]


def verify():
    """Run verification tests."""
    print("🚀 Initializing Semantic Router (loading model)...")
    warmup()
    print("✅ Model loaded!\n")
    
    print("🧪 Running constraints verification...")
    passed = 0
    total = len(TEST_CASES)
    
    for query, expected in TEST_CASES:
        predicted = classify_intent(query)
        result = "✅" if predicted == expected else f"❌ (got {predicted})"
        print(f"{result} Query: '{query}' -> Expected: {expected}")
        
        if predicted == expected:
            passed += 1
            
    print(f"\n📊 Result: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n✨ ALL TESTS PASSED! The router is ready.")
    else:
        print("\n⚠️ SOME TESTS FAILED. You may need to add more training utterances.")


if __name__ == "__main__":
    verify()
