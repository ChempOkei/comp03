from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .auth import api_auth_required
from .forms import ApiAuthForm, ApiCertificateCheckForm, ApiRegisterForm, ApiWebhookForm
from .models import Course, Lesson, Order, Student
from .services import build_pay_url, check_certificate_number, hash_password, issue_token, serialize_course, verify_password
from .utils import can_buy_course, json_body, not_found_response, validation_response


def auth_invalid_response():
    return JsonResponse({'message': 'Invalid data', 'errors': {'email': ['Invalid data']}}, status=422)


@csrf_exempt
@require_http_methods(['POST'])
def api_register(request):
    payload = json_body(request)
    if payload is None:
        return validation_response({'body': ['Invalid JSON']})

    form = ApiRegisterForm(payload)
    if not form.is_valid():
        return validation_response(form.errors)

    email = form.cleaned_data['email'].lower()
    if Student.objects.filter(email=email).exists():
        return validation_response({'email': ['Этот email уже зарегистрирован']})

    Student.objects.create(
        email=email,
        name=email.split('@')[0],
        password_hash=hash_password(form.cleaned_data['password']),
    )
    return JsonResponse({'success': True}, status=201)

def api_lesson():
    pass
@csrf_exempt
@require_http_methods(['POST'])
def api_auth(request):
    payload = json_body(request)
    if payload is None:
        return auth_invalid_response()

    form = ApiAuthForm(payload)
    if not form.is_valid():
        return auth_invalid_response()

    email = form.cleaned_data['email'].lower()
    password = form.cleaned_data['password']
    student = Student.objects.filter(email=email).first()

    if not student or not verify_password(password, student.password_hash):
        return auth_invalid_response()

    token = issue_token(student)
    return JsonResponse({'token': token}, status=200)


@require_GET
@api_auth_required
def api_courses(request):
    page_number = request.GET.get('page', '1')
    courses = Course.objects.all()
    paginator = Paginator(courses, settings.API_PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    data = [serialize_course(course, request) for course in page_obj.object_list]

    return JsonResponse(
        {
            'data': data,
            'pagination': {
                'total': paginator.num_pages,
                'current': page_obj.number,
                'per_page': settings.API_PAGE_SIZE,
            },
        },
        status=200,
    )


@require_GET
@api_auth_required
def api_course_lessons(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if not course:
        return not_found_response()
    lessons = Lesson.objects.filter(course=course)
    data = [
        {
            'id': lesson.id,
            'name': lesson.title,
            'description': lesson.content,
            'video_link': lesson.video_link or '',
            'hours': lesson.hours,
        }
        for lesson in lessons
    ]
    return JsonResponse({'data': data}, status=200)


@csrf_exempt
@require_http_methods(['POST'])
@api_auth_required
def api_course_buy(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if not course:
        return not_found_response()

    if not can_buy_course(course):
        return validation_response({'course_id': ['Нельзя записаться на курс, который уже начался или завершен']})

    order = Order.objects.filter(student=request.student, course=course).first()
    if not order:
        import secrets

        order = Order.objects.create(
            student=request.student,
            course=course,
            order_id=secrets.token_hex(12),
            payment_status=Order.STATUS_PENDING,
        )

    return JsonResponse({'pay_url': build_pay_url(request, order.order_id)}, status=200)


@csrf_exempt
@require_http_methods(['POST'])
def api_payment_webhook(request):
    payload = json_body(request)
    if payload is None:
        return HttpResponse(status=204)

    form = ApiWebhookForm(payload)
    if not form.is_valid():
        return HttpResponse(status=204)

    order = Order.objects.filter(order_id=form.cleaned_data['order_id']).first()
    if order:
        order.payment_status = form.cleaned_data['status']
        order.save(update_fields=['payment_status', 'updated_at'])

    return HttpResponse(status=204)


@require_GET
@api_auth_required
def api_orders(request):
    orders = Order.objects.filter(student=request.student).select_related('course')
    data = []
    for order in orders:
        data.append(
            {
                'id': order.id,
                'payment_status': order.payment_status,
                'course': serialize_course(order.course, request),
            }
        )
    return JsonResponse({'data': data}, status=200)


@require_GET
@api_auth_required
def api_order_cancel(request, order_pk):
    order = Order.objects.filter(id=order_pk, student=request.student).first()
    if not order:
        return not_found_response()

    if order.payment_status == Order.STATUS_SUCCESS:
        return JsonResponse({'status': 'was payed'}, status=418)

    order.delete()
    return JsonResponse({'status': 'success'}, status=200)


@csrf_exempt
@require_http_methods(['POST'])
# фулл проверка есть на апи чек церта
def api_check_certificate(request):
    payload = json_body(request)
    if payload is None:
        return validation_response({'body': ['Invalid JSON']})

    form = ApiCertificateCheckForm(payload)
    if not form.is_valid():
        return validation_response(form.errors)

    status = check_certificate_number(form.cleaned_data['sertikate_number'])
    return JsonResponse({'status': status}, status=200)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def mock_pay(request, order_id):
    order = get_object_or_404(Order.objects.select_related('course', 'student'), order_id=order_id)

    if request.method == 'POST':
        card_number = request.POST.get('card_number', '').replace(' ', '')
        if card_number == '8888000000001111':
            order.payment_status = Order.STATUS_SUCCESS
            pay_status = 'Оплата успешна'
        elif card_number == '8888000000002222':
            order.payment_status = Order.STATUS_FAILED
            pay_status = 'Ошибка оплаты'
        else:
            order.payment_status = Order.STATUS_FAILED
            pay_status = 'Некорректные реквизиты'
        order.save(update_fields=['payment_status', 'updated_at'])
        return render(request, 'payment/mock_pay.html', {'order': order, 'pay_status': pay_status})

    return render(request, 'payment/mock_pay.html', {'order': order, 'pay_status': ''})
