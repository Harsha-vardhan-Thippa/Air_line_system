from django.shortcuts import render, redirect
from io import BytesIO
from django.core.mail import EmailMessage
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import Flight, Booking
from reportlab.lib import colors
import random
from django.core. mail import send_mail
import os

def login_view(request):
    error = None
    # next_url = request.GET.get('next')
    # next_url = request.session.get('next_url')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # next_url = request.POST.get('next')
        user = authenticate(request, username=username, password=password)
        if user:
            otp = random.randint(100000, 999999)
            request.session['otp'] = otp
            request.session['user_id'] = user.id
            print("BEFORE SEND MAIL")
            print("USERNAME:", user.username)
            print("OTP EMAIL:", user.email)
            send_mail('Login OTP',
        f'Your OTP is {otp}',
        'untamedchinese@gmail.com',
        [user.email],
            fail_silently=False)
            print("AFTER SEND MAIL")
            return redirect('/verify-otp')
            # login(request, user)
            # next_url = request.session.get(
            #     'next_url'
            # )
            # if next_url:
            #     return redirect(next_url)
            # return redirect('/')
        else:
            error = "User not found"

    return render(
        request,
        'login.html',
        {
            'error': error,
        }
    )


def otp_view(request):
    error = None
    if request.method == 'POST':
        user_otp = request.POST['otp']
        session_otp = request.session.get('otp')
        if user_otp == str(session_otp):
            user = User.objects.get(id=request.session['user_id'])
            login(request, user)
            next_url = request.session.get('next_url')
            if next_url:
                del request.session['next_url']
                return redirect(next_url)
            return redirect('/')
        else:
            error = "Incorrect OTP"
    return render(request,'otp.html',{'error': error})


def register_view(request):
    message = None

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        if User.objects.filter(username=username).exists():
            message = "User already exists"
        else:
            User.objects.create_user(username=username, password=password, email=email)
            message = "Registered successfully"

    return render(request, 'register.html', {'message': message})


def home(request):
    if request.method == 'POST':
        flights = Flight.objects.all()
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        date = request.POST.get('date')
        if source:
            flights = flights.filter(source__icontains=source)

        if destination:
            flights = flights.filter(destination__icontains=destination)
        Available=[]
        if date:
            for f in flights:
                c = Booking.objects.filter(flight=f, travel_date=date).count()
                remaining = f.total_seats-c
                if remaining > 0:
                    f.remaining_seats = remaining
                    Available.append(f)
        flights=Available
        return render(request, 'show.html', {'flights': flights,'date': date})
    return render(request, 'home.html')


def seat_view(request,flight_id):
    flight = Flight.objects.get(id=flight_id)
    date = request.GET.get('date')
    booked_seats = Booking.objects.filter(flight=flight, travel_date=date).values_list(
    'seat_number',
    flat=True
)
    all_seats = ["A"+str(x) for x in range(1,flight.total_seats+1)]
    # date = request.GET.get('date')
    if len(all_seats) == len(booked_seats):
        messages.error(request, "Seats were booked")
        return redirect('/')
    if request.method == 'POST':
        selected_seats = request.POST.getlist('seats')
        error=None

        for i in selected_seats:
            if Booking.objects.filter(flight=flight, travel_date=date,seat_number=i).exists():
                error = "Seat already Booked"
        if error:
            return render(request,'seat_view.html',{'flight': flight, 'booked_seats': booked_seats, 'all_seats': all_seats,'error':error})
        seats = "-".join(selected_seats)
        return redirect(f'/payment/{flight_id}/?seats={seats}&date={date}')

    return render(request, 'seat_view.html', {'flight': flight, 'booked_seats': booked_seats, 'all_seats': all_seats})


def payment_page(request, flight_id):
    flight = Flight.objects.get(id=flight_id)
    seat_number = request.GET.get('seats').split('-')
    date = request.GET.get('date')
    number_of_seats = len(seat_number)
    total_price = number_of_seats*flight.price
    booking_id = []
    if request.method == 'POST':
        if not request.user.is_authenticated:
            request.session['next_url'] = (
                request.get_full_path()
            )

            return redirect('/login/')
        payment_method = request.POST.get('payment_method')
        for i in seat_number:
            booking = Booking.objects.create(
                user=request.user,
                flight=flight,
                travel_date=date,
                seat_number=i,
                payment_methods=payment_method,
            )
            booking_id.append(str(booking.id))
        booking_id = "-".join(booking_id)

        bookings = Booking.objects.filter(id__in=booking_id.split('-'))
        send_ticket_email(bookings)

        # request.session['download_url'] = f'/download/{booking_id}'
        # messages.success(request,f'Seat Successfully Booked Using {payment_method}')

        return redirect(f'/success/{booking_id}/')
    return render(request,'payment.html', {'flight': flight, 'total_price': total_price})

