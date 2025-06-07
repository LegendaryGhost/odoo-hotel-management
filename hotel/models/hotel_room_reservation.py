from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HotelRoomReservation(models.Model):
    _name = 'hotel.room.reservation'
    _description = 'Hotel Room Reservation'

    _order = "start_date DESC"
    _sql_constraints = [
        ('positive_people_number', 'CHECK(people_number > 0)', 'The number of people must be strictly positive')
    ]

    name = fields.Char(compute='_compute_name', store=True)
    start_date = fields.Date(required=True, default=fields.Date.today())
    end_date = fields.Date(compute="_compute_end_date", inverse="_inverse_end_date", store=True)
    days_duration = fields.Integer(required=True, default=1, string="Duration (days)")
    people_number = fields.Integer(required=True, default=1, string="Number of people")

    room_price = fields.Float(related="room_id.final_price", string="Room Price")
    equipment_price = fields.Float(compute='_compute_equipment_price', string="Additional Equipment Price", default=0, store=True)
    final_price = fields.Float(compute='_compute_final_price', default=0, store=True)

    state = fields.Selection([
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('ended_early', 'Ended Early')
    ], default='active', string='Status', required=True)
    freeing_date = fields.Date(string='Early End Date', help='Date when the reservation was ended early')
    actual_end_date = fields.Date(compute='_compute_actual_end_date', store=True, string='Actual End Date')

    room_id = fields.Many2one("hotel.room", string="Reserved Room", required=True)
    equipment_ids = fields.Many2many("hotel.room.equipment", string="Additional Equipment")
    default_equipment_ids = fields.Many2many(related="room_id.equipment_ids")
    client_id = fields.Many2one("res.users", string="Client", required=True)

    def action_end_early(self):
        """Method to end reservation early"""
        self.ensure_one()
        if self.state == 'active':
            self.write({
                'state': 'ended_early',
                'freeing_date': fields.Date.today()
            })
            return True
        return False

    def can_be_ended_early(self):
        """Check if reservation can be ended early"""
        self.ensure_one()
        today = fields.Date.today()
        return (self.state == 'active' and
                self.start_date <= today < self.end_date)

    @api.depends('state', 'freeing_date', 'end_date')
    def _compute_actual_end_date(self):
        """Compute the actual end date considering early ending"""
        for record in self:
            if record.state == 'ended_early' and record.freeing_date:
                record.actual_end_date = record.freeing_date
            else:
                record.actual_end_date = record.end_date

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for reservation in self:
            if reservation.start_date and reservation.end_date:
                if reservation.start_date < fields.Date.today():
                    raise ValidationError("Start date must not be in the past")
                if reservation.end_date < reservation.start_date:
                    raise ValidationError("The end date cannot be before start date.")

    @api.constrains("room_id", "people_number")
    def _check_people_number(self):
        for reservation in self:
            if not reservation.room_id or not reservation.people_number:
                continue
            if reservation.people_number > reservation.room_id.capacity:
                raise ValidationError(f"The number of people cannot be greater than the room capacity ({reservation.room_id.capacity})")


    @api.constrains("room_id", "start_date", "end_date")
    def _check_overlapping_reservation(self):
        for reservation in self:
            if not reservation.room_id or not reservation.start_date or not reservation.end_date:
                continue  # Skip if essential fields are missing

            overlapping_reservations = self.env["hotel.room.reservation"].search(
                [
                    ('room_id', '=', reservation.room_id.id),
                    ('id', '!=', reservation.id),
                    ('start_date', '<', reservation.end_date),
                    ('actual_end_date', '>', reservation.start_date),
                    ('state', 'not in', ['cancelled']),
                ]
            )
            if overlapping_reservations:
                raise ValidationError(
                    f"The room {reservation.room_id.name} is already reserved from "
                    f"{overlapping_reservations[0].start_date.strftime('%d/%m/%Y')} to "
                    f"{overlapping_reservations[0].end_date.strftime('%d/%m/%Y')}."
                )

    @api.depends("start_date", "days_duration")
    def _compute_end_date(self):
        for reservation in self:
            if reservation.start_date:
                reservation.end_date = fields.Date.add(reservation.start_date, days=reservation.days_duration - 1)
            else:
                reservation.end_date = fields.Date.add(fields.Date.today(), days=reservation.days_duration - 1)

    def _inverse_end_date(self):
        for reservation in self:
            if reservation.start_date and reservation.end_date:
                reservation.days_duration = (reservation.end_date - reservation.start_date).days + 1
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

    @api.depends("room_price", "equipment_price", "days_duration")
    def _compute_final_price(self):
        for reservation in self:
            real_room_price = reservation.room_price if reservation.room_price else 0
            reservation.final_price = (real_room_price + reservation.equipment_price) * reservation.days_duration