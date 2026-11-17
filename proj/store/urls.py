from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

urlpatterns = [
    # Unified SCN Dashboard (Accessible to all roles & guests)
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/distributor/', distributor_dashboard, name='distributor_dashboard'),

    # SCN Operations (Orders, Dispatch, Products, Nodes, Receipts)
    path('order/place/', place_order, name='place_order'),
    path('order/status/', update_order_status, name='update_order_status'),
    path('order/receipt/<str:order_id>/', view_receipt, name='view_receipt'),
    path('product/add/', add_product, name='add_product'),
    path('product/update-stock/', update_product_stock, name='update_product_stock'),
    path('node/remove/', remove_node, name='remove_node'),

    # Admin Auth
    path('register/admin/', register_admin, name='register_admin'),
    path('login/admin/', login_admin, name='login_admin'),
    path('forgot-password/admin/', forgot_password_admin, name='forgot_password_admin'),
    path('verify-otp/admin/', verify_otp_admin, name='verify_otp_admin'),
    path('reset-password/admin/', reset_password_admin, name='reset_password_admin'),
    path('resend-otp/admin/', resend_otp_admin, name='resend_otp_admin'),
    path('logout_admin/admin/', logout_admin, name='logout_admin'),

    # Distributor Auth
    path('register/distributor/', register_distributor, name='register_distributor'),
    path('login/distributor/', login_distributor, name='login_distributor'),
    path('forgot-password/distributor/', forgot_password_distributor, name='forgot_password_distributor'),
    path('verify-otp/distributor/', verify_otp_distributor, name='verify_otp_distributor'),
    path('reset-password/distributor/', reset_password_distributor, name='reset_password_distributor'),
    path('resend-otp/distributor/', resend_otp_distributor, name='resend_otp_distributor'),
    path('logout_distributor/distributor/', logout_distributor, name='logout_distributor'),

    # Retailer / User Auth
    path('register/user/', register_user, name='register_user'),
    path('login/user/', login_user, name='login_user'),
    path('forgot-password/user/', forgot_password_user, name='forgot_password_user'),
    path('verify-otp/user/', verify_otp_user, name='verify_otp_user'),
    path('reset-password/user/', reset_password_user, name='reset_password_user'),
    path('resend-otp/user/', resend_otp_user, name='resend_otp_user'),
    path('logout_user/user/', logout_user, name='logout_user'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
