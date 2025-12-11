# chatbot/views.py

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse

from .ai import generate_ai_reply
from .intents import detect_intent
from .models import Conversation, Prospect

PRODUCT_URL = "https://deksdigital.online/learn-chatbot"


def build_welcome_message() -> str:
    return (
        "Bienvenue dans Learn-Chatbot.\n\n"
        "Je suis ton assistant pour tout ce qui concerne la création et la vente de chatbots WhatsApp.\n\n"
        "Tu peux par exemple me demander :\n"
        "- comment créer un chatbot,\n"
        "- comment vendre des chatbots aux e-commerçants,\n"
        "- ou des informations sur l'ebook Learn-Chatbot.\n\n"
        "Dis-moi simplement ce que tu veux savoir."
    )


def build_product_message() -> str:
    return (
        "Ebook Learn-Chatbot – Guide complet pour créer et vendre des chatbots.\n\n"
        "À l'intérieur, tu vas apprendre :\n"
        "- comment créer un chatbot WhatsApp professionnel,\n"
        "- comment automatiser les réponses et qualifier les prospects,\n"
        "- comment adapter des bots pour restaurants, e-commerce, produits digitaux,\n"
        "- comment vendre des chatbots entre 30 000 et 150 000 FCFA.\n\n"
        "Prix : 1 850 FCFA.\n\n"
        "Si tu veux le lien sécurisé d'achat, dis simplement : je veux acheter."
    )


def build_buy_message() -> str:
    return (
        "Tu as fait un excellent choix.\n\n"
        "L'ebook Learn-Chatbot te montre étape par étape comment créer des chatbots que tu peux vendre aux entreprises.\n\n"
        "Lien sécurisé d'achat :\n"
        f"{PRODUCT_URL}\n\n"
        "Après le paiement, l'accès est automatique par email."
    )


def handle_qualification_step(conv: Conversation, user_message: str) -> str:
    """
    Gère les étapes de qualification :
    - type de client
    - besoin
    - budget
    - délai
    - puis enregistrement du prospect
    """
    data = conv.data or {}

    if conv.current_step == "ASK_CLIENT_TYPE":
        data["client_type"] = user_message.strip()
        conv.current_step = "ASK_NEED"
        conv.data = data
        conv.save()
        return "Très bien. Explique-moi en quelques mots ton besoin principal (pour quel type de projet ou activité tu veux utiliser les chatbots) ?"

    if conv.current_step == "ASK_NEED":
        data["need"] = user_message.strip()
        conv.current_step = "ASK_BUDGET"
        conv.data = data
        conv.save()
        return "Merci, c'est clair. Quel budget tu envisages pour mettre en place tes chatbots (même une fourchette approximative) ?"

    if conv.current_step == "ASK_BUDGET":
        data["budget"] = user_message.strip()
        conv.current_step = "ASK_DEADLINE"
        conv.data = data
        conv.save()
        return "Noté. Tu veux commencer quand idéalement (cette semaine, ce mois-ci, plus tard) ?"

    if conv.current_step == "ASK_DEADLINE":
        data["deadline"] = user_message.strip()
        conv.current_step = "ASK_NAME"
        conv.data = data
        conv.save()
        return "Dernière question : comment t'appelles-tu ?"

    if conv.current_step == "ASK_NAME":
        data["name"] = user_message.strip()
        conv.current_step = "ASK_PHONE_CONFIRM"
        conv.data = data
        conv.save()
        return (
            "Merci.\n\n"
            "Je vais aussi noter ton numéro WhatsApp comme contact principal. "
            "Si tu souhaites un autre numéro, envoie-le maintenant, sinon réponds : ok."
        )

    if conv.current_step == "ASK_PHONE_CONFIRM":
        phone = data.get("phone")  # on le remplira plus bas au besoin
        # Si l'utilisateur envoie "ok", on garde le numéro Whatsapp
        if user_message.strip().lower() in ["ok", "c'est bon", "non"]:
            # on ne change rien
            pass
        else:
            # L'utilisateur a donné un autre numéro
            phone = user_message.strip()

        # On récupère le numéro Whatsapp si pas défini
        if not phone:
            phone = data.get("whatsapp_phone", "")

        # Création du prospect
        Prospect.objects.create(
            name=data.get("name", "Inconnu"),
            phone=phone or "",
            client_type=data.get("client_type", ""),
            need=data.get("need", ""),
            budget=data.get("budget", ""),
            deadline=data.get("deadline", ""),
        )

        # Reset de la conversation
        conv.current_step = ""
        conv.data = {}
        conv.save()

        return (
            "Parfait, tes informations sont enregistrées.\n\n"
            "Tu peux déjà commencer avec l'ebook Learn-Chatbot qui te donne la méthode complète.\n\n"
            "Lien d'achat :\n"
            f"{PRODUCT_URL}\n\n"
            "Souhaites-tu que je te résume ce que tu vas apprendre dedans ?"
        )

    # Si pour une raison quelconque on arrive ici, on repart sur le flux normal
    conv.current_step = ""
    conv.data = {}
    conv.save()
    return "Je n'ai pas bien suivi l'étape précédente. Reformule ton besoin ou écris : menu pour recommencer."


