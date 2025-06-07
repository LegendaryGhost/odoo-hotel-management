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
            # Check if room has any overlapping reservations
            overlapping_reservations = request.env['hotel.room.reservation'].sudo().search([
                ('room_id', '=', room.id),
                ('start_date', '<', end_date_obj),
                ('end_date', '>', start_date_obj)
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