from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    #/users/usernames/(?P<username>\w{5,20})/count/
    url(r'^usernames/(?P<username>\w{5,20})/count/$',views.RegisterUsernameCountAPIView.as_view(),name='usernamecount'),
    #/users/phones/(?P<mobile>1[345789]\d{9})/count/
    url(r'^phones/(?P<mobile>1[345789]\d{9})/count/$',views.RegisterPhoneCountAPIView.as_view(),name='phonecount'),
    url(r'^$',views.RegisterCreateView.as_view()),

    #/users/auths/
    # url(r'auths/', obtain_jwt_token, name='auths'),
    url(r'auths/',views.UserAuthorizationView.as_view(),name='auths'),

    #GET /users/infos/
    url(r'^infos/$',views.UserDetailView.as_view(),name='detail'),
    #PUT /users/emails/
    url(r'^emails/$',views.EmailView.as_view(),name='send_mail'),
    # url(r'^adrresses/$',views.UserDetailView.as_view(),name='detail'),
    # /users/emails/verification/
    url(r'^emails/verification/$', views.VerificationEmailView.as_view()),
    #/users/browerhistories/
    url(r'^browerhistories/$',views.UserBrowsingHistoryView.as_view(),name='history'),


]
from .views import AddressViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'addresses',AddressViewSet,base_name='address')
urlpatterns += router.urls
