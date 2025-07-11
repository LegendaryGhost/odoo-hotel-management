{
    'name': "Hotel Managemenent System",
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

        'templates/website_menus.xml',
        'templates/available_rooms.xml',
        'templates/booking_form.xml',
        'templates/my_reservations.xml',
        'templates/reservation_detail.xml',
    ]
}