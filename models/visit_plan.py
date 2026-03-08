import logging
import urllib.parse
_logger = logging.getLogger(__name__)

from odoo import models, fields, api
from datetime import date, timedelta


class VisitPlan(models.Model):
    _name = 'visit.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Visit Plan'

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
                        'message': f'Productivity is only {round(rec.productivity_score, 2)}%. Please review the visit.',
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

    # ------------------------------------------------
    # Button: Send Missed Visit Email (manual trigger)
    # ------------------------------------------------
    def action_send_missed_visit_email(self):
        today = date.today()
        missed_visits = self.search([
            ('date', '<', today),
            ('state', '!=', 'done')
        ])
        template = self.env.ref('visit_performance_tracker.email_template_missed_visit_summary')
        for visit in missed_visits:
            template.send_mail(visit.id, force_send=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Missed Visits Email',
                'message': f'{len(missed_visits)} missed visit emails sent!',
                'type': 'success',
                'sticky': False,
            }
        }

    # ------------------------------------------------
    # Cron: Runs daily at 11:59 PM
    # ------------------------------------------------
    def cron_mark_missed_visits(self):
        _logger.info("=== Cron Job Started: Checking for missed visits ===")
        today = fields.Date.today()

        visits = self.search([
            ('state', '=', 'draft'),
            ('date', '<', today)
        ])

        _logger.info("Found %s visit(s) to mark as missed: %s", len(visits), visits.mapped('name'))
        visits.write({'state': 'missed'})
        _logger.info("Successfully marked %s visit(s) as missed.", len(visits))

        if visits:
            try:
                template = self.env.ref('visit_performance_tracker.email_template_missed_visit_summary')
                for visit in visits:
                    template.send_mail(visit.id, force_send=True)
                _logger.info("Summary email sent for %s missed visit(s).", len(visits))
            except Exception as e:
                _logger.error("Failed to send missed visit email: %s", str(e))

        _logger.info("=== Cron Job Completed ===")

    # ------------------------------------------------
    # Google Calendar Link Generator
    # ------------------------------------------------
    def action_add_to_google_calendar(self):
        self.ensure_one()

        # Build event details
        title = f"Visit: {self.name}"
        if self.retailer_id:
            title += f" - {self.retailer_id.name}"

        description = (
            f"Visit Reference: {self.name}\n"
            f"Salesperson: {self.salesman_id.name if self.salesman_id else 'N/A'}\n"
            f"Retailer: {self.retailer_id.name if self.retailer_id else 'N/A'}\n"
            f"Planned Duration: {self.planned_time} hrs\n"
            f"Productivity Score: {round(self.productivity_score, 2)}%"
        )

        # Format dates for Google Calendar (YYYYMMDD)
        if self.date:
            start_date = self.date.strftime('%Y%m%d')
            # End date = next day (Google Calendar all-day event)
            end_date = (self.date + timedelta(days=1)).strftime('%Y%m%d')
        else:
            from datetime import datetime
            start_date = datetime.now().strftime('%Y%m%d')
            end_date = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')

        # Build Google Calendar URL
        params = urllib.parse.urlencode({
            'action': 'TEMPLATE',
            'text': title,
            'dates': f"{start_date}/{end_date}",
            'details': description,
            'location': self.retailer_id.name if self.retailer_id else '',
        })

        google_calendar_url = f"https://calendar.google.com/calendar/render?{params}"

        # Open URL in new browser tab
        return {
            'type': 'ir.actions.act_url',
            'url': google_calendar_url,
            'target': 'new',
        }


# ------------------------------------------------
# Extend res.users for Salesman smart button
# ------------------------------------------------
class ResUsers(models.Model):
    _inherit = 'res.users'

    salesman_visit_count = fields.Integer(
        string="Visit Count",
        compute="_compute_salesman_visit_count"
    )

    def _compute_salesman_visit_count(self):
        for user in self:
            user.salesman_visit_count = self.env['visit.plan'].search_count([
                ('salesman_id', '=', user.id)
            ])

    def action_view_salesman_visits(self):
        self.ensure_one()
        return {
            'name': 'Visits',
            'type': 'ir.actions.act_window',
            'res_model': 'visit.plan',
            'view_mode': 'list,form',
            'domain': [('salesman_id', '=', self.id)],
            'context': {'default_salesman_id': self.id},
        }


# ------------------------------------------------
# Extend res.partner for Retailer smart button
# ------------------------------------------------
class ResPartner(models.Model):
    _inherit = 'res.partner'

    retailer_visit_count = fields.Integer(
        string="Visit Count",
        compute="_compute_retailer_visit_count"
    )

    def _compute_retailer_visit_count(self):
        for partner in self:
            partner.retailer_visit_count = self.env['visit.plan'].search_count([
                ('retailer_id', '=', partner.id)
            ])

    def action_view_retailer_visits(self):
        self.ensure_one()
        return {
            'name': 'Visits',
            'type': 'ir.actions.act_window',
            'res_model': 'visit.plan',
            'view_mode': 'list,form',
            'domain': [('retailer_id', '=', self.id)],
            'context': {'default_retailer_id': self.id},
        }