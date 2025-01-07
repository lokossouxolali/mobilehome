from django.contrib import admin
from .models import *
# Register your models here.
class AdminCustomer(admin.ModelAdmin):
    list_display = ('name', 'email','phone', 'address', 'sex', 'age', 'city', 'zip_code')

class AdminInvoice(admin.ModelAdmin):
    list_display = ('customer', 'save_by', 'invoice_date_time', 'total', 'paid', 'invoice_type')


admin.site.register(Customer, AdminCustomer)
admin.site.register(Invoice, AdminInvoice)
admin.site.register(Article)

admin.site.site_title = "MOBILE HOUSE"
admin.site.site_header = "MOBILE HOUSE"
admin.site.index_title = "MOBILE HOUSE"