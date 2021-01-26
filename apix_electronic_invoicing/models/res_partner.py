# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_registry = fields.Char(string="Company Registry")
    e_inv_addr = fields.Char(string="e-Invoicing Address")
    intermediator = fields.Char(string="Intermediator ID")

