from django.contrib import admin
from django.urls import path
from chatbot.views import whatsapp_bot
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('whatsapp/', whatsapp_bot),
]

urlpatterns += static('/', document_root='.')
