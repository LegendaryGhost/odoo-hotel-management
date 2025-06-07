from odoo import models, fields

class HotelRoomEquipment(models.Model):
    _name = 'hotel.room.equipment'
    _description = 'Hotel Room Equipment'

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The room equipment\'s name must be unique'),
        ('positive_price', 'CHECK(additional_price >= 0)', 'The room equipment\'s additional price must be positive')
    ]

    name = fields.Char(required=True)
    additional_price = fields.Float(required=True)