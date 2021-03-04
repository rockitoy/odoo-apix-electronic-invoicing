# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_code = fields.Char(string="Tax Code")
