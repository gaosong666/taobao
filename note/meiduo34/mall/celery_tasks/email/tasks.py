from celery_tasks.main import app
from django.core.mail import send_mail
from mall import settings

# @app.task(name='send_verify_email')
# def send_verify_email(to_email,verify_url):
#     subject = "美多商城邮箱验证"
#     html_message = '<p>尊敬的用户您好！</p>' \
#                    '<p>感谢您使用美多商城。</p>' \
#                    '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
#                    '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
#     send_mail(subject, "", settings.EMAIL_FROM, [to_email], html_message=html_message)


@app.task(name='send_verify_email')

def send_verify_email(to_email,verify_url):

    subject = "美多商城邮箱验证"
    message = ''
    from_email = settings.EMAIL_FROM
    recipient_list = [to_email]
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    send_mail(subject, message, from_email, recipient_list, html_message=html_message)

