from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('add_customer', views.AddCustomerView.as_view(), name='add-customer'),
    path('add_invoice', views.AddInvoiceView.as_view(), name='add-invoice'),
    path('add_article', views.add_article, name='add-article'),
    path('article_list', views.article_list, name='article-list'),
    path('article/<int:article_id>/modifier/', views.edit_article, name='edit-article'),
    path('sales_summary_list', views.sales_summary, name='sales-summary-list'),
    path('customer_list', views.customer_list, name='customer-list'),
    path('view_invoice/<int:pk>', views.InvoiceVisualizationView.as_view(), name='view-invoice'),
    path('invoice_pdf/<int:pk>', views.get_invoice_pdf, name="invoice-pdf"),
    path('admin_add', views.add_admin, name='add-admin'),
    path('admin_list', views.admin_list, name ='admin-list'),
]