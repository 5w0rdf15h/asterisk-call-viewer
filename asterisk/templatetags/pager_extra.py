# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import template

register = template.Library()

@register.filter
def products_pager_links(request, page_number):
    result_url = []
    full_path = request.path
    if request.GET:
        for key, value in enumerate(request.GET):
            if value == 'page':
                continue
            get_value = request.GET[value]
            if get_value:
                result_url.append('{0}={1}'.format(value, get_value))

    if page_number > 1:
        result_url.append('page={0}'.format(page_number))
    result_url = '&'.join(result_url).lstrip('&')

    return full_path + "?" + result_url if len(result_url) else full_path
