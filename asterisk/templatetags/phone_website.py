# -*- coding: utf-8 -*-
import hashlib
import re

from django import template
from django.core.cache import cache

from asterisk.models import ExternalPhoneNumber

register = template.Library()


@register.filter()
def website_info(userfield):
    if not userfield.strip():
        return '-'
    pattern = re.compile(r'^(?P<title>[a-zA-Z]+\d*)?-?(?P<number>\d{10,11})?$')
    m = pattern.match(userfield.strip())

    try:
        title, number = m.group('title'), m.group('number')

        if title:
            return title
        elif number:
            phone_hash = hashlib.sha1('{0}{1}'.format(
                'phone_website_cache', number)).hexdigest()
            website = cache.get(phone_hash)

            if not website:
                try:
                    phone_number = ExternalPhoneNumber.objects.get(
                        phone_number=number)
                    website = phone_number.website.name
                    cache.set(phone_hash, website)
                    return website
                except ExternalPhoneNumber.DoesNotExist:
                    cache.set(phone_hash, '-')
                    return '-'
            return website
    except AttributeError:
        return '<Error>'
