from odoo import http
from odoo.http import request
from datetime import datetime, timedelta


class RoomsController(http.Controller):

    @http.route('/rooms', type='http', auth='public', website=True)
    def list_rooms(self, **kwargs):
        # Get search parameters from URL
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')

        # Set default values if not provided
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Convert string dates to date objects for comparison
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            # If date parsing fails, use defaults
            start_date_obj = datetime.now().date()
            end_date_obj = (datetime.now() + timedelta(days=1)).date()
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')

        # Get all rooms
        all_rooms = request.env['hotel.room'].sudo().search([])

        # Filter available rooms based on date range
        available_rooms = []
        for room in all_rooms:
            # Check if room has any overlapping active reservations
            overlapping_reservations = request.env['hotel.room.reservation'].sudo().search([
                ('room_id', '=', room.id),
                ('state', 'not in', ['cancelled']),
                ('start_date', '<', end_date_obj),
                ('actual_end_date', '>', start_date_obj)
            ])

            # If no overlapping reservations, room is available
            if not overlapping_reservations:
                available_rooms.append(room)

        return request.render('hotel.rooms_page_template', {
            'rooms': available_rooms,
            'start_date': start_date,
            'end_date': end_date,
            'total_rooms': len(all_rooms),
            'available_rooms_count': len(available_rooms)
        })

    @http.route('/room/book/<int:room_id>', type='http', auth='public', website=True)
    def book_room(self, room_id, **kwargs):
        # Get the room
        room = request.env['hotel.room'].sudo().browse(room_id)
        if not room.exists():
            return request.redirect('/rooms')

        # Get date parameters from URL
        start_date = kwargs.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        end_date = kwargs.get('end_date', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))

        # Get all available equipment
        all_equipment = request.env['hotel.room.equipment'].sudo().search([])

        # Calculate duration in days
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            duration_days = (end_date_obj - start_date_obj).days + 1
        except ValueError:
            duration_days = 1

        return request.render('hotel.booking_form_template', {
            'room': room,
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': duration_days,
            'all_equipment': all_equipment
        })

    @http.route('/room/book/submit', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def submit_booking(self, **kwargs):
        try:
            # Create the reservation
            reservation_data = {
                'start_date': kwargs.get('start_date'),
                'end_date': kwargs.get('end_date'),
                'room_id': int(kwargs.get('room_id')),
                'people_number': int(kwargs.get('people_number', 1)),
                'client_id': request.env.user.id,
                'state': 'active'  # Set initial state
            }

            # Handle equipment selection
            equipment_ids = []
            for key, value in kwargs.items():
                if key.startswith('equipment_') and value == 'on':
                    equipment_id = int(key.replace('equipment_', ''))
                    equipment_ids.append(equipment_id)

            if equipment_ids:
                reservation_data['equipment_ids'] = [(6, 0, equipment_ids)]

            # Create reservation
            reservation = request.env['hotel.room.reservation'].sudo().create(reservation_data)

            return request.render('hotel.booking_success_template', {
                'reservation': reservation
            })

        except Exception as e:
            return request.render('hotel.booking_error_template', {
                'error_message': str(e)
            })

    @http.route('/my/reservations', type='http', auth='user', website=True)
    def my_reservations(self, **kwargs):
        """Display current user's reservations"""
        # Get current user's reservations
        reservations = request.env['hotel.room.reservation'].sudo().search([
            ('client_id', '=', request.env.user.id)
        ], order='start_date desc')

        return request.render('hotel.my_reservations_template', {
            'reservations': reservations
        })

    @http.route('/my/reservation/<int:reservation_id>', type='http', auth='user', website=True)
    def reservation_detail(self, reservation_id, **kwargs):
        """Display reservation details"""
        # Get the reservation and verify it belongs to current user
        reservation = request.env['hotel.room.reservation'].sudo().search([
            ('id', '=', reservation_id),
            ('client_id', '=', request.env.user.id)
        ])

        if not reservation:
            return request.redirect('/my/reservations')

        return request.render('hotel.reservation_detail_template', {
            'reservation': reservation
        })

    @http.route('/my/reservation/<int:reservation_id>/end', type='http', auth='user', methods=['POST'], website=True,
                csrf=False)
    def end_reservation_early(self, reservation_id, **kwargs):
        """End a reservation early"""
        try:
            # Get the reservation and verify it belongs to current user
            reservation = request.env['hotel.room.reservation'].sudo().search([
                ('id', '=', reservation_id),
                ('client_id', '=', request.env.user.id)
            ])

            if not reservation:
                return request.redirect('/my/reservations')

            # Check if reservation can be ended early
            if reservation.can_be_ended_early():
                reservation.action_end_early()
                message = "Reservation ended successfully!"
                message_type = "success"
            else:
                message = "This reservation cannot be ended early."
                message_type = "error"

            return request.render('hotel.reservation_detail_template', {
                'reservation': reservation,
                'message': message,
                'message_type': message_type
            })

        except Exception as e:
            return request.render('hotel.reservation_detail_template', {
                'reservation': reservation,
                'message': f"Error ending reservation: {str(e)}",
                'message_type': "error"
            })
