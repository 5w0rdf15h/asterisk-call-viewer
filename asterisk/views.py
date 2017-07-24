# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import time
import os
import json
import fnmatch
from django.conf import settings
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.core.paginator import Paginator
from django.utils import formats
from django.views.generic import ListView, View, UpdateView, TemplateView
from django.views.generic.edit import FormMixin, ModelFormMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from asterisk.models import (
    Cdr, Websites, ExternalPhoneNumber, InternalPhoneNumber, Employee,
    Department, CdrManager, CallComment)
from asterisk.forms import (
    CdrFilterForm, WebsitesForm, ExternalPhonesListForm, ExternalPhoneEditForm,
    InternalPhonesListForm, InternalPhoneEditForm, EmployeeListForm,
    EmployeeEditForm, DepartmentListForm, DepartmentEditForm, StatsForm
)


class PaginateFilterView(ListView, FormMixin):
    paginate_by = settings.DEFAULT_PAGES_COUNT
    paginator_class = Paginator

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        self.form = form_class(request.GET)
        if request.GET.get('num_items_on_page'):
            self.paginate_by = request.GET.get('num_items_on_page')

        if self.form.is_valid():
            self.object_list = self.form.get_queryset()
        else:
            self.object_list = self.get_queryset()

        if not self.request.user.is_admin:
            self.object_list = self.object_list.annotate(
                dst_length=Count('dst')).exclude(
                Q(dst__startswith='8') | Q(dst__startswith='7')
            )

        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(
                u"Empty list and '%(class_name)s.allow_empty' is False."
                % {'class_name': self.__class__.__name__}
            )
        context = self.get_context_data(
            object_list=self.object_list,
            form=self.form
        )
        get_request = request.GET.copy()
        for attr in get_request.keys():
            if not get_request.get(attr).strip():
                get_request.pop(attr)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


@login_required
@csrf_exempt
def get_num_comments(request):
    ids = request.POST.get('ids')
    id_list = []
    try:
        ids = ids.split(',')
        for c_id in ids:
            if c_id:
                call_id = int(c_id)
                id_list.append(call_id)
    except:
        pass
    comments = []
    for c in CallComment.objects.values('call_id')\
        .annotate(num_comments=Count('call_id')).filter(call_id__in=id_list):
        comments.append({'cid': c['call_id'], 'num': c['num_comments']})

    return HttpResponse(json.dumps(comments), 'application/json')


@login_required
@csrf_exempt
def get_call_comments(request):

    call_id = request.POST.get('call_id')
    comments_list = []
    for c in CallComment.objects.filter(call_id=call_id).order_by('pk'):
        comments_list.append(
            {'u': '{0} {1} {2}'.format(c.user.first_name or '-',
                                       c.user.middle_name or '-',
                                       c.user.last_name or '-'),
             'ts': c.added_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
             'contents': c.contents}
        )
    return HttpResponse(json.dumps(comments_list), 'application/json')


@login_required
@csrf_exempt
def add_call_comment(request):
    call_id = request.POST.get('call_id')
    contents = request.POST.get('contents')

    if call_id and contents:
        c = CallComment()
        c.contents = contents
        c.call_id = call_id
        c.user = request.user
        c.save()
    return HttpResponse('')


def get_wav_filename(provided_date, provided_uid):
    call_dir = os.path.join(settings.RECORDINGS_DIR, provided_date)
    file_name = None
    if os.path.exists(call_dir):
        for f in os.listdir(call_dir):
            if fnmatch.fnmatch(f, '*{0}*'.format(provided_uid)):
                file_name = os.path.join(call_dir, f)
    return file_name


@login_required
@csrf_exempt
def check_wav_file_exists(request):
    provided_date = request.POST.get('call_date') or request.GET.get('call_date')
    provided_uid = request.POST.get('call_uid') or request.GET.get('call_uid')
    file_name = get_wav_filename(provided_date, provided_uid)
    response = {'result': 'found' if file_name else 'none'}
    return JsonResponse(response)


@login_required
@csrf_exempt
def get_wav_file(request):
    provided_date = request.POST.get('call_date') or request.GET.get('call_date')
    provided_uid = request.POST.get('call_uid') or request.GET.get('call_uid')
    #if str(request.user) != 'admin@local.host':
    #    return HttpResponse('Unauthorized', 'text/plain')
    file_name = get_wav_filename(provided_date, provided_uid)
    if os.path.isfile(file_name):
        response = HttpResponse()
        f = open(file_name, 'rb')
        response['Content-Type'] = 'audio/x-wav'
        response['Content-Length'] = os.path.getsize(file_name)
        response['Content-Disposition'] = 'attachment; filename="%s"'\
                                          % os.path.basename(file_name)
        response.write(f.read())
        f.close()
        return response
    return HttpResponse('Unable to read file', 'text/plain')


