from odoo import models, fields, api

class VisitPlan(models.Model):
    _name = 'visit.plan'
    _description = 'Visit Plan'

    name = fields.Char(string="Visit Name", required=True)
    date = fields.Date(string="Visit Date")
    salesman_id = fields.Many2one('res.users', string="Salesperson")
    retailer_id = fields.Many2one('res.partner', string="Retailer")
    planned_time = fields.Float(string="Planned Time (hrs)")
    actual_time = fields.Float(string="Actual Time (hrs)")
    productivity_score = fields.Float(string="Productivity Score")
    is_productive = fields.Boolean(string="Is Productive")
    state = fields.Selection([
        ('draft','Draft'),
        ('done','Done'),
        ('missed','Missed'),
    ], default='draft', string="Status")

    visit_count = fields.Integer(string='Retailer Visits', compute='_compute_visit_count', store=True)

    @api.depends('retailer_id')
    def _compute_visit_count(self):
        for record in self:
            record.visit_count = self.env['visit.plan'].search_count([('retailer_id','=',record.retailer_id.id)])

    # Smart button action
    def action_view_retailer_visits(self):
        self.ensure_one()
        return {
            'name': f"Visits for {self.retailer_id.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'visit.plan',
            'view_mode': 'list,form',
            'domain': [('retailer_id','=',self.retailer_id.id)],
        }

    # Header buttons
    def action_mark_done(self):
        self.write({'state':'done'})

    def action_mark_missed(self):
        self.write({'state':'missed'})

    def action_reset_draft(self):
        self.write({'state':'draft'})