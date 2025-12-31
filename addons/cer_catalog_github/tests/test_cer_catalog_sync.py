# -*- coding: utf-8 -*-
from odoo.tests.common import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestCERCatalogSync(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.tax = cls.env["account.tax"].create({
            "name": "IVA 19",
            "amount": 19.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "company_id": cls.company.id,
        })
        cls.company.cer_catalog_default_sale_tax_id = cls.tax

        cls.source = cls.env["cer.catalog.source"].create({
            "name": "Test Source",
            "company_id": cls.company.id,
            "mode": "install",
            "source_type": "local",
            "active": True,
        })

    def test_sync_from_bytes_creates_product(self):
        csv_data = (
            "default_code,name,type,list_price,tax,categ,uom,active,charge_mode,min_people\n"
            "R001,Habitación Test,service,100,IVA 19,CER/Habitaciones,Units,1,room_person_night,0\n"
        ).encode("utf-8")

        svc = self.env["cer.catalog.service"].with_company(self.company).sudo()
        log = svc._run_sync(self.source, csv_data, initiated_by="test", filename="t.csv", url="local")

        self.assertEqual(log.state, "success")
        prod = self.env["product.product"].search([("default_code", "=", "R001")], limit=1)
        self.assertTrue(prod)
        self.assertEqual(prod.product_tmpl_id.cer_charge_mode, "room_person_night")
