from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('add_customer', views.AddCustomerView.as_view(), name='add-customer'),
    path('add_invoice', views.AddInvoiceView.as_view(), name='add-invoice'),
    path('view_invoice/<int:pk>', views.InvoiceVisualizationView.as_view(), name='view-invoice'),
    path('invoice_pdf/<int:pk>', views.get_invoice_pdf, name="invoice-pdf"),
    path('admin_add', views.add_admin, name='add-admin'),
    path('admin_list', views.admin_list, name ='admin-list'),
    #Url pour modifier un administrateur
    #path('admin_edit/<int:admin_id>/', views.edit_admin, name='edit-admin'),
]