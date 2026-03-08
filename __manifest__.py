{
    'name': 'Visit Performance Tracker',
    'version': '1.0',
    'summary': 'Smart Visit Planning & Performance Tracking',
    'description': 'Tracks planned, actual, missed visits and productivity.',
    'author': 'Your Company',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/sequence.xml',
        'data/email_template.xml',
        'data/visit_cron.xml',
        'reports/visit_report.xml',         # <-- added
        'views/visit_plan_views.xml',
        'views/retailer_views.xml',
        'views/salesman_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/visit_plan_demo.xml',
    ],
    'installable': True,
    'application': True,
}