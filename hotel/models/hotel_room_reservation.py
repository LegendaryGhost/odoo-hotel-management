from odoo import fields, models, api


class HotelRoomReservation(models.Model):
    _name = 'hotel.room.reservation'
    _description = 'Hotel Room Reservation'

    name = fields.Char(compute='_compute_name', store=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    people_number = fields.Integer(required=True, default=1, string="Number of people")

    room_id = fields.Many2one("hotel.room", string="Reserved Room")
    equipment_ids = fields.Many2many("hotel.room.equipment", string="Additional Equipment")
    default_equipment_ids = fields.Many2many(related="room_id.equipment_ids")
    client_id = fields.Many2one("res.users", string="Client")

    @api.depends("room_id", "start_date", "end_date")
    def _compute_name(self):
        for record in self:
            room_name = record.room_id.name if record.room_id else "Unknown Room"
            start = record.start_date.strftime('%Y-%m-%d') if record.start_date else "Unknown Start"
            end = record.end_date.strftime('%Y-%m-%d') if record.end_date else "Unknown End"
            record.name = f"{room_name} ({start} to {end})"