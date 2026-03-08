import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date

class VisitPlan(models.Model):
    _name = 'visit.plan'
    _description = 'Visit Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']   # <-- added for chatter

    name = fields.Char(string="Visit Reference", required=True, copy=False, default='New')
    date = fields.Date(tracking=True)
    salesman_id = fields.Many2one('res.users', string="Salesperson", tracking=True)
    retailer_id = fields.Many2one('res.partner', string="Retailer", tracking=True)
    manager_email = fields.Char(string="Manager Email")

    planned_time = fields.Float(string="Planned Time")
    actual_time = fields.Float(string="Actual Time")

    productivity_score = fields.Float(string="Productivity Score", compute="_compute_productivity", store=True)
    is_productive = fields.Boolean(string="Is Productive", compute="_compute_productivity", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('missed', 'Missed')
    ], default='draft', tracking=True)

    def action_send_missed_visit_email(self):

        today = date.today()

        missed_visits = self.search([
            ('visit_date', '<', today),
            ('state', '!=', 'done')
        ])

        template = self.env.ref('visit_plan.email_template_missed_visit_summary')

        for visit in missed_visits:
            template.send_mail(visit.id, force_send=True)

    def cron_mark_missed_visits(self):
        _logger.info("Cron job started: Checking for missed visits")

        visits = self.search([
            ('state', '=', 'draft'),
            ('date', '<', fields.Date.today())
        ])

        _logger.info("Found %s visits to mark as missed: %s", len(visits), visits.ids)

        visits.write({'state': 'missed'})

        _logger.info("Cron completed: Missed visits updated")

    visit_count = fields.Integer(string="Retailer Visits", compute="_compute_visit_count")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('visit.plan') or 'New'
        return super().create(vals_list)

    @api.depends('planned_time', 'actual_time')
    def _compute_productivity(self):
        for rec in self:
            if rec.planned_time:
                rec.productivity_score = (rec.actual_time / rec.planned_time) * 100
            else:
                rec.productivity_score = 0

            rec.is_productive = rec.productivity_score >= 70

    def action_mark_done(self):
        for rec in self:
            rec.state = 'done'

            if rec.productivity_score < 70:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Underperforming Visit',
                        'message': f'Productivity is only {round(rec.productivity_score,2)}%. Please review the visit.',
                        'type': 'warning',
                        'sticky': False,
                    }
                }

    def action_mark_missed(self):
        for rec in self:
            rec.state = 'missed'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def _compute_visit_count(self):
        for rec in self:
            rec.visit_count = self.search_count([
                ('retailer_id', '=', rec.retailer_id.id)
            ])

    def action_view_retailer_visits(self):
        self.ensure_one()

        return {
            'name': 'Retailer Visits',
            'type': 'ir.actions.act_window',
            'res_model': 'visit.plan',
            'view_mode': 'list,form',
            'domain': [('retailer_id', '=', self.retailer_id.id)],
            'context': {'create': False},
        }

