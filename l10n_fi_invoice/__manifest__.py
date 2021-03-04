# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) Avoin.Systems 2020

# noinspection PyStatementEffect
{
    "name": "Finnish Invoice",
    "version": "14.0.0.0.1",
    "author": "Avoin.Systems",
    "category": "Localization",
    "website": "https://avoin.systems",
    "license": "AGPL-3",
    "images": ["static/description/icon.png"],
    "depends": [
        "l10n_fi_invoice_delivery_date",
        "l10n_fi_bank_barcode",
    ],
    "data": [
        "views/account_move_templates.xml",
        "data/report_paperformat_data.xml", # Only after the template
        "views/account_journal_view.xml"
    ],
    "summary": "Suomalainen laskupohja",
    "active": False,
    "installable": True,
    "auto_install": False,
    "application": False
}
