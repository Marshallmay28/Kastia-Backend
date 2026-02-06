"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Admin Site Customization
admin.site.site_header = "Kastia Administration"
admin.site.site_title = "Kastia Admin Portal"
admin.site.index_title = "Welcome to Kastia Management"

def health(request):
    """Health check endpoint"""
    return JsonResponse({
        "status": "online",
        "message": "Kastia Backend is running",
        "version": "1.0.0",
        "endpoints": {
            "admin": "/admin/",
            "api": "/api/",
            "health": "/health/"
        }
    })

def redirect_to_admin(request):
    """Root redirect to admin"""
    return JsonResponse({
        "message": "Kastia Backend API",
        "admin": "/admin/",
        "api": "/api/"
    })

urlpatterns = [
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', redirect_to_admin, name='root'),
]
