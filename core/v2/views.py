from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated
from core.models import Shared, Log, Graphics
from core.v2.serializers_filtro_por_usuario import SharedHyperSerializer
from organizations.views import get_org
from core.views import custom_get_queryset
 # -*- coding: utf-8 -*-
from django.conf import settings
from django.core.paginator import Paginator
from rest_framework import viewsets
from rest_framework import permissions, viewsets
from core.serializers import *
from core.models import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from polizas.models import Assign, Polizas, Cotizacion, OldPolicies
from archivos.models import PolizasFile, RecibosFile, SiniestrosFile
from rest_framework import parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from django.http import HttpResponse
import datetime
from django.db import models
from django.db.models import *
from operator import and_, or_
from operator import __or__ as OR
from operator import __and__ as AND
import operator
from functools import reduce
from PIL import Image
import requests
from organizations.views import get_org
from organizations.serializers import UserSerializer
from claves.models import Claves
from datetime import datetime, timedelta, date
import arrow
# Importaciones para las tareas desde comentario
from endosos.models import Endorsement
from siniestros.models import Siniestros
from vendedores.models import AccountState

from core.push_messages import send_push
import json
from decimal import Decimal
from contratantes.models import Contractor
import xlwt
from django.http import HttpResponse
from recibos.models import Recibos
import pytz
import datetime
from endosos.models import *
from django.core.mail.backends.smtp import EmailBackend
import smtplib
from pytz import timezone
#
from organizations.views import get_org_info
from django.core.serializers import serialize
from generics.models import Personal_Information
from forms.models import AutomobilesDamages
from core.v2.filtros_por_usuario import polizas_por_grupo

from control.permissions import IsAuthenticatedV2, IsOrgMemberV2, KBIPermissionV2


class SharedViewSet(viewsets.ModelViewSet):
    serializer_class = SharedHyperSerializer

    def perform_create(self, serializer):
        obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))

    def get_queryset(self):
        return custom_get_queryset(self.request, Shared)



