#school_platform ctrl c + ctrl v from manager :D
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_platform.settings')

application = get_wsgi_application()