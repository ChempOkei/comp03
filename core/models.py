from django.db import models


class Student(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120, blank=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ApiToken(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='tokens')
    token = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token



class Course(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True)
    hours = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    image = models.CharField(max_length=255)
    thumbnail = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=50)
    content = models.TextField()
    video_link = models.URLField(blank=True, null=True)
    hours = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'pending'),
        (STATUS_SUCCESS, 'success'),
        (STATUS_FAILED, 'failed'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='orders')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=64, unique=True)
    payment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.student.email} - {self.course.name}'



#возврат церта
class Certificate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='certificate')
    number = models.CharField(max_length=12, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.number