@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, KBIPermissionV2 ))
def KBI(request):
    now = datetime.datetime.now()
    curr_year = now.year
    dic31 = '31/12/'+str(now.year)+' 23:59:59'
    f = "%d/%m/%Y %H:%M:%S"     
    date31 = datetime.datetime.strptime(dic31 , f)
    ene01_c_eh = '01/01/'+str(now.year)+' 00:00:00'
    date01_ehoy = datetime.datetime.strptime(ene01_c_eh , f)
    fianzas_filtered = polizas_por_grupo(request)
    polizas_filtered = polizas_por_grupo(request)
    polizas_nat = Polizas.objects.filter(pk__in = list(polizas_filtered)).values_list('contractor', flat = True)
    natural_sh =  list(polizas_nat)
    # Comisones de enero (año actual) a la fecha
    recibos_actual = Recibos.objects.filter(org_name = request.GET.get('org'), fecha_inicio__year = curr_year)
    new_recibos_actual = Recibos.objects.filter(org_name = request.GET.get('org'), vencimiento__gte = now, vencimiento__lte = date31).exclude(poliza__document_type = 2)
    # Filter
    recibos_actual = recibos_actual.filter(poliza__in = list(polizas_filtered))
    new_recibos_actual = new_recibos_actual.filter(poliza__in = list(polizas_filtered))
    new_rec_enero_hoy = Recibos.objects.filter(org_name = request.GET.get('org'),status__in = [1,5,6], vencimiento__gte = date01_ehoy, vencimiento__lte = now)
    new_rec_all_enero_hoy = Recibos.objects.filter(org_name = request.GET.get('org'), vencimiento__gte = date01_ehoy, vencimiento__lte = now)
    # Filter
    new_rec_enero_hoy = new_rec_enero_hoy.filter(poliza__in = list(polizas_filtered))
    new_rec_all_enero_hoy = new_rec_all_enero_hoy.filter(poliza__in = list(polizas_filtered))

    log_actual = Log.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)

    # Aseguradoras y Subramos
    serializer_aseg = recibos_actual.values('poliza__aseguradora__compania').annotate(Sum('prima_total')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_total'), output_field=CharField()))).order_by('poliza__aseguradora__alias')
    serializer_subramos = recibos_actual.values('poliza__subramo__subramo_name').annotate(Sum('prima_total')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_total'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    # Aseguradoiras-subranmos---nuevo prima_neta
    new_serializer_aseg = new_rec_all_enero_hoy.values('poliza__aseguradora__compania').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__aseguradora__alias')
    new_serializer_subramos = new_rec_all_enero_hoy.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    # Ejecutivos
    serializer_ejecutivos = log_actual.values('user__first_name', 'user__last_name').annotate(Count('user'))


    # Bateo y cotización
    total_cotizaciones = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year).count()
    bateadas = Cotizacion.objects.filter(org_name = request.GET.get('org'), status = 3, created_at__year = curr_year).count()
    if total_cotizaciones:
        serializer_bateo = (bateadas * 100) / total_cotizaciones
    else:
        serializer_bateo = 0

    # Comisiones
    dic31_com = '31/12/'+str(now.year)+' 23:59:59'
    ene01_com = '01/01/'+str(now.year)+' 00:00:00'
    f = "%d/%m/%Y %H:%M:%S"     
    date31_com = datetime.datetime.strptime(dic31_com , f)
    date01_com = datetime.datetime.strptime(ene01_com , f)
    new_recibos_enero_hoy = Recibos.objects.filter(org_name = request.GET.get('org'),status__in = [1,5,6], vencimiento__gte = date01_com, vencimiento__lte = now)
    # Filter
    new_recibos_enero_hoy = new_recibos_enero_hoy.filter(poliza__in = list(polizas_filtered))
    new_comision_neta = new_recibos_enero_hoy.aggregate(Sum('comision'))
    # new_comision_neta = new_recibos_actual.aggregate(Sum('comision'))

    comision_neta = recibos_actual.aggregate(Sum('comision'))
    comision_perdida = recibos_actual.filter(receipt_type = 3).aggregate(Sum('comision'))
    notas_total = recibos_actual.filter(receipt_type = 3).aggregate(Sum('prima_total'))
    new_notas_total = new_recibos_enero_hoy.filter(receipt_type = 3).aggregate(Sum('prima_total'))
    total_recibir = recibos_actual.filter(status__in = [4,3]).aggregate(Sum('comision'))
    new_total_recibir = new_recibos_actual.filter(status__in = [4,3]).aggregate(Sum('comision'))
    # Primas
    pagados_total = recibos_actual.filter(status__in = [1,5,6]).aggregate(Sum('prima_total'))
    new_pagados_total = new_recibos_enero_hoy.filter(status__in = [1,5,6]).aggregate(Sum('prima_neta'))
    pendientes_total = recibos_actual.filter(status__in = [4,3]).aggregate(Sum('prima_total'))
    new_pendientes_total = new_recibos_actual.filter(status__in = [4,3]).aggregate(Sum('prima_total'))
    emitidas_cancel = recibos_actual.filter(status__in = [2,8]).aggregate(Sum('prima_neta'))
    total_total = recibos_actual.aggregate(Sum('prima_neta'))
    new_total_total = new_recibos_enero_hoy.aggregate(Sum('prima_neta'))    
    meta = Goals.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)

    # Meta
    if meta:
        metas = {
            'value': meta[0].goal,
            'progress': total_total['prima_neta__sum'],
            'remain': str(meta[0].goal - total_total['prima_neta__sum']),
            'currency': "MXN",
            'percentajeGoal': (total_total['prima_neta__sum'] * 100) / meta[0].goal
        }
        if meta[0].goal:
            meta[0].goal  = meta[0].goal 
        else:
            meta[0].goal  = 0
        if new_total_total['prima_neta__sum']:
            new_total_total['prima_neta__sum'] = new_total_total['prima_neta__sum']
        else:
            new_total_total['prima_neta__sum'] = 0
        new_metas = {
            'value': meta[0].goal,
            'progress': new_total_total['prima_neta__sum'],
            'remain': str(meta[0].goal - new_total_total['prima_neta__sum']),
            'currency': "MXN",
            'percentajeGoal': (new_total_total['prima_neta__sum'] * 100) / meta[0].goal
        }
    else:
        metas = {
            'value': 0,
            'progress': 0,
            'remain': 0,
            'currency': "MXN",
            'percentajeGoal': 0
        }
        new_metas = {
            'value': 0,
            'progress': 0,
            'remain': 0,
            'currency': "MXN",
            'percentajeGoal': 0
        }
    data = {
        # 'aseguradoras': json.dumps(list(serializer_aseg), default=decimal_default),
        # 'subramos': json.dumps(list(serializer_subramos), default=decimal_default),
        'aseguradoras': json.dumps(list(new_serializer_aseg), default=decimal_default),
        'subramos': json.dumps(list(new_serializer_subramos), default=decimal_default),
        'ejecutivos': json.dumps(list(serializer_ejecutivos), default=decimal_default),
        'bateo': serializer_bateo,
        'cotizaciones': total_cotizaciones,
        # 'comision': comision_neta['comision__sum'],
        'comision': new_comision_neta['comision__sum'],
        'comision_perdida': comision_perdida['comision__sum'],
        # 'recibos_pagados': pagados_total['prima_total__sum'],
        'recibos_pagados': new_pagados_total['prima_neta__sum'],
        # 'prima_cobrar': pendientes_total['prima_total__sum'],
        'prima_cobrar': new_pendientes_total['prima_total__sum'],
        # 'prima_recibir': total_recibir['comision__sum'],
        'prima_recibir': new_total_recibir['comision__sum'],
        'primas_canceladas': emitidas_cancel['prima_neta__sum'],
        # 'goal': metas,
        'goal': new_metas,
        'contratantes': Contractor.objects.filter(org_name = request.GET.get('org')).filter(pk__in = natural_sh).count(),
        # 'endosos': Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__year = curr_year).count(),
        'endosos': Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__gte = date01_com, end_date__lte = now).filter(policy__in = list(polizas_filtered)).count(),
        # 'siniestros': Siniestros.objects.filter(org_name = request.GET.get('org'), fecha_ingreso__year = curr_year).count(),
        'siniestros': Siniestros.objects.filter(org_name = request.GET.get('org'), fecha_ingreso__gte = date01_com, fecha_ingreso__lte = now).filter(poliza__in = list(polizas_filtered)).count(),
        'notas_credito': notas_total['prima_total__sum'],
        # 'ot': (Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__year = curr_year, status = 5).count() + Polizas.objects.filter(org_name = request.GET.get('org'), start_of_validity__year = curr_year, status = 1).count()),
        # 'ot': (Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__gte = date01_com, end_date__lte = now, status = 5).count() + Polizas.objects.filter(org_name = request.GET.get('org'), start_of_validity__gte = date01_com, end_of_validity__lte = now, status = 1).count()),
        'ot': (Endorsement.objects.filter(org_name = request.GET.get('org'), created_at__gte = date01_com, created_at__lte = now, status__in = [1,5]).filter(policy__in = list(polizas_filtered)).count() + Polizas.objects.filter(document_type__in=list([1,3]),org_name = request.GET.get('org'), created_at__gte = date01_com, created_at__lte = now, status = 1).filter(pk__in = list(polizas_filtered)).count()),
        'polizas': Polizas.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year, status__in = [4,10,11,12,13,14,15]).filter(pk__in = list(polizas_filtered)).count(),
        # 'renovaciones': OldPolicies.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year).count(),
        'renovaciones': OldPolicies.objects.filter(org_name = request.GET.get('org'), created_at__gte = date01_com, created_at__lte = now).filter(base_policy__in =list(polizas_filtered)).count(),
        'chartDataFinancial': getChartDataFinancial(request),
        'barDataFinancial': getBarDataFinancial(request),
        'polarDataFinancial': getPolarDataFinancial(request),
        'barDataProduction': getBarDataProduction(request),
        'barDataCotization': getBarDataCotizacion(request),
        'monthsBateo': getMonthsBateo(request),
        'chartDataCotization': getChartDataCotizacion(request),
        'barDataGastos': getBarDataGastos(request, recibos_actual),
        'monthsUtilidad': getMonthsUtilidad(request, recibos_actual)
        }
    return JsonResponse(data)
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# puntos comparión
def getChartDataFinancial(request):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year
    dic31 = '31/12/'+str(now.year)+' 23:59:59'
    ene01 = '01/01/'+str(now.year)+' 00:00:00'
    f = "%d/%m/%Y %H:%M:%S"     
    date31 = datetime.datetime.strptime(dic31 , f)
    date01 = datetime.datetime.strptime(ene01 , f)
    # --------
    polizas_filtered = polizas_por_grupo(request)
    # Sum o count es lo que se modifican por atributo,fecha o x
    p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org')).filter(pk__in = list(polizas_filtered)).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('p_neta')).order_by('month')
    p_l = Polizas.objects.filter(start_of_validity__year = (curr_year- 1), org_name = request.GET.get('org')).filter(pk__in = list(polizas_filtered)).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('p_neta')).order_by('month')
    new_p_a = Recibos.objects.filter(fecha_inicio__gte = date01,fecha_fin__lte = now, org_name = request.GET.get('org'), status__in = [1,5,6]).filter(poliza__in = list(polizas_filtered)).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('prima_neta')).order_by('month')
    new_p_l = Recibos.objects.filter(fecha_inicio__year = (curr_year- 1), org_name = request.GET.get('org'),status__in = [1,5,6]).filter(poliza__in = list(polizas_filtered)).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('prima_neta')).order_by('month')
    data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': [(curr_year - 1), curr_year ],
              'data': [[searchData(1, p_l), searchData(2, p_l), searchData(3, p_l), searchData(4, p_l), searchData(5, p_l), searchData(6, p_l), searchData(7, p_l), searchData(8, p_l), searchData(9, p_l), searchData(10, p_l), searchData(11, p_l), searchData(12, p_l)],
                       [searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)]],
              'colours': ['#5DADE2', '#F1C40F'] }
    new_data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': [(curr_year - 1), curr_year ],
              'data': [[searchData(1, new_p_l), searchData(2, new_p_l), searchData(3, new_p_l), searchData(4, new_p_l), searchData(5, new_p_l), searchData(6, new_p_l), searchData(7, new_p_l), searchData(8, new_p_l), searchData(9, new_p_l), searchData(10, new_p_l), searchData(11, new_p_l), searchData(12, new_p_l)],
                       [searchData(1, new_p_a), searchData(2, new_p_a), searchData(3, new_p_a), searchData(4, new_p_a), searchData(5, new_p_a), searchData(6, new_p_a), searchData(7, new_p_a), searchData(8, new_p_a), searchData(9, new_p_a), searchData(10, new_p_a), searchData(11, new_p_a), searchData(12, new_p_a)]],
              'colours': ['#5DADE2', '#F1C40F'] }

    # return data
    return new_data

