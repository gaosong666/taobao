from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.views import APIView

from goods.models import SKU
from .serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer
from django_redis import get_redis_connection
from rest_framework.response import Response
import pickle
import base64
# Create your views here.

class CartView(APIView):

    """
    购物车

    POST /cart/ 添加商品到购物车
    """
    def perform_authentication(self, request):
        """
        重写父类的用户验证方法,不在进入视图就检查JWT
        """
        pass




    def post(self,request):
        """
        思路:
        #获取数据,进行校验
        #获取商品id,count和是否选中信息
        #判断用户是否为登录用户
            # 如果为登录用户则数据保存到redis中
            # 如果为非登录用户保存到cookie中
        """
        #获取数据,进行校验
        serializer = CartSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        #获取商品id,count和是否选中信息
        sku_id = serializer.data.get('sku_id')
        count = serializer.data.get('count')
        selected = serializer.data.get('selected')
        #判断用户是否为登录用户
        try:
            user = request.user
        except Exception:
            #验证失败,用户为登录
            user = None
        if user is not None and user.is_authenticated:
            # 如果为登录用户则数据保存到redis中
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            #记录购物车商品数量 hash
            pl.hincrby('cart_%s'%user.id,sku_id,count)
            # 勾选
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            #返回响应
            return Response(serializer.data)

        else:
            # 如果为非登录用户保存到cookie中
            cart_str= request.COOKIES.get('cart')
            #先获取cookie信息,判断是否存在购物车信息
            if cart_str is not None:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}
            #更新购物车数量
            # 如果有相同商品，求和
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count
            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }
            #设置 cookie数据
            response = Response(serializer.data)
            cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response.set_cookie('cart',cookie_cart)
            #返回响应
            return response

    def get(self, request):
        """
        思路
        #判断是否为登录用户
            #登录用户,从redis中获取数据
            #非登录用户,从cookie中获取数据
        #获取所有商品的信息
        #返回响应
        """
        try:
            user = request.user
        except Exception:
            user = None
        # 判断是否为登录用户
        if user is not None and user.is_authenticated:
            # 登录用户,从redis中获取数据
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            redis_cart_select = redis_conn.smembers('cart_selected_%s' % user.id)
            cart = {}
            for sku_id, count in redis_cart.items():
                cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_cart_select
                }

        else:
            # 非登录用户,从cookie中获取数据
            cart_str = request.COOKIES.get('cart')

            if cart_str is not None:
                cart = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart = {}

        # 获取所有商品的信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]['count']
            sku.selected = cart[sku.id]['selected']
        # 序列化数据,并返回响应
        serializer = CartSKUSerializer(skus, many=True)

        return Response(serializer.data)

    def put(self, request):
        """
        修改购物车数据
        思路:
        # 创建序列化,校验数据
        #获取数据
        #获取用户
        #判断用户是否为登录用户
             #登录用户,从redis中获取数据
            #非登录用户,从cookie中获取数据
        """
        # 创建序列化,校验数据
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.data.get('sku_id')
        count = serializer.data.get('count')
        selected = serializer.data.get('selected')
        # 获取用户
        try:
            user = request.user
        except Exception:
            user = None
        # 判断用户是否为登录用户
        if user is not None and user.is_authenticated:
            # 登录用户,从redis中获取数据
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 更新数据
            pl.hset('cart_%s' % user.id, sku_id, count)
            # 更改状态
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data)
        else:
            # 非登录用户,从cookie中获取数据
            cart_str = request.COOKIES.get('cart')
            if cart_str is not None:
                cart = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart = {}

            if sku_id in cart:
                cart[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            cookie_str = base64.b64encode(pickle.dumps(cart)).decode()

            response = Response(serializer.data)
            response.set_cookie('cart', cookie_str)

            return response

    def delete(self, request):
        """
        删除数据
        思路
        #获取提交数据,并进行校验
        #获取校验之后的数据
        #获取user信息
        #判断是否登录
            #登录用户,从redis中删除数据
            #非登录用户,从cookie中删除数据
        """
        # 获取提交数据,并进行校验
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 获取校验之后的数据
        sku_id = serializer.data.get('sku_id')
        # 获取user信息
        try:
            user = request.user
        except Exception:
            user = None
        # 判断是否登录
        if user is not None and user.is_authenticated:
            # 登录用户,从redis中删除数据
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # 非登录用户,从cookie中删除数据
            cart_str = request.COOKIES.get('cart')

            if cart_str is not None:
                cart = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart = {}

            response = Response(serializer.data)

            if sku_id in cart:
                del cart[sku_id]
                # 组织数据
                cookie_str = base64.b64encode(pickle.dumps(cart)).decode()
                response.set_cookie('cart', cookie_str)

            return response