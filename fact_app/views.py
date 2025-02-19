from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.utils.html import strip_tags
from django.shortcuts import redirect, render
from django.views import View
from .models import *
from django.contrib import messages
from django.db import transaction
import pdfkit
from django.template.loader import get_template
from .utils import pagination, get_invoice
import datetime
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .decorators import *
from django.shortcuts import render, get_object_or_404, redirect
from decimal import Decimal
from django.contrib.auth.models import User
from django import forms


# Create your views here.
class HomeView(LoginRequiredSuperuserMixin, View):
    templates_name = 'index.html'
    invoices = Invoice.objects.select_related('customer', 'save_by').all().order_by('-invoice_date_time')
    context = {
        'invoices': invoices
    }
    
    def get(self, request, *args, **kwargs):
        items = pagination(request, self.invoices)
        self.context['invoices'] = items
        return render(request, self.templates_name, self.context)
    
    def post(self, request, *args, **kwargs):

        #Modify
        if request.POST.get('id_modified'):
            paid = request.POST.get('modified')

            try:
                obj = Invoice.objects.get(id=request.POST.get('id_modified'))
                if paid == 'True':
                    obj.paid = True
                else:
                    obj.paid = False
                obj.save()
                messages.success(request, "Modification effectuée avec succès.")

            except Exception as e:
                messages.error(request, f"Désolé, l'erreur suivante s'est produite : {e}.")


        # Suppression
        if request.POST.get('id_supprimer'):
            try:
                invoice_id = request.POST.get('id_supprimer')
                print(f"ID reçu pour suppression : {invoice_id}")  # Debugging
                obj = Invoice.objects.get(pk=invoice_id)
                obj.delete()
                messages.success(request, "La suppression a réussi.")
            except Invoice.DoesNotExist:
                messages.error(request, "La facture n'existe pas.")
            except Exception as e:
                messages.error(request, f"Désolé, l'erreur suivante s'est produite : {e}.")

        items = pagination(request, self.invoices)
        self.context['invoices'] = items
        return render(request, self.templates_name, self.context)
    

class AddCustomerView(LoginRequiredSuperuserMixin, View):
    template_name = 'add_customer.html'
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    def post(self, request, *args, **kwargs):
        data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST .get('phone'),
            'address': request.POST.get('address'),
            'sex': request.POST.get('sex'),
            'age': request.POST.get('age'),
            'zip_code': request.POST.get('zip'),
            'save_by': request.user
        }
        try:
            created = Customer.objects.create(**data)
            if created:
                messages.success(request, "Le client s'est enregistré avec succès.")
                return redirect('add-invoice')
            else:
                messages.error(request, "Désolé, veuillez réessayer, les données envoyées sont corrompues.")
                return render(request, self.template_name)
        except Exception as e:
            messages.error(request, f"Désolé, le système détecte les problèmes suivants {e}.")
            return render(request, self.template_name)


from django.core.mail import EmailMessage
from django.utils.html import strip_tags
from django.templatetags.static import static
from django.core.mail import EmailMessage
from django.utils.html import strip_tags

