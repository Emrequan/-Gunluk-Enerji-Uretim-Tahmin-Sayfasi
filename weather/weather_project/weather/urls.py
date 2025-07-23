# weather/urls.py
from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.index, name='index'),  # Ana sayfa için index view'ı
    path('show-excel/', views.show_excel_data, name='show_excel_data'),  # Excel verilerini göstermek için
    path('update-from-gmail/', views.update_from_gmail, name='update_from_gmail'),  # Gmail'den güncelleme için
]
