from random import randint

from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse

from libs.yuntongxun.sms import CCP
from verifications.serializers import RegisterSMSCodeSerializer


class RegisterImageCodeView(APIView):
    def get(self, request, image_code_id):
        # 通过第三方库,生成图片和验证码,我们需要对验证码进行redis保存

        # 思路为:
        # 创建图片和验证码
        text, image = captcha.generate_captcha()

        # 通过redis进行保存验证码,需要在设置中添加 验证码数据库选项
        redis_conn = get_redis_connection('code')
        # 设置时间限制
        redis_conn.setex('img_%s' % image_code_id, 60, text)
        # 将图片返回
        # 注意,图片是二进制,我们通过HttpResponse返回
        return HttpResponse(image, content_type='image/jpeg')


class RegisterSMSCodeView(GenericAPIView):
    """
    获取短信验证码
    GET /verifications/smscodes/(?P<mobile>1[345789]\d{9})/?text=xxxx&image_code_id=xxxx
    获取短信验证码,首先需要校验 验证码

    思路:
    创建序列化器,定义text 和 image_code_id
    redis 判断该用户是否频繁获取
    生成短信验证码
    redis增加记录
    发送短信
    返回响应
    """

    serializer_class = RegisterSMSCodeSerializer

    def get(self,request,mobile):

        # 创建序列化器, 定义text和image_code_id
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # redis
        redis_conn = get_redis_connection('code')

        # 判断该用户是否频繁获取
        if redis_conn.get('sms_flag_%s'%mobile):
            return  Response(status=status.HTTP_429_TOO_MANY_REQUESTS)
        # 生成短信验证码
        sms_code = '%06d'%randint(0,999999)
        # redis增加记录
        redis_conn.setex('sms_%s'%mobile,5*60,sms_code)
        redis_conn.setex('sms_flag_%s'%mobile,60,1)
        # 发送短信
        ccp = CCP()
        ccp.send_template_sms(mobile, [sms_code,5],1)
        # 返回响应
        return Response({'message':'ok'})
