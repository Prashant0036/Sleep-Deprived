from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video', views.video, name='video'),
    path('apitest', views.apitest, name='apitest'),
    path('instructions/', views.instructions, name='instructions'),
    path('resources/', views.resources, name='resources'),
    path('contact/', views.contact, name='contact'),
    path('suggestions/', views.suggestions, name='suggestions'),
    path('previous_searches_data/', views.previous_searches_data, name='previous_searches_data'),
    path('search_suggestions_data/', views.search_suggestions_data, name='search_suggestions_data'),
]