from functools import wraps

from .models import ApiToken
from .utils import forbidden_response


ADMIN_SESSION_KEY = 'course_admin_logged' # пока что будет такое.


def is_admin_logged(request):
    result = bool(request.session.get(ADMIN_SESSION_KEY))
    return result


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_admin_logged(request):
            from django.shortcuts import redirect

            return redirect('admin_login')
        return view_func(request, *args, **kwargs)

    return wrapper


def get_student_by_request(request):
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    token_value = header.replace('Bearer ', '', 1).strip()
    if not token_value:
        return None
    token = ApiToken.objects.select_related('student').filter(token=token_value).first()
    if not token:
        return None
    return token.student


def api_auth_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        student = get_student_by_request(request)
        if not student:
            return forbidden_response()
        request.student = student
        return view_func(request, *args, **kwargs)

    return wrapper
