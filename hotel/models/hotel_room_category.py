from odoo import models, fields

class HotelRoomCategory(models.Model):
    _name = 'hotel.room.category'
    _description = 'Hotel Room Category'

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The room category\'s name must be unique'),
        ('positive_price', 'CHECK(additional_price >= 0)', 'The room category\'s additional price must be positive')
    ]

    name = fields.Char(required=True)
    additional_price = fields.Float(required=True)