from odoo import http
from odoo.http import request


class RoomsController(http.Controller):

    @http.route('/rooms', type='http', auth='public', website=True)
    def list_rooms(self, **kwargs):
        rooms = request.env['hotel.room'].sudo().search([])
        return request.render('hotel.rooms_page_template', {'rooms': rooms})