@method_decorator(login_required, name='dispatch')
class IndexPage(PaginateFilterView):
    model = Cdr
    form_class = CdrFilterForm
    template_name = 'index.html'


@login_required
@csrf_exempt
def update_call_status(request):
    call_id = request.POST.get('call_id')
    is_new = request.POST.get('is_new')
    is_new = True if is_new == 'True' else False
    try:
        call = Cdr.objects.get(pk=call_id)
        new_status = not is_new
        if new_status:
            first_call = Cdr.objects.filter(src=call.src, is_new=True).first()
            if first_call and not first_call == call:
                return JsonResponse(
                    {'error_text': _(
                        'There was a call from this number on <br><b>{0}</b> (ID {1})'
                    ).format(formats.date_format(first_call.calldate, "DATETIME_FORMAT"), first_call.pk)},
                    status=409
                )
        call.is_new = new_status
        call.save()
        return JsonResponse({'error': False, 'is_new': new_status})
    except Cdr.DoesNotExist:
        return JsonResponse({'error': True, 'error_text': 'Call with id #{0} not found'.format(call_id)})
    except Exception as e:
        return JsonResponse({'error': True, 'error_text': e})


@method_decorator(login_required, name='dispatch')
class WebsitesPage(PaginateFilterView):
    model = Websites
    form_class = WebsitesForm
    template_name = 'websites/list.html'


@login_required
@csrf_exempt
def save_website_js(request):
    website_name = request.POST.get('website')
    website_id = request.POST.get('website_id')
    if not website_name:
        return JsonResponse({'error': True,
                             'error_text': 'Website name is empty'})
    if website_id:
        try:
            w = Websites.objects.get(pk=website_id)
            w.name = strip_tags(website_name.strip())
            w.save()
        except Websites.DoesNotExist:
            return JsonResponse(
                {'error': True,
                 'error_text': 'No website with id #{0}'.format(website_id)}
            )
        except Exception as e:
            return JsonResponse(
                {'error': True,
                 'error_text': 'ERROR: {0}'.format(e)}
            )

    else:
        w = Websites()
        w.name = strip_tags(website_name.strip())
        w.save()
        return JsonResponse({'error': False})
    return JsonResponse({'error': True, 'error_text': 'WTF'})


@method_decorator(login_required, name='dispatch')
class ExternalPhonesPage(PaginateFilterView):
    model = ExternalPhoneNumber
    form_class = ExternalPhonesListForm
    template_name = 'phones/external-phones.html'


@method_decorator(login_required, name='dispatch')
class ExternalPhoneAddView(View):
    model = ExternalPhonesPage
    form_class = ExternalPhoneEditForm
    template_name = 'phones/add-external-phone.html'
    success_url = reverse_lazy('external_phones')

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            self.object = form.save()
            return HttpResponseRedirect(
                reverse_lazy('external_phones')
            )

        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class ExternalPhoneEditView(UpdateView, ModelFormMixin):
    model = ExternalPhoneNumber
    form_class = ExternalPhoneEditForm
    template_name = 'phones/edit-external-phone.html'
    success_url = reverse_lazy('external_phones')

    def get_object(self, queryset=None):
        return ExternalPhoneNumber.objects.get(id=self.kwargs['pk'])

    def form_valid(self, form):
        self.object = form.save()
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ExternalPhoneEditView, self).get_context_data(**kwargs)
        return context


@method_decorator(login_required, name='dispatch')
class InternalPhonesPage(PaginateFilterView):
    model = InternalPhoneNumber
    form_class = InternalPhonesListForm
    template_name = 'phones/internal-phones.html'


@method_decorator(login_required, name='dispatch')
class InternalPhoneAddView(View):
    model = InternalPhoneNumber
    form_class = InternalPhoneEditForm
    template_name = 'phones/add-internal-phone.html'
    success_url = reverse_lazy('internal_phones')

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            self.object = form.save()
            return HttpResponseRedirect(
                reverse_lazy('internal_phones')
            )

        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class InternalPhoneEditView(UpdateView, ModelFormMixin):
    model = InternalPhoneNumber
    form_class = InternalPhoneEditForm
    template_name = 'phones/edit-internal-phone.html'
    success_url = reverse_lazy('internal_phones')

    def get_object(self, queryset=None):
        return InternalPhoneNumber.objects.get(id=self.kwargs['pk'])

    def form_valid(self, form):
        self.object = form.save()
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(InternalPhoneEditView, self).get_context_data(**kwargs)
        return context


