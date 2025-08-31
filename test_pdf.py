#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobile_house.settings')
django.setup()

from fact_app.models import Invoice
from django.template.loader import get_template
from django.template import Context
import pdfkit

def test_pdf_generation():
    try:
        # Récupérer la première facture
        invoice = Invoice.objects.first()
        if not invoice:
            print("Aucune facture trouvée dans la base de données")
            return
        
        print(f"Test de génération PDF pour la facture #{invoice.id}")
        print(f"Client: {invoice.customer.name}")
        print(f"Type: {invoice.get_invoice_type_display()}")
        print(f"Total: {invoice.total} FCFA")
        print(f"Payé: {invoice.paid}")
        
        # Préparer le contexte
        context = {
            'obj': invoice,
        }
        
        # Récupérer le template
        template = get_template('invoice_pdf.html')
        
        # Rendre le HTML
        html = template.render(context)
        
        # Options PDF
        options = {
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'enable-local-file-access': '',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'no-outline': None,
            'quiet': ''
        }
        
        # Configuration wkhtmltopdf
        config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
        
        # Générer le PDF
        pdf = pdfkit.from_string(html, False, options, configuration=config)
        
        # Sauvegarder le PDF de test
        with open('test_invoice.pdf', 'wb') as f:
            f.write(pdf)
        
        print("✅ PDF généré avec succès: test_invoice.pdf")
        print("📄 Vérifiez le fichier test_invoice.pdf pour voir le design")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()

