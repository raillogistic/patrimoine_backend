from django.utils.encoding import smart_str
import os
from django.conf import settings
from django.http import FileResponse
import tempfile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required

from django.contrib.auth import authenticate, login as log, logout as out
from root.settings import STATIC_URL
from django.db.models import ForeignKey, ManyToManyField

from django.apps import apps
import json
from django.http import HttpResponse
from django.shortcuts import redirect, render
import xlwt


from django import template

register = template.Library()


@register.filter(name='get')
def get(d, k):
    return d.get(k, None)


@login_required(login_url='/login')
def index(request):
    return render(request, 'index.html', {
        'STATIC_URL': STATIC_URL
    })


def upload(request):
    return HttpResponse('xdsd')


def not_found(request):
    return render(request, '404.html')


def import_model(request):
    return render(request, 'export.html', {"models": apps.get_models("relations")})


def login(request):
    if request.user.is_authenticated:
        return redirect("/")

    if (request.POST):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            try:
                log(request, user)
            except:
                return redirect('/login')
            return redirect('/')
        else:
            return render(request, 'login.html', {"message": "informations d'identification non valides, veuillez réessayer"})
    return render(request, 'login.html')


def export(request, url):
    try:
        path = os.path.join(settings.MEDIA_ROOT, "export", url)
        file = open(path, 'rb')
        response = FileResponse(file)
        # os.remove(path)
        return response
    except:
        return render(request, '404.html')
