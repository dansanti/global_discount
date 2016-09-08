# -*- coding: utf-8 -*-
{
    "name": """Global Discount\
    """,
    'version': '9.0.0.0.1',
    'category': 'Accoun/invoice',
    'sequence': 12,
    'author':  'Daniel Santibáñez Polanco',
    'website': 'http://globalresponse.cl',
    'license': 'AGPL-3',
    'summary': '',
    'description': """
Make available a global discount.
===============================================================
""",
    'depends': [
        'account',
        'sale',
        ],
    'data': [
        #'security/ir.model.access.csv',
        'views/account_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