@method_decorator(login_required, name='dispatch')
class EmployeesPage(PaginateFilterView):
    model = Employee
    form_class = EmployeeListForm
    template_name = 'employees/list.html'


@method_decorator(login_required, name='dispatch')
class EmployeeAddView(View):
    model = Employee
    form_class = EmployeeEditForm
    template_name = 'employees/add-employee.html'
    success_url = reverse_lazy('employees_page')

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            self.object = form.save()
            return HttpResponseRedirect(
                reverse_lazy('employees_page')
            )

        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class EmployeeEditView(UpdateView, ModelFormMixin):
    model = Employee
    form_class = EmployeeEditForm
    template_name = 'employees/edit-employee.html'
    success_url = reverse_lazy('employees_page')

    def get_object(self, queryset=None):
        return Employee.objects.get(id=self.kwargs['pk'])

    def form_valid(self, form):
        self.object = form.save()
        self.success_url = self.request.POST.get(
            'next',
            reverse_lazy('employees_page')
        )
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(EmployeeEditView, self).get_context_data(**kwargs)
        return context


@method_decorator(login_required, name='dispatch')
class DepartmentAddView(View):
    model = Department
    form_class = DepartmentEditForm
    template_name = 'employees/add-department.html'
    success_url = reverse_lazy('departments')

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            self.object = form.save()
            return HttpResponseRedirect(
                reverse_lazy('departments')
            )

        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class DepartmentEditView(UpdateView, ModelFormMixin):
    model = Department
    form_class = DepartmentEditForm
    template_name = 'employees/edit-department.html'
    success_url = reverse_lazy('departments')

    def get_object(self, queryset=None):
        return Department.objects.get(id=self.kwargs['pk'])

    def form_valid(self, form):
        self.object = form.save()
        self.success_url = self.request.POST.get(
            'next',
            reverse_lazy('departments')
        )
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(DepartmentEditView, self).get_context_data(**kwargs)
        return context


@method_decorator(login_required, name='dispatch')
class DepartmentPage(PaginateFilterView):
    model = Department
    form_class = DepartmentListForm
    template_name = 'employees/list-department.html'


@method_decorator(login_required, name='dispatch')
class StatPageView(TemplateView):
    template_name = 'stats.html'

    def get_context_data(self, **kwargs):
        date_start = self.request.POST.get('date_start') \
                     or self.request.GET.get('date_start') \
                     or self.request.COOKIES.get('date_start')
        date_end = self.request.POST.get('date_end') \
                     or self.request.GET.get('date_end') \
                     or self.request.COOKIES.get('date_end')
        form_initial = {}
        if date_start and date_end:
            form_initial = self.request.GET
        if not date_start:
            date_start = str(datetime.datetime.now().strftime('%Y-%m-%d 00:00'))
            form_initial['date_start'] = date_start
        if not date_end:
            date_end = str(datetime.datetime.now().strftime('%Y-%m-%d 23:59'))
            form_initial['date_end'] = date_end

        date_start_ts = int(time.mktime(datetime.datetime.strptime(
            date_start, '%Y-%m-%d %H:%M').timetuple()))
        date_end_ts = int(time.mktime(datetime.datetime.strptime(
            date_end, '%Y-%m-%d %H:%M').timetuple()))
        ts_diff = date_end_ts - date_start_ts
        date_interval = 'minute' if ts_diff < 48 * 60 * 60 else 'hour'
        if ts_diff < 48 * 60 * 60:
            date_interval = 'minute'
        elif ts_diff > 7 * 24 * 60 * 60:
            date_interval = 'day'
        else:
            date_interval = 'hour'
        context = super(StatPageView, self).get_context_data(**kwargs)
        context['form'] = StatsForm(initial=form_initial)
        context['general_stat'] = CdrManager().general_stat(
            date_start, date_end, date_interval)
        context['employee_stat'] = CdrManager().employee_stat(
            date_start, date_end)

        regional_data = CdrManager().get_regional_stat(date_start, date_end)
        context['regional_stat_all'] = regional_data['all']
        context['regional_stat_new'] = regional_data['new']

        context['employee_stat_daily'] = CdrManager().employee_stat_daily(
            date_start, date_end)
        context['call_status_stat'] = CdrManager().call_status_stat(
            date_start, date_end, date_interval)

        by_site_data = CdrManager().site_calls_stat(
            date_start, date_end, date_interval)
        context['site_calls_all'] = by_site_data['all']
        context['site_calls_new'] = by_site_data['new']

        return context
