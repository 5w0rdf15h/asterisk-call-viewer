# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from asterisk.models import CALL_STATUSES
register = template.Library()


@register.filter()
def call_status(status):
    if status == CALL_STATUSES.ANSWERED:
        return '<td class="success">{0}</td>'\
            .format(CALL_STATUSES.HUMAN_NAMES[CALL_STATUSES.ANSWERED])
    elif status == CALL_STATUSES.BUSY:
        return '<td class="info">{0}</td>'.format(
            CALL_STATUSES.HUMAN_NAMES[CALL_STATUSES.BUSY])
    elif status == CALL_STATUSES.FAILED:
        return '<td class="danger">{0}</td>'.format(
            CALL_STATUSES.HUMAN_NAMES[CALL_STATUSES.FAILED])
    elif status == CALL_STATUSES.NO_ANSWER:
        return '<td class="warning">{0}</td>'.format(
            CALL_STATUSES.HUMAN_NAMES[CALL_STATUSES.NO_ANSWER])
    else:
        return '<td>{0}</td>'.format(status)
