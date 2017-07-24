# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import itertools
import json
import hashlib
import re

from django.db import models
from django.db import connections
from django.db.models import Count
from django.db.models import Q
from django.db.models.functions import Length
from django.utils.translation import ugettext_lazy as _
from collections import OrderedDict
from django.core.cache import cache
from accounts.models import User


class CALL_STATUSES:
    ANSWERED = 'ANSWERED'
    NO_ANSWER = 'NO ANSWER'
    BUSY = 'BUSY'
    FAILED = 'FAILED'

    HUMAN_NAMES = {
        ANSWERED: _('Ответ'),
        NO_ANSWER: _('Нет ответа'),
        BUSY: _('Занято'),
        FAILED: _('Ошибка')
    }


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def get_translated_call_status(status):
    result = 'Неизвестно'
    if status == CALL_STATUSES.ANSWERED:
        result = CALL_STATUSES.HUMAN_NAMES[CALL_STATUSES.ANSWERED]
    if status == CALL_STATUSES.NO_ANSWER:
        result = CALL_STATUSES.HUMAN_NAMES[CALL_STATUSES.NO_ANSWER]
    if status == CALL_STATUSES.BUSY:
        result = CALL_STATUSES.HUMAN_NAMES[CALL_STATUSES.BUSY]
    if status == CALL_STATUSES.FAILED:
        result = CALL_STATUSES.HUMAN_NAMES[CALL_STATUSES.FAILED]
    return str(result)


def clean_number(number):
    """Leave only Russian full length numbers"""

    if len(number) < 10:
        return
    number = number.replace('+', '')
    if len(number) == 11:
        if number[0] not in ['7', '8']:
            return
        number = '{0}{1}'.format('7', number[1:])
    elif len(number) == 10:
        number = '{0}{1}'.format('7', number)
    return number


