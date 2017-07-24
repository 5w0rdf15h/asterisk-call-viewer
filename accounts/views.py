from django.shortcuts import render, redirect
from accounts.forms import LoginForm
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.conf import settings


def login(request):
    next_url = request.GET.get('next') or request.POST.get('next') or '/'
    if request.user.is_authenticated():
        return redirect(next_url)
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request,
                         initial={'next': next_url})
        if form.is_valid():
            auth_login(request, form.authorized_user)
            return redirect(next_url)
    data = {'form': LoginForm()}
    return render(request, 'accounts/login.html', data)


def logout(request):
    next_url = request.GET.get('next') or request.POST.get('next') or \
               settings.AUTH_HOMEPAGE
    auth_logout(request)
    return redirect(next_url)


def check_rosetta_access(user):
    """Need this to check access to translation app (rosetta)"""
    return user.is_staff
