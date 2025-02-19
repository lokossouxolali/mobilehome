from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum

# Create your models here.
class Customer(models.Model):
    #Nom = Definition du model client

    SEX_TYPES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    name = models.CharField(max_length=132)
    email = models.EmailField()
    phone = models.CharField(max_length=132)
    address = models.CharField(max_length=132)
    sex = models.CharField(max_length=1, choices=SEX_TYPES)
    age = models.CharField(max_length=12)
    city = models.CharField(max_length=32)
    zip_code = models.CharField(max_length=32)
    created_date = models.DateTimeField(auto_now_add=True)
    save_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return self.name
    
class Invoice(models.Model):
    #Name = Definition du model Facture
    #Author : lxolalikokouguel@gmail.com


    INVOICE_TYPE = (
        ('R', 'RECU'),
        ('F', 'FACTURE')
    )

    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.PROTECT)
    save_by = models.ForeignKey(User, on_delete=models.PROTECT)
    invoice_date_time = models.DateTimeField(auto_now_add=True)
    last_updated_date = models.DateTimeField(null=True)
    paid = models.BooleanField(default=True)
    invoice_type = models.CharField(max_length=1, choices=INVOICE_TYPE)
    comments = models.TextField(null=True, max_length=1000, blank=True)


    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self):
        return f"{self.customer.name}_{self.invoice_date_time}"
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.invoice_items.all())
    @property
    def total(self):
        total_amount = 0
        for item in self.invoice_items.all():
            total_amount += item.total_price
        return total_amount

class Article(models.Model):
    name = models.CharField(max_length=132)
    stock = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return f"{self.name} (Stock: {self.stock})"
    
    @property
    def total_sold(self):
        return sum(item.quantity for item in self.invoiceitem_set.all())  # Récupère toutes les ventes liées à l'article et somme les quantités vendues
    
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL, related_name="invoice_items")
    article = models.ForeignKey(Article, null=True, blank=True, on_delete=models.SET_NULL)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    def __str__(self):
        return f"{self.article.name} - {self.quantity}"
    