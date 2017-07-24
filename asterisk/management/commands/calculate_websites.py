import sys
from django.core.management import BaseCommand

from asterisk.models import Cdr


def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '#' * filled_len + ' ' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


class Command(BaseCommand):

    def handle(self, *args, **options):
        total = Cdr.objects.count()
        counter = 0
        hits = 0

        for c in Cdr.objects.all():
            res = c.get_website()
            if res and res['new']:
                hits += 1
            counter += 1
            progress(counter, total, 'wait please')

        print(u"\n%d of %d websites calculated" % (hits, total))


