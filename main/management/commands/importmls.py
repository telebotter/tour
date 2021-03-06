from django.core.management.base import BaseCommand, CommandError
from main.models import Tour
import geojson as gj

class Command(BaseCommand):
    help = 'enter multilinestring from jsonfile'

    def add_arguments(self, parser):
        parser.add_argument('tour', type=str)
        parser.add_argument('file', type=str)


    def handle(self, *args, **options):
        fpath = options['file']
        tname = options['tour']
        tour = Tour.objects.get(alias=tname)
        self.stdout.write('found tour: {}'.format(tour.name))
        with open(fpath, 'r') as rf:
            mls = gj.load(rf)
        #self.stdout.write(gj.dumps(mls))
        tour.track = mls
        tour.save()
