"""
欄位加密輔助層。

LenientEncryptedTextField：寫入時以 Fernet 加密（透過 django-cryptography），
讀取時優先嘗試解密；若資料是欄位改回加密前留下的舊版明文（Postgres 將舊
text 欄位轉成 bytea 時，位元組內容就是原本的 UTF-8 字串），解密會因格式
不符而拋出 BadSignature，此時退回直接以 UTF-8 解碼回傳，避免讀取舊資料時
出錯。新寫入的資料一律是密文，不需要額外的資料回填 migration。
"""
from django.core.signing import BadSignature
from django.db import models
from django.utils.encoding import force_str
from django_cryptography.fields import encrypt


class LenientEncryptedTextField(encrypt(models.TextField)):
    def deconstruct(self):
        return models.Field.deconstruct(self)

    def _load(self, value):
        try:
            return super()._load(value)
        except BadSignature:
            return force_str(value)
