from django.urls import path
from bilder import views as bilder_views

urlpatterns = [
    path('', views.index, name='index_bilder'),
    path('<touralias>/', bilder_views.album, name='tour_bilder')
    # path('<touralias>/', views.tour, name='tour_karte'),
    # path('<touralias>/<int:tagnummer>', views.tag, name='schlafplatz'),
]