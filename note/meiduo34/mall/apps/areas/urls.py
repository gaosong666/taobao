# from django.conf.urls import url,include
# from rest_framework.routers import DefaultRouter
# # from .views import AreaViewSet
# from areas import views
# from areas.views import AreasViewSet
#
# router = DefaultRouter()
# router.register(r'infos',views.AreasViewSet,base_name='area')
# router.register(r'addresses',views.AddressViewSet,base_name='address')
# urlpatterns = [
#     # url(r'^',include(router.urls))
# ]
# urlpatterns += router.urls
#
# # from .views import AddressViewSet
# # from rest_framework.routers import DefaultRouter
# # router = DefaultRouter()
# #
# # #添加省市区信息查询路由
# # urlpatterns += router.urls
#
# # from django.conf.urls import url
# # from . import views
# #
# # urlpatterns = [
# #
# # ]
# #
# # #创建地址url
# # from rest_framework.routers import DefaultRouter
# # router = DefaultRouter()
# # router.register(r'infos',views.AreaViewSet,base_name='area')
# # urlpatterns += router.urls
# #
from django.conf.urls import url

from areas.views import  AreasViewSet
# from . import views

urlpatterns = [

]

#创建地址url
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'infos',AreasViewSet,base_name='area')
# router.register(r'addresses',AddressViewSet,base_name='address')
urlpatterns += router.urls

