# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import netsvc

class sale_order(osv.osv):
    _inherit = 'sale.order' 
    #    Do not touch _name it must be same as _inherit
    #_name = 'sale.order' cr
    
    def _get_order(self, cr, uid, ids, context=None):
        #result = {}
        #for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
        #    result[line.order_id.id] = True
        #return result.keys()
        return super(sale_order,self)._get_order(cr,uid,context)    
    
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        #import pdb;pdb.set_trace()
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context=None)
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id
        codici_iva_accessori = self.pool.get('res.company').read(cr, uid, company_id , (['civa_spe_inc', 'civa_spe_imb', 'civa_spe_tra', 'civa_fc']), context=context)
        tassa_inc = 0
        tassa_tra = 0
        tassa_imb = 0
        
        
        
        
        
        
        for order in self.browse(cr, uid, ids, context=context):
            if order._columns.get('cod_esenzione_iva',False):
                esenzione = order.cod_esenzione_iva
            else:
                esenzione = False 
            #import pdb;pdb.set_trace()
            tax_inc=self.pool.get('account.tax').read(cr, uid, codici_iva_accessori['civa_spe_inc'][0], (['amount', 'type']))
            tax_tra=self.pool.get('account.tax').read(cr, uid, codici_iva_accessori['civa_spe_tra'][0], (['amount', 'type']))
            tax_imb=self.pool.get('account.tax').read(cr, uid, codici_iva_accessori['civa_spe_imb'][0], (['amount', 'type']))
            imponibile = 0
            if order.payment_term:
                pagamento_id = order.payment_term.id
                order.spese_incasso = self.calcola_spese_inc_ord(cr, uid, ids, pagamento_id)
            if order.spese_incasso or order.spese_di_trasporto or order.spese_imballo or esenzione:
               
                if codici_iva_accessori['civa_spe_inc'][0] or codici_iva_accessori['civa_spe_tra'] or codici_iva_accessori['civa_spe_imb'] or esenzione:
                    
                    if esenzione:
                        imponibile = res[order.id]['amount_untaxed']+ order.spese_incasso + order.spese_di_trasporto +order.spese_imballo, 
                        res[order.id] = {'spese_incasso':order.spese_incasso,
                                         'amount_untaxed':res[order.id]['amount_untaxed'], 
                                         'amount_tax': res[order.id]['amount_tax'],
                                         'amount_total': res[order.id]['amount_total'] + order.spese_incasso + order.spese_di_trasporto + order.spese_imballo,}
                    else:
                        
                        if order.spese_incasso:
                            tassa_inc = order.spese_incasso * tax_inc['amount']
                        if order.spese_di_trasporto:
                            tassa_tra = order.spese_di_trasporto *tax_tra['amount']
                        if order.spese_imballo:
                            tassa_imb = order.spese_imballo * tax_imb['amount']
                        #import pdb;pdb.set_trace()
                        imponibile = res[order.id]['amount_untaxed']+ order.spese_incasso + order.spese_di_trasporto +order.spese_imballo,
                        res[order.id] = {
                                         'amount_untaxed':res[order.id]['amount_untaxed'],
                                         'amount_tax':  res[order.id]['amount_tax'] + tassa_inc + tassa_tra + tassa_imb,
                                         'amount_total': res[order.id]['amount_total'] + order.spese_incasso + order.spese_di_trasporto +order.spese_imballo +tassa_inc + tassa_tra + tassa_imb,
                                         'spese_incasso':order.spese_incasso,
                                         }               
        return res    
    
    
    _columns = {
                'spese_incasso':fields.float('Spese Incasso', digits_compute=dp.get_precision('Account')),
                'spese_imballo':fields.float('Spese Imballo', digits_compute=dp.get_precision('Account')),
                'amount_untaxed': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Sale Price'), string='Untaxed Amount',
                store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                },
            multi='sums', help="The amount without tax."),
                'amount_tax': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Sale Price'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
                'amount_total': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Sale Price'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
                }
    
    def calcola_spese_inc_ord(self, cr, uid, ids, pagamento_id):
            #import pdb;pdb.set_trace()
            v = {}
            if pagamento_id:
                lines = self.pool.get('account.payment.term.line').search(cr, uid, [('payment_id', "=", pagamento_id)])
                spese = 0
                for riga in self.pool.get('account.payment.term.line').browse(cr, uid, lines):
                    spese = spese + riga['costo_scadenza']
                v['spese_incasso'] = spese

            return spese
    
    

                                 
    
sale_order()
