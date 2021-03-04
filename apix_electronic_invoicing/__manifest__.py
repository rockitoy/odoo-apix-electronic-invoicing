# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Apix Electronic Invoicing',
    'version': '14.0.1.3',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Electronic Invoicing Format for APIX',
    'description': """
       Electronic Invoicing Format for APIX.
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['account', 'account_edi', 'sale', 'l10n_fi_invoice'],
    'data': [
        'data/account_edi_data.xml',
        'data/apix_invoice_template.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/account_tax_view.xml'
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
