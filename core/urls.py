from django.conf.urls import patterns, url, include
from core.v2 import views
from rest_framework.routers import DefaultRouter, SimpleRouter


router = DefaultRouter()
router.register(r'shared-items', views.SharedViewSet, 'shared')



urlpatterns = patterns('',
	url(r'^', include(router.urls)), 
    url(r'^kbi/$', views.KBI, name='kbi'),
)