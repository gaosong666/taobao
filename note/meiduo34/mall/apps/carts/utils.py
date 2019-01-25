import pickle
import base64
from django_redis import get_redis_connection

def merge_cart_cookie_to_redis(request, user, response):
    """
    合并请求用户的购物车数据，将未登录保存在cookie里的保存到redis中
    :param request: 用户的请求对象
    :param user: 当前登录的用户
    :param response: 响应对象，用于清楚购物车cookie
    :return:

    思路:
    #获取cookie数据
        #如果存在
            #获取redis中的数据
            #遍历cookie数据
            #保存redis数据
            #清空cookie中的购物车数据
        #如果不存在就不用管,直接返回请求
    """

    cookie_str = request.COOKIES.get('cart')

    if cookie_str is not None:

        #将cookies_str 转换
        cookie_cart = pickle.loads(base64.b64decode(cookie_str.encode()))

        #从redis中获取购物车数据
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s'%user.id)
        #将获取的redis的键值对的类型转换为 int
        cart = {}
        for sku_id,count in redis_cart.items():
            cart[int(sku_id)] = int(count)

        #遍历cookie_cart
        selected_sku_id_list = []
        for sku_id,selected_count_dict in cookie_cart.items():
            #如果redis购物车原有商品数据,数量覆盖,如果没有,添加新记录
            cart[sku_id] = selected_count_dict['count']

            #处理勾选状态
            if selected_count_dict['selected']:
                selected_sku_id_list.append(sku_id)

        #将cookie数据合并到购物车
        pl = redis_conn.pipeline()

        pl.hmset('cart_%s'%user.id,cart)

        #     selected_sku_id_list = [1,2,3,4,]
        # pl.sadd('cart_selected_%s' % user.id, 1, 2, 3, 4)
        pl.sadd('cart_selected_%s'%user,*selected_sku_id_list)

        pl.execute()

        # 清除cookie中的购物车数据
        response.delete_cookie('cart')

        return response
    else:
        return response