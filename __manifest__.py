{
    'name': 'Visit Performance Tracker',
    'version': '1.0',
    'summary': 'Smart Visit Planning & Performance Tracking',
    'description': 'Tracks planned, actual, missed visits and productivity.',
    'author': 'Your Company',
    'depends': ['base', 'mail'],
    'data': [
    'views/visit_plan_views.xml',
    'views/retailer_views.xml',
    'views/salesman_views.xml',
    'views/menu_views.xml',
    'security/ir.model.access.csv',
    'data/sequence.xml',
    'data/visit_cron.xml',
],
    'demo': [
    'demo/visit_plan_demo.xml',
],
    'installable': True,
    'application': True,
}