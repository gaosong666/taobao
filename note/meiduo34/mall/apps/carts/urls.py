from django.conf.urls import url
from . import views

urlpatterns = [
    # /carts/
    url(r'^$',views.CartView.as_view(),name='cart'),
]
