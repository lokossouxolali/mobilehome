from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger)
from fact_app.models import Invoice
from .models import *

def pagination(request, invoices):
     #default_page
        default_page = 1
        page = request.GET.get('page', default_page)
        #Paginate items
        items_per_page = 5
        paginator = Paginator(invoices, items_per_page)
        try:
            items_page = paginator.page(page)
        except PageNotAnInteger:
            items_page = paginator.page(default_page)
        except EmptyPage:
            items_page = paginator.page(paginator.num_pages)

        invoices = Invoice.objects.all().order_by('-invoice_date_time')  # Trie par date de manière décroissante
        paginator = Paginator(invoices, items_per_page)
        return items_page

def get_invoice(pk):
        
        obj = Invoice.objects.get(pk=pk)
        articles = obj.article_set.all()
        context = {
            'obj': obj,
            'articles': articles
        }
        return context