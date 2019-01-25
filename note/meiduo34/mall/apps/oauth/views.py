from QQLoginTool.QQtool import OAuthQQ
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from carts.utils import merge_cart_cookie_to_redis
from mall import settings
from oauth import serializers
from oauth.models import OAuthQQUser, OAuthSinaUser
from oauth.serializers import WeiboOauthSerializers
from oauth.utils import generate_save_token, OAuthWeibo


class QQAuthURLView(APIView):
    """
    提供QQ登录页面网址

    """

    def get(self, request):
        # next表示从哪个页面进入到的登录页面，将来登录成功后，就自动回到那个页面
        state = request.query_params.get('state')
        if not state:
            state = '/'

        # 获取QQ登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=state)
        login_url = oauth.get_qq_url()

        return Response({'login_url': login_url})


class QQAuthUserView(GenericAPIView):
    """用户扫码登录的回调处理"""

    # 指定序列化器
    serializer_class = serializers.QQAuthUserSerializer

    def get(self, request):
        # 提取code请求参数
        code = request.query_params.get('code')
        if not code:
            return Response({'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 使用code向QQ服务器请求access_token
            access_token = oauth.get_access_token(code)

            # 使用access_token向QQ服务器请求openid
            openid = oauth.get_open_id(access_token)
        except Exception:
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 使用openid查询该QQ用户是否在美多商城中绑定过用户
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果openid没绑定美多商城用户，创建用户并绑定到openid
            # 为了能够在后续的绑定用户操作中前端可以使用openid，在这里将openid签名后响应给前端
            access_token_openid = generate_save_token(openid)
            return Response({'access_token': access_token_openid})
        else:
            # 如果openid已绑定美多商城用户，直接生成JWT token，并返回
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            # 获取oauth_user关联的user
            user = oauth_user.user
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            response = Response({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })
            response = merge_cart_cookie_to_redis(request, user, response)

            return response

    def post(self, request):
        """openid绑定到用户"""

        # 获取序列化器对象
        serializer = self.get_serializer(data=request.data)
        # 开启校验
        serializer.is_valid(raise_exception=True)
        # 保存校验结果，并接收
        user = serializer.save()

        # 生成JWT token，并响应
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = Response({
            'token': token,
            'user_id': user.id,
            'username': user.username
        })

        response = merge_cart_cookie_to_redis(request, user, response)

        return response



class WeiboAuthURLLView(APIView):
    """定义微博第三方登录的视图类"""
    def get(self, request):
        """
        获取微博登录的链接
        oauth/weibo/authorization/?next=/
        :param request:
        :return:
        """
        # 1.通过查询字符串
        next = request.query_params.get('state')
        if not next:
            next = "/"

        # 获取微博登录网页
        oauth = OAuthWeibo(client_id=settings.WEIBO_CLIENT_ID,
                        client_secret=settings.WEIBO_CLIENT_SECRET,
                        redirect_uri=settings.WEIBO_REDIRECT_URI,
                        state=next)
        login_url = oauth.get_weibo_url()
        return Response({"login_url": login_url})



from itsdangerous import TimedJSONWebSignatureSerializer as TJS
class WeiboOauthView(APIView):
    """验证微博登录"""
    def get(self, request):
        """
        第三方登录检查
        oauth/sina/user/
        ?code=0e67548e9e075577630cc983ff79fa6a
        :param request:
        :return:
        """
        # 1.获取code值
        code = request.query_params.get("code")

        # 2.检查参数
        if not code:
            return Response({'errors': '缺少code值'}, status=400)

        # 3.获取token值
        next = "/"

        # 获取微博登录网页
        weiboauth = OAuthWeibo(client_id=settings.WEIBO_CLIENT_ID,
                        client_secret=settings.WEIBO_CLIENT_SECRET,
                        redirect_uri=settings.WEIBO_REDIRECT_URI,
                        state=next)
        weibotoken = weiboauth.get_access_token(code=code)
        print(weibotoken)

        # 5.判断是否绑定过美多账号
        try:
            weibo_user = OAuthSinaUser.objects.get(weibotoken=weibotoken)
        except:
            # 6.未绑定,进入绑定页面,完成绑定
            tjs = TJS(settings.SECRET_KEY, 300)
            weibotoken = tjs.dumps({'weibotoken': weibotoken}).decode()

            return Response({'access_token': weibotoken})
        else:
            # 7.绑定过,则登录成功
            # 生成jwt-token值
            user = weibo_user.user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)  # 生成载荷部分
            token = jwt_encode_handler(payload)  # 生成token

            response = Response(
                {
                    'token': token,
                    'username': user.username,
                    'user_id': user.id
                }
            )

        return response

    def post(self, request):
        """
        微博用户未绑定,绑定微博用户
        :return:
        """
        # 1. 获取前端数据
        data = request.data
        # 2.调用序列化起验证数据
        ser = WeiboOauthSerializers(data=data)
        ser.is_valid()
        print(ser.errors)
        # 保存绑定数据
        ser.save()
        return Response(ser.data)

