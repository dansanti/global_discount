# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import UserError
import collections
import logging
_logger = logging.getLogger(__name__)


class GlobalDiscount(models.Model):
    _inherit = "account.invoice"

    amount_untaxed_global_discount = fields.Float(
            string="Global Discount Amount",
            store=True,
            default=0.00,
            compute='_compute_amount',
        )
    amount_untaxed_global_recargo = fields.Float(
            string="Global Recargo Amount",
            store=True,
            default=0.00,
            compute='_compute_amount',
        )
    global_descuentos_recargos = fields.One2many(
            'account.invoice.gdr',
            'invoice_id',
            string="Descuentos / Recargos globales",
            readonly=True,
            states={'draft': [('readonly', False)]},
        )

    def porcentaje_dr(self):
        taxes = super(GlobalDiscount,self).get_taxes_values()
        afecto = 0.00
        exento = 0.00
        porcentaje = 0.00
        total = 0.00
        for id, t in taxes.iteritems():
            tax = self.env['account.tax'].browse(t['tax_id'])
            total += t['base']
            if tax.amount > 0:
                afecto += t['base']
            else:
                exento += t['base']
        agrupados = self.global_descuentos_recargos.get_agrupados()
        monto = agrupados['R'] - agrupados['D']
        if monto == 0:
            return 0.00
        porcentaje =   (100.0 * monto) / afecto
        return 1 + (porcentaje /100.0)

    @api.multi
    def get_taxes_values(self):
        tax_grouped = super(GlobalDiscount, self).get_taxes_values()
        if not self.global_descuentos_recargos:
            return tax_grouped
        gdr = self.porcentaje_dr()
        taxes = {}
        for t, group in tax_grouped.iteritems():
            if t not in taxes:
                taxes[t] = group
            tax = self.env['account.tax'].browse(group['tax_id'])
            if tax.amount > 0:
                taxes[t]['amount'] *= gdr
                taxes[t]['base'] *=  gdr
        return taxes

    @api.onchange('global_descuentos_recargos')
    def _compute_amount(self):
        super(GlobalDiscount, self)._compute_amount()
        for inv in self:
            if inv.global_descuentos_recargos:
                monto = inv.global_descuentos_recargos.get_monto_aplicar()
                agrupados = inv.global_descuentos_recargos.get_agrupados()
                inv.amount_untaxed_global_discount = agrupados['D']
                inv.amount_untaxed_global_recargo = agrupados['R']
                inv.amount_untaxed += monto
                inv.amount_tax = sum(line.amount for line in inv.tax_line_ids)
                inv.amount_total = inv.amount_untaxed + inv.amount_tax
                amount_total_company_signed = inv.amount_total
                amount_untaxed_signed = inv.amount_untaxed
                if inv.currency_id and inv.company_id and inv.currency_id != inv.company_id.currency_id:
                    currency_id = inv.currency_id.with_context(date=inv.date_invoice)
                    amount_total_company_signed = currency_id.compute(inv.amount_total, inv.company_id.currency_id)
                    amount_untaxed_signed = currency_id.compute(inv.amount_untaxed, inv.company_id.currency_id)
                sign = inv.type in ['in_refund', 'out_refund'] and -1 or 1
                inv.amount_total_company_signed = amount_total_company_signed * sign
                inv.amount_total_signed = inv.amount_total * sign
                inv.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.onchange('global_descuentos_recargos' )
    def _onchange_descuentos(self):
        self._onchange_invoice_line_ids()

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total, total_currency, iml = super(GlobalDiscount, self).compute_invoice_totals(company_currency, invoice_move_lines)
        if not self.global_descuentos_recargos:
            return total, total_currency, iml
        gdr = self.porcentaje_dr()
        for line in invoice_move_lines:
            line['amount_currency'] *= (gdr)
            line['price'] *= (gdr)
        total*=gdr
        total_currency*=gdr
        return total, total_currency, invoice_move_lines

    def _dte(self, n_atencion=None):
        dte = super(GlobalDiscount,self)._dte(n_atencion)
        if not self.global_descuentos_recargos:
            return dte
        result = collections.OrderedDict()
        lin_dr = 1
        dr_line = {}
        dr_line = collections.OrderedDict()
        for dr in self.global_descuentos_recargos:
            dr_line['NroLinDR'] = lin_dr
            dr_line['TpoMov'] = dr.type
            if dr.gdr_dtail:
                dr_line['GlosaDR'] = dr.gdr_dtail
            disc_type = "%"
            if dr.gdr_type == "amount":
                disc_type = "$"
            dr_line['TpoValor'] = disc_type
            dr_line['ValorDR'] = round(dr.valor,2)
            if self.sii_document_class_id.sii_code in [34] and (self.referencias and self.referencias[0].sii_referencia_TpoDocRef.sii_code == '34'):#solamente si es exento
                dr_line['IndExeDR'] = 1
            dr_lines= [{'DscRcgGlobal':dr_line}]
            for key, value in dte.iteritems():
                if key == 'reflines':
                    result['drlines'] = dr_lines
                result[key] = value
            lin_dr += 1
        return result

    def _dte_to_xml(self, dte, tpo_dte="Documento"):
        xml = super(GlobalDiscount, self)._dte_to_xml(dte, tpo_dte)
        xml = xml.replace('<drlines>','').replace('</drlines>','')
        return xml
