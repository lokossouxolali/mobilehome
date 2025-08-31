from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger)
from fact_app.models import Invoice
from .models import *

def pagination(request, items):
     #default_page
        default_page = 1
        page = request.GET.get('page', default_page)
        #Paginate items
        items_per_page = 10  # Augmenté à 10 éléments par page
        paginator = Paginator(items, items_per_page)
        try:
            items_page = paginator.page(page)
        except PageNotAnInteger:
            items_page = paginator.page(default_page)
        except EmptyPage:
            items_page = paginator.page(paginator.num_pages)

        return items_page

from django.shortcuts import get_object_or_404

def get_invoice(pk):
    obj = Invoice.objects.get(pk=pk)
    invoice_items = obj.invoice_items.all()
    context = {
        'obj': obj,
        'invoice_items': invoice_items
    }
    return context