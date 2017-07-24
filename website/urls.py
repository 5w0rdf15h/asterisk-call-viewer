from django.conf import settings
from django.conf.urls import include, url

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from website.views import (index_page, robots_txt, error_403,
                            error_404, error_500, favicon_ico)
from accounts.views import login, logout
from asterisk.views import (
    IndexPage, WebsitesPage, save_website_js, ExternalPhonesPage,
    ExternalPhoneAddView, ExternalPhoneEditView, InternalPhonesPage,
    InternalPhoneAddView, InternalPhoneEditView, EmployeesPage,
    EmployeeAddView, EmployeeEditView, StatPageView, DepartmentPage,
    DepartmentAddView, DepartmentEditView, update_call_status,
    check_wav_file_exists, get_wav_file, get_num_comments, add_call_comment,
    get_call_comments
)
admin.autodiscover()

urlpatterns = [
    url(r'^$', IndexPage.as_view(), name='home'),
    url(r'^get-num-comments/$', get_num_comments, name='get_num_comments'),
    url(r'^add-call-comment/$', add_call_comment, name='add_call_comment'),
    url(r'^get-call-comments/$', get_call_comments, name='get_call_comments'),
    url(r'^update-call-status/$', update_call_status,
        name='update_call_status'),
    url(r'^check-wav-file-exists/$', check_wav_file_exists,
        name='check_wav_file_exists'),
    url(r'^get-wav-file/$', get_wav_file, name='get_wav_file'),
    # url(r'^favicon.ico$', favicon_ico, name='favicon_ico'),
    url(r'^robots.txt$', robots_txt, name='robots_txt'),
    url(r'^login/$', login, name='main_login'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^websites/$', WebsitesPage.as_view(), name='websites'),
    url(r'^external-phones/$', ExternalPhonesPage.as_view(),
        name='external_phones'),
    url(r'^external-phone-add/$', ExternalPhoneAddView.as_view(),
        name='external_phone_add'),
    url(r'^external-phone-edit/(?P<pk>[\w-]+)/$',
        ExternalPhoneEditView.as_view(), name='external_phone_edit'),
    url(r'^internal-phones/$', InternalPhonesPage.as_view(),
        name='internal_phones'),
    url(r'^internal-phone-add/$', InternalPhoneAddView.as_view(),
        name='internal_phone_add'),
    url(r'^internal-phone-edit/(?P<pk>[\w-]+)/$',
        InternalPhoneEditView.as_view(), name='internal_phone_edit'),
    url(r'^add-website/$', login_required(save_website_js),
        name='save_website_js'),
    url(r'^employees-list/$', EmployeesPage.as_view(), name='employees_page'),
    url(r'^employee-add/$', EmployeeAddView.as_view(), name='employee_add'),
    url(r'^employee-edit/(?P<pk>[\w-]+)/$', EmployeeEditView.as_view(),
        name='employee_edit'),
    url(r'^departments/$', DepartmentPage.as_view(), name='departments'),
    url(r'^department-add/$', DepartmentAddView.as_view(),
        name='department_add'),
    url(r'^department-edit/(?P<pk>[\w-]+)/$', DepartmentEditView.as_view(),
        name='department_edit'),
    url(r'^statistics/$', StatPageView.as_view(), name='stats'),
    url(r'^admin/', include(admin.site.urls)),
]

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^rosetta/', include('rosetta.urls')),
    ]
