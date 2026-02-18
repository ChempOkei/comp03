from datetime import date

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .auth import ADMIN_SESSION_KEY, admin_required
from .forms import AdminLoginForm, CourseForm, LessonForm
from .models import Certificate, Course, Lesson, Order
from .services import build_certificate_number, delete_media_file, save_course_images
from .utils import format_date, map_order_status_for_admin


@require_http_methods(['GET', 'POST'])
def admin_login(request):
    if request.session.get(ADMIN_SESSION_KEY):
        return redirect('admin_courses')

    form = AdminLoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            if email == settings.ADMIN_EMAIL and password == settings.ADMIN_PASSWORD:
                request.session[ADMIN_SESSION_KEY] = True
                return redirect('admin_courses')
            form.add_error('email', 'Некорректные данные')
            form.add_error('password', 'Некорректные данные')
        return render(request, 'course_admin/login.html', {'form': form})

    return render(request, 'course_admin/login.html', {'form': form})


@require_GET
@admin_required
def admin_root(request):
    return redirect('admin_courses')


@require_GET
@admin_required
def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


@require_GET
@admin_required
def admin_courses(request):
    page_number = request.GET.get('page', '1')
    courses = Course.objects.all()
    paginator = Paginator(courses, settings.ADMIN_PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    return render(request, 'course_admin/courses/lessons-list.html', {'page_obj': page_obj})


@require_http_methods(['GET', 'POST'])
@admin_required
def admin_course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None, require_cover=True)

    if request.method == 'POST':
        if form.is_valid():
            image_path, thumb_path = save_course_images(form.cleaned_data['cover'])
            Course.objects.create(
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
                hours=form.cleaned_data['hours'],
                price=form.cleaned_data['price'],
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['end_date'],
                image=image_path,
                thumbnail=thumb_path,
            )
            messages.success(request, 'Курс создан')
            return redirect('admin_courses')

    return render(request, 'course_admin/courses/course-form-create.html', {'form': form, 'title': 'Создание курса', 'submit': 'Создать'})


@require_http_methods(['GET', 'POST'])
@admin_required
def admin_course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    initial = {
        'name': course.name,
        'description': course.description,
        'hours': course.hours,
        'price': f'{course.price:.2f}',
        'start_date': format_date(course.start_date),
        'end_date': format_date(course.end_date),
    }

    form = CourseForm(request.POST or None, request.FILES or None, initial=initial, require_cover=False)

    if request.method == 'POST':
        if form.is_valid():
            course.name = form.cleaned_data['name']
            course.description = form.cleaned_data.get('description', '')
            course.hours = form.cleaned_data['hours']
            course.price = form.cleaned_data['price']
            course.start_date = form.cleaned_data['start_date']
            course.end_date = form.cleaned_data['end_date']

            cover = form.cleaned_data.get('cover')
            if cover:
                old_image = course.image
                old_thumb = course.thumbnail
                image_path, thumb_path = save_course_images(cover)
                course.image = image_path
                course.thumbnail = thumb_path
                delete_media_file(old_image)
                delete_media_file(old_thumb)

            course.save()
            messages.success(request, 'Курс обновлен')
            return redirect('admin_courses')

    return render(
        request,
        'course_admin/courses/course-form-edit.html',
        {'form': form, 'title': 'Редактирование курса', 'submit': 'Сохранить', 'course': course},
    )


@require_POST
@admin_required
def admin_course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course.orders.exists():
        messages.error(request, 'Нельзя удалить курс с записями студентов')
        return redirect('admin_courses')
    delete_media_file(course.image)
    delete_media_file(course.thumbnail)
    course.delete()
    messages.success(request, 'Курс удален')
    return redirect('admin_courses')


@require_GET
@admin_required
def admin_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    return render(request, 'course_admin/courses/courses-list.html', {'course': course, 'lessons': lessons})


