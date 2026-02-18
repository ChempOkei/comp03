
import json
import tempfile
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from PIL import Image

from .models import ApiToken, Course, Lesson, Order, Student
from .services import build_certificate_number, hash_password, save_course_images
from .views import home


class FrontendTests(TestCase):
    def test_home_page_available(self):
        request = RequestFactory().get('/')
        response = home(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('School Platform', response.content.decode('utf-8'))


class ApiTests(TestCase):
    def create_course(self, name, start_offset, end_offset):
        return Course.objects.create(
            name=name,
            description='desc',
            hours=4,
            price='120.00',
            start_date=date.today() + timedelta(days=start_offset),
            end_date=date.today() + timedelta(days=end_offset),
            image='courses/orig_sample.jpg',
            thumbnail='courses/mpic_sample.jpg',
        )

#пока что так сделаю потому что не думаю что нужна тут защита нормальная
    def auth_headers(self):
        student = Student.objects.create(
            email='student@example.com',
            name='student',
            password_hash=hash_password('Abc1_'),
        )
        token = ApiToken.objects.create(student=student, token='tokentest')
        return {'HTTP_AUTHORIZATION': f'Bearer {token.token}'}, student

    def test_register_auth_and_forbidden(self):
        response = self.client.get('/school-api/courses')
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {'message': 'Forbidden for you'})

        response = self.client.post(
            '/school-api/registr',
            data=json.dumps({'email': 'user@example.com', 'password': 'Abc1_'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertJSONEqual(response.content, {'success': True})

        response = self.client.post(
            '/school-api/registr',
            data=json.dumps({'email': 'user@example.com', 'password': 'Abc1_'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['message'], 'Invalid fields')

        response = self.client.post(
            '/school-api/auth',
            data=json.dumps({'email': 'user@example.com', 'password': 'wrong'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['message'], 'Invalid data')
        self.assertEqual(response.json()['errors']['email'], ['Invalid data'])

        response = self.client.post(
            '/school-api/auth',
            data=json.dumps({'email': 'user@example.com'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['message'], 'Invalid data')
        self.assertEqual(response.json()['errors']['email'], ['Invalid data'])

        response = self.client.post(
            '/school-api/auth',
            data=json.dumps({'email': 'user@example.com', 'password': 'Abc1_'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())

    def test_courses_list_and_lessons(self):
        headers, _ = self.auth_headers()
        first = None
        for index in range(6):
            course = self.create_course(f'Course {index}', 2, 20)
            if not first:
                first = course

        Lesson.objects.create(
            course=first,
            title='Lesson A',
            content='Text',
            video_link='https://super-tube.cc/video/v23189',
            hours=2,
        )

        response = self.client.get('/school-api/courses', **headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['data']), 5)
        self.assertEqual(body['pagination']['total'], 2)
        self.assertEqual(body['pagination']['current'], 1)
        self.assertEqual(body['pagination']['per_page'], 5)

        response = self.client.get('/school-api/courses?page=2', **headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['data']), 1)
        self.assertEqual(body['pagination']['current'], 2)

        response = self.client.get(f'/school-api/courses/{first.id}', **headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Lesson A')

    def test_json_not_found_responses(self):
        headers, _ = self.auth_headers()

        response = self.client.get('/school-api/courses/999999', **headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Not found')

        response = self.client.post('/school-api/courses/999999/buy', data='{}', content_type='application/json', **headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Not found')

        response = self.client.get('/school-api/orders/999999', **headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Not found')

    def test_buy_webhook_orders_cancel(self):
        headers, student = self.auth_headers()
        future_course = self.create_course('Future Course', 5, 15)
        started_course = self.create_course('Started Course', -2, 4)

        response = self.client.post(f'/school-api/courses/{started_course.id}/buy', **headers)
        self.assertEqual(response.status_code, 422)

        response = self.client.post(f'/school-api/courses/{future_course.id}/buy', **headers)
        self.assertEqual(response.status_code, 200)
        pay_url = response.json()['pay_url']
        order_id = pay_url.rstrip('/').split('/')[-1]

        response = self.client.post(
            '/school-api/payment-webhook',
            data=json.dumps({'order_id': order_id, 'status': 'success'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/school-api/orders', **headers)
        self.assertEqual(response.status_code, 200)
        orders = response.json()['data']
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['payment_status'], Order.STATUS_SUCCESS)

        response = self.client.get(f"/school-api/orders/{orders[0]['id']}", **headers)
        self.assertEqual(response.status_code, 418)
        self.assertEqual(response.json()['status'], 'was payed')

        failed_course = self.create_course('Failed Course', 6, 16)
        response = self.client.post(f'/school-api/courses/{failed_course.id}/buy', **headers)
        self.assertEqual(response.status_code, 200)
        failed_order_id = response.json()['pay_url'].rstrip('/').split('/')[-1]

        response = self.client.post(
            '/school-api/payment-webhook',
            data=json.dumps({'order_id': failed_order_id, 'status': 'failed'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)

        order = Order.objects.get(order_id=failed_order_id, student=student)
        response = self.client.get(f'/school-api/orders/{order.id}', **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_check_certificate_aliases(self):
        response = self.client.post(
            '/school-api/check-certificate',
            data=json.dumps({'sertikate_number': 'ABCDEF123451'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        response = self.client.post(
            '/school-api/check-sertificate',
            data=json.dumps({'sertikate_number': 'ABCDEF123452'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'failed')


class ServicesTests(TestCase):
    def create_image_upload(self, filename):
        image = Image.new('RGB', (1400, 900), '#2c59cc')
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        return SimpleUploadedFile(filename, buffer.getvalue(), content_type='image/jpeg')

    def create_token_for_upload(self):
        return "123123123"


    def test_save_course_images_preserves_extension_and_thumbnail_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=temp_dir):
                upload = self.create_image_upload('cover.jpeg')
                image_rel, thumb_rel = save_course_images(upload)

                self.assertTrue(Path(image_rel).name.startswith('orig_'))
                self.assertTrue(Path(thumb_rel).name.startswith('mpic'))
                self.assertTrue(image_rel.endswith('.jpeg'))
                self.assertTrue(thumb_rel.endswith('.jpeg'))

                thumb_path = Path(temp_dir) / thumb_rel
                self.assertTrue(thumb_path.exists())
                with Image.open(thumb_path) as thumb:
                    self.assertLessEqual(thumb.width, 300)
                    self.assertLessEqual(thumb.height, 300)

    @patch('core.services.fetch_certificate_prefix', return_value='ZXCVBN')
    def test_build_certificate_number_format(self, mocked_prefix):
        number = build_certificate_number(11, 22)
        self.assertEqual(len(number), 12)
        self.assertEqual(number[:6], 'ZXCVBN')
        self.assertTrue(number[6:].isdigit())
        self.assertEqual(number[-1], '1')
        mocked_prefix.assert_called_once_with(11, 22)