# traer los meses de un query
class Month(Func):
    function = 'EXTRACT'
    template = '%(function)s(MONTH from %(expressions)s)'
    output_field = models.IntegerField()
# regresa total (enviar un mes(#) y la info (object) )
def searchData(month, data):
    concidence = [element for element in data if element['month'] == month]
    if concidence:
        return concidence[0]['total']
    else:
        return 0
# regresa suma (enviar un mes(#) y la info (onject) )
def searchDataSum(month, data):
    concidence = [element for element in data if element['month'] == month]
    if concidence:
        return concidence[0]['cantidad__sum']
    else:
        return 0

def searchDataSubramos(month, data):
    concidence = [element for element in data if element['subramo__subramo_code'] == month]
    if concidence:
        return concidence[0]['p_neta__sum']
    else:
        return 0
# puntos comparión
def getBarDataFinancial(request):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year
    polizas_filtered = polizas_por_grupo(request)
    p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org')).filter(pk__in = list(polizas_filtered)).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('p_total')).order_by('month')
    new_p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org')).filter(pk__in = list(polizas_filtered)).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('p_total')).order_by('month')
    data = {'labels':["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
            'series': ["Prima Total"],
            'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)]],
            }

    return data
# Subramos OK
def getPolarDataFinancial(request):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year
    polizas_filtered = polizas_por_grupo(request)
    p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org')).filter(pk__in = list(polizas_filtered))
    subramos = p_a.values('subramo__subramo_code').annotate(Sum('p_neta')).order_by('subramo__subramo_name')
    data = {'labels':["Vida", "GM", "Salud", "AP", "Autos", 'RC', 'Marítimo y Transportes', 'Incendio', 'Agrícola', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Riesgos Catastróficos'],
                             'series': ["Vida", "Gastos Médicos", "Salud", "Accidentes y Enfermedades", "Automóviles", 'Responsabilidad Civil y Riesgos Profesionales', 'Marítimo y Transportes', 'Incendio', 'Agrícola y de Animales', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Terremoto y Otros Riesgos Catastróficos'],
                             'data': [[searchDataSubramos(1, subramos), searchDataSubramos(3, subramos), searchDataSubramos(4, subramos), searchDataSubramos(2, subramos), searchDataSubramos(9, subramos), searchDataSubramos(5, subramos), searchDataSubramos(6, subramos), searchDataSubramos(7, subramos), searchDataSubramos(8, subramos), searchDataSubramos(10, subramos), searchDataSubramos(11, subramos), searchDataSubramos(12, subramos), searchDataSubramos(13, subramos), searchDataSubramos(14, subramos)]],
                             'colours': ['#9B59B6', '#DF01A5', '#2980B9', '#01A9DB', '#1ABC9C', '#61380B', '#00FF80', '#F7819F', '#F1C40F', '#F39C12', '#E67E22', '#D35400', '#C0392B', '#E74C3C'] }

    return data

def getBarDataProduction(request):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year
    dic31 = '31/12/'+str(now.year)+' 23:59:59'
    ene01 = '01/01/'+str(now.year)+' 00:00:00'
    f = "%d/%m/%Y %H:%M:%S"     
    date31 = datetime.datetime.strptime(dic31 , f)
    date01 = datetime.datetime.strptime(ene01 , f)
    polizas_filtered = polizas_por_grupo(request)

    p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org')).filter(pk__in = list(polizas_filtered)).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('comision')).order_by('month')
    # new_p_a = Recibos.objects.filter(fecha_inicio__gte = date01, fecha_fin__lte = date31, status__in = [1,5,6], org_name = request.GET.get('org')).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    new_p_a = Recibos.objects.filter(poliza__in = list(polizas_filtered)).filter(vencimiento__gte = date01, vencimiento__lte = date31, status__in = [1,5,6], org_name = request.GET.get('org')).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Comisión"],
          'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)]],
          'colours': ['#E67E22'] }
    new_data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Comisión"],
          'data': [[searchData(1, new_p_a), searchData(2, new_p_a), searchData(3, new_p_a), searchData(4, new_p_a), searchData(5, new_p_a), searchData(6, new_p_a), searchData(7, new_p_a), searchData(8, new_p_a), searchData(9, new_p_a), searchData(10, new_p_a), searchData(11, new_p_a), searchData(12, new_p_a)]],
          'colours': ['#E67E22'] }

    # return data
    return new_data

def getBarDataCotizacion(request):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year

    p_a = Cotizacion.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')
    data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Cotizacion"],
          'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)]],
          'colours': ['#E67E22'] }

    return data

