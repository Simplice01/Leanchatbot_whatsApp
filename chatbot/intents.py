# chatbot/intents.py

from typing import Literal


IntentType = Literal[
    "GREET",
    "ASK_PRODUCT",
    "WANT_BUY",
    "FAQ",
    "UNKNOWN",
]


GREET_KEYWORDS = [
    "salut", "bonjour", "bonsoir", "hello", "cc", "coucou",
]

BUY_KEYWORDS = [
    "acheter", "je veux acheter", "je veux payer", "je veux l'ebook",
    "je veux le livre", "je veux commander", "payer", "paiement",
    "prix", "c'est combien", "combien ça coûte", "combien coute",
    "lien d'achat", "lien achat", "je suis intéressé", "interesse",
]

PRODUCT_KEYWORDS = [
    "parle moi de l'ebook",
    "parle moi de learn chatbot",
    "learn chatbot",
    "learn-chatbot",
    "ebook chatbot",
    "formation chatbot",
    "c'est quoi l'ebook",
    "en quoi ce ebook est meilleur",
]

FAQ_KEYWORDS = [
    "horaire", "ou êtes-vous", "adresse", "localisation",
    "livraison", "frais de livraison", "mode de paiement",
    "paiement mobile", "paypal", "carte bancaire", "delai",
    "combien de temps", "support", "assistance",
]


def detect_intent(message: str) -> IntentType:
    """
    Détecte une intention simple à partir du message.
    Le message doit être déjà en minuscules.
    """
    msg = message.lower()

    if any(word in msg for word in GREET_KEYWORDS):
        return "GREET"

    if any(word in msg for word in BUY_KEYWORDS):
        return "WANT_BUY"

    if any(word in msg for word in PRODUCT_KEYWORDS):
        return "ASK_PRODUCT"

    if any(word in msg for word in FAQ_KEYWORDS):
        return "FAQ"

    return "UNKNOWN"
