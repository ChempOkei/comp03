import json
from datetime import date

from django.http import JsonResponse


def json_body(request):
    try:
        body = request.body.decode('utf-8') if request.body else '{}'
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

def json_body_hash():
    pass #хотел реализацию json в хеше, условный base64, или какой нибудь rsa, но проблемно выходила
def validation_response(form_errors, message='Invalid fields'):
    errors = {}
    for field, field_errors in form_errors.items():
        errors[field] = [str(item) for item in field_errors]
    return JsonResponse({'message': message, 'errors': errors}, status=422)

def not_found_page_site():
    return  JsonResponse({'message': 'Page not found'}, status=404) # только щас понял что по заданию не требуется, вызывать не буду. Хотел юзать если юзер перейдет не туда
def forbidden_response():
    return JsonResponse({'message': 'Forbidden for you'}, status=403)


def not_found_response():
    return JsonResponse({'message': 'Not found'}, status=404)

def format_date(value):
    if not value:
        return ''
    return value.strftime('%d-%m-%Y') #сделаю фрпмат времени потому что так красивее


def map_order_status_for_admin(status):
    mapping = {
        'pending': 'ожидает оплаты',
        'success': 'оплачено',
        'failed': 'ошибка оплаты',
    }
    return mapping.get(status, status)




def can_buy_course(course):
    today = date.today()
    return today < course.start_date