@require_http_methods(['GET', 'POST'])
@admin_required
def admin_lesson_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    form = LessonForm(request.POST or None)

    if request.method == 'POST':
        if course.lessons.count() >= 5:
            form.add_error(None, 'Максимум 5 уроков на курс')
        elif form.is_valid():
            Lesson.objects.create(
                course=course,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                video_link=form.cleaned_data.get('video_link') or None,
                hours=form.cleaned_data['hours'],
            )
            messages.success(request, 'Урок создан')
            return redirect('admin_course_view', course_id=course.id)

    return render(
        request,
        'course_admin/lessons/lesson-form-create.html',
        {'form': form, 'title': 'Создание урока', 'submit': 'Создать', 'course': course},
    )


@require_http_methods(['GET', 'POST'])
@admin_required
def admin_lesson_edit(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    initial = {
        'title': lesson.title,
        'content': lesson.content,
        'video_link': lesson.video_link or '',
        'hours': lesson.hours,
    }
    form = LessonForm(request.POST or None, initial=initial)

    if request.method == 'POST':
        if form.is_valid():
            lesson.title = form.cleaned_data['title']
            lesson.content = form.cleaned_data['content']
            lesson.video_link = form.cleaned_data.get('video_link') or None
            lesson.hours = form.cleaned_data['hours']
            lesson.save()
            messages.success(request, 'Урок обновлен')
            return redirect('admin_course_view', course_id=lesson.course_id)

    return render(
        request,
        'course_admin/lessons/lesson-form-edit.html',
        {'form': form, 'title': 'Редактирование урока', 'submit': 'Сохранить', 'course': lesson.course, 'lesson': lesson},
    )


@require_POST
@admin_required
def admin_lesson_delete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    active_orders = lesson.course.orders.filter(payment_status__in=[Order.STATUS_PENDING, Order.STATUS_SUCCESS]).exists()
    if active_orders:
        messages.error(request, 'Нельзя удалить урок при активных записях студентов')
        return redirect('admin_course_view', course_id=lesson.course_id)
    course_id = lesson.course_id
    lesson.delete()
    messages.success(request, 'Урок удален')
    return redirect('admin_course_view', course_id=course_id)


@require_GET
@admin_required
def admin_enrollments(request):
    course_id = request.GET.get('course_id', '')
    orders = Order.objects.select_related('student', 'course').all()
    if course_id.isdigit():
        orders = orders.filter(course_id=int(course_id))

    enrollment_rows = []
    for order in orders:
        enrollment_rows.append(
            {
                'id': order.id,
                'email': order.student.email,
                'name': order.student.name,
                'course': order.course.name,
                'date': format_date(order.created_at.date()),
                'payment_status': map_order_status_for_admin(order.payment_status),
                'can_print': order.payment_status == Order.STATUS_SUCCESS and order.course.end_date < date.today(),
            }
        )

    courses = Course.objects.all()
    return render(
        request,
        'course_admin/enrollments/lessons-list.html',
        {
            'rows': enrollment_rows,
            'courses': courses,
            'selected_course_id': course_id,
        },
    )


@require_GET
@admin_required
def admin_certificate_print(request, order_id):
    order = get_object_or_404(Order.objects.select_related('student', 'course'), id=order_id)

    if order.payment_status != Order.STATUS_SUCCESS:
        return HttpResponseBadRequest('Сертификат доступен только для оплаченного курса')

    if order.course.end_date >= date.today():
        return HttpResponseBadRequest('Сертификат доступен после завершения курса')

    certificate = Certificate.objects.filter(order=order).first()
    if not certificate:
        number = ''
        while not number or Certificate.objects.filter(number=number).exists():
            number = build_certificate_number(order.student_id, order.course_id)
        certificate = Certificate.objects.create(
            student=order.student,
            course=order.course,
            order=order,
            number=number,
        )

#ТЕМПЛЕЙТА НЕТ И ЕГО НАДО СОЗДАТЬ
    return render(
        request,
        'course_admin/certificates/certificate-print.html',
        {
            'certificate': certificate,
            'order': order,
        },
    )

