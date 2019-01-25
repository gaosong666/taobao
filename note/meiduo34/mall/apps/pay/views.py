from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from orders.models import OrderInfo
from rest_framework import status
from alipay import AliPay
from mall import settings


# Create your views here.
from pay.models import Payment


class PaymentView(APIView):
    """
    支付
    GET /pay/orders/(?P<order_id>)\d+/

    必须登录

    思路:
    判断订单是否正确
    创建支付对象
    调用支付对象生成 order_string
    构造支付地址
    返回响应
    """

    def get(self, request, order_id):
        user = request.user
        # 判断订单是否正确
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)
        # 创建支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type='RSA2',  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG
        )
        # 调用支付对象生成order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),  # 将浮点数转换为字符串
            subject='测试订单',
            return_url='http://www.meiduo.site:8080/pay_success.html',
        )
        # 构造支付地址
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        # 返回响应
        return Response({'alipay_url': alipay_url})


class PaymentStatusView(APIView):
    """
    支付结果
    """
    def put(self, request):
        data = request.query_params.dict()
        signature = data.pop("sign")

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,# 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        success = alipay.verify(data, signature)
        if success:
            # 订单编号
            order_id = data.get('out_trade_no')
            # 支付宝支付流水号
            trade_id = data.get('trade_no')
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])
            return Response({'trade_id': trade_id})
        else:
            return Response({'message': '参数错误'}, status=status.HTTP_400_BAD_REQUEST)