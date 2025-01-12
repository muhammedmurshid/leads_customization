{
    'name': 'Leads Customization',
    'version': '1.0.0',
    'summary': 'leads customization',
    'description': """
        A more detailed description of the module.
    """,
    'author': 'Murshid',
    'website': 'https://www.yourwebsite.com',
    'category': 'Specific Category',
    'license': 'LGPL-3',
    'depends': [
        'base',  # List of module dependencies
        'mail', 'crm', 'openeducat_admission',
        # Add other module dependencies here
    ],
    'data': [
        # 'security/ir.model.access.csv',  # Access rights
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/crm_fields.xml',
        'views/admission.xml',
        'views/connect.xml',
        'views/source.xml'

    ],


    'installable': True,
    'application': False,
    'auto_install': False,

}
