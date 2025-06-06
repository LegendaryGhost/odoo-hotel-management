from odoo import models, fields

class HotelRoomCategory(models.Model):
    _name = 'hotel.room.category'
    _description = 'Hotel Room Category'

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The room category\'s name must be unique')
    ]

    name = fields.Char(required=True)
    additional_price = fields.Float(required=True)