class CdrManager(models.Manager):
    date_intervals = {'minute': '%Y-%m-%d %H:%M',
                      'hour': '%Y-%m-%d %H:00',
                      'day': '%Y-%m-%d'}
    calls = None

    def get_interval(self, date, interval):
        return date.strftime(self.date_intervals[interval])

    def get_internal_numbers(self):
        qs = InternalPhoneNumber.objects.filter(
            employee__isnull=False).values_list(
            'phone_number', 'employee__name')
        return {k: v for k, v in qs}

    def general_stat(self, date_start, date_end, interval='hour'):
        result = []
        if not date_start or not date_end:
            return json.dumps(result)

        qs = Cdr.objects.annotate(
            cl_dst=Length('dst'), cl_src=Length('src')).filter(
            calldate__gte=date_start, calldate__lte=date_end, cl_dst__lte=4,
            cl_src__gte=5).order_by('calldate')

        if qs.count():
            result = [['Дата', 'Кол-во']]
            groups = itertools.groupby(qs, lambda x: self.get_interval(
                x.calldate, interval))
            grouped = [[group, sum(1 for _ in matches)] for
                       group, matches in groups]
            result += grouped

        return json.dumps(result)

    def employee_stat(self, date_start, date_end):
        internal_numbers = self.get_internal_numbers()
        qs = self.get_calls(date_start, date_end).filter(
            dst__in=internal_numbers).values_list('dst').annotate(
            calls=Count('dst'))
        if qs.count():
            result = [['Сотрудник', 'Звонки']]
            result += [['[%s] %s' % (item[0], internal_numbers[item[0]]),
                        item[1]] for item in qs]
        else:
            result = []

        return json.dumps(result)

    def employee_stat_daily(self, date_start, date_end):
        result = []
        if not date_start or not date_end:
            return json.dumps(result)

        internal_numbers = self.get_internal_numbers()

        qs = self.get_calls(date_start, date_end).filter(
            dst__in=internal_numbers).values('dst', 'calldate')

        if not qs.count():
            return json.dumps(result)

        dates = self.get_date_range(date_start, date_end)

        res_nums = OrderedDict()
        for num in internal_numbers:
            calls = qs.filter(dst=num)
            groups = itertools.groupby(
                calls, lambda x: x['calldate'].strftime(
                    self.date_intervals['day']))
            res_nums['[%s] %s' % (num, internal_numbers[num])] = \
                [[group, sum(1 for _ in matches)] for group, matches in groups]

        res_dates = OrderedDict()
        for date in dates:
            for k, stats in res_nums.items():
                if date not in res_dates:
                    res_dates[date] = OrderedDict()
                res_dates[date][k] = [x[1] for
                                      x in stats if x[0] == date]

        res = [['Dates'] + list(res_nums.keys())]
        for date, nums in res_dates.items():
            line = [date]
            for k, v in nums.items():
                line.append(v[0] if len(v) else 0)
            res.append(line)

        return json.dumps(res)

    def get_date_range(self, date_start, date_end):
        start = datetime.datetime.strptime(
            date_start, self.date_intervals['minute'])
        end = datetime.datetime.strptime(
            date_end, self.date_intervals['minute'])
        return [(start + datetime.timedelta(days=x)).strftime(
            self.date_intervals['day']
        ) for x in range(0, (end - start).days + 1)]

    def get_employee_name_by_dst(self, phone_number):
        employee_name = _('Unknown')
        try:
            cache_name = 'get_employee_name_{0}'.format(phone_number)
            cached_data = cache.get(cache_name)
            if cached_data:
                return cached_data
            data = InternalPhoneNumber.objects.get(phone_number=phone_number)
            if data:
                employee_name = data.employee.name
                cache.set(cache_name, employee_name, 60 * 5)
        except InternalPhoneNumber.DoesNotExist:
            pass
        return employee_name

    def get_regional_stat(self, date_start, date_end):

        result_all = []
        result_new = []

        if not date_start or not date_end:
            return {'all': json.dumps(result_all),
                    'new': json.dumps(result_new)}

        qs_all = self.get_calls(date_start, date_end).filter(
            number__region__isnull=False).values_list(
            'number__region').annotate(qty=Count('src'))
        qs_new = self.get_calls(date_start, date_end).filter(
            number__region__isnull=False, is_new=True).values_list(
            'number__region').annotate(qty=Count('src'))

        result_all = [['Регион', 'Звонки']]
        result_new = [['Регион', 'Звонки']]
        result_all += list(qs_all)
        result_new += list(qs_new)

        return {'all': json.dumps(result_all),
                'new': json.dumps(result_new)}

    def call_status_stat(self, date_start, date_end, interval='day'):
        result = []
        if not date_start or not date_end:
            return json.dumps(result)

        qs = self.get_calls(date_start, date_end).annotate(
            num_len=Length('dst')).filter(
            ~Q(disposition='ANSWERED'), num_len__gt=5, dstchannel__isnull=False
        ).order_by('calldate').values('disposition', 'calldate')
        if not qs.count():
            return json.dumps(result)

        statuses = list(self.get_calls(date_start, date_end).values_list(
            'disposition', flat=True).distinct())
        statuses.remove('ANSWERED')
        interval = 'day'

        res_stats = OrderedDict()
        for status in statuses:
            calls = qs.filter(disposition=status)
            groups = itertools.groupby(
                calls, lambda x: self.get_interval(
                    x['calldate'], interval))
            grouped = [[group, sum(1 for _ in matches)] for
                       group, matches in groups]
            res_stats[status] = grouped

        dates = self.get_date_range(date_start, date_end)

        res_dates = OrderedDict()
        for date in dates:
            for st, data in res_stats.items():
                if date not in res_dates:
                    res_dates[date] = OrderedDict()
                res_dates[date][st] = [x[1] for x in data if x[0] == date]

        result = [['Дата'] + statuses + ['Всего']]
        for date, stats in res_dates.items():
            line = [date]
            for st, qty in stats.items():
                line.append(qty[0] if len(qty) else 0)
            line.append(sum(line[1:]))
            result.append(line)

        return json.dumps(result)

    def site_calls_stat(self, date_start, date_end, interval='day'):
        result_all = []
        result_new = []

        if not date_start or not date_end:
            return {'all': json.dumps(result_all),
                    'new': json.dumps(result_new)}

        websites = OrderedDict(Websites.objects.all().values_list('pk', 'name'))

        qs_all = self.get_calls(date_start, date_end).filter(
            website__isnull=False).values('website').annotate(qty=Count(
                'website')).order_by('-qty')
        qs_new = self.get_calls(date_start, date_end).filter(
            website__isnull=False, is_new=True).values(
            'website').annotate(qty=Count('website')).order_by('-qty')

        result_all = [['Регион', 'Звонки']]
        result_new = [['Регион', 'Звонки']]
        result_all += [(websites[x['website']], x['qty']) for x in qs_all if x['website']]
        result_new += [(websites[x['website']], x['qty']) for x in qs_new if x['website']]

        res = {'all': json.dumps(result_all),
               'new': json.dumps(result_new)}
        return res

    def get_calls(self, date_start, date_end):
        if not self.calls:
            self.calls = Cdr.objects.filter(
                calldate__gte=date_start, calldate__lte=date_end)
        return self.calls


