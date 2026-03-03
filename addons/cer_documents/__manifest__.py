# -*- coding: utf-8 -*-
{
    "name": "CER Documents",
    "summary": "Plantillas y documentos CER (generación desde cotizaciones/ventas).",
    "version": "19.0.1.0.6",
    "license": "LGPL-3",
    "author": "CER",
    "website": "",
    "category": "Sales",
    "depends": [
        "cer_base",
        "cer_booking",
        "sale",
    ],
    "data": [
        # Security / data
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/cer_document_template_data.xml",

        # Views (actions first, menus last)
        "views/cer_document_template_views.xml",
        "views/cer_document_views.xml",
        "wizards/cer_document_create_wizard_views.xml",
        "views/sale_order_views.xml",
        "report/cer_document_report.xml",
        "views/cer_documents_menus.xml",
    ],
    "application": False,
    "installable": True,
}
