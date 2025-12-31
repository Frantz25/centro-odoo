# -*- coding: utf-8 -*-
from odoo.tests.common import SavepointCase, tagged


ICP_VALIDITY_DAYS_KEY = "cer_base.quote_validity_days"
ICP_DEPOSIT_PERCENT_KEY = "cer_base.default_deposit_percent"


@tagged("post_install", "-at_install")
class TestCERBaseSettings(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env["ir.config_parameter"].sudo()
        cls.Company = cls.env["res.company"].sudo()

    def test_company_scoped_params_are_isolated(self):
        c1 = self.env.company
        c2 = self.Company.create({"name": "CER Test Company 2"})

        s1 = self.env["res.config.settings"].with_company(c1).create({
            "cer_default_deposit_percent": 25.0,
            "cer_quote_validity_days": 9,
        })
        s1.execute()

        self.assertEqual(float(self.ICP.get_param(f"{ICP_DEPOSIT_PERCENT_KEY}__company_{c1.id}")), 25.0)
        self.assertEqual(int(self.ICP.get_param(f"{ICP_VALIDITY_DAYS_KEY}__company_{c1.id}")), 9)

        s2 = self.env["res.config.settings"].with_company(c2).create({
            "cer_default_deposit_percent": 40.0,
            "cer_quote_validity_days": 5,
        })
        s2.execute()

        self.assertEqual(float(self.ICP.get_param(f"{ICP_DEPOSIT_PERCENT_KEY}__company_{c2.id}")), 40.0)
        self.assertEqual(int(self.ICP.get_param(f"{ICP_VALIDITY_DAYS_KEY}__company_{c2.id}")), 5)

        self.assertEqual(float(self.ICP.get_param(f"{ICP_DEPOSIT_PERCENT_KEY}__company_{c1.id}")), 25.0)
        self.assertEqual(int(self.ICP.get_param(f"{ICP_VALIDITY_DAYS_KEY}__company_{c1.id}")), 9)

    def test_global_policy_mandatory_param(self):
        s = self.env["res.config.settings"].create({
            "cer_policy_mandatory": True,
        })
        s.execute()
        self.assertEqual(self.ICP.get_param("cer_base.policy_mandatory"), "True")

