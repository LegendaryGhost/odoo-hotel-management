from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
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

    @staticmethod
    def _authenticate_user():
        """Check if user is authenticated"""
        if request.env.user._is_public():
            return False, "Authentication required"
        return True, None

    # EQUIPMENT ENDPOINTS
    @http.route('/api/v1/equipment', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    def get_equipment(self):
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

    @http.route('/api/v1/equipment/<int:equipment_id>', type='http',
                auth='public', methods=['GET'], csrf=False, cors='*')
    def get_equipment_detail(self, equipment_id):
        """Get specific equipment details"""
        try:
            equipment = request.env['hotel.room.equipment'].sudo().browse(equipment_id)

            if not equipment.exists():
                return self._get_api_response(error="Equipment not found", status=404)

            data = {
                'id': equipment.id,
                'name': equipment.name,
                'additional_price': equipment.additional_price,
            }

            return self._get_api_response(data=data)

        except Exception as e:
            _logger.error(f"API Error in get_equipment_detail: {str(e)}")
            return self._get_api_response(error=str(e), status=400)

    # RESERVATION ENDPOINTS
    @http.route('/api/v1/reservations', type='json', auth='user',
                methods=['POST'], csrf=False, cors='*')
    def create_reservation(self):
        """Create a new reservation"""
        try:
            # Check authentication
            is_authenticated, auth_error = self._authenticate_user()
            if not is_authenticated:
                return self._get_api_response(error=auth_error, status=401)

            data = request.jsonrequest

            # Validate required fields
            required_fields = ['start_date', 'end_date', 'people_number', 'room_id']
            missing_fields = [field for field in required_fields if field not in data or data[field] is None]

            if missing_fields:
                return self._get_api_response(error=f"Missing required fields: {', '.join(missing_fields)}", status=400)

            # Parse and validate dates
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except ValueError:
                return self._get_api_response(error="Invalid date format. Use YYYY-MM-DD", status=400)

            # Validate people number
            if not isinstance(data['people_number'], int) or data['people_number'] <= 0:
                return self._get_api_response(error="People number must be a positive integer", status=400)

            # Validate room exists
            room = request.env['hotel.room'].browse(data['room_id'])
            if not room.exists():
                return self._get_api_response(error="Room not found", status=404)

            # Prepare reservation data
            reservation_vals = {
                'start_date': start_date,
                'end_date': end_date,
                'people_number': data['people_number'],
                'room_id': data['room_id'],
                'client_id': request.env.user.id,
            }

            # Handle equipment_ids (optional, empty by default)
            equipment_ids = data.get('equipment_ids', [])
            if equipment_ids:
                # Validate equipment exists
                equipment_records = request.env['hotel.room.equipment'].browse(equipment_ids)
                if len(equipment_records) != len(equipment_ids):
                    return self._get_api_response(error="One or more equipment items not found", status=404)
                reservation_vals['equipment_ids'] = [(6, 0, equipment_ids)]

            # Create reservation (this will trigger all model validations)
            reservation = request.env['hotel.room.reservation'].create(reservation_vals)

            return {
                'success': True,
                'data': {
                    'id': reservation.id,
                    'name': reservation.name,
                    'start_date': reservation.start_date.isoformat(),
                    'end_date': reservation.end_date.isoformat(),
                    'days_duration': reservation.days_duration,
                    'people_number': reservation.people_number,
                    'state': reservation.state,
                    'room': {
                        'id': reservation.room_id.id,
                        'name': reservation.room_id.name
                    },
                    'equipment': [{
                        'id': eq.id,
                        'name': eq.name,
                        'additional_price': eq.additional_price
                    } for eq in reservation.equipment_ids],
                    'pricing': {
                        'room_price': reservation.room_price,
                        'equipment_price': reservation.equipment_price,
                        'final_price': reservation.final_price
                    }
                }
            }

        except ValidationError as ve:
            _logger.error(f"Validation Error in create_reservation: {str(ve)}")
            return self._get_api_response(error=str(ve), status=400)
        except Exception as e:
            _logger.error(f"API Error in create_reservation: {str(e)}")
            return self._get_api_response(error=str(e), status=500)
