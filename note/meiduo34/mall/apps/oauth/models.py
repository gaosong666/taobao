from django.db import models

# Create your models here.
from django.db import models

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData

from mall import settings
from utils.models import BaseModel


class OAuthQQUser(BaseModel):
    """
    QQ登录用户数据
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, unique=True, verbose_name='openid', db_index=True)


    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name

    @classmethod
    def generate_save_user_token(cls, openid):

        serializer = Serializer(settings.SECRET_KEY, 3600)

        token = serializer.dumps({'openid': openid})

        return token.decode()

    @classmethod
    def check_user_token(cls, token):

        serializer = Serializer(settings.SECRET_KEY, 3600)

        try:
            result = serializer.loads(token)

        except BadData:
            return None
        else:
            openid = result.get('openid')
            return openid

# class OAuthweiboUser(BaseModel):
#     """
#     微博登录用户数据
#     """
#     user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
#     openid = models.CharField(max_length=64, unique=True, verbose_name='openid', db_index=True)
#     weibotoken = models.CharField(max_length=64, verbose_name='weibotoken', db_index=True)  # 微博用户登录Access_token
#
#     class Meta:
#         db_table = 'tb_oauth_weibo'
#         verbose_name = '微博登录用户数据'
#         verbose_name_plural = verbose_name
from django.db import models
from utils.models import BaseModel

class OAuthSinaUser(BaseModel):
    """
    Sina登录用户数据
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    access_token = models.CharField(max_length=64, verbose_name='access_token', db_index=True)

    class Meta:
        db_table = 'tb_oauth_sina'
        verbose_name = 'sina登录用户数据'
        verbose_name_plural = verbose_name




                # @classmethod
    # def generate_save_user_token(cls, openid):
    #
    #     # serializer = Serializer(settings.SECRET_KEY, 3600)
    #     #
    #     # token = serializer.dumps({'openid': openid})
    #     serializer = Serializer(settings.SECRET_KEY, 3600)
    #     token = serializer.dumps({'openid': openid})
    #
    #     return token.decode()
    #
    # @classmethod
    # def check_user_token(cls, token):
    #
    #     serializer = Serializer(settings.SECRET_KEY, 3600)
    #
    #     try:
    #         result = serializer.loads(token)
    #
    #     except BadData:
    #         return None
    #     else:
    #         openid = result.get('openid')
    #         return openid