def booking_success(request, booking_id):
    bookings = Booking.objects.filter(id__in=booking_id.split("-"))
    return render(request,'booking_success.html', {'bookings': bookings, 'booking_id': booking_id})


def show_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'show_bookings.html', {'bookings': bookings})

def cancel_bookings(request,booking_id):
    Booking.objects.filter(id=booking_id).delete()
    messages.success(request,"Booking Canceled successfully")
    return redirect('/')

def download_ticket(request, booking_id):
    booking_ids = booking_id.split('-')
    bookings = Booking.objects.filter(
        id__in=booking_ids
    )
    response = HttpResponse(
        content_type='application/pdf'
    )
    response[
        'Content-Disposition'
    ] = 'attachment; filename="ticket.pdf"'
    p = canvas.Canvas(response)
    for booking in bookings:
        # BLUE HEADER
        p.setFillColor(colors.blue)
        p.rect(
            40,
            720,
            520,
            50,
            fill=True
        )
        # HEADER TEXT
        p.setFillColor(colors.white)
        p.setFont(
            "Helvetica-Bold",
            24
        )
        p.drawString(
            60,
            735,
            "AIR TICKET"
        )
        # MAIN BOX
        p.setFillColor(colors.whitesmoke)
        p.rect(
            40,
            450,
            520,
            270,
            fill=True
        )
        # BLACK TEXT
        p.setFillColor(colors.black)
        p.setFont(
            "Helvetica",
            14
        )
        p.drawString(
            60,
            680,
            f"Passenger: {booking.user.username}"
        )
        p.drawString(
            320,
            680,
            f"Seat: {booking.seat_number}"
        )
        p.drawString(
            60,
            630,
            f"From: {booking.flight.source}"
        )
        p.drawString(
            320,
            630,
            f"To: {booking.flight.destination}"
        )
        p.drawString(
            60,
            580,
            f"Flight: {booking.flight.flight_number}"
        )
        p.drawString(
            320,
            580,
            f"Date: {booking.travel_date}"
        )
        p.drawString(
            60,
            530,
            f"Payment: {booking.payment_methods}"
        )
        p.drawString(
            320,
            530,
            "Status: Confirmed"
        )
        # FOOTER
        p.setFillColor(colors.blue)
        p.rect(
            40,
            420,
            520,
            30,
            fill=True
        )
        p.setFillColor(colors.white)
        p.drawString(
            90,
            430,
            "*********THANK YOU FOR CHOOSING SH AIRLINES********"
        )
        p.showPage()
    p.save()
    return response

def send_ticket_email(bookings):
    buffer=BytesIO()
    p=canvas.Canvas(buffer)
    y=700
    for booking in bookings:
        p.setFillColor(colors.blue)
        p.rect(40,y,520,40,fill=True)
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold",20)
        p.drawString(60,y+12,"AIR TICKET")
        p.setFillColor(colors.black)
        p.setFont("Helvetica",14)
        p.drawString(60,y-40,f"Passenger: {booking.user.username}")
        p.drawString(60,y-70,f"Flight: {booking.flight.flight_number}")
        p.drawString(60,y-100,f"From: {booking.flight.source}")
        p.drawString(60,y-130,f"To: {booking.flight.destination}")
        p.drawString(60,y-160,f"Seat: {booking.seat_number}")
        p.drawString(60,y-190,f"Date: {booking.travel_date}")
        p.drawString(60,y-220,f"Payment: {booking.payment_methods}")
        p.setFillColor(colors.blue)
        p.rect(40,y-260,520,25,fill=True)
        p.setFillColor(colors.white)
        p.drawCentredString(300,y-250,"THANK YOU FOR CHOOSING SKYJET AIRLINES")
        y-=320
    p.save()
    pdf=buffer.getvalue()
    buffer.close()
    email=EmailMessage(
        'SH AIRLINES',
        'Thank you for your Servise \n Your ticket is attached below.',
        'untamedchinese@gmail.com',
        [bookings.first().user.email]
    )
    email.attach(
        'ticket.pdf',
        pdf,
        'application/pdf'
    )
    email.send()


def logout_view(request):
    logout(request)
    return redirect('/')