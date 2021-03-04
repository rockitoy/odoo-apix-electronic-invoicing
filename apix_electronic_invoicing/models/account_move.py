# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _
import base64
import zipfile, os
from os.path import basename
from hashlib import sha256
from odoo.exceptions import UserError
from datetime import datetime
import requests
import tempfile
import urllib.request
import re
from xml.dom.minidom import parseString
import xml.dom.minidom


# urllib.request.urlopen(url).read(1000)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _default_report_template_id(self):
        report = self.env.ref("l10n_fi_invoice.report_invoice_finnish")
        return self.env.ref("l10n_fi_invoice.report_invoice_finnish").id

    apix_report_template_id = fields.Many2one('ir.actions.report', string="PDF Report Template",
                                              default=_default_report_template_id)
    apix_sent_failed = fields.Boolean(string="Apix e-invoice send failed")
    send_invisible = fields.Boolean(string="Send Invisible", default=False)
    journal_type = fields.Selection([
            ('sale', 'Sales'),
            ('purchase', 'Purchase'),
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('general', 'Miscellaneous'),
        ], required=True, related='journal_id.type')

    def find_attachments(self):
        atts = self.env['ir.attachment'].search([('res_id', '=', self.id), ('res_model', '=', 'account.move'),
                                                 ('name', '!=', self.name.replace('/', '_') + ".pdf")])
        attachments = []
        if not atts:
            return [False, attachments]
        else:
            for attach in atts:
                attachments.append(attach)
            return [True, attachments]

    # @api.depends('edi_document_ids.error')
    # def _compute_edi_error_count(self):
    #     for move in self:
    #         res = super(AccountMove, self)._compute_edi_error_count()
    #         failed_docs = move.edi_document_ids.filtered(
    #             lambda d: d.error and (d.edi_format_id == self.env.ref('apix_electronic_invoicing.edi_facturx_1_0_06')))
    #         if failed_docs:
    #             move.apix_sent_failed = True
    #         else:
    #             move.apix_sent_failed = False
    #         return res

    def send_e_invoice(self):
        atts = self.env['ir.attachment'].search([('res_id', '=', self.id), ('res_model', '=', 'account.move')])
        inv_pdf = False
        other_atts = []
        to_remove = []
        if atts:
            for att in atts:
                if att.name == "%s.pdf" % self.name.replace('/', '_'):
                    inv_pdf = att
                else:
                    other_atts.append(att)
        if not inv_pdf:
            self.apix_report_template_id._render(self.id)
            inv_pdf = self.env['ir.attachment'].search(
                [('res_id', '=', self.id), ('res_model', '=', 'account.move'),
                 ('name', '=', self.name.replace('/', '_') + ".pdf")])
            if not inv_pdf:
                attachment = self.env['ir.attachment'].create({
                    'name': self.name.replace('/', '_') + ".pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(self.apix_report_template_id._render(self.id)[0]),
                    'store_fname': self.name.replace('/', '_') + ".pdf",
                    'res_model': 'account.move',
                    'res_id': self.id,
                    'mimetype': 'application/pdf'
                })
                inv_pdf = attachment

        # output = io.BytesIO()
        path = os.path.dirname(os.path.realpath(__file__))
        file_name = self.name.replace('/', '_')
        file_name_zip = file_name + ".zip"
        zipfilepath = os.path.join(path, file_name_zip)
        zip_archive = zipfile.ZipFile(zipfilepath, 'w')
        obj_name = self.name.replace('/', '') + ".pdf"
        filepath = os.path.join(path, obj_name)
        to_remove.append(filepath)
        object_handle = open(filepath, 'wb')
        object_handle.write(base64.b64decode(inv_pdf.datas))
        zip_archive.write(filepath, basename(filepath))
        # os.remove(filepath)
        format = self.env.ref("apix_electronic_invoicing.edi_facturx_1_0_06")
        if format:
            apix_xml = self.env['account.edi.document'].search(
                [('move_id', '=', self.id), ('edi_format_id', '=', format.id), (
                    'name', '=', self.name.replace('/', '_') + "_apix_invoicing.xml")])
            if apix_xml.attachment_id:
                xml_name = self.name.replace('/', '_') + "_apix_invoicing.xml"
                xmlpath = os.path.join(path, xml_name)
                to_remove.append(xmlpath)
                xml_handle = open(xmlpath, 'wb')
                xml_handle.write(base64.b64decode(apix_xml.attachment_id.datas))
                zip_archive.write(xmlpath, basename(xmlpath))
        if len(other_atts) >= 1:
            new_zip_name = self.name.replace('/', '_') + "_attachments"
            file_new_zip = new_zip_name + ".zip"
            newzipfilepath = os.path.join(path, file_new_zip)
            new_zip_archive = zipfile.ZipFile(newzipfilepath, 'w')
            to_remove.append(newzipfilepath)
            for vals in other_atts:
                atts_path = os.path.join(path, vals.name)
                to_remove.append(atts_path)
                object_handle = open(atts_path, 'wb')
                object_handle.write(base64.b64decode(vals.datas))
                new_zip_archive.write(atts_path, basename(atts_path))
            new_zip_archive.close()
            zip_archive.write(newzipfilepath, basename(newzipfilepath))

        zip_archive.close()
        if len(to_remove) >= 1:
            for vals in to_remove:
                os.remove(vals)
        path = os.path.dirname(os.path.realpath(__file__))
        file_name = self.name.replace('/', '_')
        file_name_zip = file_name + ".zip"
        zipfilepath = os.path.join(path, file_name_zip)
        if (zipfilepath.find('://') > 0):
            ret = urllib.request.urlopen(zipfilepath).read()
            return ret
        else:
            fp = open(zipfilepath, 'rb')
            try:
                ret = fp.read()
                temp2 = tempfile.mktemp()
                object_handle2 = open(temp2, 'wb')
                object_handle2.write(ret)
                timestamp = datetime.strftime(datetime.utcnow(), "%Y%m%d%H%M%S")
                if not self.company_id.apix_transfer_id or not self.company_id.apix_transfer_key:
                    raise UserError(_("Please configure Apix Transfer ID and Transfer Key in company settings."))

                key_dig = "Odoo" + "+" + "1.0" + "+" + self.company_id.apix_transfer_id + "+" + timestamp + "+" + self.company_id.apix_transfer_key
                key_digest = sha256(key_dig.encode('utf-8')).hexdigest()

                headers = {"Content-type": "application/octet-stream",
                           "Content-Length": str(len(ret)),
                           'Authorization': "SHA-256:" + key_digest}
                url = ""
                if self.company_id.apix_enviroment == 'prod':
                    url = "https://api.apix.fi/invoices?soft=%s&ver=%s&TraID=%s&t=%s&d=SHA-256:%s" % (
                        "Odoo", "1.0", self.company_id.apix_transfer_id, timestamp, key_digest)
                else:
                    url = "https://test-api.apix.fi/invoices?soft=%s&ver=%s&TraID=%s&t=%s&d=SHA-256:%s" % (
                        "Odoo", "1.0", self.company_id.apix_transfer_id, timestamp, key_digest)

                try:
                    res = requests.put(url, headers=headers, data=ret)

                    DOMTree = xml.dom.minidom.parseString(res.content.decode('utf-8'))

                    collection = DOMTree.documentElement
                    values = collection.getElementsByTagName('Status')

                    if values[0].firstChild.nodeValue == 'ERR':
                        document = self.edi_document_ids.filtered(
                            lambda doc: doc.edi_format_id == self.env.ref(
                                'apix_electronic_invoicing.edi_facturx_1_0_06'))
                        if document:
                            document.write({
                                'state': 'fail',
                                'error': res.content,

                            })
                            self.apix_sent_failed = True
                            self.send_invisible = True
                    if values[0].firstChild.nodeValue == 'OK':
                        document = self.edi_document_ids.filtered(
                            lambda doc: doc.edi_format_id == self.env.ref(
                                'apix_electronic_invoicing.edi_facturx_1_0_06'))
                        if document:
                            document.write({
                                'state': 'sent',
                                'success_msg': res.content,
                            })
                            self.apix_sent_failed = False
                            self.send_invisible = True
                            return ret
                except Exception as e:
                    raise UserError(_(e))

            finally:
                fp.close()
                os.remove(zipfilepath)

    def re_send_e_invoice(self):
        for move in self:
            edi_document_vals_list = []
            if move.journal_id.edi_format_ids:
                for edi_format in move.journal_id.edi_format_ids:
                    is_edi_needed = move.is_invoice(include_receipts=False) and edi_format._is_required_for_invoice(
                        move)

                    if is_edi_needed:
                        existing_edi_document = move.edi_document_ids.filtered(lambda x: x.edi_format_id == edi_format)
                        if existing_edi_document:
                            existing_edi_document.write({
                                'state': 'to_send',
                                'attachment_id': False,
                            })
                        else:
                            edi_document_vals_list.append({
                                'edi_format_id': edi_format.id,
                                'move_id': move.id,
                                'state': 'to_send',
                            })

            self.env['account.edi.document'].create(edi_document_vals_list)
            move.edi_document_ids._process_documents_no_web_services()
            move.send_e_invoice()

    def _post(self, soft=True):
        context = self._context.copy()
        context.update({'edi_file_state': 'new'})
        self.env.context = context
        return super(AccountMove, self)._post(soft=soft)
