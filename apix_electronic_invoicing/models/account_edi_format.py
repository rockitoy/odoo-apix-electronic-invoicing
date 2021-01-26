# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import api, models, fields, tools, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_repr
from odoo.tests.common import Form
from odoo.exceptions import UserError

from datetime import datetime
from lxml import etree
from PyPDF2 import PdfFileReader
import base64

import io
import pytz

import logging

_logger = logging.getLogger(__name__)


DEFAULT_FACTURX_DATE_FORMAT = '%Y%m%d'


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _is_compatible_with_journal(self, journal):
        self.ensure_one()
        res = super()._is_compatible_with_journal(journal)
        if self.code != 'facturx_1_0_06':
            return res
        return journal.type == 'sale'

    def _post_invoice_edi(self, invoices, test_mode=False):
        self.ensure_one()
        if self.code != 'facturx_1_0_06':
            return super()._post_invoice_edi(invoices, test_mode=test_mode)
        res = {}
        for invoice in invoices:
            attachment = self._export_facturx_apix(invoice)

            res[invoice] = {'attachment': attachment, 'error': "File not sent "}
            if self._context.get('edi_file_state', False):
                res[invoice]['error'] = "File not sent "
        return res

    def _is_embedding_to_invoice_pdf_needed(self):
        # OVERRIDE
        self.ensure_one()
        return True if self.code == 'facturx_1_0_06' else super()._is_embedding_to_invoice_pdf_needed()

    def _export_facturx_apix(self, invoice):

        def format_date(dt):
            # Format the date in the Factur-x standard.
            dt = dt or datetime.now()
            return dt.strftime(DEFAULT_FACTURX_DATE_FORMAT)

        def format_monetary(number, currency):
            # Format the monetary values to avoid trailing decimals (e.g. 90.85000000000001).
            return float_repr(number, currency.decimal_places)

        self.ensure_one()
        # Create file content.
        template_values = {
            'record': invoice,
            'format_date': format_date,
            'format_monetary': format_monetary,
            'invoice_line_values': [],
        }

        # Tax lines.
        aggregated_taxes_details = {line.tax_line_id.id: {
            'line': line,
            'tax_amount': -line.amount_currency if line.currency_id else -line.balance,
            'tax_base_amount': 0.0,
        } for line in invoice.line_ids.filtered('tax_line_id')}
        taxes = []
        taxes_amount_rate = []
        base_sum = 0
        tax_sum = 0

        # Invoice lines.
        for i, line in enumerate(invoice.invoice_line_ids.filtered(lambda l: not l.display_type)):
            price_unit_with_discount = line.price_unit * (1 - (line.discount / 100.0))
            taxes_res = line.tax_ids.with_context(force_sign=line.move_id._get_tax_force_sign()).compute_all(
                price_unit_with_discount,
                currency=line.currency_id,
                quantity=line.quantity,
                product=line.product_id,
                partner=invoice.partner_id,
                is_refund=line.move_id.move_type in ('in_refund', 'out_refund'),
            )

            line_template_values = {
                'line': line,
                'index': i + 1,
                'tax_details': [],
                'net_price_subtotal': taxes_res['total_excluded'],
            }

            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                line_template_values['tax_details'].append({
                    'tax': tax,
                    'tax_amount': tax_res['amount'],
                    'tax_base_amount': tax_res['base'],
                    'tax_rate': tax.amount
                })
                base_sum += tax_res['base']
                tax_sum += tax_res['amount']


                if tax.id in aggregated_taxes_details:
                    aggregated_taxes_details[tax.id]['tax_base_amount'] += tax_res['base']
                if tax not in taxes:
                    taxes.append(tax)
                    taxes_amount_rate.append(int(tax.amount))


            template_values['invoice_line_values'].append(line_template_values)

        template_values['tax_details'] = list(aggregated_taxes_details.values())
        if len(taxes_amount_rate) == 1:
            template_values['tax_amount_rate'] = taxes_amount_rate[0]
        elif len(taxes_amount_rate) > 1:
            template_values['tax_amount_rate'] = tuple(taxes_amount_rate)
        else:
            template_values['tax_amount_rate'] = 0.0
        template_values['total_base_amount'] = base_sum
        template_values['total_tax_amount'] = tax_sum
        date_time = datetime.now()
        normal_invoice_date = date_time.strftime("%Y-%m-%d %H:%M:%S")
        normal_invoice_date1 = datetime.strptime(normal_invoice_date, "%Y-%m-%d %H:%M:%S")
        inv_date_time = normal_invoice_date1.astimezone(pytz.timezone(self.env.user.tz)).isoformat()
        template_values['msg_time_stamp'] = inv_date_time
        # self.invoice_date_time = inv_date_time
        xml_content = b'<?xml version="1.0" encoding="UTF-8"?><!--Finvoice verkkolasku. Passeli XML-tiedosto. 2.8.2011-->'
        xml_content += b'<!DOCTYPE Finvoice SYSTEM "Finvoice.dtd">'
        xml_content += b'<?xml-stylesheet type="text/xsl" href="Finvoice.xsl"?>'
        xml_content += self.env.ref('apix_electronic_invoicing.apix_electronic_invoice_template')._render(template_values)
        xml_name = '%s_apix_invoicing.xml' % (invoice.name.replace('/', '_'))
        return self.env['ir.attachment'].create({
            'name': xml_name,
            'datas': base64.encodebytes(xml_content),
            'mimetype': 'application/xml'
        })