def handle_faq(message: str) -> str:
    msg = message.lower()
    if "horaire" in msg or "horaire" in msg:
        return "Les ressources Learn-Chatbot sont disponibles 24h/24, tu peux acheter et commencer quand tu veux."
    if "adresse" in msg or "localisation" in msg:
        return "Learn-Chatbot est un produit 100 % digital. Tu reçois l'accès directement après paiement par email."
    if "livraison" in msg:
        return "Pas de livraison physique. Tu reçois tout par email et tu peux télécharger le contenu."
    if "paiement" in msg:
        return "Le paiement se fait en ligne via la page sécurisée indiquée dans le lien d'achat."
    if "delai" in msg or "combien de temps" in msg:
        return "L'accès à l'ebook et aux ressources est immédiat après paiement."
    return "Pour ta question, tout est géré en ligne de manière simple. Si tu veux plus de détails, précise ta question."


@csrf_exempt
def whatsapp_bot(request):
    """
    Webhook principal appelé par Twilio à chaque message WhatsApp.
    """
    if request.method != "POST":
        return HttpResponse("Only POST allowed")

    # Récupération du message et du numéro
    msg_raw = (request.POST.get("Body") or "").strip()
    msg = msg_raw.lower()
    from_phone = (request.POST.get("From") or "").replace("whatsapp:", "").strip()

    # Récupération / création de l'état de conversation
    conv, _ = Conversation.objects.get_or_create(phone=from_phone)

    twilio_response = MessagingResponse()
    reply = twilio_response.message()

    # 1) Reset / menu
    if msg in ["menu", "start", "restart"]:
        conv.current_step = ""
        conv.data = {}
        conv.save()
        reply.body(build_welcome_message())
        return HttpResponse(str(twilio_response))

    # 2) Si on est dans une étape de qualification, on continue ce flux
    if conv.current_step and conv.current_step.startswith("ASK_"):
        # On stocke le numéro whatsapp dans les données si pas déjà fait
        data = conv.data or {}
        if "whatsapp_phone" not in data:
            data["whatsapp_phone"] = from_phone
            conv.data = data
            conv.save()

        text = handle_qualification_step(conv, msg_raw)
        reply.body(text)
        return HttpResponse(str(twilio_response))

    # 3) Détection d'intention globale
    intent = detect_intent(msg)

    # 3.a) Salutations
    if intent == "GREET":
        reply.body(build_welcome_message())
        return HttpResponse(str(twilio_response))

    # 3.b) Demande d'infos sur le produit
    if intent == "ASK_PRODUCT":
        reply.body(build_product_message())
        return HttpResponse(str(twilio_response))

    # 3.c) Intention d'achat -> on envoie le message de vente + on lance qualification
    if intent == "WANT_BUY":
        # Première partie : message de vente
        text = build_buy_message()
        reply.body(text)

        # Deuxième partie : lancement qualification
        conv.current_step = "ASK_CLIENT_TYPE"
        conv.data = {}
        conv.save()

        # On enchaîne avec une deuxième réponse Twilio (nouveau message)
        reply2 = twilio_response.message()
        reply2.body(
            "Avant de continuer, j'aimerais mieux te connaître pour t'aider efficacement.\n\n"
            "Tu es plutôt :\n"
            "- entrepreneur / e-commerçant,\n"
            "- salarié,\n"
            "- étudiant,\n"
            "- ou autre profil ?"
        )

        return HttpResponse(str(twilio_response))

    # 3.d) FAQ
    if intent == "FAQ":
        reply.body(handle_faq(msg_raw))
        return HttpResponse(str(twilio_response))

    # 3.e) Sinon -> discussion IA contrôlée
    context = "Discussion générale autour des chatbots et de l'ebook Learn-Chatbot."
    ai_text = generate_ai_reply(msg_raw, context=context)
    reply.body(ai_text)
    return HttpResponse(str(twilio_response))
