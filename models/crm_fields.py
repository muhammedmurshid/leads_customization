from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class CrmFieldsCustomization(models.Model):
    _inherit = 'crm.lead'

    district = fields.Selection([('wayanad', 'Wayanad'), ('ernakulam', 'Ernakulam'), ('kollam', 'Kollam'),
                                 ('thiruvananthapuram', 'Thiruvananthapuram'), ('kottayam', 'Kottayam'),
                                 ('kozhikode', 'Kozhikode'), ('palakkad', 'Palakkad'), ('kannur', 'Kannur'),
                                 ('alappuzha', 'Alappuzha'), ('malappuram', 'Malappuram'), ('kasaragod', 'Kasaragod'),
                                 ('thrissur', 'Thrissur'), ('idukki', 'Idukki'), ('pathanamthitta', 'Pathanamthitta'),
                                 ('abroad', 'Abroad'), ('other', 'Other'), ('nil', 'Nil')],
                                string='District')
    mode_of_study = fields.Selection([('online', 'Online'), ('offline', 'Offline'), ('nil', 'Nil')],
                                     string='Mode of Study',
                                     )
    assign_to_tele_caller_id = fields.Many2one('res.users', string='Tele Caller',domain=lambda self: [("groups_id", "=",
                                                  self.env.ref("leads_customization.group_lead_tele_callers").id)])
    assigned_date = fields.Date(string='Assigned Date')
    institute_name = fields.Char(string='Institute Name')
    course_type = fields.Selection(
        [('indian', 'Indian'), ('international', 'International'), ('crash', 'Crash'), ('repeaters', 'Repeaters'),
         ('nil', 'Nil')],
        string='Course Type')
    # branch_id = fields.Many2one('logic.branches', string="Branch")
    department = fields.Selection([('crash_course', 'Crash Course'), ('regular_course', 'Regular Course'), ('nil', 'Nil')], string="Department")
    course_id = fields.Many2one('op.course', string="Course")
    batch_id = fields.Many2one('logic.batches', string="Batch")
    admission_status = fields.Boolean(string="Admission Status")
    admission_date = fields.Date(string="Admission Date")
    academic_year = fields.Selection(
        [('2020_21', '2020-2021'), ('2022_23', '2022-2023'), ('2024_25', '2024-2025'),
         ('2026_27', '2026-2027'), ('nil', 'Nil')], string='Academic Year')
    lead_quality = fields.Selection(
        [('new', 'New'), ('waiting_for_admission', 'Waiting for Admission'), ('admission', 'Admission'), ('hot', 'Hot'), ('warm', 'Warm'), ('cold', 'Cold'),
         ('bad_lead', 'Bad Lead'), ('not_responding', 'Not Responding'), ('crash_lead', 'Crash Lead'),
         ('nil', 'Nil')],
        string='Lead Quality', default='new')
    seminar_lead_id = fields.Integer(string="Seminar Lead ID")
    updated_remarks = fields.Text(string="Updated Remarks")
    expected_joining_date = fields.Date(string="Expected Joining Date")


    def action_set_won_rainbowman(self):
        print('correct')
        if self.id:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'op.admission.register',
                # 'res_id': admission_register.id,  # Use the correct admission record ID
                'view_id': self.env.ref('openeducat_admission.view_op_admission_register_form').id,
                'target': 'new',
                'context': {
                    'default_lead_id': self.id,
                    'default_course_id': self.course_id.id,
                    'default_name': self.name,
                    'default_batch_id': self.batch_id.id,


                }
            }

    @api.model
    def allocate_leads(self, lead_ids):
        # Fetch tele-callers who can handle leads
        tele_caller_group = self.env.ref('leads_customization.group_lead_tele_callers')
        if tele_caller_group:# Update the module name
            tele_callers = self.env['res.users'].search([('groups_id', 'in', [tele_caller_group.id])])
        else:
            return []
        # Fetch lead users for inbound source
        lead_user_group = self.env.ref('leads_customization.group_lead_users')  # Update the module name
        if lead_user_group:
            lead_users = self.env['res.users'].search([('groups_id', 'in', [lead_user_group.id])])
        else:
            return []
        lead_objects = self.browse(lead_ids)
        if not tele_callers and not lead_users:
            raise ValueError("No users available to allocate leads.")

        # Logic for outbound and inbound leads
        for lead in lead_objects:
            if lead.source_id.source == 'outbound_source':
                # Assign to tele-callers in FIFO order
                tele_caller_list = tele_callers.sorted(key=lambda tc: tc.create_date)
                tele_caller_count = len(tele_caller_list)
                tele_caller_id = tele_caller_list[lead.id % tele_caller_count].id
                lead.write({'assign_to_tele_caller_id': tele_caller_id})

            elif lead.source_id.source == 'inbound_source':
                # Assign to lead users in FIFO order
                lead_user_list = lead_users.sorted(key=lambda user: user.create_date)
                lead_user_count = len(lead_user_list)
                lead_user_id = lead_user_list[lead.id % lead_user_count].id
                lead.write({'user_id': lead_user_id})



    @api.model
    def create(self, values):
        # Create the lead
        lead = super(CrmFieldsCustomization, self).create(values)

        # Allocate the lead to tele-callers or lead users
        self.allocate_leads([lead.id])

        # Notify the assigned tele-caller, if any
        if lead.assign_to_tele_caller_id:
            # Create the notification
            notification_ids = [(0, 0, {
                'res_partner_id': lead.assign_to_tele_caller_id.partner_id.id,
                'notification_type': 'inbox'
            })]

            # Create the mail message
            self.env['mail.message'].create({
                'message_type': "notification",
                'body': f"Lead '{lead.name}' has been assigned to you.",
                'subject': "Lead Assigned",
                'model': 'crm.lead',
                'res_id': lead.id,
                'partner_ids': [(4, lead.assign_to_tele_caller_id.partner_id.id)],
                'author_id': self.env.user.partner_id.id,
                'notification_ids': notification_ids,
            })

        return lead

    @api.constrains('updated_remarks', 'lead_quality')
    def _check_updated_remarks(self):
        for record in self:
            if record.lead_quality:
                if record.lead_quality == 'bad_lead':
                    if not record.updated_remarks:
                        raise ValidationError("Updated Remarks is required when Lead Quality is 'Bad Lead'.")
                    if len(record.updated_remarks) < 140:
                        raise ValidationError("Updated Remarks must be at least 140 characters long.")

    @api.constrains('course_id', 'branch_id', 'batch_id', 'lead_quality')
    def _check_updated_course_details(self):
        for record in self:
            if record.lead_quality:
                if record.lead_quality in ['waiting_for_admission', 'admission']:
                    if not record.course_id or not record.branch_id or not record.batch_id:
                        raise ValidationError("Please fill in the required fields: Course, Branch, and Batch.")

    @api.depends('lead_quality')
    def _compute_update_date_time(self):
        print('yes')
        self.lead_status_updated_date = datetime.now()


    def act_connect_lead(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Connect'),
                'res_model': 'crm.connect',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_lead_quality': self.lead_quality,
                            'default_parent_id': self.id}, }
        # connect = self.env['crm.stage'].sudo().search([('name', '=', 'Connected')])
        # print(connect.id, 'id')
        # self.stage_id = connect.id

    lead_status_updated_date = fields.Datetime(string="Lead Updated Date", readonly=1)

    stage_color = fields.Char(compute='_compute_stage_color', string='Stage Color')

    @api.depends('stage_id')
    def _compute_stage_color(self):

        stage_colors = {
            'New': 'info',
            'Qualified': 'success',
            'Proposition': 'primary',
            'Negotiation': 'warning',
            'Won': 'success',
            'Lost': 'danger',
        }

        for record in self:
            # Map stage name or ID to color
            record.stage_color = stage_colors.get(record.stage_id.name, 'secondary')
            print(record.stage_color, 'colour')

    def action_send_notification(self):
        for res in self:
            if res.assign_to_tele_caller_id:
                print('yes')
                # Create the notification
                notification_ids = [(0, 0, {
                    'res_partner_id': res.assign_to_tele_caller_id.partner_id.id,
                    'notification_type': 'inbox'
                })]

                # Create the mail message
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': f"{self.name} This lead has been assigned to you.",
                    'subject': "Lead Assignment",
                    'model': 'crm.lead',
                    'res_id': res.id,
                    'partner_ids': [(4, res.assign_to_tele_caller_id.partner_id.id)],
                    'author_id': self.env.user.partner_id.id,
                    'notification_ids': notification_ids,
                })


