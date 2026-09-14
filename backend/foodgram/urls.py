from django.contrib import admin
from django.urls import include, path

from api.views import redirect_short_link

urlpatterns = [
    path('s/<str:short_code>/', redirect_short_link),
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]
