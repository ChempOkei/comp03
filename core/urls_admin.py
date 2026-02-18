from django.urls import path

from . import admin_views

from . import views



urlpatterns = [
    path('', admin_views.admin_root, name='admin_root'),
    path('login/', admin_views.admin_login, name='admin_login'),
    path('logout/', admin_views.admin_logout, name='admin_logout'),
    path('courses/', admin_views.admin_courses, name='admin_courses'),
    path('courses/create/', admin_views.admin_course_create, name='admin_course_create'),
    path('courses/<int:course_id>/', admin_views.admin_course_view, name='admin_course_view'),
    path('courses/<int:course_id>/edit/', admin_views.admin_course_edit, name='admin_course_edit'),
    path('courses/<int:course_id>/delete/', admin_views.admin_course_delete, name='admin_course_delete'),
    path('courses/<int:course_id>/lessons/create/', admin_views.admin_lesson_create, name='admin_lesson_create'),
    path('lessons/<int:lesson_id>/edit/', admin_views.admin_lesson_edit, name='admin_lesson_edit'),
    path('lessons/<int:lesson_id>/delete/', admin_views.admin_lesson_delete, name='admin_lesson_delete'),
    path('enrollments/', admin_views.admin_enrollments, name='admin_enrollments'),
    path('certificates/<int:order_id>/print/', admin_views.admin_certificate_print, name='admin_certificate_print'),


]


def get_string_route(number):
    print("мы тут")
    pass