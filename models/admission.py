from odoo import fields, models, api, _
from datetime import date


class AdmissionCustomization(models.Model):
    _inherit = 'op.admission.register'

    lead_id = fields.Many2one('crm.lead', string="Lead")
    admission_date = fields.Date(string="Admission Date")

    def confirm_register(self):
        super(AdmissionCustomization, self).confirm_register()
        won_stage = self.env['crm.stage'].search([('name', '=', 'Admission')], limit=1)
        self.admission_date = date.today()
        if self.lead_id:
            if won_stage:
                # Update the lead's stage to "Won"
                self.lead_id.stage_id = won_stage.id
                self.lead_id.admission_status = True
                self.lead_id.admission_date = date.today()
                self.lead_id.course_id = self.course_id.id
                self.lead_id.batch_id = self.batch_id.id
                self.lead_id.branch_id = self.branch_id.id
                self.lead_id.lead_quality = 'admission'