class CrmConnect(models.TransientModel):
    _name = 'crm.connect'
    _description = "Connect"

    lead_quality = fields.Selection(
        [('new', 'New'), ('waiting_for_admission', 'Waiting for Admission'), ('admission', 'Admission'), ('hot', 'Hot'),
         ('warm', 'Warm'), ('cold', 'Cold'),
         ('bad_lead', 'Bad Lead'), ('not_responding', 'Not Responding'), ('crash_lead', 'Crash Lead'),
         ('nil', 'Nil')],
        string='Lead Quality', default='new')
    expected_joining_date = fields.Date(string="Expected Joining Date")
    assign_to_crash_user_id = fields.Many2one('res.users', string="Assign to Crash User")
    remarks = fields.Text(string="Remarks")
    parent_id = fields.Many2one('crm.lead')

    @api.constrains('expected_joining_date', 'lead_quality','assign_to_crash_user_id','remarks')
    def _check_expected_joining_date(self):
        for record in self:
            if record.lead_quality in ['warm','hot']:
                if not record.expected_joining_date:
                    raise ValidationError("Please fill in the required fields: Expected Joining Date.")
            if record.lead_quality == 'crash_lead':
                if not record.assign_to_crash_user_id:
                    raise ValidationError("Please fill in the required fields: Assign to Crash User.")
            if record.lead_quality == 'bad_lead':
                if not record.remarks:
                    raise ValidationError("Please fill in the required fields: Remarks.")
                if len(record.remarks) < 140:
                    raise ValidationError("Updated Remarks must be at least 140 characters long.")

    def act_save(self):
        connect = self.env['crm.stage'].sudo().search([('name', '=', 'Connected')])
        if self.lead_quality:
            self.parent_id.lead_quality = self.lead_quality
            if self.lead_quality == 'warm' or self.lead_quality == 'hot':
                self.parent_id.expected_joining_date = self.expected_joining_date
            if self.lead_quality == 'crash_lead':
                self.parent_id.assign_to_tele_caller_id = self.assign_to_crash_user_id.id
            if self.lead_quality == 'bad_lead':
                self.parent_id.updated_remarks = self.remarks
        if connect:
            self.parent_id.stage_id = connect.id
        if not connect:
            raise ValidationError("The 'Connected' stage is not configured in CRM Stages.")