def getMonthsBateo(request):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year

    p_a = Cotizacion.objects.filter(status = 3, created_at__year = curr_year, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')

    data = [{'month': 'Enero', 'value': searchData(1, p_a)},
          {'month': 'Febrero', 'value': searchData(2, p_a)},
          {'month': 'Marzo', 'value': searchData(3, p_a)},
          {'month': 'Abril', 'value': searchData(4, p_a)},
          {'month': 'Mayo', 'value': searchData(5, p_a)},
          {'month': 'Junio', 'value': searchData(6, p_a)},
          {'month': 'Julio', 'value': searchData(7, p_a)},
          {'month': 'Agosto', 'value': searchData(8, p_a)},
          {'month': 'Septiembre', 'value': searchData(9, p_a)},
          {'month': 'Octubre', 'value': searchData(10, p_a)},
          {'month': 'Noviembre', 'value': searchData(11, p_a)},
          {'month': 'Diciembre', 'value': searchData(12, p_a)} ]

    return data

def getMonthsUtilidad(request, recibos):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year

    p_a = Expenses.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).values('month').annotate(Sum('cantidad'))
    recibos_mes = recibos.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org')).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    data = [{'month': 'Enero', 'value': (searchData(1, recibos_mes) - searchDataSum(1, p_a))},
          {'month': 'Febrero', 'value': (searchData(2, recibos_mes) - searchDataSum(2, p_a))},
          {'month': 'Marzo', 'value': (searchData(3, recibos_mes) - searchDataSum(3, p_a))},
          {'month': 'Abril', 'value': (searchData(4, recibos_mes) - searchDataSum(4, p_a))},
          {'month': 'Mayo', 'value': (searchData(5, recibos_mes) - searchDataSum(5, p_a))},
          {'month': 'Junio', 'value': (searchData(6, recibos_mes) - searchDataSum(6, p_a))},
          {'month': 'Julio', 'value': (searchData(7, recibos_mes) - searchDataSum(7, p_a))},
          {'month': 'Agosto', 'value': (searchData(8, recibos_mes) - searchDataSum(8, p_a))},
          {'month': 'Septiembre', 'value': (searchData(9, recibos_mes) - searchDataSum(9, p_a))},
          {'month': 'Octubre', 'value': (searchData(1, recibos_mes) - searchDataSum(10, p_a))},
          {'month': 'Noviembre', 'value': (searchData(1, recibos_mes) - searchDataSum(11, p_a))},
          {'month': 'Diciembre', 'value': (searchData(1, recibos_mes) - searchDataSum(12, p_a))} ]

    return data

