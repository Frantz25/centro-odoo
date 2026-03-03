# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import timedelta

from odoo import api, fields, models, _

ICP_REMINDER_DAYS_KEY = "cer_communications.validity_reminder_days"
ICP_PRECHECKIN_HOURS_KEY = "cer_communications.precheckin_hours"


class CERCommunicationService(models.AbstractModel):
    _name = "cer.communication.service"
    _description = "CER - Servicio de comunicación"

    @api.model
    def _scoped_key(self, key: str, company_id: int) -> str:
        return f"{key}__company_{company_id}"

    @api.model
    def _get_param(self, key: str, default=None, *, company=None):
        company = company or self.env.company
        icp = self.env["ir.config_parameter"].sudo()
        scoped = icp.get_param(self._scoped_key(key, company.id), default=None)
        if scoped not in (None, ""):
            return scoped
        return icp.get_param(key, default)

    @api.model
    def _resolve_recipients(self, rule, record):
        partner_ids = set()
        emails = set()

        if rule.recipient_mode == "customer":
            partner = getattr(record, "partner_id", False)
            if partner:
                partner_ids.add(partner.id)
                if partner.email:
                    emails.add(partner.email)

        elif rule.recipient_mode == "salesperson":
            user = getattr(record, "user_id", False)
            partner = user.partner_id if user else False
            if partner:
                partner_ids.add(partner.id)
                if partner.email:
                    emails.add(partner.email)

        elif rule.recipient_mode == "followers":
            followers = getattr(record, "message_follower_ids", self.env["mail.followers"])
            for fol in followers:
                p = fol.partner_id
                if p:
                    partner_ids.add(p.id)
                    if p.email:
                        emails.add(p.email)

        elif rule.recipient_mode == "company":
            comp = getattr(record, "company_id", False) or rule.company_id
            if comp and comp.email:
                emails.add(comp.email)

        elif rule.recipient_mode == "custom":
            raw = (rule.custom_emails or "")
            for e in [x.strip() for x in raw.split(",") if x.strip()]:
                emails.add(e)

        for p in rule.extra_partner_ids:
            partner_ids.add(p.id)
            if p.email:
                emails.add(p.email)

        return sorted(partner_ids), ", ".join(sorted(emails))

    @api.model
    def trigger(self, event_code: str, records):
        if not records:
            return True

        Rule = self.env["cer.communication.rule"]

        # Agrupa por compañía + modelo (multi-company safe)
        buckets = {}
        for rec in records:
            company = getattr(rec, "company_id", False) or self.env.company
            buckets.setdefault((company.id, rec._name), []).append(rec)

        for (company_id, model_name), recs in buckets.items():
            rules = Rule.search(
                [
                    ("active", "=", True),
                    ("company_id", "=", company_id),
                    ("event_code", "=", event_code),
                    ("model_id.model", "=", model_name),
                ],
                order="sequence asc, id asc",
            )
            if not rules:
                continue
            for rec in recs:
                for rule in rules:
                    self._apply_rule(rule, rec)

        return True

    @api.model
    def _apply_rule(self, rule, record):
        template = rule.template_id
        if not template:
            return True

        partner_ids, email_to = self._resolve_recipients(rule, record)

        subject_map = template._render_field("subject", [record.id], compute_lang=True)
        body_map = template._render_field("body_html", [record.id], compute_lang=True)
        subject = subject_map.get(record.id) or template.subject or ""
        body_html = body_map.get(record.id) or template.body_html or ""

        if rule.channel_chatter and hasattr(record, "message_post"):
            record.message_post(
                body=body_html,
                subject=subject,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

        if rule.channel_email:
            if not (partner_ids or email_to):
                return True

            email_values = {}
            if email_to:
                email_values["email_to"] = email_to
            if partner_ids:
                email_values["recipient_ids"] = [(6, 0, partner_ids)]

            template.send_mail(record.id, force_send=bool(rule.force_send), email_values=email_values)

        return True

    @api.model
    def cron_send_validity_reminders(self):
        SaleOrder = self.env["sale.order"]
        today = fields.Date.context_today(self)

        company = self.env.company
        days = int(self._get_param(ICP_REMINDER_DAYS_KEY, 2, company=company) or 2)
        target = today + timedelta(days=days)

        orders = SaleOrder.search(
            [
                ("company_id", "=", company.id),
                ("state", "=", "sent"),
                ("validity_date", "=", target),
            ]
        )
        return self.trigger("sale_validity_reminder", orders)

    @api.model
    def cron_send_precheckin_reminders(self):
        SaleOrder = self.env["sale.order"]
        today = fields.Date.context_today(self)

        company = self.env.company
        # por ahora operamos por día (24h = 1 día), extensible a horas después
        hours = int(self._get_param(ICP_PRECHECKIN_HOURS_KEY, 24, company=company) or 24)
        days_before = 1 if hours <= 24 else max(1, round(hours / 24))
        target_date = today + timedelta(days=days_before)

        orders = SaleOrder.search(
            [
                ("company_id", "=", company.id),
                ("cer_is_booking", "=", True),
                ("cer_booking_state", "=", "confirmed"),
                ("cer_date_from", "=", target_date),
            ]
        )
        return self.trigger("pre_checkin_reminder", orders)
