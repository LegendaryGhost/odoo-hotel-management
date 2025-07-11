from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from datetime import datetime
import logging
import json

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

    # ROOM ENDPOINTS
    @http.route('/api/v1/rooms/available', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    def get_available_rooms(self, start_date=None, end_date=None):
        """Get available rooms between two dates"""
        try:
            # Validate required parameters
            if not start_date or not end_date:
                return self._get_api_response(
                    error="Missing required parameters: start_date and end_date",
                    status=400
                )

            # Parse and validate dates
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return self._get_api_response(
                    error="Invalid date format. Use YYYY-MM-DD",
                    status=400
                )

            # Validate date logic
            if start_date_obj >= end_date_obj:
                return self._get_api_response(
                    error="End date must be after start date",
                    status=400
                )

            # Call the existing model method
            room_model = request.env['hotel.room']
            available_rooms = room_model.get_available_rooms(start_date_obj, end_date_obj)

            # Format response data
            data = []
            for room in available_rooms:
                data.append({
                    'id': room.id,
                    'name': room.name,
                    'base_price': room.base_price,
                    'capacity': room.capacity,
                    'category_price': room.category_price,
                    'equipment_price': room.equipment_price,
                    'final_price': room.final_price,
                    'category': {
                        'id': room.category_id.id,
                        'name': room.category_id.name
                    } if room.category_id else None,
                    'equipment': [{
                        'id': eq.id,
                        'name': eq.name,
                        'additional_price': eq.additional_price
                    } for eq in room.equipment_ids]
                })

            return self._get_api_response(data={
                'rooms': data,
                'count': len(data),
                'search_period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            })

        except Exception as e:
            _logger.error(f"API Error in get_available_rooms: {str(e)}")
            return self._get_api_response(error=str(e), status=500)

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
    @http.route('/api/v1/reservations', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    def get_user_reservations(self, state=None, limit=None, offset=None):
        """Get current user's reservations"""
        try:
            # Check authentication
            is_authenticated, auth_error = self._authenticate_user()
            if not is_authenticated:
                return self._get_api_response(error=auth_error, status=401)

            # Build search domain
            domain = [('client_id', '=', request.env.user.id)]

            # Add state filter if provided
            if state:
                valid_states = ['draft', 'confirmed', 'in_progress', 'ended', 'ended_early', 'cancelled']
                if state not in valid_states:
                    return self._get_api_response(
                        error=f"Invalid state. Valid states: {', '.join(valid_states)}",
                        status=400
                    )
                domain.append(('state', '=', state))

            # Parse pagination parameters
            try:
                limit_int = int(limit) if limit else None
                offset_int = int(offset) if offset else 0

                if limit_int is not None and limit_int <= 0:
                    return self._get_api_response(error="Limit must be a positive integer", status=400)
                if offset_int < 0:
                    return self._get_api_response(error="Offset must be a non-negative integer", status=400)

            except ValueError:
                return self._get_api_response(error="Invalid limit or offset format", status=400)

            # Get reservations with pagination
            reservations = request.env['hotel.room.reservation'].sudo().search(
                domain,
                limit=limit_int,
                offset=offset_int,
                order='start_date desc'
            )

            # Get total count for pagination info
            total_count = request.env['hotel.room.reservation'].sudo().search_count(domain)

            # Format response data
            data = []
            for reservation in reservations:
                data.append({
                    'id': reservation.id,
                    'name': reservation.name,
                    'start_date': reservation.start_date.isoformat(),
                    'end_date': reservation.end_date.isoformat(),
                    'actual_end_date': reservation.actual_end_date.isoformat() if reservation.actual_end_date else None,
                    'days_duration': reservation.days_duration,
                    'people_number': reservation.people_number,
                    'state': reservation.state,
                    'room': {
                        'id': reservation.room_id.id,
                        'name': reservation.room_id.name,
                        'capacity': reservation.room_id.capacity
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
                    },
                    'can_be_ended_early': reservation.can_be_ended_early() if hasattr(reservation,
                                                                                      'can_be_ended_early') else False
                })

            return self._get_api_response(data={
                'reservations': data,
                'count': len(data),
                'total_count': total_count,
                'pagination': {
                    'limit': limit_int,
                    'offset': offset_int,
                    'has_next': (offset_int + len(data)) < total_count if limit_int else False
                }
            })

        except Exception as e:
            _logger.error(f"API Error in get_user_reservations: {str(e)}")
            return self._get_api_response(error=str(e), status=500)

    @http.route('/api/v1/reservations/<int:reservation_id>/end', type='http', auth='public',
                methods=['POST'], csrf=False, cors='*')
    def end_reservation_early(self, reservation_id):
        """End a reservation early to free up the room"""
        try:
            # Check authentication
            is_authenticated, auth_error = self._authenticate_user()
            if not is_authenticated:
                return self._get_api_response(error=auth_error, status=401)

            # Get the reservation and verify it belongs to current user
            reservation = request.env['hotel.room.reservation'].sudo().search([
                ('id', '=', reservation_id),
                ('client_id', '=', request.env.user.id)
            ])

            if not reservation:
                return self._get_api_response(
                    error="Reservation not found or you don't have permission to access it",
                    status=404
                )

            # Check if reservation can be ended early
            if not reservation.can_be_ended_early():
                return self._get_api_response(
                    error=f"This reservation cannot be ended early because it has not started yet or it has already ended. It can only be ended earlier between {reservation.start_date.strftime('%d/%m/%Y')} and {reservation.end_date.strftime('%d/%m/%Y')}",
                    status=400
                )

            # End the reservation early
            reservation.action_end_early()

            # Return updated reservation data
            return self._get_api_response(data={
                'id': reservation.id,
                'name': reservation.name,
                'start_date': reservation.start_date.isoformat(),
                'end_date': reservation.end_date.isoformat(),
                'actual_end_date': reservation.actual_end_date.isoformat() if reservation.actual_end_date else None,
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
                },
                'message': 'Reservation ended successfully! Room is now available.'
            })

        except Exception as e:
            _logger.error(f"API Error in end_reservation_early: {str(e)}")
            return self._get_api_response(error=str(e), status=500)

    @http.route('/api/v1/reservations', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_reservation(self):
        """Create a new reservation"""
        try:
            # Check authentication
            is_authenticated, auth_error = self._authenticate_user()
            if not is_authenticated:
                return self._get_api_response(error=auth_error, status=401)

            # Parse JSON data from request body
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                return self._get_api_response(error="Invalid JSON data", status=400)

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
            reservation = request.env['hotel.room.reservation'].sudo().create(reservation_vals)

            return self._get_api_response(data={
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
            })

        except ValidationError as ve:
            _logger.error(f"Validation Error in create_reservation: {str(ve)}")
            return self._get_api_response(error=str(ve), status=400)
        except Exception as e:
            _logger.error(f"API Error in create_reservation: {str(e)}")
            return self._get_api_response(error=str(e), status=500)
