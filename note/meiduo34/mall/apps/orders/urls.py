from django.conf.urls import url
from . import views

urlpatterns = [
    #/orders/places/
    url(r'^places/$',views.PlaceOrderView.as_view(),name='placeorder'),
    #/orders/
    url(r'^$',views.OrderView.as_view(),name='commitorder'),
]