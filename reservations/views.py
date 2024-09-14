from django.shortcuts import render, HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Bus, Reservation
from .serializers import BusSerializer, ReservationSerializer
from django.db.models import F, Sum
# Create your views here.
def index(request):
    return HttpResponse("Welcome to Bus resevation platform")

class BusViewSet(viewsets.ViewSet):
    def list(self, request):
        source = request.query_params.get('source')
        destination = request.query_params.get('destination')
        date = request.query_params.get('date')

        if not source or not destination or not date:
            return Response({'error': 'Source, destination, and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        buses = Bus.objects.filter(source=source, destination=destination)
        reservations = Reservation.objects.filter(reservation_date=date)
        
        bus_seat_reservation = reservations.values('bus').annotate(total_reserved=Sum('seats_reserved'))

        available_buses = []
        for bus in buses:
            reserved_seats = next((item['total_reserved'] for item in bus_seat_reservation if item['bus'] == bus.id), 0)
            available_seats = bus.capacity - reserved_seats
            if available_seats > 0:
                available_buses.append({
                    'bus_number': bus.bus_number,
                    'company_name': bus.company_name,
                    'start_time': bus.start_time,
                    'end_time': bus.end_time,
                    'available_seats': available_seats,
                })

        return Response(available_buses, status=status.HTTP_200_OK)

class ReservationViewSet(viewsets.ViewSet):
    def create(self, request):
        bus_number = request.data.get('bus_number')
        user_id = request.data.get('user_id')
        reservation_date = request.data.get('reservation_date')
        seats_reserved = request.data.get('seats_reserved')

        try:
            bus = Bus.objects.get(bus_number=bus_number)
        except Bus.DoesNotExist:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)

        reservations = Reservation.objects.filter(bus=bus, reservation_date=reservation_date)
        reserved_seats = reservations.aggregate(total_reserved=Sum('seats_reserved'))['total_reserved'] or 0
        available_seats = bus.capacity - reserved_seats

        if seats_reserved > available_seats:
            return Response({'error': 'Not enough seats available.'}, status=status.HTTP_400_BAD_REQUEST)

        reservation = Reservation.objects.create(
            bus=bus,
            user_id=user_id,
            reservation_date=reservation_date,
            seats_reserved=seats_reserved
        )
        return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)

    def list(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        reservations = Reservation.objects.filter(user_id=user_id)
        return Response(ReservationSerializer(reservations, many=True).data, status=status.HTTP_200_OK)
