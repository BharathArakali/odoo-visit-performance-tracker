{
    'name': 'Visit Performance Tracker',
    'version': '1.0',
    'summary': 'Smart Visit Planning & Performance Tracking',
    'description': 'Tracks planned, actual, missed visits and productivity.',
    'author': 'Your Company',
    'depends': ['base', 'mail'],
    'data': [
    'security/ir.model.access.csv',
    'data/sequence.xml',
    'views/visit_plan_views.xml',
],
    'installable': True,
    'application': True,
}