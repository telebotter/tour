#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.urls import include, path
from django.contrib import admin
from main import views


urlpatterns = [
    path('/', views.index, name='index'),
    #path('karte/', include('karte.urls')),
    #path('bilder/', include('bilder.urls')),
]