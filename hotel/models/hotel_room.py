from odoo import models, fields, api

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'

    _sql_constraints = [
        ('positive_price', 'CHECK(base_price >= 0)', 'The room\'s base price must be positive')
    ]

    name = fields.Char(required=True)
    base_price = fields.Float(required=True)
    capacity = fields.Integer(required=True, default=2)
    category_price = fields.Float(related="category_id.additional_price", default=0, store=True, string="Category Price")
    equipment_price = fields.Float(compute='_compute_equipment_price', default=0, store=True)
    final_price = fields.Float(compute="_compute_final_price", default=0, store=True)

    category_id = fields.Many2one("hotel.room.category")
    equipment_ids = fields.Many2many("hotel.room.equipment", string="Default Equipment")
    reservation_ids = fields.One2many("hotel.room.reservation", "room_id", string="Reservations")

    @api.depends("equipment_ids")
    def _compute_equipment_price(self):
        for room in self:
            equipment_price = 0
            if room.equipment_ids:
                equipment_price = sum(room.equipment_ids.mapped("additional_price"))
            room.equipment_price = equipment_price

    @api.depends("base_price", "category_price", "equipment_price")
    def _compute_final_price(self):
        for room in self:
            real_category_price = 0
            real_equipment_price = 0
            if room.category_price:
                real_category_price = room.category_price

            if room.equipment_price:
                real_equipment_price = room.equipment_price

            room.final_price = room.base_price + real_category_price + real_equipment_price