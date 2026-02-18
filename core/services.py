import random
import secrets
import string
from pathlib import Path

import requests
from PIL import Image
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password

from .models import ApiToken


def hash_password(password):
    return make_password(password)


def verify_password(password, password_hash):
    return check_password(password, password_hash)


def issue_token(student):
    ApiToken.objects.filter(student=student).delete()
    token = secrets.token_hex(32)
    ApiToken.objects.create(student=student, token=token)
    return token

def check_hash():
    pass
def save_course_images(uploaded_file):
    media_dir = Path(settings.MEDIA_ROOT) / 'courses'
    media_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in ['.jpg', '.jpeg']:
        extension = '.jpg'
    image_name = f'orig_{secrets.token_hex(10)}{extension}'
    thumb_name = f'mpic{secrets.token_hex(10)}{extension}'

    image_path = media_dir / image_name
    thumb_path = media_dir / thumb_name

    with Image.open(uploaded_file) as image:
        rgb_image = image.convert('RGB')
        rgb_image.save(image_path, format='JPEG', quality=90)
        thumbnail = rgb_image.copy()
        thumbnail.thumbnail((300, 300), Image.Resampling.LANCZOS)
        thumbnail.save(thumb_path, format='JPEG', quality=90)

    return f'courses/{image_name}', f'courses/{thumb_name}'


def delete_media_file(relative_path):
    if not relative_path:
        return
    file_path = Path(settings.MEDIA_ROOT) / relative_path
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

def decrypt_hash(arg):
    pass # перспектива доделать после перерыва


def serialize_course(course, request=None):
    if request:
        img_url = request.build_absolute_uri(settings.MEDIA_URL + course.thumbnail)
    else:
        img_url = settings.SITE_URL.rstrip('/') + settings.MEDIA_URL + course.thumbnail
    return {
        'id': course.id,
        'name': course.name,
        'description': course.description,
        'hours': course.hours,
        'img': img_url,
        'start_date': course.start_date.strftime('%d-%m-%Y'),
        'end_date': course.end_date.strftime('%d-%m-%Y'),
        'price': f'{course.price:.2f}',
    }


def build_certificate_number(student_id, course_id):
    prefix = fetch_certificate_prefix(student_id, course_id)
    digits = ''.join(random.choices(string.digits, k=5)) + '1'
    return f'{prefix}{digits}'


def fetch_certificate_prefix(student_id, course_id):
    url = settings.SERVICE_HOST.rstrip('/') + '/create-sertificate'
    headers = {
        'ClientId': settings.CERT_CLIENT_ID,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    payload = {
        'student_id': student_id,
        'course_id': course_id,
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            number = str(data.get('course_number', '')).strip()
            if len(number) >= 6:
                return number[:6]
    except Exception:
        pass
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def check_certificate_number(number):
    url = settings.SERVICE_HOST.rstrip('/') + '/check-sertificate'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    payload = {
        'sertikate_number': number,
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            if status in ['success', 'failed']:
                return status
    except Exception:
        pass
    return 'success' if str(number).endswith('1') else 'failed'


def build_pay_url(request, order_id):
    return request.build_absolute_uri(f'/school-api/mock-pay/{order_id}')