class AddInvoiceView(LoginRequiredMixin, View):
    template_name = "add_invoice.html"

    def get(self, request, *args, **kwargs):
        customers = Customer.objects.all()
        articles = Article.objects.filter(is_active=True)
        context = {
            'customers': customers,
            'articles': articles
        }
        return render(request, self.template_name, context)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        try:
            customer_id = request.POST.get('customer')
            invoice_type = request.POST.get('invoice_type')
            article_ids = request.POST.getlist('article')
            quantities = request.POST.getlist('qty')
            unit_prices = request.POST.getlist('unit')
            comments = request.POST.get('comment')

            customer = Customer.objects.get(id=customer_id)

            errors = []  # Liste pour stocker les erreurs

            # Vérification du stock AVANT de créer la facture
            for article_id, qty in zip(article_ids, quantities):
                article = Article.objects.get(id=article_id)
                qty = Decimal(qty)

                if article.stock < qty:
                    errors.append(f"Stock insuffisant pour l'article {article.name}. Stock disponible : {article.stock}.")

            if errors:
                for error in errors:
                    messages.error(request, error)
                    return redirect('add-invoice')
                return redirect('add-invoice')  # Redirection et arrêt du code si erreur

            # Si pas d'erreur, création de la facture
            invoice = Invoice.objects.create(
                customer=customer,
                save_by=request.user,
                invoice_type=invoice_type,
                comments=comments
            )

            invoice_items_details = [] #Creation d'une liste pour stocker les details de chaque article
            total_amount = 0 #initialisation du montant total
            # Création des InvoiceItems et mise à jour du stock
            for article_id, qty, unit_price in zip(article_ids, quantities, unit_prices):
                article = Article.objects.get(id=article_id)
                qty = Decimal(qty)
                unit_price = Decimal(unit_price)

                # Mise à jour du stock
                article.stock -= qty
                article.save()

                InvoiceItem.objects.create(
                    invoice=invoice,
                    article=article,
                    quantity=qty,
                    unit_price=unit_price
                )
                item_total = qty * unit_price #calcul du total pour chaque article
                total_amount += item_total #ajout du total de l'article au montant total
                invoice_items_details.append(f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">{article.name}</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{qty}</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{unit_price}</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{item_total}</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{article.stock}</td>
                    </tr>
                """) #Ajout des details de chaque article dans la liste

             # Construction du tableau HTML pour les détails des articles
            article_table = f"""
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #663399; color: white;">
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">ARTICLE</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">QUANTITÉ</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">PRIX UNITAIRE</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">TOTAL</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">STOCK RESTANT</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(invoice_items_details)}
                    </tbody>
                </table>
            """
            # Construction du corps du message HTML
            html_message = f"""
                <html>
                <head>
                    <style>
                        /* Ajoutez du CSS pour embellir l'e-mail si vous le souhaitez */
                        body {{ font-family: Arial, sans-serif; }}
                        .header {{
                            background-color: #663399;
                            color: white;
                            padding: 10px;
                            text-align: center; /* Centrer le texte */
                        }}
                        .content {{ padding: 10px; }}
                        .button {{
                            background-color: #4CAF50; /* Green */
                            border: none;
                            color: white;
                            padding: 10px 20px;
                            text-align: center;
                            text-decoration: none;
                            display: inline-block;
                            font-size: 16px;
                            margin: 4px 2px;
                            cursor: pointer;
                            border-radius: 5px;
                        }}
                        .footer {{
                            text-align: center; /* Centrer les boutons */
                            padding: 20px;
                        }}
                        .total-date {{
                            color: #6A0DAD;
                            font-size: 18px;
                            font-weight: bold;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2><span style="font-weight: bold; text-transform: uppercase;"> 📢 NOUVELLE FACTURE ENREGISTRÉE !</span></h2>
                    </div>
                    <div class="content">
                        <p>📢 Une nouvelle facture a été générée par <strong>{request.user.username}</strong> pour le client <strong>{customer.name}</strong>.</p>
                        <h3>Détails de la Facture :</h3>
                        {article_table}

                        <div class="total-date">
                            <p><strong>Montant Total :</strong> {total_amount}</p>
                            <p><strong>Date :</strong> {invoice.invoice_date_time}</p>
                        </div>

                        <!-- Bouton d'action -->
                        <div style="text-align: center; padding: 20px;  height: 100px;">
                            <a href="http://127.0.0.1:8000/view_invoice/{invoice.id}" 
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
                    </div>
                            <!-- Pied de page -->
                <div style="background-color: #6A0DAD; padding: 10px; text-align: center; font-size: 12px; color: #fff;">
                </body>
                </html>
            """

            plain_message = strip_tags(html_message)  # Version texte brut pour les clients de messagerie qui ne supportent pas HTML

            email = EmailMessage(
                subject="Nouvelle vente effectuée",
                body=html_message, #utilisation de html_message et non plain_message pour le corps de l'email
                from_email=request.user.email,
                to=["lxolalikokouguel@gmail.com"],
            )
            email.content_subtype = "html"  # Indique que le contenu est HTML
            email.send()

            header_image_url = static("images/mobilehouseacceuil.svg")

            # Icônes des réseaux sociaux (remplace les liens avec ceux de tes réseaux)
            social_media_icons = """
            <div style="text-align: center; padding: 10px;">
                <a href="https://facebook.com/tonpage" style="margin: 0 5px;">
                    <img src="https://cdn-icons-png.flaticon.com/24/174/174848.png" width="24" height="24">
                </a>
                <a href="https://instagram.com/tonpage" style="margin: 0 5px;">
                    <img src="https://cdn-icons-png.flaticon.com/24/2111/2111463.png" width="24" height="24">
                </a>
                <a href="https://twitter.com/tonpage" style="margin: 0 5px;">
                    <img src="https://cdn-icons-png.flaticon.com/24/733/733579.png" width="24" height="24">
                </a>
                <a href="https://linkedin.com/tonpage" style="margin: 0 5px;">
                    <img src="https://cdn-icons-png.flaticon.com/24/174/174857.png" width="24" height="24">
                </a>
                <a href="https://www.tiktok.com/@tonpage" style="margin: 0 5px;">
                    <img src="https://cdn-icons-png.flaticon.com/24/3046/3046125.png" width="24" height="24">
                </a>
                <a href="https://wa.me/+22896393780" style="margin: 0 5px;">
                    <img src="https://cdn-icons-png.flaticon.com/24/733/733585.png" width="24" height="24">
                </a>
                <a href="https://www.youtube.com/c/tonpage" style="margin: 0 5px;">
                    <img src="https://cdn-icons-png.flaticon.com/24/1384/1384060.png" width="24" height="24">
                </a>
            </div>
            """

            # Corps du message HTML
            html_message = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                    }}
                    body {{
                        font-family: 'Arial', sans-serif;
                        background-color: #1c1c1c; /* Noir clair ultra classe */
                        color: #f1f1f1;
                        text-align: center;
                        padding: 40px;
                    }}
                    h1 {{
                        color: #6A0DAD;
                    }}
                    p {{
                        font-size: 16px;
                        line-height: 1.6;
                    }}
                    .header {{
                        text-align: center;
                        background-color : #6A0DAD;
                        padding: 20px;
                    }}
                    .content {{
                        padding: 20px;
                        text-align: center;
                    }}
                    .button {{
                        display: inline-block;
                        background-color: #27ae60;
                        color: white;
                        padding: 10px 20px;
                        text-decoration: none;
                        font-weight: bold;
                        border-radius: 5px;
                        margin-top: 20px;
                    }}
                    .footer {{
                        text-align: center;
                        background-color: #f1f1f1;
                        padding: 20px;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="{header_image_url}" width="100%" alt="En-tête">
                </div>
                    <h1>🛍️ Merci pour votre achat, {customer.name} !</h1>
                    <p>Nous sommes ravis de vous compter parmi nos précieux clients. Votre confiance signifie tout pour nous !</p>
                    <p>🌟 Chaque achat chez nous est une promesse de qualité et de satisfaction.</p>
                    <p>Si vous avez la moindre question, nous sommes là pour vous.</p>

                {social_media_icons}

                <div class="footer">
                    <p>Besoin d'aide ? <a href="mailto:lxolalikokouguel@gmail.com">Contactez-nous</a></p>
                    <p>© 2025 Mobile House. Tous droits réservés.</p>
                </div>
            </body>
            </html>
            """

            # Version texte brut (au cas où l'email HTML ne s'affiche pas)
            plain_message = strip_tags(html_message)

            # Envoi de l'email
            email = EmailMessage(
                subject="Merci pour votre achat !",
                body=html_message,
                from_email="lxolalikokouguel@gmail.com",
                to=[customer.email],
            )
            email.content_subtype = "html"  # Indique que l'email est au format HTML
            email.send()


            messages.success(request, "Facture créée avec succès.")
            return redirect('home')

        except Exception as e:
            messages.error(request, f"Désolé, une erreur s'est produite : {e}.")
            return render(request, self.template_name)


class InvoiceVisualizationView(LoginRequiredSuperuserMixin, View):
    template_name = 'invoice.html'
    def get(self,request, *args, **kwargs):
        pk = kwargs.get('pk')
        context = get_invoice(pk)

        return render(request, self.template_name, context)


@superuser_required  
def get_invoice_pdf(request, *args, **kwargs):
        #Generer un fichier pdf a partir de html
        pk =kwargs.get('pk')
        context = get_invoice(pk)
        context['date'] = datetime.datetime.today()
        #Get html file
        template = get_template('invoice_pdf.html')
        #Render html with context variable : Envoyer les variables de context directement vers le template
        html = template.render(context)
        #Option of pdf format
        options = {
            'page-size':'Letter',
            'encoding':'UTF-8',
            'enable-local-file-access': ''
        }

        #Generate pdf
        try:
        # Générer le PDF
            pdf = pdfkit.from_string(html, False, options)
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
            return response

        except Exception as e:
            return HttpResponse(f"Erreur lors de la génération du PDF : {e}", status=500)
        

# Formulaire personnalisé pour créer un administrateur
class AdminCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # Définit l'utilisateur comme administrateur
        user.set_password(self.cleaned_data['password'])  # Hache le mot de passe
        if commit:
            user.save()
        return user

# Vue pour ajouter un administrateur
@login_required
def add_admin(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Administrateur créé avec succès !")
            return redirect('admin_list')  # Remplacez par votre URL cible
    else:
        form = AdminCreationForm()

    return render(request, 'add_admin.html', {'form': form})

# views.py
@login_required
def admin_list(request):
    admins = User.objects.filter(is_staff=True)
    return render(request, 'admin_list.html', {'admins': admins})

# Vue pour ajouter un nouvel article
def add_article(request):
    if request.method == "POST":
        try:
            # Récupération des données du formulaire
            name = request.POST.get('name')
            stock = request.POST.get('stock')

            # Création de l'article dans la base de données
            article = Article.objects.create(
                name=name,
                stock=stock
            )

            # Message de succès
            messages.success(request, "L'article a été ajouté avec succès.")
            return redirect('article-list')  # Rediriger vers la même page ou une autre page après l'ajout

        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout de l'article : {e}")

    # Si la requête est en GET, on affiche simplement le formulaire
    return render(request, "add_article.html")

def article_list(request):
    articles = Article.objects.filter(is_active=True)  # Récupérer tous les produits

    if request.method == 'POST' and 'id_supprimer' in request.POST:
        try:
            article_id = request.POST.get('id_supprimer')
            print(f"ID reçu pour suppression : {article_id}")  # Debugging
            # Get the Article object
            article = Article.objects.get(pk=article_id)
            # Delete the Article object
            article.is_active = False
            article.save()
            messages.success(request, "L'article a été supprimé avec succès.")
        except Article.DoesNotExist:
            messages.error(request, "L'article n'existe pas.")
        except Exception as e:
            messages.error(request, f"Désolé, l'erreur suivante s'est produite : {e}.")


    return render(request, 'article_list.html', {'articles': articles})

def customer_list(request):
    customers = Customer.objects.all()  # Récupérer tous les produits
    return render(request, 'customer_list.html', {'customers': customers})

def sales_summary(request):
    sales_data = []
    invoice_items = InvoiceItem.objects.all().order_by('-invoice__invoice_date_time')

    for item in invoice_items:
        sales_data.append({
            'article_name': item.article.name,
            'quantity_sold': item.quantity,
            'sale_date': item.invoice.invoice_date_time,
            'customer_name': item.invoice.customer.name,
            'unit_price': item.unit_price,
            'total_price': item.total_price,
        })

    context = {
        'sales_data': sales_data
    }
    return render(request, 'sales_summary_list.html', context)


def edit_article(request, article_id):
    article = get_object_or_404(Article, pk=article_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        stock = request.POST.get('stock')

        # Validation manuelle
        errors = {}
        if not name:
            errors['name'] = "Le nom de l'article est obligatoire."
        if not stock:
            errors['stock'] = "Le stock est obligatoire."
        try:
            stock = int(stock)
            if stock < 0:
                errors['stock'] = "Le stock doit être un nombre positif."
        except ValueError:
            errors['stock'] = "Le stock doit être un nombre entier."

        if errors:
            context = {'article': article, 'errors': errors, 'name': name, 'stock': stock}
            return render(request, 'edit_article.html', context)

        # Si la validation réussit, enregistrez les modifications
        article.name = name
        article.stock = stock
        article.save()
        messages.success(request, "L'article a été modifié avec succès.")
        return redirect('article-list')  # Redirige vers la liste des articles
    else:
        # Affiche le formulaire pré-rempli
        context = {'article': article, 'name': article.name, 'stock': article.stock}
        return render(request, 'edit_article.html', context)