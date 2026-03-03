# -*- coding: utf-8 -*-
{
    "name": "CER Booking",
    "version": "19.0.1.0.4",
    "category": "Sales",
    "summary": "Reservas CER sobre sale.order con control de disponibilidad y PDF de comprobante.",
    "description": "Booking CER usando sale.order (cotización/venta) como documento único, con vistas de reservas (lista/calendario), control de disponibilidad por recurso y reporte PDF 'Comprobante de Reserva'.",
    "author": "CER",
    "license": "LGPL-3",
    "depends": ["sale", "product", "account", "cer_base", "cer_pricing"],
    "data": [
        "data/ir_sequence_data.xml",

        "security/ir.model.access.csv",

        "views/product_template_views.xml",
        "views/sale_order_views.xml",
        "views/cer_booking_views.xml",     # acciones/vistas primero
        "views/cer_booking_capacity_views.xml",
        "views/cer_unit_views.xml",
        "views/cer_booking_menus.xml",     # menús después (para evitar XMLID missing)
        "report/cer_booking_report.xml",
    ],
    "installable": True,
    "application": False,
}
