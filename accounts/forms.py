# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.contrib.auth import authenticate
import datetime


class LoginForm(forms.Form):

    email = forms.CharField(
        max_length=255,
        required=True,
        label='Email',
        widget=forms.widgets.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.widgets.PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль'
    )
    next = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput()
    )
    authorized_user = None

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(LoginForm, self).clean()
        if 'captcha' not in self._errors:

            user = authenticate(
                username=data['email'],
                password=data['password']
            )

            ip_address = self.request.META['REMOTE_ADDR']
            if user is None:
                raise forms.ValidationError(
                    'Неправильный email или пароль'
                )
            else:
                user.last_login_ip = ip_address
                user.last_login = datetime.datetime.now()
                user.save()
            if not user.is_active:
                raise forms.ValidationError(
                    'Пользователь заблокирован'
                )
            self.authorized_user = user
        return data