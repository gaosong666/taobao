#coding:utf8
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings
from django.utils.deconstruct import deconstructible

@deconstructible
class FastDFSStorage(Storage):
    """
        自定义文件上传类
        """

    def __init__(self, conf_path=None, ip=None):
        if conf_path is None:
            conf_path = settings.FDFS_CLIENT_CONF
        self.conf_path = conf_path

        if ip is None:
            ip = settings.FDFS_URL
        self.ip = ip

    #打开文件方法，不需要实现
    def _open(self, name, mode='rb'):
        pass

    #保存文件
    def _save(self, name, content, max_length=None):


        #创建client对象
        # client = Fdfs_client('client.conf')
        client = Fdfs_client(self.conf_path)
        #获取上传的数据
        data = content.read()
        #进行上传
        result = client.upload_by_buffer(data)
        #判断上传是否成功
        if result['Status'] == 'Upload successed.':
            #如果成功返回 Remote file_id
            return result['Remote file_id']
        else:
            raise Exception('上传失败')

    def exists(self, name):
        return False

    def url(self, name):

        # return 'http://192.168.229.133:8888/' + name
        return self.ip + name