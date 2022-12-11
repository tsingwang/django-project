import datetime

import requests
from django.conf import settings


class Lark:
    def __init__(self, app_id="", app_secret=""):
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = None
        self.expire_at = None

    def prepare_headers(self, need_tenant_access_token=True) -> dict:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if need_tenant_access_token:
            headers["Authorization"] = "Bearer " + self.get_tenant_access_token()
        return headers

    def get_tenant_access_token(self):
        now = datetime.datetime.now()
        if self.expire_at and self.expire_at > now:
            return self.tenant_access_token
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        headers = self.prepare_headers(need_tenant_access_token=False)
        r = requests.request('POST', url, json=body, headers=headers)
        if r.json().get('code') != 0:
            print('get_tenant_access_token error')
            return ''
        self.tenant_access_token = r.json()['tenant_access_token']
        self.expire_at = now + datetime.timedelta(seconds=(r.json()['expire'] - 300))
        return self.tenant_access_token

    def request(self, method, url, params=None, json=None):
        headers = self.prepare_headers()
        r = requests.request(method, url, headers=headers, params=params, json=json)
        return r.json()


lark = Lark(app_id=settings.LARK_APP_ID, app_secret=settings.LARK_APP_SECRET)
