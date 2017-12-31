# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class UploadXMLWizardGD(models.TransientModel):
    _inherit = 'sii.dte.upload_xml.wizard'

    def process_dr(self, dr):
        data = {
                    'type': dr['TpoMov'],
                }
        disc_type = "percent"
        if dr['TpoValor'] == '$':
            disc_type = "amount"
        data['gdr_type'] = disc_type
        data['global_discount'] = dr['ValorDR']
        data['gdr_dtail'] = dr['GlosaDR']
        return data

    def _prepare_invoice(self, dte, company_id, journal_document_class_id):
        data = super(UploadXMLWizardGD, self)._prepare_invoice(dte, company_id, journal_document_class_id)
        if 'DscRcgGlobal' in dte:
            disc_type = "%"
            DscRcgGlobal = dte['DscRcgGlobal']
            drs = [(5,)]
            if 'TpoMov' in DscRcgGlobal:
                dsr.append((0,0,self.process_dr(dte['DscRcgGlobal'])))
            else:
                for dr in DscRcgGlobal:
                    drs.append((0,0,self.process_dr(dr)))
        data.update({
                'global_descuentos_recargos': drs,
            })
        return data
