from django.conf import settings

from .tasks import send_email


def notify_register(user):
    msg = f"""新用户注册

    姓名: {user.profile.full_name}
    邮箱: {user.profile.email}
    手机: {user.profile.mobile}

    - {settings.EMAIL_SIGNATURE}
    """
    send_email.delay(
        settings.EMAIL_SUBJECT_PREFIX + '新用户注册等待审核',
        msg,
        settings.ADMIN_EMAIL_LIST,
    )

    msg = f"""{user.username} 您好：

    感谢您的申请，我们会尽快审核，审核结果将发送至您的邮箱，请您关注！

    - {settings.EMAIL_SIGNATURE}
    """
    send_email.delay(
        settings.EMAIL_SUBJECT_PREFIX + '您已成功提交帐号申请',
        msg,
        [user.email],
    )


def notify_active(user):
    msg = f"""{user.username} 您好：

    您的帐号已激活！

    - {settings.EMAIL_SIGNATURE}
    """
    send_email.delay(
        settings.EMAIL_SUBJECT_PREFIX + '您的帐号已激活',
        msg,
        [user.email],
    )


def notify_inactive(user):
    msg = f"""{user.username} 您好：

    抱歉，您的帐号没有通过审核，您可以尝试重新提交申请。

    - {settings.EMAIL_SIGNATURE}
    """
    send_email.delay(
        settings.EMAIL_SUBJECT_PREFIX + '抱歉，您的帐号申请未通过',
        msg,
        [user.email],
    )


def send_email_code(code):
    msg = f"""{code.user.username} 您好：

    验证码: {code.code}
    有效期1小时，请尽快验证

    - {settings.EMAIL_SIGNATURE}
    """
    send_email.delay(
        settings.EMAIL_SUBJECT_PREFIX + '验证码',
        msg,
        [code.user.email],
    )
