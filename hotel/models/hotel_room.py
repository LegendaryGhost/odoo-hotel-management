from odoo import models, fields

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'

    name = fields.Char(required=True)
    base_price = fields.Float(required=True)
    capacity = fields.Integer(required=True, default=2)

    category_id = fields.Many2one("hotel.room.category")
    equipment_ids = fields.Many2many("hotel.room.equipment")