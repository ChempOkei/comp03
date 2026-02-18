from django.urls import path

from . import api_views

#роуты + тут настроить темплейты
urlpatterns = [
    path('registr', api_views.api_register, name='api_register'),
    path('auth', api_views.api_auth, name='api_auth'),
    path('courses', api_views.api_courses, name='api_courses'),
    path('courses/<int:course_id>', api_views.api_course_lessons, name='api_course_lessons'),
    path('courses/<int:course_id>/buy', api_views.api_course_buy, name='api_course_buy'),
    path('payment-webhook', api_views.api_payment_webhook, name='api_payment_webhook'),
    path('orders', api_views.api_orders, name='api_orders'),
    path('orders/<int:order_pk>', api_views.api_order_cancel, name='api_order_cancel'),
    path('check-certificate', api_views.api_check_certificate, name='api_check_certificate'),
    path('check-sertificate', api_views.api_check_certificate, name='api_check_sertificate'),
    path('mock-pay/<str:order_id>', api_views.mock_pay, name='api_mock_pay'),
]

