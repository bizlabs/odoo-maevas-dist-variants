# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class DistVariantValues(http.Controller):
    @http.route('/dist_variant_values/update_variants', auth='user')
    def update_variants(self):
        request.env['product.template'].update_all_variants()
        return request.make_response('Product variants updated successfully.')


#     @http.route('/dist_variant_values/dist_variant_values/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dist_variant_values.listing', {
#             'root': '/dist_variant_values/dist_variant_values',
#             'objects': http.request.env['dist_variant_values.dist_variant_values'].search([]),
#         })

#     @http.route('/dist_variant_values/dist_variant_values/objects/<model("dist_variant_values.dist_variant_values"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dist_variant_values.object', {
#             'object': obj
#         })

