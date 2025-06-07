# hotel_reservation_api/controllers/api.py
from odoo import http
from odoo.http import request
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class HotelReservationAPI(http.Controller):

    @staticmethod
    def _get_api_response(data=None, error=None, status=200):
        """Standardized API response format"""
        response = {
            'success': error is None,
            'timestamp': datetime.now().isoformat(),
        }
        if data is not None:
            response['data'] = data
        if error is not None:
            response['error'] = error

        return request.make_json_response(response, status=status)

    # EQUIPMENT ENDPOINTS
    @http.route('/api/v1/equipment', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    def get_equipment(self, **params):
        """Get all available equipment"""
        try:
            equipment_list = request.env['hotel.room.equipment'].sudo().search([])

            data = []
            for equipment in equipment_list:
                data.append({
                    'id': equipment.id,
                    'name': equipment.name,
                    'additional_price': equipment.additional_price,
                })

            return self._get_api_response(data=data)

        except Exception as e:
            _logger.error(f"API Error in get_equipment: {str(e)}")
            return self._get_api_response(error=str(e), status=400)
