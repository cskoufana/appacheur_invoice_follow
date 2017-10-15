# -*- coding: utf-8 -*-
#__author__ = 'koufana'

from odoo import api, exceptions, fields, models, _
import time
from datetime import datetime

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    """
    Account invoice
    """
    _inherit = 'account.invoice'
    
    
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic account')
    state2 = fields.Selection([
            ('open0','Project leader'),
            ('open1', 'Engineer market'),
            ('open2', 'Service manager'),
            ('open3', 'Project manager'),
            ('open4', 'MINMAP'),
            ('open5', 'Pending payment'),
            ('paid','Paid'),

            ],'Status', index=True, readonly=True, track_visibility='onchange',default='open0', copy = False,
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma status,invoice does not have an invoice number. \
            \n* The \'Open\' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice. \
            \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
            \n* The \'Cancelled\' status is used when user cancel invoice.')
    stage_ids =  fields.One2many('account.invoice.stage', 'invoice_id', 'Stages')

    @api.one
    def invoice_follow_validate(self):
        if self.state2 == 'draft':
            return self.action_open0()
        elif self.state2 == 'open0':
            return self.action_open1()
        elif self.state2 == 'open1':
            return self.action_open2()
        elif self.state2 == 'open2':
            return self.action_open3()
        elif self.state2 == 'open3':
            return self.action_open4()
        elif self.state2 == 'open4':
            return self.action_open()
            
    
    @api.one
    def action_open0(self):
        st_obj = self.env['account.invoice.stage']
        stage = st_obj.search([('state','=','open0'),('invoice_id.id','=',self.id)])
        if stage:
            stage.write({'date_start': time.strftime('%Y-%m-%d %H:%M:%S')})
        self.sudo().write({'state2': 'open0'})

    @api.one
    def action_open_custom(self,start,end):
        for stage in self.stage_ids:
            if stage.state == start:
                stage.write({'date_end': time.strftime('%Y-%m-%d %H:%M:%S')})
            if stage.state == end:
                stage.write({'date_start': time.strftime('%Y-%m-%d %H:%M:%S')})
        return self.sudo().write( {'state2': end})

    @api.one
    def action_open1(self):
        return self.action_open_custom('open0','open1')

    @api.one
    def action_open2(self):
        return self.action_open_custom('open1','open2')
    @api.one
    def action_open3(self):
        return self.action_open_custom('open2','open3')
    @api.one
    def action_open4(self):
        return self.action_open_custom('open3','open4')
    @api.one
    def action_open(self):
        return self.action_open_custom('open4','open5')
    @api.model
    def create(self,values):
        invoices = super(AccountInvoice, self).create(values)
        if not 'type' in values or ('type' in values and values['type'] == 'out_invoice'):
            invoices.create_default_stage()
        return invoices
    
    @api.multi
    def write(self,values):
        if 'state' in values and values['state'] == 'paid' :
            values['state2'] = 'paid'
        return super(AccountInvoice, self).write(values)
    
    @api.multi
    def create_default_stage(self):
        stage_obj = self.env['account.invoice.stage']
        for inv in self :
            values = {
                'name': 'Project leader',
                'state': 'open0',
                'sequence': 1,
                'default': 1,
                'delay': 2,
                'invoice_id': inv.id,
                'date_start' :time.strftime('%Y-%m-%d %H:%M:%S')
            }
            stage_obj.create(values)
            values['name'] = 'Engineer market'
            values['state'] = 'open1'
            values['sequence'] = 2
            values['date_start'] = None
            stage_obj.create(values)
            values['name'] = 'Service manager'
            values['state'] = 'open2'
            values['sequence'] = 3
            stage_obj.create(values)
            values['name'] = 'Project Manager'
            values['state'] = 'open3'
            values['sequence'] = 4
            stage_obj.create(values)
            values['name'] = 'MINMAP'
            values['state'] = 'open4'
            values['sequence'] = 5
            stage_obj.create(values)
        return True

    @api.model
    def get_critical_delay(self):
        invoices = self.search([('state', 'not in', ('draft','cancel','paid')), ('type', '=', 'out_invoice')])
        for record in invoices:
            for stage in record.stage_ids:
                if stage.state == record.state:
                    #compute delay
                    delay = ((datetime.strptime(time.strftime('%Y-%m-%d'),'%Y-%m-%d') - datetime.strptime(stage.date_start[:10], '%Y-%m-%d')).days)
                    if delay >= stage.delay:
                        record.message_post(body=_('Step %s of the invoice %s has exceeded the time limit.') % (stage.name, record.name))
        return True

    @api.model
    def scheduler_stage_delay(self):
        self.get_critical_delay()
        return True



class AccountInvoiceStage(models.Model):
    _name = 'account.invoice.stage'
    _description = 'Customer invoice stage'
    _order = 'sequence'
    
    name = fields.Char('Name', size=64, required=True, translate=True)
    sequence = fields.Integer('Sequence')
    default = fields.Boolean('Default for invoices')
    delay = fields.Integer('Delay (Days)')
    state = fields.Selection([
            ('open0','Project leader'),
            ('open1', 'Engineer market'),
            ('open2', 'Service manager'),
            ('open3', 'Project manager'),
            ('open4', 'MINMAP'),
        ], string='State',index=True, readonly=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    date_start = fields.Datetime('Date start', readonly=True)
    date_end = fields.Datetime('Date end', readonly=True)