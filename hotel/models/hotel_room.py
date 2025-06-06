from odoo import models, fields

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'

    _sql_constraints = [
        ('positive_price', 'CHECK(base_price >= 0)', 'The room\'s base price must be positive')
    ]

    name = fields.Char(required=True)
    base_price = fields.Float(required=True)
    capacity = fields.Integer(required=True, default=2)

    category_id = fields.Many2one("hotel.room.category")
    equipment_ids = fields.Many2many("hotel.room.equipment")