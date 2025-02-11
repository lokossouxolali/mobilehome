from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.html import format_html
from django.conf import settings
from .models import *

@receiver(post_save, sender=Invoice)
def invoice_saved_handler(sender, instance, created, **kwargs):
    """
    Envoie un e-mail bien structuré et attrayant à l'administrateur lorsqu'une facture est enregistrée.
    """
    if created:  # Vérifie si une nouvelle facture est créée
        subject = f"📄 Nouvelle Facture : {instance.customer.name}"
        # Message principal avec un design moderne
        html_message = format_html(f"""
            <div style="max-width: 600px; margin: auto; font-family: Arial, sans-serif; background: #fff; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                <!-- En-tête -->
                <div style="background-color: #6A0DAD; padding: 20px; text-align: center; font-size: 18px; font-weight: bold; color: #fff;">
                    📢 NOUVELLE FACTURE ENREGISTRÉE !
                </div>

                <div style="padding: 20px; color: #333; text-align: center;">
                    <p>Une nouvelle facture a été enregistrée pour le client <strong>{instance.customer.name}</strong>.</p>
                </div>
                <!-- Bouton d'action -->
                <div style="text-align: center; padding: 20px;  height: 100px;">
                    <a href="http://127.0.0.1:8000/view_invoice/{instance.id}" 
                    style="background-color: #27ae60; color: #fff; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px; display: inline-block; margin: 5px;">
                        📝 Voir la Facture
                    </a>
                    <a href="http://127.0.0.1:8000/sales_summary_list" 
                    style="background-color: #27ae60; color: #fff; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px; display: inline-block; margin: 5px;">
                        📝 Voir les ventes
                    </a>
                    <a href="http://127.0.0.1:8000/article_list" 
                    style="background-color: #27ae60; color: #fff; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px; display: inline-block; margin: 5px;">
                        📝 Voir les articles
                    </a>
                </div>
                            <!-- Pied de page -->
                <div style="background-color: #6A0DAD; padding: 10px; text-align: center; font-size: 12px; color: #fff;">
            </div>
            </div>
        """)

        # Envoi du mail en format HTML
        admin_email = [settings.DEFAULT_FROM_EMAIL]
        email = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, admin_email)
        email.attach_alternative(html_message, "text/html")
        email.send()
