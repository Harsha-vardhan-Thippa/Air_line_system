from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),#correct
    path('login/',views.login_view),#correct
    path('register/', views.register_view),#correct
    path('logout/', views.logout_view),
    path('seat/<int:flight_id>/', views.seat_view),
    path('payment/<int:flight_id>/', views.payment_page),#correct
    path('download/<str:booking_id>/', views.download_ticket),
    path('booking/', views.show_bookings),
    path('cancel_booking/<int:booking_id>/', views.cancel_bookings),
    path('success/<str:booking_id>/', views.booking_success),
    path('verify-otp/',views.otp_view),

]