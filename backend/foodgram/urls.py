from django.contrib import admin
from django.urls import path

from api.views import redirect_short_link

urlpatterns = [
    path('s/<str:short_code>/', redirect_short_link),
    path('admin/', admin.site.urls),
]
