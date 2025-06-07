from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HotelRoomReservation(models.Model):
    _name = 'hotel.room.reservation'
    _description = 'Hotel Room Reservation'

    name = fields.Char(compute='_compute_name', store=True)
    start_date = fields.Date(required=True, default=fields.Date.today())
    end_date = fields.Date(compute="_compute_end_date", inverse="_inverse_end_date", store=True)
    days_duration = fields.Integer(required=True, default=1, string="Duration (days)")
    people_number = fields.Integer(required=True, default=1, string="Number of people")

    room_price = fields.Float(related="room_id.final_price", string="Room Price")
    equipment_price = fields.Float(compute='_compute_equipment_price', string="Additional Equipment Price", default=0, store=True)

    room_id = fields.Many2one("hotel.room", string="Reserved Room")
    equipment_ids = fields.Many2many("hotel.room.equipment", string="Additional Equipment")
    default_equipment_ids = fields.Many2many(related="room_id.equipment_ids")
    client_id = fields.Many2one("res.users", string="Client")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for reservation in self:
            if reservation.start_date and reservation.end_date:
                if reservation.end_date < reservation.start_date:
                    raise ValidationError("The end date cannot be before start date.")

    @api.depends("start_date", "days_duration")
    def _compute_end_date(self):
        for reservation in self:
            if reservation.start_date:
                reservation.end_date = fields.Date.add(reservation.start_date, days=reservation.days_duration)
            else:
                reservation.end_date = fields.Date.add(fields.Date.today(), days=reservation.days_duration)

    def _inverse_end_date(self):
        for reservation in self:
            if reservation.start_date and reservation.end_date:
                reservation.days_duration = (reservation.end_date - reservation.start_date).days
            else:
                reservation.days_duration = 0

    @api.depends("room_id", "start_date", "end_date")
    def _compute_name(self):
        for record in self:
            room_name = record.room_id.name if record.room_id else "Unknown Room"
            start = record.start_date.strftime('%Y-%m-%d') if record.start_date else "Unknown Start"
            end = record.end_date.strftime('%Y-%m-%d') if record.end_date else "Unknown End"
            record.name = f"{room_name} ({start} to {end})"

    @api.depends("equipment_ids")
    def _compute_equipment_price(self):
        for reservation in self:
            equipment_price = 0
            if reservation.equipment_ids:
                equipment_price = sum(reservation.equipment_ids.mapped("additional_price"))
            reservation.equipment_price = equipment_price