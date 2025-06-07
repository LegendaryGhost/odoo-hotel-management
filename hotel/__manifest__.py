{
    'name': "Hotel",
    'version': '1.0',
    'depends': ['base', 'website'],
    'author': "Tiarintsoa",
    'description': "An app module to manage the rooms in an hotel",
    'category': "Hotel Management",
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        # 'security/groups.xml',

        'data/hotel_room_data.xml',

        'demo/hotel_room_demo.xml',
        'demo/hotel_room_reservation_demo.xml',

        'views/hotel_room_views.xml',
        'views/hotel_room_category_views.xml',
        'views/hotel_room_equipment_views.xml',
        'views/hotel_room_reservation_views.xml',
        'views/hotel_menus.xml',

        'views/rooms_template.xml',
        'views/booking_template.xml',
    ]
}