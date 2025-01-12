from odoo import fields, models, api, _

class InheritSources(models.Model):
    _inherit = 'utm.source'

    source = fields.Selection([('inbound_source', 'Inbound Source'), ('outbound_source', 'Outbound Source')], string="Source")