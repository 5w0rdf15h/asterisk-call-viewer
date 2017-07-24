# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django import forms
from django.utils.html import strip_tags
from asterisk.models import (
    Cdr, Websites, ExternalPhoneNumber, InternalPhoneNumber, Employee,
    Department
)
from django.db.models import Q

PAGINATE_NUM_ITEMS = (
    (20, 20),
    (50, 50),
    (100, 100),
    (500, 500),
    (1000, 1000)
)


class CdrFilterForm(forms.ModelForm):
    sort = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    date_start = forms.CharField(
        label='Дата от',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    date_end = forms.CharField(
        label='Дата до',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    src = forms.CharField(
        label='Исходящий номер',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    dst = forms.CharField(
        label='Набранный номер',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    num_items_on_page = forms.ChoiceField(
        label='Количество результатов на страницу',
        choices=PAGINATE_NUM_ITEMS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    website = forms.ModelChoiceField(
        label='Сайт',
        queryset=Websites.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    def get_queryset(self):
        data = self.cleaned_data

        qs = Cdr.objects.all().order_by('-pk')
        if data.get('sort'):
            qs = qs.order_by(data.get('sort'))
        if data.get('src'):
            qs = qs.filter(src__icontains=data.get('src'))
        if data.get('dst'):
            qs = qs.filter(dst__icontains=data.get('dst'))
        if data.get('date_start'):
            qs = qs.filter(calldate__gte=data.get('date_start'))
        if data.get('date_end'):
            qs = qs.filter(calldate__lte=data.get('date_end'))
        if data.get('website'):
            phones_list = []
            for p in ExternalPhoneNumber.objects.filter(website=data.get('website')):
                alias_1 = '+{0}'.format(p.phone_number)
                alias_2 = '8{0}'.format(str(p.phone_number)[1:len(str(p.phone_number))])
                alias_3 = str(p.phone_number)[1:len(str(p.phone_number))]
                if p.phone_number not in phones_list:
                    phones_list.append(p.phone_number)
                    phones_list.append(alias_1)
                    phones_list.append(alias_2)
                    phones_list.append(alias_3)
            qs = qs.filter(Q(userfield__in=phones_list))

        return qs

    class Meta:
        model = Cdr
        exclude = []


class WebsitesForm(forms.ModelForm):
    num_items_on_page = forms.ChoiceField(
        label='Количество результатов на страницу',
        choices=PAGINATE_NUM_ITEMS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    sort = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    name = forms.CharField(
        label='Название',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )

    def get_queryset(self):
        data = self.cleaned_data
        qs = Websites.objects.all().order_by('-pk')
        if data.get('sort'):
            qs = qs.order_by(data.get('sort'))
        if data.get('name'):
            qs = qs.filter(name__icontains=data.get('name'))
        return qs

    class Meta:
        model = Websites
        exclude = []


class ExternalPhonesListForm(forms.ModelForm):
    phone_number = forms.CharField(
        label='Номер телефона',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    website = forms.ModelChoiceField(
        label='Сайт',
        queryset=Websites.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    num_items_on_page = forms.ChoiceField(
        label='Количество результатов на страницу',
        choices=PAGINATE_NUM_ITEMS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    sort = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def get_queryset(self):
        data = self.cleaned_data
        qs = ExternalPhoneNumber.objects.all().order_by('-pk')
        if data.get('sort'):
            qs = qs.order_by(data.get('sort'))
        if data.get('phone_number'):
            qs = qs.filter(phone_number__icontains=data.get('phone_number'))
        if data.get('website'):
            qs = qs.filter(website=data.get('website'))
        return qs

    class Meta:
        model = ExternalPhoneNumber
        exclude = []


class ExternalPhoneEditForm(forms.ModelForm):
    phone_number = forms.CharField(
        label='Номер телефона',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=True
    )
    website = forms.ModelChoiceField(
        label='Сайт',
        queryset=Websites.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    note = forms.CharField(
        label='Примечание, 500 символов максимум (необязательно)',
        widget=forms.Textarea(
            attrs={'class': 'form-control'}
        ),
        required=False
    )

    def clean(self):
        cleaned_data = super(ExternalPhoneEditForm, self).clean()
        cleaned_data['phone_number'] = strip_tags(
            cleaned_data.get('phone_number').strip()
        )
        return cleaned_data

    class Meta:
        model = ExternalPhoneNumber
        exclude = []


class InternalPhonesListForm(forms.ModelForm):
    phone_number = forms.CharField(
        label='Номер телефона',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    employee = forms.ModelChoiceField(
        label='Сотрудник',
        queryset=Employee.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    department = forms.ModelChoiceField(
        label='Департамент/Отдел',
        queryset=Department.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    num_items_on_page = forms.ChoiceField(
        label='Количество результатов на страницу',
        choices=PAGINATE_NUM_ITEMS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    sort = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean(self):
        cleaned_data = super(InternalPhonesListForm, self).clean()
        cleaned_data['phone_number'] = strip_tags(
            cleaned_data.get('phone_number').strip()
        )
        return cleaned_data

    def get_queryset(self):
        data = self.cleaned_data
        qs = InternalPhoneNumber.objects.all().order_by('-pk')
        if data.get('sort'):
            qs = qs.order_by(data.get('sort'))
        if data.get('phone_number'):
            qs = qs.filter(phone_number__icontains=data.get('phone_number'))
        if data.get('employee'):
            qs = qs.filter(employee=data.get('employee'))
        if data.get('department'):
            qs = qs.filter(department=data.get('department'))
        return qs

    class Meta:
        model = InternalPhoneNumber
        exclude = []


class InternalPhoneEditForm(forms.ModelForm):
    phone_number = forms.CharField(
        label='Номер телефона',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=True
    )
    employee = forms.ModelChoiceField(
        label='Сотрудник (необязательно)',
        queryset=Employee.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    department = forms.ModelChoiceField(
        label='Департамент/Отдел (необязательно)',
        queryset=Department.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    def clean(self):
        cleaned_data = super(InternalPhoneEditForm, self).clean()
        cleaned_data['phone_number'] = strip_tags(
            cleaned_data.get('phone_number').strip()
        )
        return cleaned_data

    class Meta:
        model = InternalPhoneNumber
        exclude = []


class EmployeeListForm(forms.ModelForm):
    name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    department = forms.ModelChoiceField(
        label='Департамент/Отдел',
        queryset=Department.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    num_items_on_page = forms.ChoiceField(
        label='Количество результатов на страницу',
        choices=PAGINATE_NUM_ITEMS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    sort = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean(self):
        cleaned_data = super(EmployeeListForm, self).clean()
        cleaned_data['name'] = strip_tags(
            cleaned_data.get('name').strip()
        )
        return cleaned_data

    def get_queryset(self):
        data = self.cleaned_data
        qs = Employee.objects.all().order_by('name')
        if data.get('sort'):
            qs = qs.order_by(data.get('sort'))
        if data.get('name'):
            qs = qs.filter(name__icontains=data.get('name'))
        if data.get('department'):
            qs = qs.filter(department=data.get('department'))
        return qs

    class Meta:
        model = Employee
        exclude = ['name']


class EmployeeEditForm(forms.ModelForm):
    name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    department = forms.ModelChoiceField(
        label='Департамент/Отдел',
        queryset=Department.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Employee
        exclude = []


class DepartmentListForm(forms.ModelForm):
    name = forms.CharField(
        label='Название',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    num_items_on_page = forms.ChoiceField(
        label='Количество результатов на страницу',
        choices=PAGINATE_NUM_ITEMS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    sort = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def get_queryset(self):
        data = self.cleaned_data
        qs = Department.objects.all().order_by('name')
        if data.get('sort'):
            qs = qs.order_by(data.get('sort'))
        if data.get('name'):
            qs = qs.filter(name__icontains=data.get('name'))
        return qs

    class Meta:
        model = Department
        exclude = []


class DepartmentEditForm(forms.ModelForm):
    name = forms.CharField(
        label='Название',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )

    class Meta:
        model = Department
        exclude = []


class StatsForm(forms.Form):
    date_start = forms.CharField(
        label='Дата от',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )
    date_end = forms.CharField(
        label='Дата до',
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ),
        required=False
    )