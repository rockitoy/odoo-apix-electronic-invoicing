# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class AccountEdiDocument(models.Model):
    _inherit = 'account.edi.document'

    state = fields.Selection(selection_add=[('fail', 'Failed')])
    success_msg = fields.Text(string="Message Content")


    def write(self, vals):
        if 'error' in vals:
            if vals['error'] == 'File not sent ':
                vals['error'] = ''
        return super(AccountEdiDocument, self).write(vals)