def getBarDataGastos(request, recibos):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year

    p_a = Expenses.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).values('month').annotate(Sum('cantidad'))
    p_a_serializer = Expenses.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org'))
    ser_expenses = ExpensesInfoSerializer(p_a_serializer,context={'request':request}, many= True)
    recibos_mes = recibos.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org')).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ['Gastos', 'Comisiones'],
          'data': [[searchDataSum(1, p_a), searchDataSum(2, p_a), searchDataSum(3, p_a), searchDataSum(4, p_a), searchDataSum(5, p_a), searchDataSum(6, p_a), searchDataSum(7, p_a), searchDataSum(8, p_a), searchDataSum(9, p_a), searchDataSum(10, p_a), searchDataSum(11, p_a), searchDataSum(12, p_a)],
                   [searchData(1, recibos_mes), searchData(2, recibos_mes), searchData(3, recibos_mes), searchData(4, recibos_mes), searchData(5, recibos_mes), searchData(6, recibos_mes), searchData(7, recibos_mes), searchData(8, recibos_mes), searchData(9, recibos_mes), searchData(10, recibos_mes), searchData(11, recibos_mes), searchData(12, recibos_mes)]],
          'colours': ['#E74C3C', '#949FB1'],
          'concepts': ser_expenses.data }

    return data

def getChartDataCotizacion(request):
    lst = [0] * 12
    now = datetime.datetime.now()
    curr_year = now.year

    p_a = Cotizacion.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')
    p_l = Cotizacion.objects.filter(status = 2, created_at__year = curr_year, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')

    data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': ['Cotización', 'Emisión'],
              'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)],
                       [searchData(1, p_l), searchData(2, p_l), searchData(3, p_l), searchData(4, p_l), searchData(5, p_l), searchData(6, p_l), searchData(7, p_l), searchData(8, p_l), searchData(9, p_l), searchData(10, p_l), searchData(11, p_l), searchData(12, p_l)]],
              'colours': ['#27AE60', '#884EA0'] }

    return data
