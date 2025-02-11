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
                return redirect('add-invoice')  # Redirection et arrêt du code si erreur

            # Si pas d'erreur, création de la facture
            invoice = Invoice.objects.create(
                customer=customer,
                save_by=request.user,
                invoice_type=invoice_type,
                comments=comments
            )

            # Création des InvoiceItems et mise à jour du stock
            for article_id, qty, unit_price in zip(article_ids, quantities, unit_prices):
                article = Article.objects.get(id=article_id)
                qty = Decimal(qty)
                unit_price = Decimal(unit_price)

                InvoiceItem.objects.create(
                    invoice=invoice,
                    article=article,
                    quantity=qty,
                    unit_price=unit_price
                )

                # Décrémenter le stock
                article.stock -= qty
                article.save()

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