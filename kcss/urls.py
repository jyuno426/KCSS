from django.urls import path
from . import views

app_name = "kcss"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("sort/", views.SortView.as_view(), name="sort"),
    path("women/", views.WomenView.as_view(), name="women"),
    path("<str:type>/results/", views.ResultsView.as_view(), name="results"),
    path("results/", views.ResultsView.as_view(), name="results"),
]
