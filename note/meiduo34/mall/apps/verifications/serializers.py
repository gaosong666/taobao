from rest_framework import serializers
from django_redis import get_redis_connection
from redis.exceptions import RedisError
import logging

logger = logging.getLogger('meiduo')


class RegisterSMSCodeSerializer(serializers.Serializer):

    text = serializers.CharField(label='用户输入的验证码', max_length=4, min_length=4, required=True)
    image_code_id = serializers.UUIDField(label='验证码唯一性ID')

    # def validate(self, attrs):
    #
    #
    #     # 获取用户提交的验证码
    #     text = attrs['text']
    #     image_code_id = attrs['image_code_id']
    #
    #     # 链接redis,获取redis中的验证码
    #     redis_conn = get_redis_connection('code')
    #     redis_text = redis_conn.get('img_%s'%image_code_id)
    #
    #     # 判断从redis中获取的验证码是否存在
    #     if redis_text is None:
    #         raise serializers.ValidationError('验证码已过期')
    #
    #     # 将redis中的验证码删除
    #     try:
    #         redis_conn.delete('img_%s'%image_code_id)
    #     except RedisError as e:
    #         logger.error(e)
    #
    #     # 对redis的验证码编码之后进行比对,要注意大小写问题
    #     if redis_text.decode().lower() != text.lower():
    #         raise serializers.ValidationError('验证码错误')
    #
    #     return attrs
    def validate(self, attrs):

        # 1. 获取用户提交的验证码
        text = attrs.get('text')
        # 2. 获取redis的验证码
        # 2.1连接redis
        redis_conn = get_redis_connection('code')
        # 2.2 获取数据
        image_id = attrs.get('image_code_id')
        redis_text = redis_conn.get('img_' + str(image_id))

        # 2.3 redis的数据有时效
        if redis_text is None:
            raise serializers.ValidationError('图片验证码过期')

        # 3. 比对
        # 3.1. redis的数据是bytes类型
        # 3.2  大小写的问题
        if redis_text.decode().lower() != text.lower():
            raise serializers.ValidationError('输入错误')

        return attrs






