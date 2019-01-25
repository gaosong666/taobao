from django.conf.urls import url
from . import views

urlpatterns = [
    #/oauth/qq/statues/
    url(r'^qq/statues/$',views.QQAuthURLView.as_view()),
    #qq/users/
    url(r'^qq/users/$',views.QQAuthUserView.as_view()),
    # oauth/weibo/authorization/
    url(r'^weibo/authorization/$',views.WeiboAuthURLLView.as_view()),
    # oauth/sina/user/
    url(r'^sina/user/$',views.WeiboOauthView.as_view()),
]