#school_platform ссылочки

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from core.views import home

urlpatterns = [
    path('', home, name='home'),
    path('course-admin/', include('core.urls_admin')),
    path('school-api/', include('core.urls_api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # print("!!! Watch !!! ", urlpatterns)


# if settings.DEBUG:
#     pass

#     idk, dedlube, потом сделаю
# if settings.configured:
#     print("settings was configured")


#добавить в перспективе сюда по мере возможности помимо джанго еще и локальный сервер с дб, но это конечно в идеале. А так , не особо хочется, 10 минут