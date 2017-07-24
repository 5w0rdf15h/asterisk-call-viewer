# -*- coding: utf-8 -*-
import math
from django import template
register = template.Library()


@register.filter()
def format_seconds(s):
    mins = math.floor(s / 60)
    secs = math.floor(s - (mins * 60))
    return "%d:%02d" % (mins, secs)
