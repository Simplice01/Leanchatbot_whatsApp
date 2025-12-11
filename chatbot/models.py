
# Create your models here.
# chatbot/models.py

from django.db import models


class Conversation(models.Model):
    """
    Stocke l'état de la conversation par numéro WhatsApp.
    Permet de savoir à quelle étape on en est (qualification, prise de commande, etc.).
    """
    phone = models.CharField(max_length=50, unique=True)
    current_step = models.CharField(max_length=50, blank=True, null=True)
    data = models.JSONField(default=dict, blank=True)  # infos temporaires
    last_interaction = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation({self.phone}) - step={self.current_step}"


class Prospect(models.Model):
    """
    Prospect qualifié, prêt à être recontacté.
    Tu peux utiliser ce modèle plus tard pour faire des relances, export Sheets, etc.
    """
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=50)
    client_type = models.CharField(max_length=100, blank=True, null=True)
    need = models.TextField(blank=True, null=True)
    budget = models.CharField(max_length=100, blank=True, null=True)
    deadline = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=50, default="whatsapp")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"
