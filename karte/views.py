from django.shortcuts import render, get_object_or_404, get_list_or_404
from main.models import Tour
from djgeojson.serializers import Serializer as GeoJSONSerializer
from karte.models import Schlafplatz
from django.http import HttpResponse
# Create your views here.

def index(request):
    #schlaf_plaetze = get_list_or_404(Schlafplatz)
    context = {}
    return render(request, 'karte/index.html')


def data_tour(request, touralias):
    tour = get_object_or_404(Tour, alias=touralias)
    context = {}
    #context['color'] = tour.color
    geoms = Schlafplatz.objects.all()
    return GeoJSONSerializer().serialize(Schlafplatz.objects.all(),
                                  use_natural_keys=True, with_modelname=False)

