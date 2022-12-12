from django.conf import settings
from django.contrib.auth.models import Permission
from guardian.shortcuts import assign_perm, remove_perm

from .models import PermReview
from .tasks import send_email


def perm_request(perm, user, obj):
    if not isinstance(perm, Permission):
        try:
            app_label, codename = perm.split('.', 1)
        except ValueError:
            raise ValueError("For global permissions, first argument must be in"
                             " format: 'app_label.codename' (is %r)" % perm)
        perm = Permission.objects.get(content_type__app_label=app_label,
                                      codename=codename)

    exist = PermReview.objects.filter(
        object_id=obj.id, permission=perm, requester=user, status=0).count()
    if exist:
        return

    pr = PermReview(content_object=obj, permission=perm, requester=user)
    pr.save()

    msg = f"""权限申请审核

    姓名: {user.username}
    申请权限: {perm.codename}
    资源名称: {obj.name}

    - {settings.EMAIL_SIGNATURE}
    """
    send_email.delay(
        settings.EMAIL_SUBJECT_PREFIX + '权限申请',
        msg,
        settings.ADMIN_EMAIL_LIST,
    )


def perm_approve(perm, user, obj):
    assign_perm(perm, user, obj)

    msg = f"""{user.username} 您好：

    您申请的权限已通过

    权限：{perm.codename}
    资源：{obj.name}

    - {settings.EMAIL_SIGNATURE}
    """
    send_email.delay(
        settings.EMAIL_SUBJECT_PREFIX + '您申请的权限已通过',
        msg,
        [user.email],
    )

def perm_reject(perm, user, obj):
    remove_perm(perm, user, obj)

    msg = f"""{user.username} 您好：

    抱歉，您申请的权限未通过

    权限：{perm.codename}
    资源：{obj.name}

    - {settings.EMAIL_SIGNATURE}
    """
    send_email.delay(
        settings.EMAIL_SUBJECT_PREFIX + '抱歉，您申请的权限未通过',
        msg,
        [user.email],
    )
