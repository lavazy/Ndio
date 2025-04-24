from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', views.home, name='home'),
    # Referral home page
    path('home_referral/<str:ref_code>/', views.referral_home, name='referral_home'),
    path('lte/', views.lte_view, name='lte_view'),
    path('switch/', views.switch, name='switch'),
    path('about/', views.about_us, name='about_us'),
    path('packages/', views.packages, name='packages'),
    path('home_fibre/', views.home_fibre, name='home_fibre'),
    path('business_fibre/', views.business_fibre, name='business_fibre'),
    path('voip/', views.voip, name='voip'),
    path('wireless/', views.wireless, name='wireless'),
    path('network_cabling/', views.network_cabling, name='network_cabling'),
    path('managed/', views.managed, name='managed'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('faqs/', views.faqs, name='faqs'),
    path('register/', views.register_view, name='register_view'),
    path('login_user/', views.login_view, name='login_view'),
    path('user_account/', views.user_account, name='user_account'),
    path('logout_view/', views.logout_view, name='logout_view'),
    path('login_view_order/', views.login_view_order, name='login_view_order'),
    path('order_details/', views.order_details, name='order_details'),
    path('payments/', views.payment_view, name='payment_view'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('unsuccessful_payment/', views.unsuccessful_payment, name='unsuccessful_payment'),

    # Password rest urls
    path('reset_password/', auth_views.PasswordResetView.as_view(), name='reset_password'),
    path('reset_password_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    ]