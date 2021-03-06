"""tour URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls import url
from django.urls import include, path
from django.contrib import admin
from markdownx import urls as mdurls

urlpatterns = [
    path('admin/', admin.site.urls, name='tour_admin'),
    path('', include('main.urls')),
    path('karte/', include('karte.urls')),
    path('logbuch/', include('logbuch.urls')),
    path('bilder/', include('bilder.urls')),
    path('markdownx/', include(mdurls)),
    url(r'^', include('django_telegrambot.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns= urlpatterns + static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
    urlpatterns= urlpatterns + static(settings.STATIC_URL, document_root= settings.STATIC_ROOT)
