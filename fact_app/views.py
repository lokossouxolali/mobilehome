from django.shortcuts import redirect, render
from django.views import View
from .models import *
from django.contrib import messages
from django.db import transaction
import pdfkit
from django.template.loader import get_template
from .utils import pagination, get_invoice
import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .decorators import *


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


class AddInvoiceView(LoginRequiredSuperuserMixin, View):
    template_name = "add_invoice.html"
    customers = Customer.objects.select_related('save_by').all()
    context = {
        'customers': customers
    }
    
    def get(self, request, *arg, **kwargs):
        return render(request, self.template_name, self.context)
    
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        items = []
        try:
            customer = request.POST.get('customer')
            type = request.POST.get('invoice_type')  # Correspond au champ type de la facture
            articles = request.POST.getlist('article')  # Utiliser .getlist pour une liste
            qties = request.POST.getlist('qty')  # Quantités
            units = request.POST.getlist('unit')  # Prix unitaire
            total_a = request.POST.getlist('total-a')  # Totaux par article
            total = request.POST.get('total')  # Total général
            comment = request.POST.get('comment')  # Commentaire
            
            # Création de l'objet facture
            invoice_object = {
                'customer_id': customer,
                'save_by': request.user,
                'total': total,
                'invoice_type': type,
                'comments': comment
            }
            invoice = Invoice.objects.create(**invoice_object)

            # Création des articles liés à la facture
            for index, article in enumerate(articles):
                data = Article(
                    invoice_id=invoice.id,
                    name=article,
                    quantity=float(qties[index]),
                    unit_price=float(units[index]),
                    total=float(total_a[index]),
                )
                items.append(data)
            
            created = Article.objects.bulk_create(items)
            
            if created:
                messages.success(request, "Données enregistrées avec succès.")
                return redirect('home')
            else:
                messages.error(request, "Désolé, veuillez réessayer ; les données envoyées sont corrompues.")
                return redirect('add-invoice')
        
        except Exception as e:
            messages.error(request, f"Désolé, l'erreur suivante s'est produite : {e}.")
        
        return render(request, self.template_name, self.context)

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