class Cdr(models.Model):

    objects = CdrManager()

    calldate = models.DateTimeField(
        blank=True
    )
    clid = models.CharField(
        max_length=80,
        blank=True
    )
    src = models.CharField(
        max_length=80,
        blank=True
    )
    dst = models.CharField(
        max_length=80,
        blank=True
    )
    dcontext = models.CharField(
        max_length=80,
        blank=True
    )
    channel = models.CharField(
        max_length=80,
        blank=True
    )
    dstchannel = models.CharField(
        max_length=80,
        blank=True
    )
    lastapp = models.CharField(
        max_length=80,
        blank=True
    )
    lastdata = models.CharField(
        max_length=80,
        blank=True
    )
    duration = models.IntegerField(
        blank=True
    )
    billsec = models.IntegerField(
        blank=True
    )
    disposition = models.CharField(
        max_length=45,
        blank=True
    )
    amaflags = models.IntegerField(
        blank=True
    )
    accountcode = models.CharField(
        max_length=20,
        blank=True
    )
    uniqueid = models.CharField(
        max_length=32,
        blank=True
    )
    userfield = models.CharField(
        max_length=255,
        blank=True
    )
    is_new = models.BooleanField(
        default=False
    )
    number = models.ForeignKey(
        'asterisk.Numbers',
        blank=True,
        null=True,
        default=None
    )
    website = models.ForeignKey(
        'Websites', blank=True, null=True
    )

    class Meta:
        # managed = False
        db_table = 'cdr'

    def get_website(self):
        if not self.userfield.strip():
            return

        if self.website:
            return {'website': self.website, 'new': False}

        # Calculate website from userfield
        #
        pattern = re.compile(r'^(?P<title>[a-zA-Z]+\d*)?-?(?P<number>\d{10,11})?$')
        m = pattern.match(self.userfield.strip())

        if not m:
            return

        title, number = m.group('title'), m.group('number')

        if not number:
            return
        else:
            phone_hash = hashlib.sha1('{0}{1}'.format(
                'phone_website_cache', number)).hexdigest()
            website = cache.get(phone_hash)

            if not website:
                try:
                    phone_number = ExternalPhoneNumber.objects.get(
                        phone_number=number)
                    website = phone_number.website
                    cache.set(phone_hash, website)
                except ExternalPhoneNumber.DoesNotExist:
                    cache.set(phone_hash, None)
                    return

            self.website = website
            self.save()
            return {'website': self.website, 'new': True}


class Cel(models.Model):
    eventtype = models.CharField(
        max_length=30
    )
    eventtime = models.DateTimeField()
    cid_name = models.CharField(
        max_length=80
    )
    cid_num = models.CharField(
        max_length=80
    )
    cid_ani = models.CharField(
        max_length=80
    )
    cid_rdnis = models.CharField(
        max_length=80
    )
    cid_dnid = models.CharField(
        max_length=80
    )
    exten = models.CharField(
        max_length=80
    )
    context = models.CharField(
        max_length=80
    )
    channame = models.CharField(
        max_length=80
    )
    src = models.CharField(
        max_length=80
    )
    dst = models.CharField(
        max_length=80
    )
    channel = models.CharField(
        max_length=80
    )
    dstchannel = models.CharField(
        max_length=80
    )
    appname = models.CharField(
        max_length=80
    )
    appdata = models.CharField(
        max_length=80
    )
    amaflags = models.IntegerField()
    accountcode = models.CharField(
        max_length=20
    )
    uniqueid = models.CharField(
        max_length=32
    )
    linkedid = models.CharField(
        max_length=32
    )
    peer = models.CharField(
        max_length=80
    )
    userdeftype = models.CharField(
        max_length=255
    )
    eventextra = models.CharField(
        max_length=255
    )
    userfield = models.CharField(
        max_length=255
    )

    class Meta:
        # managed = False
        db_table = 'cel'


class Numbers(models.Model):
    abc = models.IntegerField()
    of = models.IntegerField()
    to = models.IntegerField()
    capacity = models.IntegerField()
    operator = models.CharField(
        max_length=255
    )
    region = models.CharField(
        max_length=255
    )

    class Meta:
        # managed = False
        db_table = 'numbers'


class QueueLog(models.Model):
    time = models.CharField(
        max_length=32,
        blank=True,
        null=True
    )
    callid = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    queuename = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    agent = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    event = models.CharField(
        max_length=32,
        blank=True,
        null=True
    )
    data = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    data1 = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    data2 = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    data3 = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    data4 = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    data5 = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'queue_log'


class Websites(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'websites'


class ExternalPhoneNumber(models.Model):
    phone_number = models.CharField(
        max_length=20
    )
    note = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )
    website = models.ForeignKey(
        Websites,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.phone_number

    class Meta:
        db_table = 'external_phone_number'


class Department(models.Model):
    name = models.CharField(
        max_length=100
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'department'


class Employee(models.Model):
    name = models.CharField(
        max_length=255
    )
    department = models.ForeignKey(
        Department,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'employee'


class InternalPhoneNumber(models.Model):
    phone_number = models.CharField(
        max_length=20
    )
    employee = models.ForeignKey(
        Employee,
        blank=True,
        null=True
    )
    department = models.ForeignKey(
        Department,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.phone_number

    class Meta:
        db_table = 'internal_phone_number'


class CallComment(models.Model):
    call_id = models.IntegerField()
    user = models.ForeignKey(User)
    added_timestamp = models.DateTimeField(
        auto_now_add=True
    )
    contents = models.TextField(
        default=''
    )

    def __str__(self):
        return self.call_id

    class Meta:
        db_table = 'call_comment'
