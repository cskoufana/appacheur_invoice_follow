# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Appacheur Invoice Follow',
    'version' : '1.0',
    'summary': 'Custom account module for follow customer invoice',
    'sequence': 30,
    'description': """
    """,
    'category': 'Accounting',
    'website': 'https://www.appacheur.org/odoo',
    'depends' : ['account_invoicing'],
    'data': [
        'security/invoice_follow_security.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'report/account_invoice_report_view.xml',
        'data/account_invoice_data.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False
}
