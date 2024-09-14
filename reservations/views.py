from django.shortcuts import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Bus, Reservation, Day
from .serializers import BusSerializer, ReservationSerializer
from django.db.models import Sum
from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend

def get_day_of_week(date_str):
    try:
        date_obj = parse_date(date_str)
        if not date_obj:
            return None, 'Invalid date format. Use YYYY-MM-DD.'
        
        day_of_week = date_obj.strftime('%A')
        day = Day.objects.filter(name=day_of_week).first()
        if not day:
            return None, 'Invalid day.'

        return day, None
    except Exception as e:
        return None, str(e)

# Create your views here
def index(request):
    return HttpResponse("Welcome to Bus reservation platform")

class BusViewSet(viewsets.ViewSet):
    def list(self, request):
        source = request.query_params.get('source')
        destination = request.query_params.get('destination')
        date = request.query_params.get('date')

        if not source or not destination or not date:
            return Response({'error': 'Source, destination, and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        day, error = get_day_of_week(date)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        buses = Bus.objects.filter(
            source=source, 
            destination=destination, 
            frequency=day
        )

        if not buses.exists():
            return Response({'message': 'No buses available for the selected route and day.'}, status=status.HTTP_404_NOT_FOUND)

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

        if not available_buses:
            return Response({'message': 'No buses with available seats.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(available_buses, status=status.HTTP_200_OK)

class ReservationViewSet(viewsets.ViewSet):
    def create(self, request):
        bus_number = request.data.get('bus_number')
        user_id = request.data.get('user_id')
        reservation_date = request.data.get('reservation_date')
        seats_reserved = request.data.get('seats_reserved')

        if not all([bus_number, user_id, reservation_date, seats_reserved]):
            return Response({'error': 'All fields (bus_number, user_id, reservation_date, seats_reserved) are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bus = Bus.objects.get(bus_number=bus_number)
        except Bus.DoesNotExist:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)

        day_of_week = parse_date(reservation_date).strftime('%A')
        if not bus.frequency.filter(name=day_of_week).exists():
            return Response({'error': 'Bus does not operate on this day.'}, status=status.HTTP_400_BAD_REQUEST)

        reservations = Reservation.objects.filter(bus=bus, reservation_date=reservation_date)
        reserved_seats = reservations.aggregate(total_reserved=Sum('seats_reserved'))['total_reserved'] or 0
        available_seats = bus.capacity - reserved_seats

        if int(seats_reserved) > available_seats:
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
        if not reservations.exists():
            return Response({'message': 'No reservations found for the user.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(ReservationSerializer(reservations, many=True).data, status=status.HTTP_200_OK)
