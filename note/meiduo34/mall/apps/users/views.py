from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.views import ObtainJSONWebToken

from areas.serializers import AddressSerializer, AddressTitleSerializer
from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from goods.serializers import SKUSerializer
from users.models import User
from users.serialziers import RegisterCreateSerializer, UserDetailSerializer, EmailSerializer, \
    AddUserBrowsingHistorySerializer
from django.shortcuts import render
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# from .serializers import EmailSerializer


class RegisterUsernameCountAPIView(APIView):
    """
    获取用户名的个数
    GET:  /users/usernames/(?P<username>\w{5,20})/count/
    """

    def get(self,request,username):

        #通过模型查询,获取用户名个数
        count = User.objects.filter(username=username).count()
        #组织数据
        context = {
            'count':count,
            'username':username
        }
        return Response(context)

class RegisterPhoneCountAPIView(APIView):
    """
    查询手机号的个数
    GET: /users/phones/(?P<mobile>1[345789]\d{9})/count/
    """
    def get(self,request,mobile):

        #通过模型查询获取手机号个数
        count = User.objects.filter(mobile=mobile).count()
        #组织数据
        context = {
            'count':count,
            'phone':mobile
        }

        return Response(context)


class RegisterCreateView(APIView):
    """
    用户注册
    POST /users/

    用户注册我们需要对数据进行校验,同时需要数据入库
    """

    # serializer_class = RegisterCreateSerializer
    def post(self, reqeust):
        # 1. 接收数据
        data = reqeust.data
        # 2. 校验数据
        serializer = RegisterCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3. 数据入库
        serializer.save()
        # 4. 返回相应
        return Response(serializer.data)


class UserDetailView(RetrieveAPIView):
    """
    获取登录用户的信息
    GET /users/
    既然是登录用户,我们就要用到权限管理
    在类视图对象中也保存了请求对象request
    request对象的user属性是通过认证检验之后的请求用户对象
    """
    permission_classes = [IsAuthenticated]

    serializer_class = UserDetailSerializer

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    """
    保存邮箱
    PUT /users/emails/
    """

    permission_classes = [IsAuthenticated]

    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user


class VerificationEmailView(APIView):
    """
    验证激活邮箱
    GET /users/emails/verification/?token=xxxx

    思路:
    获取token,并判断
    获取 token中的id
    查询用户,并判断是否存在
    修改状态
    返回响应
    """

    def get(self,request):
        # 获取token, 并判断
        token = request.query_params.get('token')
        if not token:
            return Response({'message':'缺少token'},status=status.HTTP_400_BAD_REQUEST)
        # 获取token中的id,email
        # 查询用户, 并判断是否存在
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message':'链接无效'},status=status.HTTP_400_BAD_REQUEST)
        else:
            # 修改状态
            user.email_active = True
            user.save()
            # 返回响应
            return Response({'message':'ok'})

class AddressViewSet(mixins.ListModelMixin,mixins.CreateModelMixin,mixins.UpdateModelMixin,GenericViewSet):
    """
    用户地址新增与修改
    list GET: /users/addresses/
    create POST: /users/addresses/
    destroy DELETE: /users/addresses/
    action PUT: /users/addresses/pk/status/
    action PUT: /users/addresses/pk/title/
    """

    #制定序列化器
    serializer_class = AddressSerializer
    #添加用户权限
    permission_classes = [IsAuthenticated]
    #由于用户的地址有存在删除的状态,所以我们需要对数据进行筛选
    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        count = request.user.addresses.count()
        if count >= 20:
            return Response({'message':'保存地址数量已经达到上限'},status=status.HTTP_400_BAD_REQUEST)

        return super().create(request,*args,**kwargs)

    def list(self, request, *args, **kwargs):
        """
        获取用户地址列表
        """
        # 获取所有地址
        queryset = self.get_queryset()
        # 创建序列化器
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        # 响应
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': 20,
            'addresses': serializer.data,
        })

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)


class UserBrowsingHistoryView(mixins.CreateModelMixin, GenericAPIView):
    """
    用户浏览历史记录
    POST /users/browerhistories/
    GET  /users/browerhistories/
    数据只需要保存到redis中
    """
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        保存
        """
        return self.create(request)

    def get(self, request):
        """获取"""
        # 获取用户信息
        user_id = request.user.id
        # 连接redis
        redis_conn = get_redis_connection('history')
        # 获取数据
        history_sku_ids = redis_conn.lrange('history_%s' % user_id, 0, 5)
        skus = []
        for sku_id in history_sku_ids:
            sku = SKU.objects.get(pk=sku_id)
            skus.append(sku)
        # 序列化
        serializer = SKUSerializer(skus, many=True)
        return Response(serializer.data)


class UserAuthorizationView(ObtainJSONWebToken):

    def post(self, request):
        # 调用jwt扩展的方法，对用户登录的数据进行验证
        response = super().post(request)

        # 如果用户登录成功，进行购物车数据合并
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 表示用户登录成功
            user = serializer.validated_data.get("user")
            # 合并购物车
            #merge_cart_cookie_to_redis(request, user, response)
            response = merge_cart_cookie_to_redis(request, user, response)

        return response