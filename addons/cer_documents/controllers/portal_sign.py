# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class CERDocumentPortalSignController(http.Controller):

    def _get_doc_or_404(self, doc_id, access_token):
        doc = request.env["cer.document"].sudo().browse(int(doc_id)).exists()
        if not doc or not access_token or doc.portal_access_token != access_token:
            return None
        return doc

    @http.route(["/cer/document/<int:doc_id>/sign"], type="http", auth="public")
    def cer_document_sign_form(self, doc_id, access_token=None, **kwargs):
        doc = self._get_doc_or_404(doc_id, access_token)
        if not doc:
            return request.not_found()
        return request.render("cer_documents.portal_document_sign_form", {
            "doc": doc,
            "access_token": access_token,
            "error": kwargs.get("error"),
            "success": kwargs.get("success"),
        })

    @http.route(["/cer/document/<int:doc_id>/sign/submit"], type="http", auth="public", methods=["POST"])
    def cer_document_sign_submit(self, doc_id, access_token=None, signer_name=None, signature_file=None, **kwargs):
        doc = self._get_doc_or_404(doc_id, access_token)
        if not doc:
            return request.not_found()

        upload = signature_file or request.httprequest.files.get("signature_file")
        if not upload:
            return request.redirect(f"/cer/document/{doc_id}/sign?access_token={access_token}&error=no_file")

        file_bytes = upload.read()
        if not file_bytes:
            return request.redirect(f"/cer/document/{doc_id}/sign?access_token={access_token}&error=empty_file")

        doc.action_portal_sign(file_bytes=file_bytes, signer_name=signer_name)
        return request.redirect(f"/cer/document/{doc_id}/sign?access_token={access_token}&success=1")
