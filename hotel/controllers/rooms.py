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

        # Search for available rooms
        rooms = request.env['hotel.room'].sudo().search([])

        return request.render('hotel.rooms_page_template', {
            'rooms': rooms,
            'start_date': start_date,
            'end_date': end_date
        })
