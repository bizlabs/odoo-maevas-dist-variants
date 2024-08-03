# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
# import logging
# _logger = logging.getLogger(__name__)


class ProductTemplateAttributeValue(models.Model):
    '''override create, write, unlink to auto run syncing to products on any change'''
    _inherit = "product.template.attribute.value"

    def write(self,vals):
        ### check and allow if coming from the global sync method
        
        if "price_extra" in vals.keys() or "name" in vals.keys():
            if not "allow_sync" in vals.keys():
                if not self.attribute_id.name == 'size':
                    msg = "You cannot change individual product attribute values (when variant creation mode is 'Never') \n"
                    msg += "You must edit the global attribute at Inventory/Configuration/Attributes. \n"
                    msg += "The system will copy your changes to all products that use that attribute."
                    raise UserError(msg)
            else:
                del vals['allow_sync']
        records = super(ProductTemplateAttributeValue, self).write(vals)
        return records
        pass

class ProductTemplateAttributeLine(models.Model):
    '''override creating product.template.attibute.line to auto add all variant values
    whenever an attribute line is added to a product (if type is never add)'''

    _inherit = "product.template.attribute.line"

    def create(self, vals):
        for val in vals:
            if "attribute_id" in val.keys():
                attr = self.env['product.attribute'].search([('id','=',val['attribute_id'])])
            if sync_values(attr):
                val['value_ids'] = [(6, 0, attr.value_ids.ids)]
            
        records = super(ProductTemplateAttributeLine, self).create(vals)
        return records

    def write(self, vals):
            # copy any missing variant values (may have been deleted by user)
        if hasattr(self, 'attribute_id'):
            attr = self.env['product.attribute'].search([('id','=',self['attribute_id'].id)])
        if sync_values(attr):
            ### if called from deleting a value from the global attr line, allow
            # the delete (keep value_ids), otherwise reset value_ids so no delete
            if "allow_sync" in vals.keys():
                del vals['allow_sync']
            else:
                vals['value_ids'] = [(6, 0, attr.value_ids.ids)]

        result = super(ProductTemplateAttributeLine, self).write(vals)
        return result

class ProductAttributeValue(models.Model):
    '''override create, write, unlink to auto run syncing to products on any change'''
    _inherit = "product.attribute.value"    

    def x_create_variant(self, records):
        product_templates = self.env['product.template'].search([])
        for product in product_templates:
            for attribute_line in product.attribute_line_ids:
                for record in records:
                    if record.attribute_id.id == attribute_line.attribute_id.id:
                      attribute_line.write({'value_ids' : [(4,record.id)]})

    def x_update_variant(self):
        # Fetch all product templates
        product_template_attribute_values = self.env['product.template.attribute.value'].search([
            ('product_attribute_value_id.id', '=', self.id)])
        for tval in product_template_attribute_values:
            for record in self:
                tval.write({
                    'allow_sync':   True,
                    'price_extra':  record.default_extra_price,
                    'name':         record.name,
                })

    def create(self, vals):
        records = super(ProductAttributeValue, self).create(vals)
        for record in records:
            attr = record.attribute_id
            if sync_values(attr):
                self.x_create_variant(record)
        return records

    def write(self, vals):
        attr = self.attribute_id
        result = super(ProductAttributeValue, self).write(vals)
        if sync_values(attr):
            self.x_update_variant()
        return result

    def unlink(self):
        if sync_values(self.attribute_id):
            for record in self:
                product_template_attribute_values = self.env['product.template.attribute.value'].search([
                    ('product_attribute_value_id.id', '=', record.id)])
                
                for tval in product_template_attribute_values:
                    tline = tval.attribute_line_id
                    tval_id = tval.product_attribute_value_id.id
                    # tline.value_ids = [(3,tval_id)]
                    tline.write({
                        'value_ids':    [(3,tval_id)],
                        'allow_sync':   True
                        })
                pass
        result = super(ProductAttributeValue, self).unlink()
        return result

def sync_values(attrval):
    """return True if desired to sync attribute values to all products
    currently, this is done for all variants of creation type 'never' except 
    for the variant named 'size'"""

    if attrval.create_variant == 'no_variant' and \
        attrval.name != 'size':
        return True
    else:
        return False