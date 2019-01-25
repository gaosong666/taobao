from django.shortcuts import render

# Create your views here.
# from django.shortcuts import render
# from rest_framework import mixins
# from rest_framework import status
# from rest_framework.decorators import action
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet

from areas.serializers import AreaSerializer, SubAreaSerializer, AddressSerializer, AddressTitleSerializer
from .models import Area
# from .serializers import AreaSerializer, SubAreaSerializer, AddressSerializer, AddressTitleSerializer
from rest_framework_extensions.cache.mixins import CacheResponseMixin

# Create your views here.


class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """
    行政区划信息
    """
    pagination_class = None  # 区划信息不分页

    def get_queryset(self):
        """
        提供数据集
        """
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        """
        提供序列化器
        """
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer


# class AddressViewSet(mixins.ListModelMixin,mixins.CreateModelMixin,mixins.UpdateModelMixin,GenericViewSet):
#     """
#     用户地址新增与修改
#     list GET: /users/addresses/
#     create POST: /users/addresses/
#     destroy DELETE: /users/addresses/
#     action PUT: /users/addresses/pk/status/
#     action PUT: /users/addresses/pk/title/
#     """
#
#     #制定序列化器
#     serializer_class = AddressSerializer
#     #添加用户权限
#     permission_classes = [IsAuthenticated]
#     #由于用户的地址有存在删除的状态,所以我们需要对数据进行筛选
#     def get_queryset(self):
#         return self.request.user.addresses.filter(is_deleted=False)
#
#     def create(self, request, *args, **kwargs):
#         """
#         保存用户地址数据
#         """
#         count = request.user.addresses.count()
#         if count >= 20:
#             return Response({'message':'保存地址数量已经达到上限'},status=status.HTTP_400_BAD_REQUEST)
#
#         return super().create(request,*args,**kwargs)
#
#     def list(self, request, *args, **kwargs):
#         """
#         获取用户地址列表
#         """
#         # 获取所有地址
#         queryset = self.get_queryset()
#         # 创建序列化器
#         serializer = self.get_serializer(queryset, many=True)
#         user = self.request.user
#         # 响应
#         return Response({
#             'user_id': user.id,
#             'default_address_id': user.default_address_id,
#             'limit': 20,
#             'addresses': serializer.data,
#         })
#
#     def destroy(self, request, *args, **kwargs):
#         """
#         处理删除
#         """
#         address = self.get_object()
#
#         # 进行逻辑删除
#         address.is_deleted = True
#         address.save()
#
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#
#     @action(methods=['put'], detail=True)
#     def title(self, request, pk=None, address_id=None):
#         """
#         修改标题
#         """
#         address = self.get_object()
#         serializer = AddressTitleSerializer(instance=address, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
#
#     @action(methods=['put'], detail=True)
#     def status(self, request, pk=None, address_id=None):
#         """
#         设置默认地址
#         """
#         address = self.get_object()
#         request.user.default_address = address
#         request.user.save()
#         return Response({'message': 'OK'}, status=status.HTTP_200_OK)
