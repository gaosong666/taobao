from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)



class OrderCommitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """保存订单"""

        # 获取当前下单用户
        user = self.context['request'].user
        # 生成订单编号
        # 保存订单的基本信息数据 OrderInfo
        # 创建订单编号
        # 20180523160505+ user_id  100
        # timezone.now() -> datetime

        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 保存订单基本信息数据 OrderInfo
        address = validated_data['address']
        pay_method = validated_data['pay_method']

        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.0'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )

                # 从redis中获取购物车结算商品数据
                redis_conn = get_redis_connection('cart')
                cart_redis = redis_conn.hgetall('cart_%s' % user.id)
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
                # 遍历结算商品：
                cart = {}
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(cart_redis[sku_id])

                sku_id_list = cart.keys()

                for sku_id in sku_id_list:
                    while True:
                        sku = SKU.objects.get(pk=sku_id)
                        # 判断商品库存是否充足
                        count = cart[sku.id]
                        if sku.stock < count:
                            transaction.savepoint_rollback(save_id)
                            raise serializers.ValidationError('库存不足')

                        print(sku.stock)
                        import time
                        time.sleep(5)
                        # 减少商品库存，增加商品销量
                        # sku.stock -= count
                        # sku.sales += count
                        # sku.save()

                        origin_stock = sku.stock

                        origin_sales = sku.sales

                        new_stock = origin_stock - count
                        new_sales = origin_sales + count

                        # 返回受影响的行数
                        ret = SKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        if ret == 0:
                            continue

                        # 保存订单商品数据
                        order.total_count += count
                        order.total_amount += (sku.price * count)

                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=count,
                            price=sku.price
                        )
                        # 记得 break
                        break

                order.save()

            except ValueError:
                raise
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                raise serializers.ValidationError('下单失败')

            # 提交失误
            transaction.savepoint_commit(save_id)

            # 清除购物车中已经结算的商品
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem('cart_selected_%s' % user.id, *cart_selected)
            pl.execute()

            return order