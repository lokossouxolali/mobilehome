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
    path('export_sales_pdf', views.export_sales_pdf, name='export-sales-pdf'),
    path('export_sales_excel', views.export_sales_excel, name='export-sales-excel'),
    path('export_articles_pdf', views.export_articles_pdf, name='export-articles-pdf'),
    path('export_articles_excel', views.export_articles_excel, name='export-articles-excel'),
    path('export_customers_pdf', views.export_customers_pdf, name='export-customers-pdf'),
    path('export_customers_excel', views.export_customers_excel, name='export-customers-excel'),
    path('export_admins_pdf', views.export_admins_pdf, name='export-admins-pdf'),
    path('export_admins_excel', views.export_admins_excel, name='export-admins-excel'),
    path('export_dashboard_pdf', views.export_dashboard_pdf, name='export-dashboard-pdf'),
    path('export_dashboard_excel', views.export_dashboard_excel, name='export-dashboard-excel'),
    path('customer_list', views.customer_list, name='customer-list'),
    path('view_invoice/<int:pk>', views.InvoiceVisualizationView.as_view(), name='view-invoice'),
    path('invoice_pdf/<int:pk>', views.get_invoice_pdf, name="invoice-pdf"),
    path('admin_add', views.add_admin, name='add-admin'),
    path('admin_list', views.admin_list, name ='admin-list'),
] 