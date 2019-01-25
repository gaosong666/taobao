# #coding:utf8
# from rest_framework import serializers
# from .models import OAuthQQUser
# from django_redis import get_redis_connection
# from users.models import User
#
#
# class QQAuthUserSerializer(serializers.Serializer):
#
#     access_token = serializers.CharField(label='操作token')
#     mobile = serializers.RegexField(label='手机号', regex=r'^1[345789]\d{9}$')
#     password = serializers.CharField(label='密码', max_length=20, min_length=8)
#     sms_code = serializers.CharField(label='短信验证码', max_length=6, min_length=6)
#
#
#     def validate(self, attrs):
#
#         #判断短信验证码是否正确
#         sms_code = attrs.get('sms_code')
#         mobile = attrs.get('mobile')
#         redis_conn = get_redis_connection('code')
#         redis_code = redis_conn.get('sms_%s'%mobile)
#         if redis_code is None:
#             raise serializers.ValidationError('短信验证码过期')
#         if redis_code.decode() != sms_code:
#             raise serializers.ValidationError('短信验证码不一致')
#
#         #判断token
#         token = attrs.get('access_token')
#         openid = OAuthQQUser.check_user_token(token)
#         if openid is None:
#             raise serializers.ValidationError('绑定验证码失效')
#         #将openid放置到 attr中备用
#         attrs['openid'] = openid
#
#         #判断手机号是否被注册
#         try:
#             user = User.objects.get(mobile=mobile)
#         except User.DoesNotExist:
#             user = None
#         else:
#             #判断用户的密码是否正确
#             if not user.check_password(attrs['password']):
#                 raise serializers.ValidationError('密码错误')
#             attrs['user'] = user
#
#
#         return attrs
#
#     #数据入库
#     def create(self, validated_data):
#
#         user = validated_data.get('user')
#
#         if user is None:
#             user = User.objects.create(
#                 username = validated_data['username'],
#                 password = validated_data['password'],
#                 mobile = validated_data['mobile']
#             )
#             user.set_password(validated_data['password'])
#
#         qquser = OAuthQQUser.objects.create(
#             user = user,
#             openid = validated_data['openid']
#         )
#
#         return user
import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.settings import api_settings

from mall import settings
from oauth.models import OAuthQQUser, OAuthSinaUser
from oauth.utils import check_save_user_token
from users.models import User
from verifications.views import RegisterSMSCodeView


class QQAuthUserSerializer(serializers.Serializer):
    """
    QQ登录创建用户序列化器
    """
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, data):
        # 检验access_token
        access_token = data['access_token']
        # 获取身份凭证
        openid = check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError('无效的access_token')

        # 将openid放在校验字典中，后面会使用
        data['openid'] = openid

        # 检验短信验证码
        mobile = data['mobile']
        sms_code = data['sms_code']
        redis_conn = get_redis_connection('code')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        # 如果用户存在，检查用户密码
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = data['password']
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')

            # 将认证后的user放进校验字典中，后续会使用
            data['user'] = user
        return data

    def create(self, validated_data):
        # 获取校验的用户
        user = validated_data.get('user')

        if not user:
            # 用s户不存在,新建用户
            user = User.objects.create_user(
                username=validated_data['mobile'],
                password=validated_data['password'],
                mobile=validated_data['mobile'],
            )

        # 将用户绑定openid
        OAuthQQUser.objects.create(
            openid=validated_data['openid'],
            user=user
        )
        # 返回用户数据
        return user


from itsdangerous import TimedJSONWebSignatureSerializer as TJS
class WeiboOauthSerializers(serializers.ModelSerializer):
    """微博验证序列化器"""

    # 指名模型类中没有的字段
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    # mobile = serializers.CharField(max_length=11)
    sms_code = serializers.CharField(max_length=6, min_length=6, write_only=True)
    access_token = serializers.CharField(write_only=True)  # 反序列化输入

    token = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)  # 序列化输出

    class Meta:
        model = User
        fields = ('password', 'mobile', 'username', 'sms_code', 'token', 'access_token', 'user_id')

        extra_kwargs = {
            'username': {
                'read_only': True
            },
            'password': {
                'write_only': True
            }
        }

    def validated_mobile(self, value):
        """
        验证手机号
        :param value:
        :return:
        """
        if not re.match(r"1[3-9]\d{9}$", value):
            raise serializers.ValidationError("手机号格式错误")
        return value

    def validate(self, attrs):
        """
        验证access_token
        :param attrs:
        :return:
        """
        tjs = TJS(settings.SECRET_KEY, 300)
        try:
            data = tjs.loads(attrs["access_token"])  # 解析token
        except:
            raise serializers.ValidationError("无效的token")

        # 获取weibotoken
        weibotoken = data.get("weibotoken")
        # attrs中添加weibotoken
        attrs["weibotoken"] = weibotoken
        # # 验证短信验证码:
        # rel_sms_code = RegisterSMSCodeView.checkSMSCode(attrs["mobile"])
        # if not rel_sms_code:
        #     raise serializers.ValidationError('短信验证码失效')
        # 检验短信验证码
        mobile = data['mobile']
        sms_code = data['sms_code']
        redis_conn = get_redis_connection('code')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

            # 3、比对用户输入的短信和redis中真实短信
        if attrs['sms_code'] != real_sms_code:
            raise serializers.ValidationError('短信验证不一致')
        # 验证手机号是否被注册过
        try:
            user = User.objects.get(mobile=attrs['mobile'])
        except:
            # 未注册过，注册为新用户
            return attrs
        else:
            # 注册过 查询用户进行绑定
            # 判断密码
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError('密码错误')
            attrs['user'] = user
            return attrs

    def create(self, validated_data):
        """
        保存用户
        :param self:
        :param validated_data:
        :return:
        """
        # 判断用户
        user = validated_data.get('user', None)
        if user is None:
            # 创建用户
            user = User.objects.create_user(username=validated_data['mobile'],
                                            password=validated_data['password'],
                                            mobile=validated_data['mobile'])
        # 绑定操作
        OAuthSinaUser.objects.create(user=user, weibotoken=validated_data["weibotoken"])
        # user_id=user.id
        # 生成加密后的token数据
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)  # 生成载荷部分
        token = jwt_encode_handler(payload)  # 生成token

        # user添加token属性
        user.token = token
        user.user_id = user.id

        return user
