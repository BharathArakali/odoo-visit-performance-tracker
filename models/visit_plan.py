from odoo import models, fields, api


class VisitPlan(models.Model):
    _name = "visit.plan"
    _description = "Visit Plan"
    _rec_name = "name"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        default="New"
    )

    date = fields.Date(
        string="Visit Date",
        required=True
    )

    salesman_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        required=True,
        default=lambda self: self.env.user
    )

    retailer_id = fields.Many2one(
        "res.partner",
        string="Retailer",
        required=True,
    )

    planned_time = fields.Float(
        string="Planned Duration (Hours)"
    )

    actual_time = fields.Float(
        string="Actual Duration (Hours)"
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
            ("missed", "Missed"),
        ],
        string="Status",
        default="draft",
        tracking=True
    )

    is_productive = fields.Boolean(
        string="Is Productive",
        compute="_compute_productivity",
        store=True
    )

    productivity_score = fields.Float(
        string="Productivity (%)",
        compute="_compute_productivity",
        store=True
    )

    @api.depends("planned_time", "actual_time")
    def _compute_productivity(self):
        for rec in self:
            if rec.planned_time > 0:
                rec.productivity_score = (rec.actual_time / rec.planned_time) * 100
                rec.is_productive = rec.actual_time >= rec.planned_time
            else:
                rec.productivity_score = 0.0
                rec.is_productive = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('visit.plan') or 'New'
        return super().create(vals_list)

    def action_mark_done(self):
        for rec in self:
            rec.state = 'done'

    def action_mark_missed(self):
        for rec in self:
            rec.state = 'missed'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'