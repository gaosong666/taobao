import xadmin
from xadmin import views

from . import models

class BaseSetting(object):
    """xadmin的基本配置"""
    enable_themes = True  # 开启主题切换功能
    use_bootswatch = True

xadmin.site.register(views.BaseAdminView, BaseSetting)

class GlobalSettings(object):
    """xadmin的全局配置"""
    site_title = "美多商城运营管理系统"  # 设置站点标题
    site_footer = "美多商城集团有限公司"  # 设置站点的页脚
    menu_style = "accordion"  # 设置菜单折叠

xadmin.site.register(views.CommAdminView, GlobalSettings)


class SKUAdmin(object):
    model_icon = 'fa fa-gift'

    list_display = ['id', 'name', 'price', 'stock', 'sales', 'comments']

    search_fields = ['id', 'name']

    list_filter = ['category']

    list_editable = ['price', 'stock']

    show_detail_fields = ['name']

    show_bookmarks = True

    list_export = ['xls', 'csv', 'xml']

    readonly_fields = ['sales', 'comments']


xadmin.site.register(models.SKU, SKUAdmin)

import xadmin
# Register your models here.

from users.models import User
from xadmin.plugins import auth


# class UserAdmin(auth.UserAdmin):
#     list_display = ['id', 'username', 'mobile', 'email', 'date_joined']
#     readonly_fields = ['last_login', 'date_joined']
#     search_fields = ('username', 'first_name', 'last_name', 'email', 'mobile')
#     style_fields = {'user_permissions': 'm2m_transfer', 'groups': 'm2m_transfer'}
#
#     def get_model_form(self, **kwargs):
#         if self.org_obj is None:
#             self.fields = ['username', 'mobile', 'is_staff']
#
#         return super().get_model_form(**kwargs)


class UserAdmin(auth.UserAdmin):
    list_display = ['id', 'username', 'mobile', 'email', 'date_joined']
    readonly_fields = ['last_login', 'date_joined']
    search_fields = ('username', 'first_name', 'last_name', 'email', 'mobile')
    style_fields = {'user_permissions': 'm2m_transfer', 'groups': 'm2m_transfer'}

    def get_model_form(self, **kwargs):
        if self.org_obj is None:
            self.fields = ['username', 'mobile', 'is_staff']

        return super().get_model_form(**kwargs)


xadmin.site.unregister(User)
xadmin.site.register(User, UserAdmin)


class OrderAdmin(object):
    list_display = ['order_id', 'create_time', 'total_amount', 'pay_method', 'status']
    refresh_times = [3, 5]  # 可选以支持按多长时间(秒)刷新页面

    data_charts = {
        "order_amount": {'title': '订单金额', "x-field": "create_time", "y-field": ('total_amount',),
                         "order": ('create_time',)},
        "order_count": {'title': '订单量', "x-field": "create_time", "y-field": ('total_count',),
                        "order": ('create_time',)},
    }
from orders.models import OrderInfo
xadmin.site.register(OrderInfo,OrderAdmin)

# class SKUSpecificationAdmin(object):
#     def save_models(self):
#         # 保存数据对象
#         obj = self.new_obj
#         obj.save()
#
#         # 补充自定义行为
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(obj.sku.id)
#
#     def delete_model(self):
#         # 删除数据对象
#         obj = self.obj
#         sku_id = obj.sku.id
#         obj.delete()
#
#         # 补充自定义行为
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(sku_id)