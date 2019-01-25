from django.conf.urls import url
from . import views


urlpatterns = [
    #/goods/categories/
    url(r'^categories/$',views.CategoryView.as_view(),name='cagegories'),
    #/goods/categories/(?P<category_id>\d+)/hotskus/
    url(r'^categories/(?P<category_id>\d+)/hotskus/$',views.HotSKUListView.as_view(),name='hot'),
    #/goods/categories/(?P<category_id>\d+)/skus/
    url(r'^categories/(?P<category_id>\d+)/skus/$',views.SKUListView.as_view(),name='list'),

]
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('search', views.SKUSearchViewSet, base_name='skus_search')

urlpatterns += router.urls