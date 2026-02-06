from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MarketViewSet, PositionViewSet, TradeViewSet, LoginView, ChangePasswordView

router = DefaultRouter()
router.register(r'markets', MarketViewSet)
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'trades', TradeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
