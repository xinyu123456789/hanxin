from django import forms

from .models import UserProfile, UserPreference


class ProfileForm(forms.ModelForm):
    """個人檔案設定表單。"""

    class Meta:
        model = UserProfile
        fields = [
            "nickname",
            "self_description_tags",
            "interested_topics",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relation",
        ]
        widgets = {
            "nickname": forms.TextInput(attrs={"class": "form-input", "placeholder": "你想讓涵涵怎麼稱呼你？"}),
            "emergency_contact_name": forms.TextInput(attrs={"class": "form-input"}),
            "emergency_contact_phone": forms.TextInput(attrs={"class": "form-input", "type": "tel"}),
            "emergency_contact_relation": forms.TextInput(attrs={"class": "form-input", "placeholder": "例如：媽媽、室友"}),
        }
        labels = {
            "nickname": "暱稱",
            "self_description_tags": "自我描述標籤（逗號分隔）",
            "interested_topics": "關注主題（逗號分隔）",
            "emergency_contact_name": "緊急聯絡人姓名",
            "emergency_contact_phone": "緊急聯絡人電話",
            "emergency_contact_relation": "與我的關係",
        }


class AppearanceForm(forms.ModelForm):
    """外觀偏好設定表單。"""

    class Meta:
        model = UserPreference
        fields = ["accent", "font_scale", "board_react", "tree_style", "soft_bg"]
        widgets = {
            "accent": forms.RadioSelect(attrs={"class": "radio-color"}),
            "font_scale": forms.NumberInput(attrs={"class": "form-input", "min": 90, "max": 115, "step": 5}),
            "board_react": forms.RadioSelect(),
            "tree_style": forms.RadioSelect(),
            "soft_bg": forms.CheckboxInput(attrs={"class": "toggle"}),
        }
        labels = {
            "accent": "主題色調",
            "font_scale": "字級 (%)",
            "board_react": "看板互動模式",
            "tree_style": "成長視覺",
            "soft_bg": "柔光漸層背景",
        }
