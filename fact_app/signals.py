from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Invoice, InvoiceItem

@receiver(post_save, sender=Invoice)
def invoice_saved_handler(sender, instance, created, **kwargs):
    """
    Envoie un e-mail à l'administrateur lorsqu'une facture est enregistrée.
    """
    if created:  # Vérifie si une nouvelle facture est créée
        subject = f"Nouvelle facture enregistrée : {instance.customer.name}"
        message = f"Une nouvelle facture a été enregistrée pour le client {instance.customer.name}.\n\n"
        message += "Détails des articles vendus :\n"

        for item in instance.invoice_items.all():
            message += f"- {item.article.name}: Quantité = {item.quantity}, Prix unitaire = {item.unit_price}, Total = {item.total_price}\n"

        message += f"\nTotal de la facture : {instance.total}\n"
        message += f"Voir la facture : http://127.0.0.1:8000/view_invoice/{instance.id}\n" # Adjust the link

        admin_email = [settings.DEFAULT_FROM_EMAIL]  # Récupère l'adresse e-mail de l'administrateur depuis les paramètres
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, admin_email)

        # print('E-mail envoyé à l\'administrateur')
