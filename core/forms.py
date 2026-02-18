import re
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError


PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[_#!%]).{3,}$')
VIDEO_PATTERN = re.compile(r'^https://super-tube\.cc/video/v\d+$')
PRICE_PATTERN = re.compile(r'^\d+\.\d{2}$')


class AdminLoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput)


class CourseForm(forms.Form):
    name = forms.CharField(required=True, max_length=30)
    description = forms.CharField(required=False, max_length=100, widget=forms.Textarea(attrs={'rows': 3}))
    hours = forms.IntegerField(required=True, min_value=1, max_value=10)
    price = forms.CharField(required=True)
    start_date = forms.DateField(required=True, input_formats=['%d-%m-%Y'])
    end_date = forms.DateField(required=True, input_formats=['%d-%m-%Y'])
    cover = forms.ImageField(required=False)

    def __init__(self, *args, require_cover=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.require_cover = require_cover

    def clean_price(self):
        price_text = self.cleaned_data['price'].strip()
        if not PRICE_PATTERN.match(price_text):
            raise ValidationError('Цена должна быть в формате xx.xx')
        price = Decimal(price_text)
        if price < Decimal('100.00'):
            raise ValidationError('Цена должна быть не менее 100.00')
        return price

    def clean(self):
        cleaned_data = super().clean()
        cover = cleaned_data.get('cover')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if self.require_cover and not cover: #если что можем убрать проверку,
            self.add_error('cover', 'Обложка обязательна при создании')

        if cover:
            name = cover.name.lower()
            if not (name.endswith('.jpg') or name.endswith('.jpeg')):
                self.add_error('cover', 'Допустимы только JPG/JPEG')
            # if cover.size > 2000: Я ХЗ ПОЧЕМУ НЕ ТАК, позже глянуть!!!
            #     self.add_error('cover', 'Максимальный размер 2000 Кб')
            sizer = 2000 * 1024 #fixed
            if cover.size > sizer:
                self.add_error('cover', 'Максимальный размер 2000 Кб')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'Дата окончания не может быть раньше даты начала')

        return cleaned_data

    def edit(self):
        clean_data = super.clean()
        start_date = clean_data.get('start_date')


class LessonForm(forms.Form):
    title = forms.CharField(required=True, max_length=50)
    content = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 6}))
    video_link = forms.CharField(required=False)
    hours = forms.IntegerField(required=True, min_value=1, max_value=4)

    def clean_video_link(self):
        link = self.cleaned_data.get('video_link', '').strip()
        if not link:
            return ''
        if not VIDEO_PATTERN.match(link):
            raise ValidationError('Неверная ссылка SuperTube')
        return link


class ApiRegisterForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True)

    def clean_password(self):
        password = self.cleaned_data['password']
        if not PASSWORD_PATTERN.match(password):
            raise ValidationError('Пароль не такой должен быть ')
        return password



class ApiAuthForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True)


class ApiWebhookForm(forms.Form):
    order_id = forms.CharField(required=True)
    status = forms.ChoiceField(required=True, choices=[('success', 'success'), ('failed', 'failed')])


class ApiCertificateCheckForm(forms.Form):
    sertikate_number = forms.CharField(required=True, min_length=12, max_length=12)
