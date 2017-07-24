# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db.models.functions import Length
from asterisk.models import Cdr, Numbers


class Command(BaseCommand):

    def handle(self, *args, **options):
        for c in Cdr.objects.annotate(d_length=Length('src')).filter(
                number=None, d_length__gte=10):
            call_data = self.get_phone_data(c.src)
            if call_data:
                if call_data['number']:
                    c.number = call_data['number']
                    c.save()

    def get_phone_data(self, phone):
        phone = phone.replace('+', '')
        phone_len = len(phone)
        data = {}
        if phone_len == 11:
            data = {
                'country': phone[0],
                'code': phone[1:4],
                'phone': phone[4:11]
            }
        if phone_len == 10:
            data = {
                'country': '8',
                'code': phone[:3],
                'phone': phone[3:]
            }
        if data:
            if data['country'] not in ['7', '8']:
                return {}
            try:
                data['number'] = Numbers.objects.get(
                    abc=data['code'], of__lte=data['phone'],
                    to__gte=data['phone'])
            except Numbers.DoesNotExist:
                data['number'] = None
        return data
