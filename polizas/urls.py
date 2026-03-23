from django.conf.urls import patterns, url, include
from polizas.v2 import views
from polizas.v2 import modulo_views
from polizas.v2 import views_reports
from polizas.v2 import renovaciones_views
from polizas.v2 import reports_graphics_dashboard_views as rgdb

from rest_framework.routers import DefaultRouter, SimpleRouter
# from generics.v2.views_report_polizas import 

router = DefaultRouter()
# router.register(r'formatos', FormatosViewSet, 'formatos')
router.register(r'cotizacion-to-show', views.CotizacionShowViewSet, 'cotizacion-show')
router.register(r'filtros-renovaciones', renovaciones_views.FiltrosRenovaciones, 'FiltrosRenovaciones')


urlpatterns = patterns('',
    url(r'^', include(router.urls)), 
    url(r'^chart-polizas/$', views.chart_polizas, name='chart_polizas_v2'),
    url(r'^graficas-polizas/$', views.providers_graphic, name = 'graficas_polizas' ),
    url(r'^graficas-endosos/$', views.endo_graphic, name = 'endo_polizas' ),
    url(r'^chart-renovaciones/$', views.renewals_initial, name = 'chart_renovaciones' ),
    url(r'^graficas-renovaciones/$', views.renewals_graphic.as_view({'get': 'list'}), name = 'graficas_renovaciones' ),
    url(r'^filtros-polizas/$', modulo_views.PolicyFilters, name = 'policyFilters'),
    url(r'^filtros-polizas-ot/$', modulo_views.PolicyOTFilters, name = 'policyOTFilters'),
    url(r'^leer-ots-resume-dash/$', views.OTReadResume, name = 'leer-ots-resume-dash' ),
	url(r'^reporte-renovaciones-rep/$', views_reports.GetReportRenovacionesViewSet, name = 'GetReportRenovacionesViewSet'),
    url(r'^excel-graficas-polizas/$', rgdb.ReportePolizasDashboard, name = 'reporte_graficas_polizas' ),
    url(r'^excel-graficas-endosos/$', rgdb.ReporteEndososDashboard, name = 'reporte_graficas_endosos' ),
    url(r'^reporte-edoclientes/$', views_reports.GetReportEdoClientes, name = 'GetReportEdoClientes'),
    url(r'^reporte-edoClientes-excel/$', views_reports.GetReportExcelEdoClientes, name = 'GetReportExcelEdoClientes'),
    url(r'^get-endorsements-policies/$', views.PolizasForEndorsementsViewSet, name = 'v2-get-endorsements-policies'),
    url(r'^get-endorsements-collect/$', views.CollectForEndorsementsViewSet, name = 'get-endorsements-collect'), 
)
