# -*- coding: utf-8 -*-
from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.template import RequestContext


def index_page(request):
    return render(request, 'index.html')


def robots_txt(request):
    contents = "User-agent: *\n" \
               "Disallow: /"
    return HttpResponse(contents, 'text/plain')


def favicon_ico(request):
    return HttpResponse('', 'text/plain')


def error_403(request):
    response = render_to_response('errors/403.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 403
    return response


def error_404(request):
    response = render_to_response('errors/404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def error_500(request):
    response = render_to_response('errors/500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response
