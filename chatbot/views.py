from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq
import os
from dotenv import load_dotenv
import httpx

# ======== Chargement du .env ========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# ======== Lien produit ========
PRODUCT_URL = "https://deksdigital.online/learn-chatbot"

# ======== Client GROQ avec SSL désactivé pour Windows ========
http_client = httpx.Client(verify=False)

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    http_client=http_client
)

# ======== Intentions d’achat ========
BUY_STRICT = [
    "je veux acheter",
    "je veux payer",
    "je veux le lien",
    "payer maintenant",
    "envoye le lien",
    "envoie le lien",
    "donne le lien",
    "payement",
    "paiement",
    "où payer",
    "ou payer",
    "comment payer",
    "acheter maintenant",
    "je veux commander",
]

BUY_SOFT = [
    "acheter",
    "prix",
    "payer",
    "combien",
    "ebook",
    "learn chatbot",
    "learn-chatbot",
    "acheter le produit",
    "acheter l'ebook",
]


def detect_buy_intent(msg: str) -> bool:
    msg = msg.lower().strip()

    # 1) phrases très explicites
    for w in BUY_STRICT:
        if w in msg:
            return True

    # 2) "je veux" + mot lié à l'achat
    if "je veux" in msg:
        for w in BUY_SOFT:
            if w in msg:
                return True

    # 3) question = on laisse l'IA répondre, pas d'achat direct
    if "?" in msg:
        return False

    return False


# ======== IA conversationnelle ========
def ia_response(user_message: str) -> str:

    SYSTEM_PROMPT = """
Tu es LearnBot, un assistant ultra naturel, expert en chatbots et excellent vendeur.

Ton rôle :
- Répondre de façon claire, simple, humaine, pas de langage robotique.
- Toujours donner une valeur réelle au client.
- Rattacher les réponses à la création de chatbot et au ebook Learn-Chatbot.
- Jamais envoyer le lien d’achat (c’est géré ailleurs).
- Terminer CHAQUE réponse par une question ouverte pour relancer.
- Ton style doit être fluide, moderne, motivant, jamais scolaire.
- Ne jamais dire que tu es un robot ou une IA.

Règles spéciales :
- Si le message est très court (“cc”, “ok”, “oui”, “non”), répondre avec un message court et chaleureux.
- Donner des explications simples, imagées, orientées vers l’action.
- Positionner l’ebook Learn-Chatbot comme la solution la plus simple pour apprendre et réussir.
"""

    # Cas ultra courts : répondre immédiatement
    short_msgs = ["cc", "ok", "oui", "non", "bjr", "slt", "yo", "hey", "hi"]
    if user_message.lower().strip() in short_msgs:
        return "Yes 😊 Je suis là ! Tu veux qu’on parle des chatbots ou de l’ebook Learn-Chatbot ?"

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",  # modèle supporté en production
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.75,
        max_tokens=350,
    )

    return response.choices[0].message.content


# ======== Message d’achat ========
def buy_message():
    return (
        "📘 *Learn-Chatbot – Ebook complet pour créer et vendre des chatbots*\n\n"
        "Tu vas apprendre :\n"
        "✓ Créer un chatbot WhatsApp professionnel\n"
        "✓ Automatiser les réponses\n"
        "✓ Adapter des bots pour restaurants, ecommerce, infoproduits\n"
        "✓ Vendre des chatbots entre 30 000 et 150 000 FCFA\n\n"
        "💰 *Prix : 1 850 FCFA*\n\n"
        f"👉 Lien sécurisé d'achat : {PRODUCT_URL}\n\n"
        "L’accès est automatique après paiement 🔓"
    )


# ======== Webhook Twilio ========
@csrf_exempt
def whatsapp_bot(request):
    msg_raw = (request.POST.get("Body") or "").strip()
    msg = msg_raw.lower()

    r = MessagingResponse()
    reply = r.message()

    # 1) Accueil
    if msg in ["menu", "start", "salut", "bonjour", "hello"]:
        reply.body(
            "👋 Bienvenue dans *Learn-Chatbot* !\n"
            "Tu peux me poser toutes tes questions sur les chatbots, la vente, ou l’ebook Learn-Chatbot. 😊"
        )
        return HttpResponse(str(r))

    # 2) Achat strict
    if detect_buy_intent(msg):
        reply.body(buy_message())
        return HttpResponse(str(r))

    # 3) Sinon -> IA
    ai_text = ia_response(msg_raw)
    reply.body(ai_text)
    return HttpResponse(str(r))
