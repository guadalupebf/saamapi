# -*- coding: utf-8 -*-
from cmath import log
from rest_framework import permissions, viewsets, status

from archivos.models import CotizacionesFile, RecibosFile, BannerFile, SiniestrosFile
from generics.pdfs import PDF_OT_LOCAL
from polizas.models import *
from django.core import serializers
from polizas.serializers import *
from rest_framework.decorators import api_view, permission_classes as pm
from rest_framework.response import Response
from organizations.views import get_org_by_env, get_org
from core.views import custom_get_queryset, custom_org_create, send_log, send_log_complete
from django.contrib.auth.models import User
import requests
import json
from organizations.serializers import UserSerializer
import os
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from contratantes.views import ContractorMediumViewSet
from ramos.models import Ramos
from rest_framework.decorators import api_view, permission_classes
from django.db.models import *
from operator import and_, or_
from operator import __or__ as OR
from operator import __and__ as AND
import operator
from functools import reduce
from generics.models import Personal_Information
from core.models import Log, Graphics, Remitente, ReferenciadoresInvolved, LogEmail, Signature
from endorsements.models import *
from endosos.models import *
from endosos.serializers import *
from recibos.serializers import ReciboHyperSerializer
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from email.mime.image import MIMEImage

from recibos.views import checkCurrency
from siniestros.models import Siniestros, Accidentes, Autos, Vida, Danios
from siniestros.serializers import SiniestrosResumeSerializer
import urllib.request
import os
from django.conf import settings
from decimal import Decimal
from django.core.paginator import Paginator
from itertools import chain
from django.db import IntegrityError
import random
from dateutil import parser
from operator import attrgetter
import xlwt
from PIL import Image
import requests
from django.conf import settings
from claves.views import getInfoOrg
from organizations.models import UserInfo
import smtplib
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from aseguradoras.serializers import ProviderReadListClaveSerializer
from fianzas.models import *
from recibos.models import Pagos
from rest_framework.exceptions import APIException
from organizations.views import get_org_info
from rest_framework.pagination import PageNumberPagination
from archivos.presigned_url import get_presigned_url
from django.utils.safestring import mark_safe
from control.permissions import IsAuthenticatedV2, IsOrgMemberV2
from control.permission_functions import admin_archivos_sensibles, admin_archivos
import base64

folder = settings.MEDIAFILES_LOCATION
host = settings.MAILSERVICE
#host = 'http://mail.mbservicios.com/'

def status_poliza(val):
    status = {
        0  : 'Desactivado',
        1  : 'OT Pendiente',
        2  : 'OT Cancelada',
        4  : 'Precancelada',
        10 : 'Por iniciar',
        11 : 'Cancelada',
        12 : 'Renovada',
        13 : 'Vencida',
        14 : 'Vigente',
        15 : 'No Renovada'
    }
    return status.get(val, val)

def user_remitente(request):
    org_info = get_org_info(request)
    if request.user.email:
        remitente = "{} <{}>".format(org_info['name'], request.user.email)
    elif org_info['email']:
        remitente = "{} <{}>".format(org_info['name'], org_info['email'])
    else:
        remitente = "{} <no-reply@miurabox.com>".format(org_info['name'])

    if len(org_info['logo']) != 0:
        logo = 'https://miurabox-public.s3.amazonaws.com/cas/'+ org_info['logo']
    else:
        logo = ''
        #logo = 'https://miurabox-public.s3.amazonaws.com/estaticos-publicos/avatar_logo.png'
    if len(org_info['logo_mini']) != 0:
        logo_mini = 'https://miurabox-public.s3.amazonaws.com/cas/'+ org_info['logo_mini']
    else:
        logo_mini = ''
    rem = remitente
    # Para enviar correos (headers correctos, con acentos)
    from_header = build_from_header(rem)          # recomendado
    # Para log (sin reventar)
    log_remitente(rem)
    # Para ASCII-only si algún sistema no acepta UTF-8
    from_ascii = remitente_ascii(rem)
    # return
    return (from_header if from_header else remitente), logo, logo_mini

# -- Correo externo del contacto
@api_view(['POST'])
def external_contactNV(request):
    info = ''
    if request.user != 'AnonymousUser':
        try:
            info = request.user.user_info.org.urlname
            info = ' de ' + info.upper()
        except:
            info = ''

    try:
        data = {
            'name': request.data['from_name'],
            'email': request.data['from_email'],
            'message': request.data['message'],
            'subject': 'Servicio de mensajeria' + info,
            'receptor': json.dumps(['vicky@ixulabs.com', 'vicky+1@ixulabs.com'])
            # ['oscar.zarco@ixulabs.com', 'diego@ixulabs.com', 'josue@ixulabs.com', 'vicky@ixulabs.com','fernando.hernandez@miurabox.com', 'david.cantu@miurabox.com']
        }


    except:
        return Response({'error': 'No se recibio la información'}, status='400')

    url = host + "mails/external_contact/"
    headers = {"user_agent": "mozilla", }
    req = requests.post(url, data=data, headers=headers)

    try:
        if str(req) == str('<Response [200]>'):
            return Response({}, status=status.HTTP_200_OK, headers=headers)
        else:
            return Response({'response': 'Error', }, status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({'response': 'Error!', }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def SharePolicyEmailNV(request, id=None):
#    import pdb; pdb.set_trace()
    fechaLimitePago=''
    try:
        orginfo = OrgInfo.objects.filter(org_name = request.GET.get('org')).order_by('-created_at')
        configuracion_org = OrgInfo.objects.filter(org_name =request.GET.get('org')).order_by('-created_at')
    except:
        orginfo =None
        configuracion_org=None
    if request.method == 'POST':
        org_name =request.GET.get('org')
        plantillaSeleccionada=None
        try:
            plantilla = request.data['template_id']
            plantillaSeleccionada = EmailTemplate.objects.get(id=int(plantilla),org_name=org_name)
        except Exception as epl:
            print('no se reconocio idplantilla seleccionada',epl)
        model_log = request.data['model'] if 'model' in request.data else None
        try:
            poliza = Polizas.objects.get(pk=int(request.data['id']))
        except:
            return Response({'error': 'No existe la poliza'})
        receiver =  json.dumps(request.data['emails']) #request.data['emails']
        try:
            r_files = request.data['files']
        except Exception as error_file:
            r_files = []
        try:
            r_files_r = request.data['files_r']
        except Exception as error_rfiles:
            r_files_r = []
        if poliza.contractor:
            contratante = poliza.contractor.full_name
        else:
            contratante = ''

        try:
            sov = str(poliza.start_of_validity.strftime("%d/%m/%Y"))
        except:
            sov = ''

        try:
            eov = str(poliza.end_of_validity.strftime("%d/%m/%Y"))
        except:
            eov = ''
        if 'subject' in request.data and request.data['subject']:
            subject = request.data['subject']
        else:
            subject = str(contratante)+'  te compartimos tu Póliza '+str(poliza.poliza_number)+\
                      ' - '+str(poliza.subramo.subramo_name if poliza.subramo else '')
        try:
            filesCG = request.data['idsShared']
        except Exception as error_file:
            filesCG = []
        remitente,logo,logo_mini = user_remitente(request)
        files = PolizasFile.objects.filter(id__in=list(r_files))
        files_r = RecibosFile.objects.filter(id__in=list(r_files_r))
        archivosCG = CondicionGeneral.objects.filter(id__in=filesCG, org_name=org_name)
        files_data = []
        if poliza.ramo:
            if poliza.ramo.ramo_code ==1:#vida
                form = Life.objects.filter(policy = poliza.id)
                tipo_poliza = 'VIDA'
                if form:
                    if form[0]:
                        if form[0].personal:
                            asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
                if not asegurado:
                    form = Personal_Information.objects.filter(policy = poliza.id)
                    if form:
                        if form[0]:
                            if form[0]:
                                asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
            elif poliza.ramo.ramo_code ==2:#acc
                tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                form = AccidentsDiseases.objects.filter(policy = poliza.id)
                if form:
                    if form[0]:
                        if form[0].personal:
                            asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                        else:
                            asegurado = ''
                else:
                    asegurado = ''
            elif poliza.ramo.ramo_code ==3 and poliza.subramo.subramo_code ==9:#aut
                tipo_poliza = 'DAÑOS/AUTOS'
                form = AutomobilesDamages.objects.filter(policy = poliza.id)
                if form:
                    asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                else:
                    asegurado = ''
            elif poliza.ramo.ramo_code ==3  and poliza.subramo.subramo_code !=9:#dañ
                tipo_poliza = 'DAÑOS DIVERSOS'
                form = Damages.objects.filter(policy = poliza.id)
                if form:
                    asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                else:
                    asegurado = ''
            else:
                asegurado = ''
        else:
            asegurado = ''
        if poliza.document_type ==3:                
            tipo_poliza = 'PÓLIZA DE GRUPO'
        if poliza.document_type ==8:                
            tipo_poliza = 'FIANZA DE GRUPO'
        if files or files_r:
            if admin_archivos(request):
                for file in files:                    
                    file.arch = get_presigned_url(folder+"/{url}".format(url=file.arch),28800)  
                    URL = str(file.arch).replace(" ", "+")
                    # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26")
                    files_data.append({'url':URL,'name':file.nombre})
                for file_r in files_r:
                    file_r.arch = get_presigned_url(folder+"/{url}".format(url=file_r.arch),28800)  
                    URL = str(file_r.arch).replace(" ", "+")
                    # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26");
                    files_data.append({'url':URL,'name':file_r.nombre})
        if filesCG or archivosCG:
            if admin_archivos(request):
                for file_cg in archivosCG:                    
                    file_cg.arch = get_presigned_url(folder+"/{url}".format(url=file_cg.arch),28800)  
                    URL = str(file_cg.arch).replace(" ", "+")
                    # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26")
                    files_data.append({'url':URL,'name':file_cg.nombre})
        print('files_data*******',files_data)

        status = status_poliza(poliza.status)
        parCurrency = checkCurrency(poliza.f_currency)
        recibos = Recibos.objects.filter(isActive = True, isCopy = False, poliza = poliza.id,receipt_type=1).order_by('fecha_inicio')

        if recibos:
            primaT = recibos[0].prima_total
            fi = recibos[0].fecha_inicio.strftime("%d/%m/%Y") if recibos and recibos[0] and recibos[0].fecha_inicio else ''
            if orginfo and orginfo[0].fecha_limite_email:
                fechaLimitePago = recibos[0].vencimiento.strftime("%d/%m/%Y") if recibos and recibos[0] and recibos[0].vencimiento else ''
        else:
            primaT = 0
            fi = '*'
        if poliza.org_name and poliza.org_name=='gpi':
            cc = [request.user.email,'paula.sanchez@grupogpi.mx','cobranza.seguros@grupogpi.mx']
            # https://miurabox.atlassian.net/browse/DES-682
            # Si el usuario erik_acosta comparte una póliza, se agregará en copia a autos@grupogpi.mx.
            # Si el usuario azamora comparte una póliza, se agregará en copia a erik.tapia@grupogpi.mx.
            if request.user.username=='erik_acosta':
                cc = [request.user.email,'paula.sanchez@grupogpi.mx','cobranza.seguros@grupogpi.mx','autos@grupogpi.mx']
            if request.user.username=='azamora':
                cc = [request.user.email,'paula.sanchez@grupogpi.mx','cobranza.seguros@grupogpi.mx','erik.tapia@grupogpi.mx']

        else:
            cc = [request.user.email]
 
        org_info = get_org_info(request)
        direccion =  org_info['address']

        data = {
            'logo':logo,
            'logo_mini':logo_mini,
            'poliza_number': poliza.poliza_number,
            'contratante': contratante,
            'start_of_validity': sov,
            'end_of_validity': eov,
            'aseguradora': poliza.aseguradora.compania if poliza.aseguradora else '',
            'ramo': poliza.ramo,
            'subramo': poliza.subramo,
            'moneda':parCurrency,
            'frecuencia_de_pago': poliza.get_forma_de_pago_display(),
            'prima_neta': '$' + '{:,.2f}'.format(poliza.p_neta),
            'rpf': '$' + '{:,.2f}'.format(poliza.rpf),
            'derecho': '$' + '{:,.2f}'.format(poliza.derecho),
            'iva': '$' + '{:,.2f}'.format(poliza.iva),
            'prima_total': '$' + '{:,.2f}'.format(poliza.p_total),
            'prima_total_recibo': '$' + '{:,.2f}'.format(primaT),
            'fecha_recibo': fi,
            'files': json.dumps(files_data),
            'remitente': remitente,
            'subject': subject,
            'receiver': receiver,
            'fechaLimitePago':fechaLimitePago,
            'cc': json.dumps(cc),
            'asegurado':asegurado,
            'direccion':direccion,
            'org':request.GET.get('org'),
            'dato_pvigencia': configuracion_org[0].dato_pvigencia if configuracion_org and configuracion_org.exists() else True,
            'dato_paseguradora': configuracion_org[0].dato_paseguradora if configuracion_org and configuracion_org.exists() else True,
            'dato_psubramo': configuracion_org[0].dato_psubramo if configuracion_org and configuracion_org.exists() else True,
            'dato_pmoneda': configuracion_org[0].dato_pmoneda if configuracion_org and configuracion_org.exists() else True,
            'dato_pfrecuenciapago': configuracion_org[0].dato_pfrecuenciapago if configuracion_org and configuracion_org.exists() else True,
            'dato_pasegurado': configuracion_org[0].dato_pasegurado if configuracion_org and configuracion_org.exists() else True,
            'dato_ptotal': configuracion_org[0].dato_ptotal if configuracion_org and configuracion_org.exists() else True,
            'dato_ptotalrecibo': configuracion_org[0].dato_ptotalrecibo if configuracion_org and configuracion_org.exists() else True,
        }
        org_name = request.GET.get('org')
        # banner_file = BannerFile.objects.filter(org_name = request.GET.get('org')) 
        # if banner_file.exists():
        #     if banner_file[0].header:
        #         header = get_url_file(banner_file[0].header)  
        #     if banner_file[0].footer:
        #         footer = get_url_file(banner_file[0].footer)   
        data.update({'b_header': '','b_footer': ''})
        if 'custom_email' in request.data  and request.data['custom_email']:
            first_comment = request.data['first_comment'] if 'first_comment' in request.data else '' 
            second_comment = request.data['second_comment'] if 'second_comment' in request.data else '' 
            try:
                textinitial =first_comment if first_comment else ''
                result = re.sub('\?[^"]+', '', textinitial)
                textinitial = result
                img_pattern = r'<img.*?src="data:image/(.*?);base64,(.*?)".*?>'
                images = re.findall(img_pattern, textinitial)
                # print('imagesimages',images)
                if images:
                    for i, (img_type, img_data) in enumerate(images):
                        rnd =random.randint(1,10001)
                        img_name = 'image_'+str(i+1)+'_'+str(rnd)+'.'+str(img_type) 
                        s3_url = upload_to_s3_img_rec_poliza(img_data, img_name, img_type,img_name,org_name)
                        search_str = 'data:image/' + img_type + ';base64,' + img_data
                        width = 200
                        height = 200 
                        img_tag = s3_url + '" style="text-align:center;'
                        first_comment = first_comment.replace(search_str, img_tag)
                textinitial_2 =second_comment if second_comment else ''
                result = re.sub('\?[^"]+', '', textinitial_2)
                textinitial_2 = result
                img_pattern = r'<img.*?src="data:image/(.*?);base64,(.*?)".*?>'
                images_2 = re.findall(img_pattern, textinitial_2)
                # print('images_2images_2',images_2)
                if images_2:
                    for i, (img_type, img_data) in enumerate(images_2):
                        rnd =random.randint(1,10001)
                        img_name = 'image_'+str(i+1)+'_'+str(rnd)+'.'+str(img_type) 
                        s3_url = upload_to_s3_img_rec_poliza(img_data, img_name, img_type,img_name,org_name)
                        search_str = 'data:image/' + img_type + ';base64,' + img_data
                        width = 200
                        height = 200 
                        img_tag = s3_url + '" style="text-align:center;'
                        second_comment = second_comment.replace(search_str, img_tag)
            except Exception as yimage:
                print('errrrrrrrrrr',yimage)
            data.update({'first_comment': first_comment,'second_comment':second_comment })

            body = render_to_string("share_policyNV_custom.html", data)
            data.update({'body': body})
        url = host + "mails/share-policy-manual/"
        headers = {"user_agent": "mozilla", }
        req = requests.post(url, data=data, headers=headers)

        try:
            if str(req) == str('<Response [200]>'):
                # LOG 
                if poliza.document_type==3:
                    model = 18 
                    tipo = ' la colectividad: '
                    number = poliza.poliza_number
                elif poliza.document_type == 6:
                    model = 25
                    tipo = ' el certificado: '
                    number = poliza.certificate_number 
                    # crear registro en pendients report certificados
                    for emCert in request.data['emails']:
                        if not Pendients.objects.filter(poliza = poliza, email__iexact = emCert).exists():
                            obj = Pendients(
                                email = emCert,
                                poliza = poliza,
                                is_owner = False,
                                active = True
                                )
                            obj.save()
                elif poliza.document_type == 1:
                    model = 1
                    tipo = ' la póliza: '
                    number = poliza.poliza_number
                else:
                    model = 1
                    tipo = ' la póliza: '
                    number = poliza.poliza_number
                dataIdent = ' compartio' +str(tipo)+str(number)
                original = {}
                change= dataIdent                    
                try:
                    send_log_complete(request.user, poliza.org_name, 'POST', model, '%s' % str(dataIdent),'%s' % str(original),'%s' % str(change), poliza.id)
                except Exception as eee:
                    pass
                # LOG-------------
                if model_log:
                    if not request.data['custom_email']:
                        body = render_to_string("share_policyNV.html", data)
                    comment = Comments(model=model_log, id_model=request.data['id'], content="Se ha compartido la póliza", org_name = request.GET.get('org'), user= request.user)
                    comment.save()
                    email_log = LogEmail(model=model_log, associated_id=request.data['id'], comment=comment, to=str(receiver).replace('[', '').replace(']', '').replace('"', ''), cc=request.user.email, subject=subject, body=body, files=files_data)
                    email_log.save()
                try:
                    for r in recibos:
                        if r.recibo_numero == 1:
                            comment = Comments(model=4, id_model=r.id, content="Se ha compartido la póliza", org_name = request.GET.get('org'), user= request.user)
                            comment.save()
                            email_log = LogEmail(model=4, associated_id=r.id, comment=comment, to=str(receiver).replace('[', '').replace(']', '').replace('"', ''), cc=request.user.email, subject=subject, body=body, files=files_data)
                            email_log.save()
                            r.track_bitacora = True
                            r.save()
                except Exception as e:
                    pass

                return Response({'response': 'sent'}, status=200, headers=headers)
            else:
                try:
                    data = json.loads(req.text)
                    return Response({'response': 'Error: '+str(data['info'])}, status=400,)
                except:
                    return Response({'response': 'Error'}, status=400,)
        except Exception as e:
            return Response({'response': 'Error!'}, status=400,)
    elif request.method == 'GET':
        try:
            body = ''
            try:
                poliza = Polizas.objects.get(pk=int(id))
            except:
                return Response({'error': 'No existe la poliza'})
            if poliza.contractor:
                contratante = poliza.contractor.full_name
            else:
                contratante = ''
            if poliza.ramo:
                if poliza.ramo.ramo_code ==1:#vida
                    form = Life.objects.filter(policy = poliza.id)
                    tipo_poliza = 'VIDA'
                    if form:
                        if form[0]:
                            if form[0].personal:
                                asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                    if not asegurado:
                        form = Personal_Information.objects.filter(policy = poliza.id)
                        if form:
                            if form[0]:
                                if form[0]:
                                    asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                                else:
                                    asegurado = ''
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                elif poliza.ramo.ramo_code ==2:#acc
                    tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                    form = AccidentsDiseases.objects.filter(policy = poliza.id)
                    if form:
                        if form[0]:
                            if form[0].personal:
                                asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                            else:
                                asegurado = ''
                    else:
                        asegurado = ''
                elif poliza.ramo.ramo_code ==3 and poliza.subramo.subramo_code ==9:#aut
                    tipo_poliza = 'DAÑOS/AUTOS'
                    form = AutomobilesDamages.objects.filter(policy = poliza.id)
                    if form:
                        asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                    else:
                        asegurado = ''
                elif poliza.ramo.ramo_code ==3  and poliza.subramo.subramo_code !=9:#dañ
                    tipo_poliza = 'DAÑOS DIVERSOS'
                    form = Damages.objects.filter(policy = poliza.id)
                    if form:
                        asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
            else:
                asegurado = ''
            if poliza.document_type ==3:                
                tipo_poliza = 'PÓLIZA DE GRUPO'
            if poliza.document_type ==8:                
                tipo_poliza = 'FIANZA DE GRUPO'
            status = status_poliza(poliza.status)
            remitente,logo,logo_mini = user_remitente(request)
            parCurrency = checkCurrency(poliza.f_currency)
            # subject = str(poliza.poliza_number)+';'+str(contratante)+';'+str(poliza.subramo)+';'+\
            #           str(poliza.start_of_validity.strftime("%d/%m/%Y"))+';'+str(poliza.get_forma_de_pago_display())
            subject = str(contratante)+'  te compartimos tu Póliza '+str(poliza.poliza_number)+\
                      ' - '+str(poliza.subramo.subramo_name if poliza.subramo else '')
            recibos = Recibos.objects.filter(isActive = True, isCopy = False, poliza = poliza.id,receipt_type=1).order_by('fecha_inicio')
            files_data = []
            if recibos:
                primaT = recibos[0].prima_total
                fi = recibos[0].fecha_inicio.strftime("%d/%m/%Y") if recibos and recibos[0] and recibos[0].fecha_inicio else ''
                if orginfo and orginfo[0].fecha_limite_email:
                    fechaLimitePago = recibos[0].vencimiento.strftime("%d/%m/%Y") if recibos and recibos[0] and recibos[0].vencimiento else ''
            else:
                primaT = 0
                fi = ''
            
            org_info = get_org_info(request)
            direccion =  org_info['address']
            data = {
                'logo':logo,
                'logo_mini':logo_mini,
                'poliza_number': poliza.poliza_number,
                'contratante': contratante,
                'start_of_validity': poliza.start_of_validity.strftime("%d/%m/%Y"),
                'end_of_validity': poliza.end_of_validity.strftime("%d/%m/%Y"),
                'aseguradora': poliza.aseguradora.compania if poliza.aseguradora else '',
                'ramo': poliza.ramo,
                'subramo': poliza.subramo,
                'moneda':parCurrency,
                'frecuencia_de_pago': poliza.get_forma_de_pago_display(),
                'prima_neta': '$' + '{:,.2f}'.format(poliza.p_neta),
                'rpf': '$' + '{:,.2f}'.format(poliza.rpf),
                'derecho': '$' + '{:,.2f}'.format(poliza.derecho),
                'iva': '$' + '{:,.2f}'.format(poliza.iva),
                'prima_total': '$' + '{:,.2f}'.format(poliza.p_total),
                'prima_total_recibo': '$' + '{:,.2f}'.format(primaT),
                'fecha_recibo': fi if fi else '',
                'fechaLimitePago':fechaLimitePago,
                'subject': subject,
                'asegurado':asegurado,
                'direccion':direccion,
                'dato_pvigencia': configuracion_org[0].dato_pvigencia if configuracion_org and configuracion_org.exists() else True,
                'dato_paseguradora': configuracion_org[0].dato_paseguradora if configuracion_org and configuracion_org.exists() else True,
                'dato_psubramo': configuracion_org[0].dato_psubramo if configuracion_org and configuracion_org.exists() else True,
                'dato_pmoneda': configuracion_org[0].dato_pmoneda if configuracion_org and configuracion_org.exists() else True,
                'dato_pfrecuenciapago': configuracion_org[0].dato_pfrecuenciapago if configuracion_org and configuracion_org.exists() else True,
                'dato_pasegurado': configuracion_org[0].dato_pasegurado if configuracion_org and configuracion_org.exists() else True,
                'dato_ptotal': configuracion_org[0].dato_ptotal if configuracion_org and configuracion_org.exists() else True,
                'dato_ptotalrecibo': configuracion_org[0].dato_ptotalrecibo if configuracion_org and configuracion_org.exists() else True,
            }
            banner_file = BannerFile.objects.filter(org_name = request.GET.get('org')) 
            header = ''
            footer = ''
            if banner_file.exists():
                if banner_file[0].header:
                    header = get_url_file(banner_file[0].header)  
                if banner_file[0].footer:
                    footer = get_url_file(banner_file[0].footer)  
            data.update({'b_header': header,'b_footer': footer})
            body = render_to_string("share_policyNV_body.html", data)
            head = render_to_string("share_policyNV_head.html", data)
            footer = render_to_string("share_policyNV_footer.html", data)
            return Response({'body':body, 'head':head, 'footer':footer,'subject_default':subject}, status=200)
        except Exception as e:
            return Response({'response': 'Error!', 'error': str(e)})


def makeNice(s):
    return re.subn('(#U[0-9a-f]{4})', lambda cp: chr(int(cp.groups()[0][2:],16)), s) [0]


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def ShareCotizacionEmail(request, id=None):
    if request.method == 'POST':
        model_log = request.data['model'] if 'model' in request.data else None
        try:
            cotizacion = Cotizacion.objects.get(pk=int(request.data['id']))
        except:
            return Response({'error': 'No existe la poliza'})
        receiver =  json.dumps(request.data['emails']) #request.data['emails']
        cco_aseguradoras = json.dumps(request.data['emails_aseguradora']) if 'emails_aseguradora' in request.data else []
        try:
            r_files = request.data['files']
        except Exception as error_file:
            r_files = []

    
        subject = 'Entrega de cotización de sistema SAAM'
        remitente,logo, logo_mini = user_remitente(request)
        
        
        from django.core.files import File
        obj_last_update = None

        file = open(request.data['pdf_name'], "rb") 

        if 'sendPdf' in request.data and request.data['sendPdf']:
            obj_last_update = CotizacionesFile.objects.create(
                owner = cotizacion ,
                arch = File(file= file),
                nombre = request.data['pdf_name'],
                org_name = cotizacion.org_name,
            )
            os.remove(request.data['pdf_name'])
        else:
            os.remove(request.data['pdf_name'])

        files = CotizacionesFile.objects.filter(id__in=list(r_files))
        files_data = []
        if files:
            if admin_archivos(request):
                for file in files:
                    file.arch = get_presigned_url(folder+"/{url}".format(url=file.arch),28800)  
                    URL = str(file.arch).replace(" ", "+")
                    # URL = settings.MEDIA_URL + str(file.arch).replace(" ", "+")
                    # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26");
                    files_data.append({'url':URL,'name':file.nombre})

        if 'sendPdf' in request.data and request.data['sendPdf']:
            # URL = settings.MEDIA_URL + str(obj_last_update.arch).replace(" ", "+")
            file.arch = get_presigned_url(folder+"/{url}".format(url=obj_last_update.arch),28800)  
            URL = str(file.arch).replace(" ", "+")
            # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26");
            files_data.append({'url':URL,'name':obj_last_update.nombre})
 
        
        if obj_last_update and obj_last_update.id:
            CotizacionesFile.objects.filter(nombre = request.data['pdf_name'], org_name = obj_last_update.org_name ).delete()

        contratante = ''
        if cotizacion.prospecto == 1:
            contratante = "%s %s %s"%(cotizacion.first_name, cotizacion.last_name, cotizacion.second_last_name)
        if cotizacion.prospecto == 2:
            contratante = cotizacion.contractor.full_name
        
        if isinstance(cotizacion.ramo, dict):
            ramo = cotizacion.ramo
        else:
            ramo = json.loads(cotizacion.ramo.replace('\'','"'))
        
        if isinstance(cotizacion.subramo, dict):
            subramo = cotizacion.subramo
        else:
            subramo = json.loads(cotizacion.subramo.replace('\'','"'))

        if cotizacion.aseguradora:
            try:
                aseguradoras = [ aseguradora for aseguradora in cotizacion.aseguradora]
            except:
                aseguradoras = [(json.loads(aseguradora.replace('\'','"'))['alias']) for aseguradora in cotizacion.aseguradora]
            aseguradoras = ", ".join(aseguradoras)
        else:
            aseguradoras = ""
    
        asegurado = ''
        if ramo['value'] == 1:
            try:
                life = json.loads(cotizacion.life.replace('\'', '"'))
                life = life['aseguradosList']
                life = [ "%s %s %s"%(asegurado['first_name'],asegurado['last_name'],asegurado['second_last_name']) for asegurado in life]
                asegurado =  ", ".join(life)
            except:
                asegurado = ''

        if ramo['value'] == 2:
            try:
                accidents = json.loads(cotizacion.accidents.replace('\'', '"'))
                asegurado = "%s %s %s"%(accidents['first_name'], accidents['last_name'], accidents['second_last_name'])
            except:
                asegurado = ''

        if ramo['value'] == 3 and subramo['value'] != 9:
            try:
                danios = json.loads(cotizacion.danios.replace('\'', '"'))
                asegurado = danios['insured_item']
            except:
                asegurado = ''
        if ramo['value'] == 3 and subramo['value'] == 9:
            try:
                auto = json.loads(cotizacion.auto.replace('\'', '"'))
                asegurado = auto['selectedCar']['val']
            except:
                asegurado = ''

        data = {
            'logo':logo,
            'asegurado': asegurado,
            'contratante': contratante,
            'aseguradoras': aseguradoras,
            'ramo': ramo['name'],
            'status': cotizacion.get_status_display(),
            'subramo': subramo['name'],
            'files': json.dumps(files_data),
            'remitente': remitente,
            'subject': subject,
            'receiver': receiver,
            'cc': json.dumps([request.user.email]),
            'cco': cco_aseguradoras
        }

        banner_file = BannerFile.objects.filter(org_name = request.GET.get('org')) 
        if banner_file.exists():
            if banner_file[0].header:
                header = get_url_file(banner_file[0].header)  
            if banner_file[0].footer:
                footer = get_url_file(banner_file[0].footer)
            data.update({'b_header': header,'b_footer': footer})

        first_comment = request.data['first_comment'] if 'first_comment' in request.data else '' 
        data.update({'first_comment': first_comment })
        body = render_to_string("share_quote_saam.html", data)
        data.update({'body': body})
            
        url = host + "mails/share-cotizacion-manual"
        headers = {"user_agent": "mozilla", }
        req = requests.post(url, data=data, headers=headers)
        
        

        try:
            if str(req) == str('<Response [200]>'):
                model = 1
                tipo = ' la cotización: '
                number = cotizacion.id
                dataIdent = ' compartió' +str(tipo)+str(number)
                original = {}
                change= dataIdent                    
                try:
                    send_log_complete(request.user, cotizacion.org_name, 'POST', model, '%s' % str(dataIdent),'%s' % str(original),'%s' % str(change), cotizacion.id)
                except Exception as eee:
                    pass
                # LOG-------------
                if model_log:
                    if not request.data['custom_email']:
                        body = render_to_string("share_policyNV.html", data)
                    comment = Comments(model=model_log, id_model=request.data['id'], content="Se ha compartido la cotización", org_name = request.GET.get('org'), user= request.user)
                    comment.save()
                    email_log = LogEmail(model=model_log, associated_id=request.data['id'], comment=comment, to=str(receiver).replace('[', '').replace(']', '').replace('"', ''), cc=request.user.email, subject=subject, body=body, files=files_data)
                    email_log.save()

                return Response({'response': 'sent'}, status=200, headers=headers)
            else:
                return Response({'response': 'Error'}, status=400,)
        except Exception as e:
            print(e)
            return Response({'response': 'Error!'}, status=400,)
  

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def SendToProviderNV(request):
    receiver = []
    try:
        poliza = Polizas.objects.get(pk=int(request.data['id']), org_name = request.GET.get('org'))
    except:
        return Response({'error': 'No existe la poliza'})

    try:
        if poliza.contractor:
            contratante = poliza.contractor.full_name
        else:
            contratante = ''
    except Exception as e:
        contratante = ''

    for em in request.data['email']:
        receiver.append(em)

    remitente,logo,logo_mini = user_remitente(request)

    subject = 'Póliza: ' + str(poliza.poliza_number) + ', ' + str(poliza.aseguradora) + ' ' + str(poliza.subramo)

    files_data = []
    media = {'media': ''}
    if request.data['pdf'] != 'ot':
        files_type = 'url'
        files_data.append({'url': request.data['pdf'], 'name': request.data['pdf']})
        #email.attach(str(request.data['pdf']), open(str(request.data['pdf']), 'rb').read(), 'application/pdf')
    else:
        files_type = 'media'
        pdf_name = PDF_OT_LOCAL(request)
        media = {'media': open(pdf_name, "rb")}
        os.remove(pdf_name)

    data = {
        'start_of_validity': poliza.start_of_validity.strftime("%d/%m/%Y"),
        'end_of_validity': poliza.end_of_validity.strftime("%d/%m/%Y"),
        'ramo': poliza.ramo,
        'subramo': poliza.subramo,
        'frecuencia_de_pago': poliza.get_forma_de_pago_display(),
        'contratante': contratante,

        'files': json.dumps(files_data),
        'logo': logo,
        'logo_mini': logo_mini,
        'remitente': remitente,
        'subject': subject,
        'receiver': json.dumps(receiver),
        'cc': json.dumps([request.user.email]),
    }

    url = host + "mails/send-to-provider/"
    headers = {"user_agent": "mozilla", }
    req = requests.post(url, data=data, files=media, headers=headers)
    try:
        if str(req) == str('<Response [200]>'):
            return Response({'response': 'sent'}, status=200, headers=headers)
        else:
            return Response({'response': 'Error'}, status=400, )
    except Exception as e:
        return Response({'response': 'Error!'}, status=400, )


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def CancelPolicyEmailNV(request):
    try:
        poliza = Polizas.objects.get(pk=int(request.data['id']))
    except:
        return Response({'error': 'No existe la poliza'})

    receiver = []
    user_ = request.data['user_cancel']
    emails_ = requests.get(settings.CAS_URL + 'get-emails/?org_id=' + str(request.GET.get('org')))
    response = json.loads(emails_.text)
    users = response['data']
    for email in users:
        if email['email']:
            receiver.append(email['email'])

    if poliza.contractor:
        contratante = poliza.contractor.full_name
    else:
        contratante = ''

    poliza.p_neta = '$' + '{:,.2f}'.format(poliza.p_neta)
    poliza.p_total = '$' + '{:,.2f}'.format(poliza.p_total)
    poliza.derecho = '$' + '{:,.2f}'.format(poliza.derecho)
    poliza.rpf = '$' + '{:,.2f}'.format(poliza.rpf)
    poliza.iva = '$' + '{:,.2f}'.format(poliza.iva)

    remitente, logo, logo_mini = user_remitente(request)

    subject = 'Póliza: ' + str(poliza.poliza_number) + ', ' + str(poliza.aseguradora) + ' ' + str(poliza.subramo)

    data = {
        'poliza_number': poliza.poliza_number,
        'start_of_validity': poliza.start_of_validity,
        'end_of_validity': poliza.end_of_validity,
        'ramo': poliza.ramo,
        'subramo': poliza.subramo,
        'frecuencia_de_pago': poliza.get_forma_de_pago_display(),
        'contratante': contratante,
        'aseguradora': poliza.aseguradora,
        'prima_neta': poliza.p_neta,
        'prima_total': poliza.p_total,
        'derecho': poliza.derecho,
        'rpf': poliza.rpf,
        'iva': poliza.iva,
        'user_cancel': user_,
        'reason_cancel': poliza.reason_cancel,

        'remitente': remitente,
        'subject': subject,
        'receiver': json.dumps(receiver),
        'cc': json.dumps([request.user.email]),
    }

    url = host + "mails/cancel-policy-manual/"
    headers = {"user_agent": "mozilla", }
    req = requests.post(url, data=data, headers=headers)
    try:
        if str(req) == str('<Response [200]>'):
            return Response({'response': 'sent'}, status=200, headers=headers)
        else:
            return Response({'response': 'Error'}, status=400, )
    except Exception as e:
        return Response({'response': 'Error!'}, status=400, )


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def SendEmailNV(request):
    model = int(request.data['model'])
    email_to = []
    files_data = []
    data_extra = {}

    if model == 1 or model == 2 or model == 9:
        remitentes = Remitente.objects.filter(org_name = request.GET.get('org'), area=2, is_active=True)
        try:
            poliza = Polizas.objects.get(pk=int(request.data['id']))
        except Exception as e :
            return Response({'error': 'No existe la poliza'})
    elif model == 3 or model == 4 or model == 11 or model == 12 or model == 13 or model == 14:
        remitentes = Remitente.objects.filter(org_name = request.GET.get('org'), area=3, is_active=True)
        try:
            siniestro = Siniestros.objects.get(pk=int(request.data['id']))
        except:
            return Response({'error': 'No existe el Siniestro'})
    elif model == 6:
        remitentes = Remitente.objects.filter(org_name = request.GET.get('org'), area=1, is_active=True)
        try:
            recibo = Recibos.objects.get(pk=int(request.data['id']))
        except:
            return Response({'error': 'No existe el Recibo'})
    elif model == 7 or model == 8:
        remitentes = Remitente.objects.filter(org_name = request.GET.get('org'), area=1, is_active=True)
        try:
            nota = Recibos.objects.get(pk=int(request.data['id']), receipt_type=3)
        except:
            return Response({'error': 'No existe la Nota'})

    elif model == 15 or model == 16 or model == 17 or model == 18:
        remitentes = Remitente.objects.filter(org_name = request.GET.get('org'), area=0, is_active=True).values()
        try:
            fianza = Polizas.objects.get(pk=int(request.data['id']))
        except:
            return Response({'error': 'No existe la fianza'})
    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    if model == 1:
        subject = 'Aviso de creación de orden de trabajo: ' + str(poliza.internal_number)
    elif model == 2:
        subject = 'Se ha emitido la póliza ' + str(poliza.poliza_number)
    elif model == 3:
        subject = 'Aviso de solicitud de siniestro ' + str(siniestro.numero_siniestro)
    elif model == 4:
        subject = 'Se ha finalizado el siniestro ' + str(siniestro.numero_siniestro)
    elif model == 9:
        subject = 'Se ha renovado una póliza con número: ' + str(poliza.poliza_number)
    elif model == 6:
        subject = 'Se ha pagado el Recibo: #' + str(recibo.recibo_numero) + ' de la póliza: ' + str(
            recibo.poliza.poliza_number)
    elif model == 7:
        # subject = 'Se ha creado la Nota de Crédito: ' + str(nota.folio if nota.folio else '')
        subject = 'Se ha creado la Nota de Crédito: ' + (str(nota.folio) if nota.folio is not None else '')
    elif model == 8:
        subject = 'Se ha aplicado la Nota de Crédito: ' + str(nota.folio)
    elif model == 11:
        subject = 'Aviso de Trámite de siniestro ' + str(siniestro.numero_siniestro)
    elif model == 12:
        subject = 'Aviso de Cancelación de siniestro ' + str(siniestro.numero_siniestro)
    elif model == 13:
        subject = 'Aviso de Rechazo de siniestro ' + str(siniestro.numero_siniestro)
    elif model == 14:
        subject = 'Aviso de Espera de siniestro ' + str(siniestro.numero_siniestro)
    # CORREOS DE FIANZA
    elif model == 15:
        subject = 'Aviso Trámite de Fianza ' + str(fianza.fianza_number)
    elif model == 16:
        subject = 'Aviso de Fianza Vigente ' + str(fianza.fianza_number)
    elif model == 17:
        subject = 'Aviso de Cancelación de Fianza ' + str(fianza.fianza_number)
    elif model == 18:
        subject = 'Aviso de Cierre de Fianza ' + str(fianza.fianza_number)

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    try:
        email_info = EmailInfo.objects.get(org_name = request.GET.get('org'), model=model)
        email_info_text = email_info.text
    except:
        email_info_text = "Información de la operación"
    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
    response_org = org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
    if 'logo' in org_info.keys() and len(org_info['logo']) != 0:
        _imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
        if _imagen:
            archivo_imagen = _imagen
        else:
            archivo_imagen = archivo_imagen
    direccion =  org_info['address']
    # OT, Póliza, Renovación
    if model == 1 or model == 2 or model == 9:

        if poliza.contractor:
            contratante = poliza.contractor
            contratante_name = poliza.contractor.full_name #json.dumps(poliza.juridical)
        else:
            contratante = ''
            contratante_name = ''

        if poliza.forma_de_pago == 1:
            forma_de_pago = "Mensual"
        elif poliza.forma_de_pago == 2:
            forma_de_pago = "Bimestral"
        elif poliza.forma_de_pago == 3:
            forma_de_pago = "Trimestral"
        elif poliza.forma_de_pago == 5:
            forma_de_pago = "Contado"
        elif poliza.forma_de_pago == 6:
            forma_de_pago = "Semestral"
        elif poliza.forma_de_pago == 12:
            forma_de_pago = "Anual"
        else:
            forma_de_pago = poliza.forma_de_pago

        email_to = contratante.email

        if model == 2:
            if admin_archivos(request):
                files = PolizasFile.objects.filter(owner=poliza, org_name = request.GET.get('org'))
                if files:
                    for file in files:
                        # URL = settings.MEDIA_URL + str(file.arch).replace(" ", "+")
                        file.arch = get_presigned_url(folder+"/{url}".format(url=file.arch),28800)  
                        URL = str(file.arch).replace(" ", "+")
                        # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26");
                        files_data.append({'url': URL, 'name': file.nombre})

                        # URL = settings.MEDIA_URL + str(file.arch).replace(" ", "+")
                        # with urllib.request.urlopen(URL) as url:
                        #     with open(str(file.nombre), 'wb') as f:
                        #         f.write(url.read())
                        # email.attach(file.nombre, open(file.nombre, 'rb').read(), 'application/pdf')
      

        data_extra = {
            'html': "correo_auto_2024.html",
            'files': json.dumps(files_data),
            'custom_txt': email_info_text,
            'num_policy': poliza.poliza_number,
            'ot': poliza.internal_number,
            'aseguradora': poliza.aseguradora.compania,
            'start_of_validity': poliza.start_of_validity.strftime("%d/%m/%y"),
            'end_of_validity': poliza.end_of_validity.strftime("%d/%m/%y"),
            'ramo': poliza.ramo.ramo_name,
            'subramo': poliza.subramo.subramo_name,
            'frecuencia_de_pago': forma_de_pago,
            'logo': archivo_imagen,
            'direccion':direccion,
            'colorBackground':'#e6f0f7',
            'colorLine':'#3387bf',
            'contratante': contratante_name,
            'prima_neta': '$' + '{:,.2f}'.format(poliza.p_neta),
            'derecho': '$' + '{:,.2f}'.format(poliza.derecho),
            'rpf': '$' + '{:,.2f}'.format(poliza.rpf),
            'iva': '$' + '{:,.2f}'.format(poliza.iva),
            'prima_total': '$' + '{:,.2f}'.format(poliza.p_total),
        }

    # Siniestro
    elif model == 3 or model == 4 or model == 11 or model == 12 or model == 13 or model == 14:

        if siniestro.poliza.contractor:
            contratante = siniestro.poliza.contractor.full_name
            email_to = siniestro.poliza.contractor.email
        else:
            contratante =''
            email_to = ''
        #email_to = contratante.email
        if  model == 12 or model == 13:
            back = '#fdf1e6'
            color = '#ed8f39'
        else:
            back = '#e6faea'
            color =  '#33d456'

        if siniestro.poliza.forma_de_pago == 1:
            forma_de_pago = "Mensual"
        elif siniestro.poliza.forma_de_pago == 2:
            forma_de_pago = "Bimestral"
        elif siniestro.poliza.forma_de_pago == 3:
            forma_de_pago = "Trimestral"
        elif siniestro.poliza.forma_de_pago == 5:
            forma_de_pago = "Contado"
        elif siniestro.poliza.forma_de_pago == 6:
            forma_de_pago = "Semestral"
        elif siniestro.poliza.forma_de_pago == 12:
            forma_de_pago = "Anual"
        else:
            forma_de_pago = siniestro.poliza.forma_de_pago

        if siniestro.tipo_siniestro_general == 2:
            tipo = "Accidentes y Enfermedades"
        elif siniestro.tipo_siniestro_general == 3:
            tipo = "Automóviles"
        elif siniestro.tipo_siniestro_general == 1:
            tipo = "Vida"
        elif siniestro.tipo_siniestro_general == 4:
            tipo = "Daños"

        if siniestro.status == 1:
            status = "Pendiente"
        elif siniestro.status == 2:
            status = "En Trámite"
        elif siniestro.status == 3:
            status = "Completado"
        elif siniestro.status == 4:
            status = "Cancelado"
        elif siniestro.status == 5:
            status = "Rechazado"
        elif siniestro.status == 6:
            status = "En Espera"

        if siniestro.fecha_ingreso:
            fecha_ingreso = siniestro.fecha_ingreso.strftime("%d/%m/%y")

        if siniestro.fecha_siniestro:
            fecha_sin = siniestro.fecha_siniestro.strftime("%d/%m/%y")


        siniestro_esp = siniestro
        if siniestro_esp.tipo_siniestro_general == 2:
            accident = Accidentes.objects.filter(siniestro=request.data['id'], org_name = request.GET.get('org'))
            try:
                reclamado = accident[0].total_reclamado
                reclamado = '$' + '{:,.2f}'.format(reclamado)
            except:
                reclamado = 0.00
            try:
                if siniestro.poliza.aseguradora:
                    asegurador = siniestro.poliza.aseguradora.compania
                else:
                    asegurador = siniestro.poliza.aseguradora
            except Exception as e:
                asegurador = ''

            data_extra = {
                'html': "correo_auto_sin_2024.html",
                'custom_txt': email_info_text,
                'num_policy': siniestro.poliza.poliza_number,
                'ot': siniestro.poliza.internal_number,
                'aseguradora': asegurador,
                'start_of_validity': siniestro.poliza.start_of_validity.strftime("%d/%m/%y"),
                'end_of_validity': siniestro.poliza.end_of_validity.strftime("%d/%m/%y"),
                'ramo': siniestro.poliza.ramo.ramo_name,
                'subramo': siniestro.poliza.subramo.subramo_name,
                'frecuencia_de_pago': forma_de_pago,
                'contratante': contratante,
                'var_title': 'Total Reclamado',
                'var': reclamado,
                'prima_neta': '$' + '{:,.2f}'.format(siniestro.poliza.p_neta),
                'derecho': '$' + '{:,.2f}'.format(siniestro.poliza.derecho),
                'rpf': '$' + '{:,.2f}'.format(siniestro.poliza.rpf),
                'iva': '$' + '{:,.2f}'.format(siniestro.poliza.iva),
                'prima_total': '$' + '{:,.2f}'.format(siniestro.poliza.p_total),
                'num_siniestro': siniestro.numero_siniestro,
                'tipo_sin': tipo,
                'afectado': siniestro.affected_item,
                'reason': siniestro.reason,
                'observations': siniestro.observations,
                'status': status,
                'fecha_ingreso': fecha_ingreso,
                'fecha_sin': fecha_sin,
                'colorBackground': back,
                'colorLine': color,
                'logo': archivo_imagen,
                'direccion':direccion,
            }

        elif siniestro_esp.tipo_siniestro_general == 3:
            damage = Autos.objects.filter(siniestro=request.data['id'], org_name = request.GET.get('org'))
            try:
                reclamado = damage[0].indemnizacion
                reclamado = '$' + '{:,.2f}'.format(reclamado)
            except:
                reclamado = 0.00

            data_extra = {
                'html':"correo_auto_sin_2024.html",

                'custom_txt': email_info_text,
                'num_policy': siniestro.poliza.poliza_number,
                'ot': siniestro.poliza.internal_number,
                'aseguradora': siniestro.poliza.aseguradora.compania,
                'start_of_validity': siniestro.poliza.start_of_validity.strftime("%d/%m/%y"),
                'end_of_validity': siniestro.poliza.end_of_validity.strftime("%d/%m/%y"),
                'ramo': siniestro.poliza.ramo.ramo_name,
                'subramo': siniestro.poliza.subramo.subramo_name,
                'frecuencia_de_pago': forma_de_pago,
                'contratante': contratante,
                'var_title': 'Indemnización',
                'var': reclamado,
                'prima_neta': '$' + '{:,.2f}'.format(siniestro.poliza.p_neta),
                'derecho': '$' + '{:,.2f}'.format(siniestro.poliza.derecho),
                'rpf': '$' + '{:,.2f}'.format(siniestro.poliza.rpf),
                'iva': '$' + '{:,.2f}'.format(siniestro.poliza.iva),
                'prima_total': '$' + '{:,.2f}'.format(siniestro.poliza.p_total),
                'num_siniestro': siniestro.numero_siniestro,
                'tipo_sin': tipo,
                'afectado': siniestro.affected_item,
                'reason': siniestro.reason,
                'observations': siniestro.observations,
                'status': status,
                'fecha_ingreso': fecha_ingreso,
                'fecha_sin': fecha_sin,
                'colorBackground': '#e6faea',
                'colorLine': '#33d456',
                'logo': archivo_imagen,
                'direccion':direccion,
            }
        elif siniestro_esp.tipo_siniestro_general == 1:
            vida = Vida.objects.filter(siniestro=request.data['id'], org_name = request.GET.get('org'))
            try:
                reclamado = vida[0].tipo_pago
            except:
                reclamado = "No definido"
            if reclamado == 1:
                reclamado = "Cheque"
            elif reclamado == 2:
                reclamado = "Transferencia"
            else:
                reclamado = reclamado
            data_extra = {
                'html':"correo_auto_sin_2024.html",
                'custom_txt': email_info_text,
                'num_policy': siniestro.poliza.poliza_number,
                'ot': siniestro.poliza.internal_number,
                'aseguradora': siniestro.poliza.aseguradora.compania,
                'start_of_validity': siniestro.poliza.start_of_validity.strftime("%d/%m/%y"),
                'end_of_validity': siniestro.poliza.end_of_validity.strftime("%d/%m/%y"),
                'ramo': siniestro.poliza.ramo.ramo_name,
                'subramo': siniestro.poliza.subramo.subramo_name,
                'frecuencia_de_pago': forma_de_pago,
                'contratante': contratante,
                'var_title': 'Tipo Pago',
                'var': reclamado,
                'prima_neta': '$' + '{:,.2f}'.format(siniestro.poliza.p_neta),
                'derecho': '$' + '{:,.2f}'.format(siniestro.poliza.derecho),
                'rpf': '$' + '{:,.2f}'.format(siniestro.poliza.rpf),
                'iva': '$' + '{:,.2f}'.format(siniestro.poliza.iva),
                'prima_total': '$' + '{:,.2f}'.format(siniestro.poliza.p_total),
                'num_siniestro': siniestro.numero_siniestro,
                'tipo_sin': tipo,
                'afectado': siniestro.affected_item,
                'reason': siniestro.reason,
                'observations': siniestro.observations,
                'status': status,
                'fecha_ingreso': fecha_ingreso,
                'fecha_sin': fecha_sin,
                'colorBackground': '#e6faea',
                'colorLine': '#33d456',
                'logo': archivo_imagen,
                'direccion':direccion,
            }
        elif siniestro_esp.tipo_siniestro_general == 4:
            damage = Danios.objects.filter(siniestro=request.data['id'], org_name = request.GET.get('org'))
            try:
                reclamado = damage[0].indemnizacion
                reclamado = '$' + '{:,.2f}'.format(reclamado)
            except:
                reclamado = 0.00

            data_extra = {
                'html':"correo_auto_sin_2024.html",

                'custom_txt': email_info_text,
                'num_policy': siniestro.poliza.poliza_number,
                'ot': siniestro.poliza.internal_number,
                'aseguradora': siniestro.poliza.aseguradora.compania,
                'start_of_validity': siniestro.poliza.start_of_validity.strftime("%d/%m/%y"),
                'end_of_validity': siniestro.poliza.end_of_validity.strftime("%d/%m/%y"),
                'ramo': siniestro.poliza.ramo.ramo_name,
                'subramo': siniestro.poliza.subramo.subramo_name,
                'frecuencia_de_pago': forma_de_pago,
                'contratante': contratante,
                'var_title': 'Indemnización',
                'var': reclamado,
                'prima_neta': '$' + '{:,.2f}'.format(siniestro.poliza.p_neta),
                'derecho': '$' + '{:,.2f}'.format(siniestro.poliza.derecho),
                'rpf': '$' + '{:,.2f}'.format(siniestro.poliza.rpf),
                'iva': '$' + '{:,.2f}'.format(siniestro.poliza.iva),
                'prima_total': '$' + '{:,.2f}'.format(siniestro.poliza.p_total),
                'num_siniestro': siniestro.numero_siniestro,
                'tipo_sin': tipo,
                'afectado': siniestro.affected_item,
                'reason': siniestro.reason,
                'observations': siniestro.observations,
                'status': status,
                'fecha_ingreso': fecha_ingreso,
                'fecha_sin': fecha_sin,
                'colorBackground': '#e6faea',
                'colorLine': '#33d456',
                'logo': archivo_imagen,
                'direccion':direccion,
            }
            # Pago de recibo
    elif model == 6:
        if recibo.poliza.contractor:
            contratante = recibo.poliza.contractor.full_name
            email_to = recibo.poliza.contractor.email
        else:
            contratante = ''
            email_to = ''

        if recibo.poliza.forma_de_pago == 1:
            forma_de_pago = "Mensual"
        elif recibo.poliza.forma_de_pago == 2:
            forma_de_pago = "Bimestral"
        elif recibo.poliza.forma_de_pago == 3:
            forma_de_pago = "Trimestral"
        elif recibo.poliza.forma_de_pago == 5:
            forma_de_pago = "Contado"
        elif recibo.poliza.forma_de_pago == 6:
            forma_de_pago = "Semestral"
        elif recibo.poliza.forma_de_pago == 12:
            forma_de_pago = "Anual"
        else:
            forma_de_pago = recibo.poliza.forma_de_pago

        if recibo.f_currency == 1:
            moneda = "Pesos"
        elif recibo.f_currency == 2:
            moneda = "Dólares"

        if recibo.receipt_type == 1:
            tipo_rec = "Póliza"
        elif recibo.receipt_type == 2:
            tipo_rec = "Endoso"



        if recibo.poliza.aseguradora:
            company = recibo.poliza.aseguradora.compania
        else:
            company = 'No encontrada'

        if recibo.poliza.start_of_validity:
            start = recibo.poliza.start_of_validity.strftime("%d/%m/%y")
        else:
            start = 'No encontrada'

        if recibo.poliza.end_of_validity:
            end = recibo.poliza.end_of_validity.strftime("%d/%m/%y")
        else:
            end = 'No encontrada'

        if recibo.poliza.ramo:
            if recibo.poliza.ramo.ramo_name:
                ramo = recibo.poliza.ramo.ramo_name
        else:
            ramo = ''
        if recibo.poliza.subramo:
            if recibo.poliza.subramo.subramo_name:
                subramo = recibo.poliza.subramo.subramo_name
        else:
            subramo = ''

        data_extra = {
            'html':"correo_auto_rec.html",
            'custom_txt': email_info_text,
            'num_policy': recibo.poliza.poliza_number,
            'ot': recibo.poliza.internal_number,
            'aseguradora': company,
            'start_of_validity': str(start),
            'end_of_validity': str(end),
            'ramo': ramo,
            'subramo': subramo,
            'frecuencia_de_pago': forma_de_pago,
            'contratante': contratante,
            'subtotal': '$' + '{:,.2f}'.format(recibo.sub_total),
            'prima_neta': '$' + '{:,.2f}'.format(recibo.prima_neta),
            'derecho': '$' + '{:,.2f}'.format(recibo.derecho),
            'rpf': '$' + '{:,.2f}'.format(recibo.rpf),
            'iva': '$' + '{:,.2f}'.format(recibo.iva),
            'prima_total': '$' + '{:,.2f}'.format(recibo.prima_total),
            'num_recibo': recibo.recibo_numero,
            'moneda': moneda,
            'fecha_inicio': recibo.fecha_inicio.strftime("%d/%m/%y"),
            'fecha_fin': recibo.fecha_fin.strftime("%d/%m/%y"),
            'bank': recibo.bank if recibo.bank else '',
            'vencimiento': recibo.vencimiento.strftime("%d/%m/%y"),
            'pay_doc': recibo.pay_doc,
            'tipo_rec': tipo_rec,
        }
    # Creación y aplicación de nota de crédito
    elif model == 7 or model == 8:
         
        if nota.poliza:
            if nota.poliza.contractor:
                contratante = nota.poliza.contractor.full_name
                email_to = nota.poliza.contractor.email
            else:
                contratante =''
                email_to = ''

            if nota.poliza.forma_de_pago == 1:
                forma_de_pago = "Mensual"
            elif nota.poliza.forma_de_pago == 2:
                forma_de_pago = "Bimestral"
            elif nota.poliza.forma_de_pago == 3:
                forma_de_pago = "Trimestral"
            elif nota.poliza.forma_de_pago == 5:
                forma_de_pago = "Contado"
            elif nota.poliza.forma_de_pago == 6:
                forma_de_pago = "Semestral"
            elif nota.poliza.forma_de_pago == 12:
                forma_de_pago = "Anual"
            else:
                forma_de_pago = nota.poliza.forma_de_pago

            if nota.poliza.f_currency == 1:
                moneda = "Pesos"
            elif nota.poliza.f_currency == 2:
                moneda = "Dólares"

            if nota.poliza.subramo.subramo_name == 'Vida':
                endoso = "Endoso de Vida"
            elif nota.poliza.subramo.subramo_name == 'Automóviles':
                endoso = "Endoso de Autos"
            elif nota.poliza.subramo.subramo_name == 'Gastos Médicos':
                endoso = "Endoso de Accidentes y Enfermedades"
            elif nota.poliza.ramo.ramo_name == 'Daños' and nota.poliza.subramo.subramo_name != 'Automóviles':
                endoso = str("Endoso de Daños: ") + nota.poliza.subramo.subramo_name
            else:
                endoso = 'Endoso'

            np = nota.poliza.poliza_number
            internal = nota.poliza.internal_number
            aseg = nota.poliza.aseguradora.compania
            fi = nota.poliza.start_of_validity
            fe = nota.poliza.end_of_validity
            ramo = nota.poliza.ramo.ramo_name
            sramo = nota.poliza.subramo.subramo_name

        elif nota.fianza:
            if nota.fianza.contractor:
                contratante = nota.fianza.contractor.full_name
            else:
                contratante =''
            forma_de_pago = "Anual"

            if nota.fianza.f_currency == 1:
                moneda = "Pesos"
            elif nota.fianza.f_currency == 2:
                moneda = "Dólares"

            if nota.fianza.subramo.subramo_name == 'Vida':
                endoso = "Endoso de Vida"
            elif nota.fianza.subramo.subramo_name == 'Automóviles':
                endoso = "Endoso de Autos"
            elif nota.fianza.subramo.subramo_name == 'Gastos Médicos':
                endoso = "Endoso de Accidentes y Enfermedades"
            elif nota.fianza.ramo.ramo_name == 'Daños' and nota.fianza.subramo.subramo_name != 'Automóviles':
                endoso = str("Endoso de Daños: ") + nota.fianza.subramo.subramo_name
            else:
                endoso = 'Endoso'

            np = nota.fianza.fianza_number
            internal = nota.fianza.internal_number
            aseg = nota.fianza.afianzadora.compania
            fi = nota.fianza.start_of_validity
            fe = nota.fianza.end_of_validity
            ramo = nota.fianza.ramo.ramo_name
            sramo = nota.fianza.subramo.subramo_name,

        if nota.status == 1:
            status_nc = "Cobrada"
        elif nota.status == 2:
            status_nc = "Cancelada"
        elif nota.status == 3:
            status_nc = "Prorrogada"
        elif nota.status == 4:
            status_nc = "Pendiente de pago"
        elif nota.status == 5:
            status_nc = "Liquidado"
        elif nota.status == 6:
            status_nc = "Conciliada"
        elif nota.status == 7:
            status_nc = "Cerrada"
        else:
            status_nc = 'No establecido'

        #email_to = contratante.email
        if model == 8:
          colorBackground = '#e6faea'
          colorLine = '#33d456'
        else:
          colorBackground = '#e6f0f7'
          colorLine = '#3387bf'

        data_extra = {
            'html':"correo_auto_note_2024.html",

            'custom_txt': email_info_text,
            'num_policy': np,
            'ot': internal,
            'aseguradora': aseg,
            'start_of_validity': fi.strftime("%d/%m/%y"),
            'end_of_validity': fe.strftime("%d/%m/%y"),
            'ramo': ramo,
            'subramo': sramo,
            'frecuencia_de_pago': forma_de_pago,
            'contratante': contratante,
            'subtotal': '$' + '{:,.2f}'.format(nota.sub_total),
            'prima_neta': '$' + '{:,.2f}'.format(nota.prima_neta),
            'rpf': '$' + '{:,.2f}'.format(nota.rpf),
            'iva': '$' + '{:,.2f}'.format(nota.iva),
            'prima_total': '$' + '{:,.2f}'.format(nota.prima_total),
            'moneda': moneda,
            'fecha_emision': nota.created_at.strftime("%d/%m/%y"),
            'folio': nota.folio,
            'endoso': endoso,
            'status': status_nc,
            'gastos': '$' + '{:,.2f}'.format(nota.derecho),
            'logo': archivo_imagen,
            'direccion':direccion,
            'colorBackground':colorBackground,
            'colorLine':colorLine,
        }

    elif model == 15 or model == 16 or model == 17 or model == 18:

        f_beneficiarios = BeneficiariesContract.objects.filter(fianza_many=int(request.data['id'])).values('full_name',
                                                                                                           'email');

        for fb in f_beneficiarios:
            email_to.append(fb['email'])
        try:
            email_to = email_to[0]
        except Exception as e:
            email_to = email_to
        # email_to = 'david.cantu@miurabox.com'
        data_extra = {
            'html':"fianza_email.html",
            'custom_txt': email_info_text,
            'fianza_number': fianza.fianza_number,
            'afianzadora': fianza.afianzadora,
            'ramo': fianza.ramo,
            'subramo': fianza.subramo,
            'fianza_type': fianza.fianza_type,
        }

    remitente,logo,logo_mini = user_remitente(request)

    data = {
        'data_extra': json.dumps(data_extra),

        'remitente': remitente,
        'subject': subject,
        'receiver': json.dumps(email_to),
        'cc': json.dumps([request.user.email]),
    }


    url = host + "mails/send-email/"
    headers = {"user_agent": "mozilla", }
    req = requests.post(url, data=data, headers=headers)

    try:
        if str(req) == str('<Response [200]>'):
            return Response({'response': 'sent'}, status=200, headers=headers)
        else:
            return Response({'response': 'Error'}, status=400, )
    except Exception as e:
        print(e)
        return Response({'response': 'Error!'}, status=400, )

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def SendEmailRecNV(request):
    model = int(request.data['model'])
    email = request.data['emails']
    if model == 10:
        try:
            poliza = Polizas.objects.get(pk=int(request.data['id']))
        except:
            return Response({'error': 'No existe la poliza'})

    if model == 10:
        subject = 'Recordatorio de renovación: ' + str(poliza.poliza_number)

    try:
        email_info = EmailInfo.objects.get(org_name = request.GET.get('org'), model=model)
        email_info_text = email_info.text
    except:
        email_info_text = "Información de la operación "

    if poliza.contractor:
        contratante = poliza.contractor.full_name
    else:
        contratante =''

    if poliza.forma_de_pago == 1:
        forma_de_pago = "Mensual"
    elif poliza.forma_de_pago == 2:
        forma_de_pago = "Bimestral"
    elif poliza.forma_de_pago == 3:
        forma_de_pago = "Trimestral"
    elif poliza.forma_de_pago == 5:
        forma_de_pago = "Contado"
    elif poliza.forma_de_pago == 6:
        forma_de_pago = "Semestral"
    elif poliza.forma_de_pago == 12:
        forma_de_pago = "Anual"
    else:
        forma_de_pago = poliza.forma_de_pago

    email_info = 'Recordatorio de renovación de póliza'

    if model == 10:
        try:
            if poliza.start_of_validity:
                p_start = (poliza.start_of_validity).strftime("%d/%m/%y")
            else:
                p_start = 'Sin fecha vigencia inicial'
        except:
            p_start = 'Sin fecha vigencia inicial'
        try:
            if poliza.end_of_validity:
                p_end = (poliza.end_of_validity).strftime("%d/%m/%y")
            else:
                p_end = 'Sin fecha vigencia final'
        except:
            p_end = 'Sin fecha vigencia final'

        message = render_to_string("correo_reminder_poliza.html", {
            'custom_txt': email_info,
            'tipo': 'Pólza a renovar',
            'num_policy': poliza.poliza_number,
            'aseguradora': poliza.aseguradora.compania,
            'start_of_validity': p_start,
            'end_of_validity': p_end,
            'ramo': poliza.ramo.ramo_name,
            'subramo': poliza.subramo.subramo_name,
            'contratante': contratante,
            'forma_de_pago': forma_de_pago,
            'fecha_i': p_start,
            'fecha_f': p_end,
            'prima_neta': '$' + '{:,.2f}'.format(poliza.p_neta),
            'derecho': '$' + '{:,.2f}'.format(poliza.derecho),
            'rpf': '$' + '{:,.2f}'.format(poliza.rpf),
            'iva': '$' + '{:,.2f}'.format(poliza.iva),
            'prima_total': '$' + '{:,.2f}'.format(poliza.p_total),
        })

        # GET ORG INFO
        org_info = get_org_info(request)
        # Sendgrit Piloto test
        if request.user.email:
            remitente = "{} <{}>".format(org_info['name'], request.user.email)
        elif org_info['email']:
            remitente = "{} <{}>".format(org_info['name'], org_info['email'])
        else:
            remitente = "{} <no-reply@miurabox.com>".format(org_info['name'])

        email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email, cc=[request.user.email])

    email.content_subtype = "html"
    email.mixed_subtype = 'related'

    try:
        email.send()
        val = {'status': 'sent'}
        return JsonResponse(val, status=200)

    except smtplib.SMTPAuthenticationError:
        val = {'status': 'Credenciales de correo mal configuradas. Comuniquese con su administrador'}
        return JsonResponse(val, status=400)

    except:
        val = {'status': 'Error al enviar el recordatorio de renovación'}
        return JsonResponse(val, status=400)

from email.header import Header
from email.utils import parseaddr, formataddr
import logging,unicodedata


logger = logging.getLogger(__name__)
def ascii_sin_acentos(texto):
    if texto is None:
        return ""
    # quita acentos y caracteres no-ASCII
    return (unicodedata.normalize('NFKD', str(texto))
            .encode('ascii', 'ignore')
            .decode('ascii'))

def safe_print(obj):
    s = str(obj)
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode("utf-8", "ignore").decode("utf-8"))
def remitente_ascii(remitente):
    name, addr = parseaddr(remitente or "")
    return "{} <{}>".format(ascii_sin_acentos(name), ascii_sin_acentos(addr))
def log_remitente(remitente):
    name, addr = parseaddr(remitente or "")
    logger.info("remitente: name=%s addr=%s", name, addr)
# def build_from_header(remitente):
#     print('remiteeeeeeeeeeeeeeee***',remitente)
#     # remitente puede ser "Nombre con acentos <correo@dominio.com>"
#     name, addr = parseaddr(remitente or "")
#     # Codifica el nombre (con acentos) como header RFC
#     safe_name = str(Header(name, 'utf-8')) if name else ""
#     return formataddr((safe_name, addr))   # -> "=?utf-8?b?...?= <correo@dominio.com>"
import re
from email.header import Header
from email.utils import parseaddr, formataddr

EMAIL_RE = re.compile(r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})")

def build_from_header(remitente):
    raw = (remitente or "").strip()
    # 1) Si trae <...> y el nombre tiene coma, pon el display-name entre comillas
    #    para que parseaddr no lo corte.
    if "<" in raw and ">" in raw:
        display = raw.split("<", 1)[0].strip()
        rest = "<" + raw.split("<", 1)[1].strip()
        if "," in display and not (display.startswith('"') and display.endswith('"')):
            display = '"' + display.replace('"', '') + '"'
        raw = display + " " + rest

    # 2) parseaddr
    name, addr = parseaddr(raw)

    # 3) Fallback por si addr vino vacío o raro
    if not addr:
        m = EMAIL_RE.search(raw)
        if not m:
            raise ValueError("Remitente sin email válido: {0}".format(remitente))
        addr = m.group(1)

    # 4) Si el nombre quedó vacío (o demasiado corto), reconstruye desde raw
    if not name:
        name = raw.replace(addr, "")
        name = name.replace("<", " ").replace(">", " ")
        name = re.sub(r"\s+", " ", name).strip().strip('"')

    # 5) RFC2047 para UTF-8 (acentos)
    safe_name = str(Header(name, "utf-8")) if name else ""

    return formataddr((safe_name, addr))

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def payment_reminder_manualNV(request, id=None):
    orgName = request.GET.get('org')
    try:
        configuracion_org = OrgInfo.objects.filter(org_name =orgName)
    except:
        configuracion_org =None
    if request.method == 'POST':
        try:
            recibo = Recibos.objects.get(pk=int(request.data['r_id']))
            asunto = request.data['asunto']
            # filesSend = request.data['files']
            mensaje = request.data['mensaje']
            recibo.track_email = True
            model_log = request.data['model'] if 'model' in request.data else None
        except:
            return Response({'error': 'No existe el recibo'})
        try:
            if int(request.data['nota_id']) != 0:
                nota_credito = Recibos.objects.get(pk=int(request.data['nota_id']), receipt_type=3)
            else:
                nota_credito = ''
        except Exception as rr:
            nota_credito = ''
        org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
        response_org = org_.text
        org_data = json.loads(response_org)
        org_info = org_data['data']['org']
        archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
        type_recibo = 'Póliza'
        tipo_poliza = ''
        asegurado = ''
        if recibo.poliza: 
            if recibo.poliza.document_type == 7 or recibo.poliza.document_type == 8:
                type_recibo = 'Fianza' 
                asegurado = 'FIANZA'  
            elif recibo.poliza.document_type == 1 or recibo.poliza.document_type == 3:
                type_recibo = 'Póliza'
            elif recibo.poliza.document_type ==3:                
                tipo_poliza = 'PÓLIZA DE GRUPO'
            else:
                type_recibo = 'Póliza'
            parCurrency = checkCurrency(recibo.poliza.f_currency)
            currency_format = checkCurrency2(recibo.poliza.f_currency)
            if recibo.poliza.contractor:                
                contratante = recibo.poliza.contractor.full_name
            else:
                contratante = 'no especificado'
            if recibo.poliza.ramo:
                if recibo.poliza.ramo.ramo_code ==1:#vida
                    form = Life.objects.filter(policy = recibo.poliza.id)
                    tipo_poliza = 'VIDA'
                    if form:
                        if form[0]:
                            if form[0].personal:
                                asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                    if not asegurado:
                        form = Personal_Information.objects.filter(policy = recibo.poliza.id)
                        if form:
                            if form[0]:
                                if form[0]:
                                    asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                                else:
                                    asegurado = ''
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                elif recibo.poliza.ramo.ramo_code ==2:#acc
                    tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                    form = AccidentsDiseases.objects.filter(policy = recibo.poliza.id)
                    if form:
                        if form[0]:
                            if form[0].personal:
                                asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                            else:
                                asegurado = ''
                    else:
                        asegurado = ''
                elif recibo.poliza.ramo.ramo_code ==3 and recibo.poliza.subramo.subramo_code ==9:#aut
                    tipo_poliza = 'DAÑOS/AUTOS'
                    form = AutomobilesDamages.objects.filter(policy = recibo.poliza.id)
                    if form:
                        asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                    else:
                        asegurado = ''
                elif recibo.poliza.ramo.ramo_code ==3  and recibo.poliza.subramo.subramo_code !=9:#dañ
                    tipo_poliza = 'DAÑOS DIVERSOS'
                    form = Damages.objects.filter(policy = recibo.poliza.id)
                    if form:
                        asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                    else:
                        asegurado = ''
                if recibo.poliza.document_type ==3:                
                    tipo_poliza = 'PÓLIZA DE GRUPO'
                if recibo.poliza.document_type ==8:                
                    tipo_poliza = 'FIANZA DE GRUPO'
        elif recibo.endorsement:
            asegurado = 'Endoso'
            tipo_poliza = 'ENDOSO'
            if recibo.endorsement.policy: 
                if recibo.endorsement.policy.document_type == 7 or recibo.endorsement.policy.document_type == 8:
                    type_recibo = 'Fianza'  
                    tipo_poliza = 'FIANZA'                 
                elif recibo.endorsement.policy.document_type == 1 or recibo.endorsement.policy.document_type == 3:
                    type_recibo = 'Póliza'                  
                else:
                    type_recibo = 'Póliza' 
                parCurrency = checkCurrency(recibo.endorsement.policy.f_currency)
                if recibo.endorsement.policy.contractor:
                    contratante = recibo.endorsement.policy.contractor.full_name
                else:
                    contratante = 'no especificado'
            else:
                contratante = 'no especificado'
                if recibo.endorsement.policy.document_type == 7 or recibo.endorsement.policy.document_type == 8:
                    type_recibo = 'Fianza'  
                elif recibo.endorsement.policy.document_type == 1 or recibo.endorsement.policy.document_type == 3:
                    type_recibo = 'Póliza'  
                else:
                    type_recibo = 'Póliza' 
                tipo_poliza = '' 

        else:
            contratante = '***'
            asegurado = 'Endoso'
            tipo_poliza = 'NA'
    
        fecha_inicio = (recibo.fecha_inicio).strftime("%d/%m/%y")
        if recibo.poliza:
            f_pago = recibo.poliza.get_forma_de_pago_display()
            subramo = recibo.poliza.subramo
            # subject = str(recibo.poliza.poliza_number) + ';' + str(contratante) + ';' + str(subramo) \
            #         + ';' + str(fecha_inicio)+ ';' + str(f_pago)
            subject = '📆  Recordatorio de pago de recibo de Póliza: '+str(recibo.poliza.poliza_number)
            # subject = 'Recibo: #' + str(recibo.recibo_numero) + ' de la póliza: ' + str(recibo.poliza.poliza_number)
        elif recibo.endorsement:
            if recibo.endorsement.policy:                
                f_pago = recibo.endorsement.policy.get_forma_de_pago_display()
                subramo = recibo.endorsement.policy.subramo
                # subject = str(recibo.endorsement.policy.poliza_number) + ';' + str(contratante) + ';' + str(subramo) \
                #         + ';' + str(fecha_inicio) + ';' + str(f_pago)
                subject = '📆  Recordatorio de pago de recibo de Endoso: '+str(recibo.endorsement.policy.poliza_number)
            elif recibo.endorsement.fianza:                
                f_pago = recibo.endorsement.fianza.get_forma_de_pago_display()
                subramo = recibo.endorsement.fianza.subramo
                # subject = str(recibo.endorsement.fianza.fianza_number) + ';' + str(contratante) + ';' + str(subramo) \
                #         + ';' + str(fecha_inicio) + ';' + str(f_pago)
            else:
                subject = 'Recibo: #' + str(recibo.recibo_numero)
        else:
            subject = 'Recibo: #' + str(recibo.recibo_numero)
    
        if nota_credito:
            # Nota
            prima_neta_nota = float(nota_credito.prima_neta)
            prima_total_nota = float(nota_credito.prima_total)
            derecho_nota = float(nota_credito.derecho)
            iva_nota = float(nota_credito.iva)
            rpf_nota = float(nota_credito.rpf)
            # Recibo
            prima_neta_recibo = float(recibo.prima_neta)
            prima_total_recibo = float(recibo.prima_total)
            derecho_recibo = float(recibo.derecho)
            iva_recibo = float(recibo.iva)
            rpf_recibo = float(recibo.rpf)
            # Resta
            primaNeta = prima_neta_recibo + prima_neta_nota
            primaTotal = prima_total_recibo + prima_total_nota
            derecho_ = derecho_recibo + derecho_nota
            iva_ = iva_recibo + iva_nota
            rpf_ = rpf_recibo + rpf_nota
        else:
            prima_neta_nota = 0
            prima_total_nota = 0
            derecho_nota = 0
            iva_nota = 0
            rpf_nota = 0
            #
            primaNeta = 0
            primaTotal = 0
            derecho_ = 0
            iva_ = 0
            rpf_ = 0
        cc = []
        cco = []
        to_send = []

        if  'emails' in request.data and request.data['emails']:
            to_send = (request.data['emails'])
        if 'emails_cc' in  request.data and request.data['emails_cc']:
            cc = (request.data['emails_cc'])
        if 'emails_cco' in request.data and request.data['emails_cco']:
            cco = (request.data['emails_cco'])
        if configuracion_org and configuracion_org[0] and configuracion_org[0].copia_user_envio:
            if request and request.user and request.user.email:
                cc.append(request.user.email)
        archivo_imagen = 'https://cas.miurabox.com/media/logos/miurabox-01_4ma4N8J.png'
        if 'logo' in org_info.keys() and len(org_info['logo']) != 0:
            _imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
            # _imagen = 'https://miurabox.s3.amazonaws.com/cas/' + org_info['logo']
            # _imagen =get_presigned_url("cas/{url}".format(url=org_info['logo']),28800) 
            # archivo_imagen = 'https://cas.miurabox.com/media/logos/'+org_info['logo']
            if _imagen:
                archivo_imagen = _imagen
            else:
                archivo_imagen = archivo_imagen
                # archivo_imagen = 'https://cas.miurabox.com/media/logos/miurabox-01_4ma4N8J.png'
    
        remitente, logo, logo_mini = user_remitente(request)
        if asunto:
            # subject = str(asunto) 
            subject = '📆 '+str(asunto)  
        files_data = []
        files_selected = request.data['files']

        if files_selected:
            files = RecibosFile.objects.filter(pk__in = files_selected, owner=recibo, org_name = request.GET.get('org'))
            if files:
                for file in files:
                    file.arch = get_presigned_url(folder+"/{url}".format(url=file.arch),28800)  
                    URL = str(file.arch).replace(" ", "+")
                    # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26")
                    files_data.append({'url': URL, 'name': file.nombre})
    
        if recibo.poliza:
            if recibo.poliza.document_type == 1 or recibo.poliza.document_type == 3:
                type_recibo = 'Póliza'
            elif recibo.poliza.document_type == 7 or recibo.poliza.document_type == 8:
                type_recibo = 'Fianza'
            else:
                type_recibo = 'Póliza'
            if recibo.poliza.document_type == 4:
                poliza_number = recibo.poliza.parent.poliza_number
                aseguradora = recibo.poliza.parent.aseguradora
                ramo = recibo.poliza.parent.ramo
                subramo = recibo.poliza.parent.subramo
                frec_pago = recibo.poliza.parent.get_forma_de_pago_display()
            else:
                poliza_number = recibo.poliza.poliza_number
                aseguradora = recibo.poliza.aseguradora
                ramo = recibo.poliza.ramo
                subramo = recibo.poliza.subramo
                frec_pago = recibo.poliza.get_forma_de_pago_display()
        elif recibo.endorsement:
            tipo_poliza = 'ENDOSO'

            if recibo.endorsement.policy:
                if recibo.endorsement.policy.document_type == 1 or recibo.endorsement.policy.document_type == 3:
                    type_recibo = 'Endoso Póliza'
                elif recibo.endorsement.policy.document_type == 7 or recibo.endorsement.policy.document_type == 8:
                    type_recibo = 'Endoso Fianza'
                else:
                    type_recibo = 'Endoso Póliza'
                if recibo.endorsement.policy.document_type == 4:
                    poliza_number = recibo.endorsement.policy.parent.poliza_number
                    aseguradora = recibo.endorsement.policy.parent.aseguradora
                    ramo = recibo.endorsement.policy.parent.ramo
                    subramo = recibo.endorsement.policy.parent.subramo
                    frec_pago = recibo.endorsement.policy.parent.get_forma_de_pago_display()
                else:
                    poliza_number = recibo.endorsement.policy.poliza_number
                    aseguradora = recibo.endorsement.policy.aseguradora
                    ramo = recibo.endorsement.policy.ramo
                    subramo = recibo.endorsement.policy.subramo
                    frec_pago = recibo.endorsement.policy.get_forma_de_pago_display()
            elif recibo.endorsement.fianza:
                type_recibo = 'Endoso Fianza'
                if recibo.endorsement.fianza.document_type == 4:
                    poliza_number = recibo.endorsement.fianza.parent.fianza_number
                    aseguradora = recibo.endorsement.fianza.parent.aseguradora
                    ramo = recibo.endorsement.fianza.parent.ramo
                    subramo = recibo.endorsement.fianza.parent.subramo
                    frec_pago = recibo.endorsement.fianza.parent.get_forma_de_pago_display()
                else:
                    poliza_number = recibo.endorsement.fianza.fianza_number
                    aseguradora = recibo.endorsement.fianza.aseguradora
                    ramo = recibo.endorsement.fianza.ramo
                    subramo = recibo.endorsement.fianza.subramo
                    frec_pago = recibo.endorsement.fianza.get_forma_de_pago_display()
            else:
                type_recibo = 'Póliza'
                poliza_number = recibo.endorsement.number_endorsement
                aseguradora =''
                ramo = ''
                subramo = ''
                frec_pago = ''
        else:
            poliza_number = ''
            aseguradora = ''
            ramo = ''
            subramo = ''
            frec_pago = ''
            type_recibo = 'Póliza'

        identifier = ''
        if recibo.poliza:
            if recibo.poliza.document_type == 4:
                identifier = recibo.poliza.parent.identifier    
            else:
                identifier = recibo.poliza.identifier

            if recibo.poliza.document_type == 7 or recibo.poliza.document_type == 8:
                type_recibo = 'Fianza'  
                tipo_poliza = 'FIANZA'
            elif recibo.poliza.document_type == 1 or recibo.poliza.document_type == 3:
                type_recibo = 'Póliza'
            elif recibo.poliza.document_type ==3:                
                tipo_poliza = 'PÓLIZA DE GRUPO'
            else:
                type_recibo = 'Póliza'

        elif recibo.endorsement:
            if recibo.endorsement.policy:
                if recibo.endorsement.policy.document_type == 7 or recibo.endorsement.policy.document_type == 8:
                    type_recibo = 'Fianza'  
                elif recibo.endorsement.policy.document_type == 1 or recibo.endorsement.policy.document_type == 3:
                    type_recibo = 'Póliza'
                else:
                    type_recibo = 'Póliza'
                identifier = recibo.endorsement.policy.identifier
            elif recibo.endorsement.fianza:
                identifier = recibo.endorsement.fianza.identifier
            else:
                identifier = ''
        else:
            identifier = ''       
        if request.user:
            user = str(request.user.first_name) +' '+str(request.user.last_name)
        else:
            user = ''
        if recibo.endorsement:            
            tipo_poliza = 'ENDOSO'
        try:
            fecha = datetime.today()
            final_time = fecha
            fecha = final_time.date()
        except:
            try:
                fecha = datetime.datetime.today()
                final_time = fecha
                fecha = final_time.date()
            except:
                fecha = ''

        direccion =  org_data['data']['org']['address']
        if recibo.endorsement:
            endos_numero = recibo.endorsement.number_endorsement if recibo.endorsement.number_endorsement else  recibo.endorsement.internal_number
        else:
            endos_numero = ''
        data = {
            'organizacion':orgName,
            'logo': archivo_imagen if archivo_imagen else '',    
            'poliza_number': poliza_number,
            'identificador': identifier,
            'contratante': contratante,
            'aseguradora': aseguradora,
            'ramo': ramo,
            'subramo': subramo,
            'moneda': parCurrency,
            'frecuencia_de_pago': frec_pago,
            'recibo_number': recibo.recibo_numero,
            'vigencia_recibo_i': (recibo.fecha_inicio).strftime("%d/%m/%y"),
            'vigencia_recibo_f': (recibo.fecha_fin).strftime("%d/%m/%y"),
            'prima_neta': '$' + '{:,.2f}'.format(recibo.prima_neta),
            'rpf': '$' + '{:,.2f}'.format(recibo.rpf),
            'derecho': '$' + '{:,.2f}'.format(recibo.derecho),
            'iva': '$' + '{:,.2f}'.format(recibo.iva),
            'primaTotal': '$' + '{:,.2f}'.format(recibo.prima_total),
            'payment_date': (recibo.vencimiento).strftime("%d/%m/%y") if recibo.vencimiento else '',
            'type_recibo': type_recibo,
            'mensaje': mensaje,
            'asegurado': asegurado,
            'endoso': endos_numero,    
            'remitente': remitente,
            'subject': subject,
            'currency_format':currency_format,
            'tipo_poliza':tipo_poliza,
            'fecha':(fecha).strftime("%d/%m/%Y") if fecha else '',
            'user':user,
            'fechaLimitePago':configuracion_org[0].fecha_limite_email_cobranza if configuracion_org and configuracion_org.exists() else True,
            'botonSegumovil':configuracion_org[0].boton_segumovil if configuracion_org and configuracion_org.exists() else True,
            'dato_contratante':configuracion_org[0].dato_contratante if configuracion_org and configuracion_org.exists() else True,
            'dato_numero_poliza':configuracion_org[0].dato_numero_poliza if configuracion_org and configuracion_org.exists() else True,
            'dato_concepto':configuracion_org[0].dato_concepto if configuracion_org and configuracion_org.exists() else True,
            'dato_aseguradora':configuracion_org[0].dato_aseguradora if configuracion_org and configuracion_org.exists() else True,
            'dato_serie':configuracion_org[0].dato_serie if configuracion_org and configuracion_org.exists() else True,
            'dato_subramo':configuracion_org[0].dato_subramo if configuracion_org and configuracion_org.exists() else True,
            'dato_total':configuracion_org[0].dato_total if configuracion_org and configuracion_org.exists() else True, 
            'direccion':direccion,
            'receiver': json.dumps(to_send),
            'cc': json.dumps(cc),
            'cco': json.dumps(cco),
            'files': json.dumps(files_data),
            }
        signature = Signature.objects.filter(user=request.user)
        if signature.exists():            
            data.update({'signature': (signature[0].signature)})
            try:
                # Example usage
                input_str =signature[0].signature
                base64_image = extract_base64_image(input_str)
                if base64_image:
                    # data['firma']='data:image/png;base64,'+base64_image
                    base64_image = extract_base64_image(input_str)
                    if base64_image:                   
                        data.update({'signature_imagen': (signature[0].image_amazon)})
                        data.update({'signature': ''})
                else:
                    print("No base64 image data found.")
            except Exception as ee:
                print('error extract imageeee',ee)
        banner_file = BannerFile.objects.filter(org_name = request.GET.get('org')) 
        if banner_file.exists():
            # data.update({'b_header': banner_file[0].header.url,'b_footer': banner_file[0].footer.url})
            if banner_file[0].header:
                data.update({'logo':''})
                data.update({'b_header':get_url_file(banner_file[0].header)})
            if banner_file[0].footer:
                data.update({'logo':''})
                data.update({'b_footer':get_url_file(banner_file[0].footer)})
       
        if 'custom_email' in request.data  and request.data['custom_email']:
            org_name = request.GET.get('org')
            first_comment = request.data['first_comment'] if 'first_comment' in request.data else '' 
            second_comment = request.data['second_comment'] if 'second_comment' in request.data else '' 
            try:
                textinitial =first_comment if first_comment else ''
                result = re.sub('\?[^"]+', '', textinitial)
                textinitial = result
                img_pattern = r'<img.*?src="data:image/(.*?);base64,(.*?)".*?>'
                images = re.findall(img_pattern, textinitial)
                # print('imagesimages',images)
                if images:
                    for i, (img_type, img_data) in enumerate(images):
                        rnd =random.randint(1,10001)
                        img_name = 'image_'+str(i+1)+'_'+str(rnd)+'.'+str(img_type) 
                        s3_url = upload_to_s3_img_recordatorios(img_data, img_name, img_type,img_name,org_name)
                        search_str = 'data:image/' + img_type + ';base64,' + img_data
                        width = 200
                        height = 200 
                        img_tag = s3_url + '" style="text-align:center;'
                        first_comment = first_comment.replace(search_str, img_tag)
                textinitial_2 =second_comment if second_comment else ''
                result = re.sub('\?[^"]+', '', textinitial_2)
                textinitial_2 = result
                img_pattern = r'<img.*?src="data:image/(.*?);base64,(.*?)".*?>'
                images_2 = re.findall(img_pattern, textinitial_2)
                # print('images_2images_2',images_2)
                if images_2:
                    for i, (img_type, img_data) in enumerate(images_2):
                        rnd =random.randint(1,10001)
                        img_name = 'image_'+str(i+1)+'_'+str(rnd)+'.'+str(img_type) 
                        s3_url = upload_to_s3_img_recordatorios(img_data, img_name, img_type,img_name,org_name)
                        search_str = 'data:image/' + img_type + ';base64,' + img_data
                        width = 200
                        height = 200 
                        img_tag = s3_url + '" style="text-align:center;'
                        second_comment = second_comment.replace(search_str, img_tag)
            except Exception as yimage:
                print('errrrrrrrrrr',yimage)

            data.update({'first_comment':first_comment,'second_comment':second_comment })
            # body = render_to_string("payment_reminderNV_custom.html", data)
            body = render_to_string("mail_recordatorio.html", data)
            data.update({'body': body})
        else:
            # body = render_to_string("payment_reminderNV_custom.html", data)
            body = render_to_string("mail_recordatorio.html", data)
            data.update({'body': body})
        url = host + "mails/payment-reminder-manual/"
        headers = {"user_agent": "mozilla", }
        req = requests.post(url, data=data, headers=headers)
        try:
            if str(req) == str('<Response [200]>'):
                if model_log:
                    if not request.data['custom_email']:
                        body = render_to_string("mail_recordatorio.html", data)
                    comment = Comments(model=model_log, id_model=request.data['r_id'], content="Se ha enviado recordatorio de pago", org_name = request.GET.get('org'), user= request.user)
                    comment.save()
                    email_log = LogEmail(model=model_log, associated_id=request.data['r_id'], comment=comment, to=str(to_send).replace('[', '').replace(']', '').replace('"', '').replace("'", ""), cc=str(cc).replace('[', '').replace(']', '').replace('"', '').replace("'", ""),cco=str(cco).replace('[', '').replace(']', '').replace('"', '').replace("'", ""), subject=subject, body=body, files=files_data)
                    email_log.save()
                    recibo.track_email = True
                    recibo.track_bitacora = True
                    recibo.save()
                return Response({'response': 'sent'}, status=200, headers=headers)
            else:
                return Response({'response': 'Error'}, status=400, )
        except Exception as e:
            return Response({'response': 'Error!'}, status=400, )
    else:
        try:
            recibo = Recibos.objects.get(pk=id)
            model_log = request.data['model'] if 'model' in request.data else None
        except:
            return Response({'error': 'No existe el recibo'})
        try:
            if int(request.data['nota_id']) != 0:
                nota_credito = Recibos.objects.get(pk=int(request.data['nota_id']), receipt_type=3)
            else:
                nota_credito = ''
        except Exception as rr:
            nota_credito = ''
        org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
        response_org = org_.text
        org_data = json.loads(response_org)
        org_info = org_data['data']['org']
        archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
        # archivo_imagen =get_presigned_url("cas/{url}".format(url=org_info['logo']),28800) 
        type_recibo = 'Póliza'
        tipo_poliza = ''
        asegurado = ''
        if recibo.poliza: 
            if recibo.poliza.document_type == 7 or recibo.poliza.document_type == 8:
                type_recibo = 'Fianza' 
                asegurado = 'FIANZA' 
            elif recibo.poliza.document_type == 1 or recibo.poliza.document_type == 3:
                type_recibo = 'Póliza'
            elif recibo.poliza.document_type ==3:                
                tipo_poliza = 'PÓLIZA DE GRUPO'
            else:
                type_recibo = 'Póliza'
            

            if recibo.poliza.document_type == 4: 
                receipts_by = recibo.poliza.parent.receipts_by
                if receipts_by == 2:
                    parCurrency = checkCurrency(recibo.poliza.parent.f_currency)
                    currency_format = checkCurrency2(recibo.poliza.f_currency)
                else:
                    parCurrency = checkCurrency(recibo.poliza.f_currency)
                    currency_format = checkCurrency2(recibo.poliza.f_currency)
            else:
                parCurrency = checkCurrency(recibo.poliza.f_currency)
                currency_format = checkCurrency2(recibo.poliza.f_currency)

            if recibo.poliza.contractor:                
                contratante = recibo.poliza.contractor.full_name
            else:
                contratante = 'no especificado'
            if recibo.poliza.ramo:
                if recibo.poliza.ramo.ramo_code ==1:#vida
                    form = Life.objects.filter(policy = recibo.poliza.id)
                    tipo_poliza = 'VIDA'
                    if form[0]:
                        if form[0].personal:
                            asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                    if not asegurado:
                        form = Personal_Information.objects.filter(policy = recibo.poliza.id)
                        if form:
                            if form[0]:
                                if form[0]:
                                    asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                                else:
                                    asegurado = ''
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                elif recibo.poliza.ramo.ramo_code ==2:#acc
                    tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                    form = AccidentsDiseases.objects.filter(policy = recibo.poliza.id)
                    if form:
                        if form[0]:
                            if form[0].personal:
                                asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                elif recibo.poliza.ramo.ramo_code ==3 and recibo.poliza.subramo.subramo_code ==9:#aut
                    tipo_poliza = 'DAÑOS/AUTOS'
                    form = AutomobilesDamages.objects.filter(policy = recibo.poliza.id)
                    if form:
                        asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                    else:
                        asegurado = ''
                elif recibo.poliza.ramo.ramo_code ==3  and recibo.poliza.subramo.subramo_code !=9:#dañ
                    tipo_poliza = 'DAÑOS DIVERSOS'
                    form = Damages.objects.filter(policy = recibo.poliza.id)
                    if form:
                        asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                    else:
                        asegurado = ''
                if recibo.poliza.document_type ==3:                
                    tipo_poliza = 'PÓLIZA DE GRUPO'
                if recibo.poliza.document_type ==8:                
                    tipo_poliza = 'FIANZA DE GRUPO'
        elif recibo.endorsement:
            asegurado = 'Endoso'
            tipo_poliza = 'ENDOSO'
            if recibo.endorsement.policy: 
                if recibo.endorsement.policy.document_type == 7 or recibo.endorsement.policy.document_type == 8:
                    type_recibo = 'Fianza'  
                    tipo_poliza = 'FIANZA'                 
                elif recibo.endorsement.policy.document_type == 1 or recibo.endorsement.policy.document_type == 3:
                    type_recibo = 'Póliza'                  
                else:
                    type_recibo = 'Póliza' 
                parCurrency = checkCurrency(recibo.endorsement.policy.f_currency)
                currency_format = checkCurrency2(recibo.endorsement.policy.f_currency)
                if recibo.endorsement.policy.contractor:
                    contratante = recibo.endorsement.policy.contractor.full_name
                else:
                    contratante = 'no especificado'
            else:
                contratante = 'no especificado'
                if recibo.endorsement.policy.document_type == 7 or recibo.endorsement.policy.document_type == 8:
                    type_recibo = 'Fianza'  
                elif recibo.endorsement.policy.document_type == 1 or recibo.endorsement.policy.document_type == 3:
                    type_recibo = 'Póliza'  
                else:
                    type_recibo = 'Póliza' 
                tipo_poliza = '' 

        else:
            contratante = '***'
            asegurado = 'Endoso'
            tipo_poliza = 'NA'
    
        fecha_inicio = (recibo.fecha_inicio).strftime("%d/%m/%y")
        if recibo.poliza:
            f_pago = recibo.poliza.get_forma_de_pago_display()
            subramo = recibo.poliza.subramo
            # subject = str(recibo.poliza.poliza_number) + ';' + str(contratante) + ';' + str(subramo) \
            #         + ';' + str(fecha_inicio)+ ';' + str(f_pago)

            subject = '📆  Recordatorio de pago de recibo de Póliza: '+str(recibo.poliza.poliza_number)
            # subject = 'Recibo: #' + str(recibo.recibo_numero) + ' de la póliza: ' + str(recibo.poliza.poliza_number)
        elif recibo.fianza:
            f_pago = recibo.fianza.get_forma_de_pago_display()
            subramo = recibo.fianza.subramo
            # subject = str(recibo.fianza.fianza_number) + ';' + str(contratante) + ';' + str(subramo) \
            #         + ';' + str(fecha_inicio) + ';' + str(f_pago)
            subject = '📆  Recordatorio de pago de recibo de Póliza: '+str(recibo.poliza.poliza_number)
        elif recibo.endorsement:
            if recibo.endorsement.policy:                
                f_pago = recibo.endorsement.policy.get_forma_de_pago_display()
                subramo = recibo.endorsement.policy.subramo
                # subject = str(recibo.endorsement.policy.poliza_number) + ';' + str(contratante) + ';' + str(subramo) \
                #         + ';' + str(fecha_inicio) + ';' + str(f_pago)
                subject = '📆  Recordatorio de pago de recibo de Endoso: '+str(recibo.endorsement.policy.poliza_number)
            elif recibo.endorsement.fianza:                
                f_pago = recibo.endorsement.fianza.get_forma_de_pago_display()
                subramo = recibo.endorsement.fianza.subramo
                # subject = str(recibo.endorsement.fianza.fianza_number) + ';' + str(contratante) + ';' + str(subramo) \
                #         + ';' + str(fecha_inicio) + ';' + str(f_pago)
                subject = '📆 Recordatorio de pago de recibo de Póliza: '+str(recibo.endorsement.policy.poliza_number)
            else:
                # subject = 'Recibo: #' + str(recibo.recibo_numero)
                subject = '📆  Recordatorio de pago de recibo #'+str(recibo.recibo_numero)
        else:
            # subject = 'Recibo: #' + str(recibo.recibo_numero)
            subject = '📆  Recordatorio de pago de recibo #'+str(recibo.recibo_numero)
    
        if nota_credito:
            # Nota
            prima_neta_nota = float(nota_credito.prima_neta)
            prima_total_nota = float(nota_credito.prima_total)
            derecho_nota = float(nota_credito.derecho)
            iva_nota = float(nota_credito.iva)
            rpf_nota = float(nota_credito.rpf)
            # Recibo
            prima_neta_recibo = float(recibo.prima_neta)
            prima_total_recibo = float(recibo.prima_total)
            derecho_recibo = float(recibo.derecho)
            iva_recibo = float(recibo.iva)
            rpf_recibo = float(recibo.rpf)
            # Resta
            primaNeta = prima_neta_recibo + prima_neta_nota
            primaTotal = prima_total_recibo + prima_total_nota
            derecho_ = derecho_recibo + derecho_nota
            iva_ = iva_recibo + iva_nota
            rpf_ = rpf_recibo + rpf_nota
        else:
            prima_neta_nota = 0
            prima_total_nota = 0
            derecho_nota = 0
            iva_nota = 0
            rpf_nota = 0
            #
            primaNeta = 0
            primaTotal = 0
            derecho_ = 0
            iva_ = 0
            rpf_ = 0
        cc = []
        cco = []
        to_send = []

        if  'emails' in request.data and request.data['emails']:
            to_send = (request.data['emails'])
        if 'emails_cc' in  request.data and request.data['emails_cc']:
            cc = (request.data['emails_cc'])
        if 'emails_cco' in request.data and request.data['emails_cco']:
            cco = (request.data['emails_cco'])
        archivo_imagen = 'https://cas.miurabox.com/media/logos/miurabox-01_4ma4N8J.png'
        if 'logo' in org_info.keys() and len(org_info['logo']) != 0:
            _imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
            # _imagen =get_presigned_url("cas/{url}".format(url=org_info['logo']),28800) 
            # archivo_imagen = 'https://cas.miurabox.com/media/logos/'+org_info['logo']
            if _imagen:
                archivo_imagen = _imagen
            else:
                archivo_imagen = archivo_imagen
                # archivo_imagen = 'https://cas.miurabox.com/media/logos/miurabox-01_4ma4N8J.png'
    
        remitente, logo, logo_mini = user_remitente(request)
    
        if recibo.poliza:
            if recibo.poliza.document_type == 1 or recibo.poliza.document_type == 3:
                type_recibo = 'Póliza'
            elif recibo.poliza.document_type == 7 or recibo.poliza.document_type == 8:
                type_recibo = 'Fianza'
            else:
                type_recibo = 'Póliza'
            if recibo.poliza.document_type == 4:
                poliza_number = recibo.poliza.parent.poliza_number
                aseguradora = recibo.poliza.parent.aseguradora
                ramo = recibo.poliza.parent.ramo
                subramo = recibo.poliza.parent.subramo
                frec_pago = recibo.poliza.parent.get_forma_de_pago_display()
            else:
                poliza_number = recibo.poliza.poliza_number
                aseguradora = recibo.poliza.aseguradora
                ramo = recibo.poliza.ramo
                subramo = recibo.poliza.subramo
                frec_pago = recibo.poliza.get_forma_de_pago_display()
        elif recibo.fianza:
            if recibo.fianza.document_type == 1 or recibo.fianza.document_type == 3:
                type_recibo = 'Póliza'
            elif recibo.fianza.document_type == 7 or recibo.fianza.document_type == 8:
                type_recibo = 'Fianza'
            else:
                type_recibo = 'Póliza'
            if recibo.fianza.document_type == 4:
                poliza_number = recibo.fianza.parent.fianza_number
                aseguradora = recibo.fianza.parent.aseguradora
                ramo = recibo.fianza.parent.ramo
                subramo = recibo.fianza.parent.subramo
                frec_pago = recibo.fianza.parent.get_forma_de_pago_display()
            else:
                poliza_number = recibo.fianza.fianza_number
                aseguradora = recibo.fianza.parent.aseguradora
                ramo = recibo.fianza.ramo
                subramo = recibo.fianza.subramo
                frec_pago = recibo.fianza.get_forma_de_pago_display()
        elif recibo.endorsement:
            tipo_poliza = 'ENDOSO'

            if recibo.endorsement.policy:
                if recibo.endorsement.policy.document_type == 1 or recibo.endorsement.policy.document_type == 3:
                    type_recibo = 'Endoso Póliza'
                elif recibo.endorsement.policy.document_type == 7 or recibo.endorsement.policy.document_type == 8:
                    type_recibo = 'Endoso Fianza'
                else:
                    type_recibo = 'Endoso Póliza'
                if recibo.endorsement.policy.document_type == 4:
                    poliza_number = recibo.endorsement.policy.parent.poliza_number
                    aseguradora = recibo.endorsement.policy.parent.aseguradora
                    ramo = recibo.endorsement.policy.parent.ramo
                    subramo = recibo.endorsement.policy.parent.subramo
                    frec_pago = recibo.endorsement.policy.parent.get_forma_de_pago_display()
                else:
                    poliza_number = recibo.endorsement.policy.poliza_number
                    aseguradora = recibo.endorsement.policy.aseguradora
                    ramo = recibo.endorsement.policy.ramo
                    subramo = recibo.endorsement.policy.subramo
                    frec_pago = recibo.endorsement.policy.get_forma_de_pago_display()
            elif recibo.endorsement.fianza:
                type_recibo = 'Endoso Fianza'
                if recibo.endorsement.fianza.document_type == 4:
                    poliza_number = recibo.endorsement.fianza.parent.fianza_number
                    aseguradora = recibo.endorsement.fianza.parent.aseguradora
                    ramo = recibo.endorsement.fianza.parent.ramo
                    subramo = recibo.endorsement.fianza.parent.subramo
                    frec_pago = recibo.endorsement.fianza.parent.get_forma_de_pago_display()
                else:
                    poliza_number = recibo.endorsement.fianza.fianza_number
                    aseguradora = recibo.endorsement.fianza.aseguradora
                    ramo = recibo.endorsement.fianza.ramo
                    subramo = recibo.endorsement.fianza.subramo
                    frec_pago = recibo.endorsement.fianza.get_forma_de_pago_display()
            else:
                type_recibo = 'Póliza'
                poliza_number = recibo.endorsement.number_endorsement
                aseguradora =''
                ramo = ''
                subramo = ''
                frec_pago = ''
        else:
            poliza_number = ''
            aseguradora = ''
            ramo = ''
            subramo = ''
            frec_pago = ''
            type_recibo = 'Póliza'

        identifier = ''
        if recibo.poliza:
            if recibo.poliza.document_type == 4:
                identifier = recibo.poliza.parent.identifier    
            else:
                identifier = recibo.poliza.identifier

            if recibo.poliza.document_type == 7 or recibo.poliza.document_type == 8:
                type_recibo = 'Fianza'  
                tipo_poliza = 'FIANZA'
            elif recibo.poliza.document_type == 1 or recibo.poliza.document_type == 3:
                type_recibo = 'Póliza'
            elif recibo.poliza.document_type ==3:                
                tipo_poliza = 'PÓLIZA DE GRUPO'
            else:
                type_recibo = 'Póliza'

        elif recibo.fianza:
            identifier = recibo.fianza.identifier
        elif recibo.endorsement:
            if recibo.endorsement.policy:
                if recibo.endorsement.policy.document_type == 7 or recibo.endorsement.policy.document_type == 8:
                    type_recibo = 'Fianza'  
                elif recibo.endorsement.policy.document_type == 1 or recibo.endorsement.policy.document_type == 3:
                    type_recibo = 'Póliza'
                else:
                    type_recibo = 'Póliza'
                identifier = recibo.endorsement.policy.identifier
            elif recibo.endorsement.fianza:
                identifier = recibo.endorsement.fianza.identifier
            else:
                identifier = ''
        else:
            identifier = ''       
        if request.user:
            user = str(request.user.first_name) +' '+str(request.user.last_name)
        else:
            user = ''
        if recibo.endorsement:            
            tipo_poliza = 'ENDOSO'        
        try:
            fecha = datetime.today()
            final_time = fecha
            fecha = final_time.date()
        except:
            try:
                fecha = datetime.datetime.today()
                final_time = fecha
                fecha = final_time.date()
            except:
                fecha = ''
        direccion =  org_data['data']['org']['address']
        data = {
            'logo': archivo_imagen if archivo_imagen else '',    
            'poliza_number': poliza_number,
            'identificador': identifier,
            'contratante': contratante,
            'aseguradora': aseguradora,
            'ramo': ramo,
            'subramo': subramo,
            'moneda': parCurrency,
            'currency_format': currency_format,
            'frecuencia_de_pago': frec_pago,
            'recibo_number': recibo.recibo_numero,
            'vigencia_recibo_i': (recibo.fecha_inicio).strftime("%d/%m/%y"),
            'vigencia_recibo_f': (recibo.fecha_fin).strftime("%d/%m/%y"),
            'prima_neta': '$' + '{:,.2f}'.format(recibo.prima_neta),
            'rpf': '$' + '{:,.2f}'.format(recibo.rpf),
            'derecho': '$' + '{:,.2f}'.format(recibo.derecho),
            'iva': '$' + '{:,.2f}'.format(recibo.iva),
            'primaTotal': '$' + '{:,.2f}'.format(recibo.prima_total),
            'payment_date': (recibo.vencimiento).strftime("%d/%m/%y") if recibo.vencimiento else '',
            'type_recibo': type_recibo,
            'asegurado': asegurado,
            'endoso': recibo.endorsement.number_endorsement if recibo.endorsement else None,    
            'remitente': remitente,
            'subject': subject,
            'tipo_poliza':tipo_poliza,
            'user':user,
            'organizacion':orgName,
            'direccion':direccion,
            'first_comment':' ',
            'fecha':(fecha).strftime("%d/%m/%Y") if fecha else '',
            'fechaLimitePago':configuracion_org[0].fecha_limite_email_cobranza if configuracion_org and configuracion_org.exists() else True,
            'botonSegumovil':configuracion_org[0].boton_segumovil if configuracion_org and configuracion_org.exists() else True,
            'dato_contratante':configuracion_org[0].dato_contratante if configuracion_org and configuracion_org.exists() else True,
            'dato_numero_poliza':configuracion_org[0].dato_numero_poliza if configuracion_org and configuracion_org.exists() else True,
            'dato_concepto':configuracion_org[0].dato_concepto if configuracion_org and configuracion_org.exists() else True,
            'dato_aseguradora':configuracion_org[0].dato_aseguradora if configuracion_org and configuracion_org.exists() else True,
            'dato_serie':configuracion_org[0].dato_serie if configuracion_org and configuracion_org.exists() else True,
            'dato_subramo':configuracion_org[0].dato_subramo if configuracion_org and configuracion_org.exists() else True,
            'dato_total':configuracion_org[0].dato_total if configuracion_org and configuracion_org.exists() else True,     
            'receiver': json.dumps(to_send),
            'cc': json.dumps(cc),
            'cco': json.dumps(cco),
            }
        try:
            banner_file = BannerFile.objects.filter(org_name = request.GET.get('org')) 
            if banner_file.exists():
                # data.update({'b_header': banner_file[0].header.url,'b_footer': banner_file[0].footer.url})
                if banner_file[0].header:
                    data.update({'logo':''})
                    data.update({'b_header':get_url_file(banner_file[0].header)})
                if banner_file[0].footer:
                    data.update({'logo':''})
                    data.update({'b_footer':get_url_file(banner_file[0].footer)})
            
            signature = Signature.objects.filter(user=request.user)
            if signature.exists():
                data.update({'signature': (signature[0].signature)})
                try:
                    # Example usage
                    input_str =signature[0].signature
                    base64_image = extract_base64_image(input_str)
                    if base64_image:
                        # data['firma']='data:image/png;base64,'+base64_image
                        base64_image = extract_base64_image(input_str)
                        if base64_image:                   
                            data.update({'signature_imagen': (signature[0].image_amazon)})
                            data.update({'signature': ''})
                    else:
                        print("No base64 image data found.")
                except Exception as ee:
                    print('error extract imageeee',ee)
            data.update({'section': 'h'})
            # head = render_to_string("payment_reminderNV_body.html", data)
            head = render_to_string("mail_recordatorio.html", data)
            data['section'] = 'b'
            body = render_to_string("mail_recordatorio.html", data)
            data['section'] = 'f'
            footer = render_to_string("mail_recordatorio.html", data)
            return Response({'body':body, 'head':head, 'footer':footer}, status=200)
        except Exception as e:
            return Response({'response': 'Error!', 'error': str(e)})

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def payment_reminder_whatsapp(request, id=None):    
    if request.method == 'POST':
        try:
            recibo = Recibos.objects.get(pk=int(request.data['r_id']))
            mensaje = request.data['mensaje']
            recibo.track_mensajeria = True
            model_log = request.data['model'] if 'model' in request.data else None
        except Exception as erx:
            return Response({'error': 'No existe el recibo \n'+str(erx)})
        try:
            orginfo = OrgInfo.objects.filter(org_name = request.GET.get('org'))
        except:
            orginfo =None
        org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
        response_org = org_.text
        org_data = json.loads(response_org)
        org_info = org_data['data']['org']
        phone_org = org_info['phone_mensajeria']
        phone_sms = org_info['phone_sms']
        auth_token = org_info['auth_token']
        messaging_service_sid = org_info['messaging_service_sid']
        account_sid = org_info['account_sid']
        phones_sms = request.data['phones_sms']
        asegurado = ''
        aliasorg = org_info['alias']
        t_asegurado = 'Bien Asegurado: '
        if recibo.poliza.ramo:
            if recibo.poliza.ramo.ramo_code ==1:#vida
                form = Life.objects.filter(policy = recibo.poliza.id)
                tipo_poliza = 'VIDA'
                t_asegurado = 'Asegurado: '
                if form.exists():
                    if form[0].personal:
                        asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
                if not asegurado:
                    form = Personal_Information.objects.filter(policy = recibo.poliza.id)
                    if form.exists():
                        asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                    else:
                        asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==2:#acc
                tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                t_asegurado = 'Asegurado: '
                form = AccidentsDiseases.objects.filter(policy = recibo.poliza.id)
                if form.exists():
                    if form[0].personal:
                        asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==3 and recibo.poliza.subramo.subramo_code ==9:#aut
                tipo_poliza = 'DAÑOS/AUTOS'
                t_asegurado = 'Bien Asegurado: '
                form = AutomobilesDamages.objects.filter(policy = recibo.poliza.id)
                if form:
                    asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                else:
                    asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==3  and recibo.poliza.subramo.subramo_code !=9:#dañ
                tipo_poliza = 'DAÑOS DIVERSOS'
                t_asegurado = 'Bien Asegurado: '
                form = Damages.objects.filter(policy = recibo.poliza.id)
                if form:
                    asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                else:
                    asegurado = ''
        vigencia = str(recibo.fecha_inicio.strftime("%d/%m/%y") if recibo.fecha_inicio else '')+' - '+str(recibo.fecha_fin.strftime("%d/%m/%y") if recibo.fecha_fin else '')
        vencimeinto = str(recibo.vencimiento.strftime("%d/%m/%y") if recibo.vencimiento else '')
        vigenciap = str(recibo.poliza.start_of_validity.strftime("%d/%m/%y") if recibo.poliza and  recibo.poliza.start_of_validity else '')+' - '+str(recibo.poliza.end_of_validity.strftime("%d/%m/%y") if  recibo.poliza and recibo.poliza.end_of_validity else '')
        tipoMensaje = request.data['type_msj'] if 'type_msj' in request.data else 'all'
        try:
            if 'mensaje' in request.data and request.data['mensaje']:
                
                # estatico hasta que crezca y se haga dinamico
                if request.GET.get('org') == 'arasesores':
                    content_sid = 'HXbad1eb82f915bc85dfa07003bd1032ea'
                    from polizas.mensajes_whatsapp_twilio import MENSAJES_ARASEGUROS as MENSAJES
                else:
                    content_sid = 'HX37b3397b1620e2306690d5d97ba45b7e'
                    from polizas.mensajes_whatsapp_twilio import MENSAJES_GPI as MENSAJES
                    
                    
                for mensaje in MENSAJES:
                    aux_mensaje = mensaje['mensaje'].replace('[org]', str(request.GET.get('org')).upper())
                    if aux_mensaje == request.data['mensaje']:
                        content_sid = mensaje['content_template_id']
                
                mensaje_ok = str(request.data['mensaje'])
            else:
                mensaje_ok = "Estimado(a) Asegurado, le recordamos que su recibo está próximo a vencer, quedamos al pendiente para cualquier duda o aclaración al respecto."
            moneda = checkCurrency(int(recibo.poliza.f_currency if recibo.poliza and recibo.poliza.f_currency else 1))
            body_message =  mensaje_ok+"\n"+ \
            " Póliza: " + str(recibo.poliza.poliza_number)+ "\n" + \
            " Subramo: " + str(recibo.poliza.subramo.subramo_name if recibo.poliza and recibo.poliza.subramo else '') + "\n"+ \
            " Serie: " + str(recibo.recibo_numero )+ "\n"+ \
            " Asegurado: " + str(asegurado) + "\n"+ \
            " Prima Total: " + str('$'+ '{:,.2f}'.format(recibo.prima_total))+ "\n"+ \
            " Moneda: " + str(moneda)+ "\n"+ \
            " Fecha Límite de Pago: " + str(vencimeinto)

            # ✅ Mostrar solo si activar_contacto_dudas es True
            if orginfo and orginfo[0].activar_contacto_dudas:
                body_message += "\nDudas o comentarios: " + str(orginfo[0].contacto_dudas or 'Sin comentarios')

                    
            content_variables =  {
                "1" : str(recibo.poliza.poliza_number),
                "2" : str(recibo.poliza.subramo.subramo_name if recibo.poliza and recibo.poliza.subramo else ''),
                "3" : str(recibo.recibo_numero ),
                "4" : str(asegurado),
                "5" : str('$'+ '{:,.2f}'.format(recibo.prima_total)),
                "6" : str(moneda),
                "7" : str(vencimeinto),
                "8" : str(orginfo[0].contacto_dudas if orginfo[0].contacto_dudas else 'Sin comentarios')
            }
        except Exception as ferror:
            print('ferror',ferror)
        data = {
            'greet_message': request.data['mensaje'] if 'mensaje' in request.data else 'Estimado(a) Asegurado, es un placer saludarle, le recordamos que su recibo está próximo a vencer.',
            'mensaje': request.data['mensaje'] if 'mensaje' in request.data else 'Estimado(a) Asegurado, es un placer saludarle, le recordamos que su recibo está próximo a vencer.',
            'additional_message':body_message,
            'content_sid': content_sid,
            'remitente':recibo.poliza.contractor.phone_mensajeria,
            'message_type': request.data['type_msj'] if 'type_msj' in request.data else 'all',
            'account_sid':account_sid,
            'auth_token':auth_token,
            'phone_org':phone_org
        }
        banner_file = BannerFile.objects.filter(org_name = request.GET.get('org')) 
        try:
            if banner_file.exists():
                data.update({'media_content': get_url_file(banner_file[0].image_sms)})
        except:
            data.update({'media_content': ''})

        dataSMS = {
            'content_variables': json.dumps(content_variables),
            'remitente': recibo.poliza.contractor.phone_mensajeria,
            'account_sid': account_sid,
            'content_sid': content_sid,
            'auth_token': auth_token,
            'messaging_service_sid': messaging_service_sid,
            'phone_org': phone_org,
            'mensaje': body_message

        }

        if tipoMensaje =='whatsapp':
            url = 'https://notifyme.multicotizador.com/whatsapp-saam'
            # url = 'http://127.0.0.1:5001/whatsapp-saam'
        else:
            dataSMS.update({'phone_org': phone_sms})
            url = 'https://notifyme.multicotizador.com/sms-saam'
            # url = 'http://127.0.0.1:5001/sms-saam'
        headers = {"user_agent": "mozilla", }
        # if phones_sms and account_sid and auth_token and phone_org:
        enviados = 0
        if phone_org and auth_token and account_sid:
            if phones_sms:
                for ph in phones_sms:
                    dataSMS['remitente'] = ph
                    req = requests.post(url, data=dataSMS)
                    enviados+=1
                    try:
                        if (str(req) == str('<Response [200]>') or (str(req) == str('<Response [201]>'))):
                            if model_log:
                                comment = Comments(model=model_log, id_model=request.data['r_id'], content="Se ha enviado mensaje vía móvil de recordatorio de pago, mensaje: "+str(dataSMS['mensaje']), org_name = request.GET.get('org'), user= request.user)
                                comment.save()
                                email_log = LogEmail(model=model_log, associated_id=request.data['r_id'], comment=comment,subject=dataSMS['mensaje'], to=str(phones_sms).replace('[', '').replace(']', '').replace('"', '').replace("'", ""), )
                                email_log.save()
                                recibo.track_mensajeria = True
                                recibo.track_bitacora = True
                                recibo.save()                   
                        else:
                            print('error post notifyme',str(req))
                            return Response({'response': str(req)}, status=400, headers=headers)
                    except Exception as e:
                        print('error exception',e)
                if enviados == len(phones_sms):
                    return Response({'response': 'sent'}, status=200, headers=headers)
        else:
            return Response({'response': 'No cuenta con las credenciales configuradas en su Organización. \ncontacte a su Administrador'}, status=400, headers=headers)
    if request.method == 'GET':
        try:
            recibo = Recibos.objects.get(pk=int(request.GET.get('r_id')))
        except Exception as erx:
            return Response({'error': 'No existe el recibo \n'+str(erx)})
        org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
        response_org = org_.text
        org_data = json.loads(response_org)
        org_info = org_data['data']['org']
        phone_org = org_info['phone_mensajeria']
        auth_token = org_info['auth_token']
        account_sid = org_info['account_sid']
        asegurado = ''
        t_asegurado = 'Bien Asegurado: '
        try:
            orginfo = OrgInfo.objects.filter(org_name = request.GET.get('org'))
        except:
            orginfo =None
        if recibo.poliza.ramo:
            if recibo.poliza.ramo.ramo_code ==1:#vida
                form = Life.objects.filter(policy = recibo.poliza.id)
                tipo_poliza = 'VIDA'
                t_asegurado = 'Asegurado: '
                if form.exists():
                    if form[0].personal:
                        asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
                if not asegurado:
                    form = Personal_Information.objects.filter(policy = recibo.poliza.id)
                    if form.exists():
                        asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                    else:
                        asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==2:#acc
                tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                t_asegurado = 'Asegurado: '
                form = AccidentsDiseases.objects.filter(policy = recibo.poliza.id)
                if form.exists():
                    if form[0].personal:
                        asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==3 and recibo.poliza.subramo.subramo_code ==9:#aut
                tipo_poliza = 'DAÑOS/AUTOS'
                t_asegurado = 'Asegurado: '
                form = AutomobilesDamages.objects.filter(policy = recibo.poliza.id)
                if form:
                    asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                else:
                    asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==3  and recibo.poliza.subramo.subramo_code !=9:#dañ
                tipo_poliza = 'DAÑOS DIVERSOS'
                t_asegurado = 'Asegurado: '
                form = Damages.objects.filter(policy = recibo.poliza.id)
                if form:
                    asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                else:
                    asegurado = ''
        vigencia = str(recibo.fecha_inicio.strftime("%d/%m/%y") if recibo.fecha_inicio else '')+' - '+str(recibo.fecha_fin.strftime("%d/%m/%y") if recibo.fecha_fin else '')
        vencimeinto = str(recibo.vencimiento.strftime("%d/%m/%y") if recibo.vencimiento else '')
        vigenciap = str(recibo.poliza.start_of_validity.strftime("%d/%m/%y") if recibo.poliza and  recibo.poliza.start_of_validity else '')+' - '+str(recibo.poliza.end_of_validity.strftime("%d/%m/%y") if  recibo.poliza and recibo.poliza.end_of_validity else '')
        try:
            tipomensaje = int(request.GET.get('tipo'))
        except Exception as esd:
            tipomensaje = 2
        if tipomensaje ==1:            
            try:
                # mensaje_ok = "Estimado Asegurado: Usted tiene un recibo pendiente de pago, comuníquese con "+str(recibo.org_name.upper() if recibo.org_name else '')+" para más Información " + "\n"
                mensaje_ok = ''
                moneda = checkCurrency(int(recibo.poliza.f_currency if recibo.poliza and recibo.poliza.f_currency else 1))
                body_message =  mensaje_ok+"\n"+ \
                        " Póliza: " + str(recibo.poliza.poliza_number)+ "\n" + \
                        " Subramo: " + str(recibo.poliza.subramo.subramo_name if recibo.poliza and recibo.poliza.subramo else '') + "\n"+ \
                        " Serie: " + str(recibo.recibo_numero )+ "\n"+ \
                        " Asegurado: " + str(asegurado) + "\n"+ \
                        " Prima Total: " + str('$'+ '{:,.2f}'.format(recibo.prima_total))+ "\n"+ \
                        " Moneda: " + str(moneda)+ "\n"+ \
                        " Fecha Límite de Pago: " + str(vencimeinto)

                # ✅ Mostrar solo si activar_contacto_dudas es True
                if orginfo and orginfo[0].activar_contacto_dudas:
                    body_message += "\nDudas o comentarios: " + str(orginfo[0].contacto_dudas or 'Sin comentarios')

            except Exception as ferror:
                print('ferror',ferror)
        else:                      
            try:
                # mensaje_ok = "Estimado Asegurado: Usted tiene un recibo pendiente de pago, comuníquese con "+str(recibo.org_name.upper() if recibo.org_name else '')+" para más Información " + "\n"
                mensaje_ok = ''
                moneda = checkCurrency(int(recibo.poliza.f_currency if recibo.poliza and recibo.poliza.f_currency else 1))
                body_message =  mensaje_ok+"<br>"+ \
                        " Póliza: " + str(recibo.poliza.poliza_number)+ "<br>" + \
                        " Subramo: " + str(recibo.poliza.subramo.subramo_name if recibo.poliza and recibo.poliza.subramo else '') + "<br>"+ \
                        " Serie: " + str(recibo.recibo_numero )+ "<br>"+ \
                        str(t_asegurado) + str(asegurado) + "<br>"+ \
                        " Prima Total: " + str('$'+ '{:,.2f}'.format(recibo.prima_total))+ "<br>"+ \
                        " Moneda: " + str(moneda)+ "<br>"+ \
                        " Fecha Límite de Pago: " + str(vencimeinto)

                # ✅ Agregar solo si activar_contacto_dudas es True
                if orginfo and orginfo[0].activar_contacto_dudas:
                    body_message += "<br>Dudas o comentarios: " + str(orginfo[0].contacto_dudas or '')

            except Exception as ferror:
                print('ferror',ferror)
        data = {
        'greet_message': 'Estimado(a) Asegurado, es un placer saludarle, le recordamos que su recibo está próximo a vencer.',
        'mensaje': 'Estimado(a) Asegurado, es un placer saludarle, le recordamos que su recibo está próximo a vencer.',
        'additional_message':body_message,
        'remitente':recibo.poliza.contractor.phone_mensajeria,
        'message_type': 'all',
        'sender_number': phone_org ,   
        'auth_token': auth_token,   
        'account_sid': account_sid, 
        }
        banner_file = BannerFile.objects.filter(org_name = request.GET.get('org')) 
        try:
            if banner_file.exists():
                data.update({'media_content': get_url_file(banner_file[0].image_sms)})
        except:
            data.update({'media_content': ''})
        dataSMS = {
            'mensaje': str(body_message if body_message else ''),
            'remitente':recibo.poliza.contractor.phone_mensajeria
        }
        return Response({'response': dataSMS}, status=200)


@api_view(['POST'])
# @permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def sendEmailGpiContact(request):
    email_ = request.data['email']
    nombre = request.data['nombre']
    contacto = request.data['contacto']
    asunto = request.data['asunto']
    mensaje = request.data['mensaje']
    subject = asunto
    fecha = datetime.now().strftime("%d/%m/%y")
    message = render_to_string("contact_gpi.html", {
        'subject': subject,
        'nombre': str(nombre),
        'telefono': contacto,
        'mensaje':mensaje,
        'email': email_,
        'fecha': fecha,
    })

    # GET ORG INFO
    org_ = requests.get(settings.CAS_URL + 'get-org-info/' + 'gpi',verify=False)
    response_org = org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    # Sendgrit Piloto test
    if org_info['email']:
        remitente = "{} <{}>".format('gpi', org_info['email'])
    else:
        remitente = "{} <no-reply@miurabox.com>".format('GPI')
    # remitente = "{} <no-reply@miurabox.com>".format('Miurabox')
    destinatario = 'contacto@grupogpi.mx'
    try:
        remitente=build_from_header(remitente)
    except:
        remitente=remitente
    email = EmailMultiAlternatives(subject, message, from_email=remitente, to=[destinatario])

    email.content_subtype = "html"
    email.mixed_subtype = 'related'

    try:
        email.send()
        val = {'status': 'sent'}
        return JsonResponse(val, status=200)

    except smtplib.SMTPAuthenticationError:
        val = {'status': 'Credenciales de correo mal configuradas. Comuniquese con su administrador'}
        return JsonResponse(val, status=400)

    except:
        val = {'status': 'Error al enviar el recordatorio de renovación'}
        return JsonResponse(val, status=400)

@api_view(['POST'])
# @permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def sendEmailGpiCotization(request):
    org_ = requests.get(settings.CAS_URL + 'get-org-info/' + 'gpi',verify=False)
    response_org = org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    if len(org_info['logo']) != 0:
        logo = 'https://miurabox-public.s3.amazonaws.com/cas/'+ org_info['logo']
        # logo =get_presigned_url("cas/{url}".format(url=org_info['logo']),28800) 
    else:
        logo = ''
    fecha = datetime.now().strftime("%d/%m/%y")
    subject = 'Solicitud Cotización Auto Grupo GPI'
    name_full=(
        request.data['first_name'].capitalize() + ' ' +
        str(request.data['last_name']).capitalize() + ' ' +
        str(request.data['second_last_name']).capitalize()
    )

    if 'car_sex' in request.data:
        if request.data['car_sex'] == 'F':
            sex='Femenino' 
        else:
            sex='Masculino' 
    else:
        sex = 'Sin definir'
    modelo=''
    if 'model_name' in request.data and request.data['model_name']:
        modelo = request.data['model_name'] 
    if 'car_model' in request.data and request.data['car_model']:
        modelo = request.data['car_model'] 
    message = render_to_string("cotization-gpi.html", {
        'subject': subject,
        'nombre': name_full if name_full else str('Grupo GPI'),
        'telefono': 'contacto',
        'mensaje':'Solicitud de Cotización de Auto Grupo GPI',
        'email': request.data['email'] if 'email' in request.data else '',
        'car_sex': sex,
        'birthdate': request.data['birthdate'] if 'birthdate' in request.data else '',
        'phone_number': request.data['phone'] if 'birthdate' in request.data else '',
        'zip_code': request.data['zip_code'] if 'zip_code' in request.data else '',
        'car_class': request.data['car_class'] if 'car_class' in request.data else request.data['car_clases'] if 'car_clases' in request.data else '',
        'car_year': request.data['car_year'] if 'car_year' in request.data else '',
        'car_brand': request.data['car_brand'] if 'car_brand' in request.data else '',
        'model_name': modelo,
        'fecha': fecha,
        'logo':logo
    })
    # GET ORG INFO
    # Sendgrit Piloto test
    if org_info['email']:
        remitente = "{} <{}>".format('gpi', org_info['email'])
    else:
        remitente = "{} <no-reply@miurabox.com>".format('GPI')
    # remitente = "{} <no-reply@miurabox.com>".format('Miurabox')
    destinatario = 'contacto@grupogpi.mx'
    # remitente = "{} <no-reply@miurabox.com>".format('GPI')
    # destinatario = 'guadalupe.becerril@miurabox.com'
    try:
        remitente=build_from_header(remitente)
    except:
        remitente=remitente
    email = EmailMultiAlternatives(subject, message, from_email=remitente, to=[destinatario], bcc=['enrique.bojorges@grupogpi.mx'])
    # email = EmailMultiAlternatives(subject, message, from_email=remitente, to=['guadalupe.becerril@miurabox.com'], cc=['guadalupe.becerril@miurabox.com'])

    email.content_subtype = "html"
    email.mixed_subtype = 'related'

    try:
        email.send()
        val = {'status': 'sent'}
        return JsonResponse(val, status=200)

    except smtplib.SMTPAuthenticationError:
        val = {'status': 'Credenciales de correo mal configuradas. Comuniquese con su administrador'}
        return JsonResponse(val, status=400)

    except:
        val = {'status': 'Error al enviar el recordatorio de renovación'}
        return JsonResponse(val, status=400)
#--- inicio compartir cetrificado
@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def ShareCertificateEmailNV(request, id=None):
#    import pdb; pdb.set_trace()
    org_name = request.GET.get('org')
    fechaLimitePago=''
    try:
        orginfo = OrgInfo.objects.filter(org_name = request.GET.get('org'))
    except:
        orginfo =None
    if request.method == 'POST':
        plantillaSeleccionada=None
        try:
            plantilla = request.data['plantilla']
            plantillaSeleccionada = EmailTemplate.objects.get(id=int(plantilla),org_name=org_name)
        except Exception as epl:
            print('no se reconocio plantilla seleccionada',epl)
        model_log = request.data['model'] if 'model' in request.data else None
        try:
            poliza = Polizas.objects.get(pk=int(request.data['id']))
        except:
            return Response({'error': 'No existe el Certificado'})
        receiver =  json.dumps(request.data['emails']) 
        try:
            r_files = request.data['files']
        except Exception as error_file:
            r_files = []
        try:
            r_files_r = request.data['files_r']
        except Exception as error_rfiles:
            r_files_r = []
        if poliza.contractor:
            contratante = poliza.contractor.full_name
        else:
            contratante = ''

        try:
            sov = str(poliza.start_of_validity.strftime("%d/%m/%Y"))
        except:
            sov = ''

        try:
            eov = str(poliza.end_of_validity.strftime("%d/%m/%Y"))
        except:
            eov = ''
        if 'subject' in request.data and request.data['subject']:
            subject = request.data['subject']
        else:
            subject = str(contratante)+'  te compartimos tu Certificado '+str(poliza.poliza_number)+\
                      ' - '+str(poliza.subramo.subramo_name if poliza.subramo else '')
        remitente,logo,logo_mini = user_remitente(request)
        files = PolizasFile.objects.filter(id__in=list(r_files))
        files_r = RecibosFile.objects.filter(id__in=list(r_files_r))
        files_data = []
        if poliza.ramo:
            if poliza.ramo.ramo_code ==1:#vida
                form = Life.objects.filter(policy = poliza.id)
                tipo_poliza = 'VIDA'
                if form:
                    if form[0]:
                        if form[0].personal:
                            asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
                if not asegurado:
                    form = Personal_Information.objects.filter(policy = poliza.id)
                    if form:
                        if form[0]:
                            if form[0]:
                                asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
            elif poliza.ramo.ramo_code ==2:#acc
                tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                form = AccidentsDiseases.objects.filter(policy = poliza.id)
                if form:
                    if form[0]:
                        if form[0].personal:
                            asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                        else:
                            asegurado = ''
                else:
                    asegurado = ''
            elif poliza.ramo.ramo_code ==3 and poliza.subramo.subramo_code ==9:#aut
                tipo_poliza = 'DAÑOS/AUTOS'
                form = AutomobilesDamages.objects.filter(policy = poliza.id)
                if form:
                    asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                else:
                    asegurado = ''
            elif poliza.ramo.ramo_code ==3  and poliza.subramo.subramo_code !=9:#dañ
                tipo_poliza = 'DAÑOS DIVERSOS'
                form = Damages.objects.filter(policy = poliza.id)
                if form:
                    asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                else:
                    asegurado = ''
            else:
                asegurado = ''
        else:
            asegurado = ''
        if poliza.document_type ==3:                
            tipo_poliza = 'PÓLIZA DE GRUPO'
        if poliza.document_type ==8:                
            tipo_poliza = 'FIANZA DE GRUPO'
        if files or files_r:
            if admin_archivos(request):
                for file in files:                    
                    file.arch = get_presigned_url(folder+"/{url}".format(url=file.arch),28800)  
                    URL = str(file.arch).replace(" ", "+")
                    # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26")
                    files_data.append({'url':URL,'name':file.nombre})
                for file_r in files_r:
                    file_r.arch = get_presigned_url(folder+"/{url}".format(url=file_r.arch),28800)  
                    URL = str(file_r.arch).replace(" ", "+")
                    # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26");
                    files_data.append({'url':URL,'name':file_r.nombre})


        status = status_poliza(poliza.status)
        parCurrency = checkCurrency(poliza.f_currency)
        recibos = Recibos.objects.filter(isActive = True, isCopy = False, poliza = poliza.id,receipt_type=1).order_by('fecha_inicio')

        if recibos:
            primaT = recibos[0].prima_total
            fi = recibos[0].fecha_inicio.strftime("%d/%m/%Y") if recibos and recibos[0] and recibos[0].fecha_inicio else ''
            if orginfo and orginfo[0].fecha_limite_email:
                fechaLimitePago = recibos[0].vencimiento.strftime("%d/%m/%Y") if recibos and recibos[0] and recibos[0].vencimiento else ''
        else:
            primaT = 0
            fi = '*'
        # if poliza.org_name and poliza.org_name=='gpi':
        #     cc = [request.user.email,'cobranza.seguros@grupogpi.mx']
        # else:
        #     cc = [request.user.email]
        if poliza.document_type ==6:
            aseguradora = getattr(
                poliza.parent.parent.parent.aseguradora, 'alias', 
                getattr(poliza.parent.parent.parent.aseguradora, 'compania', None)
            )
        else:
            aseguradora=''
        org_info = get_org_info(request)
        direccion =  org_info['address']
        data = {
            'logo':logo,
            'poliza_number': poliza.poliza_number,
            'contratante': contratante,
            'start_of_validity': sov,
            'end_of_validity': eov,
            'aseguradora': aseguradora,
            'ramo': poliza.ramo,
            'subramo': poliza.subramo,
            'moneda':parCurrency,
            'frecuencia_de_pago': poliza.get_forma_de_pago_display(),
            'prima_neta': '$' + '{:,.2f}'.format(poliza.p_neta),
            'rpf': '$' + '{:,.2f}'.format(poliza.rpf),
            'derecho': '$' + '{:,.2f}'.format(poliza.derecho),
            'iva': '$' + '{:,.2f}'.format(poliza.iva),
            'prima_total': '$' + '{:,.2f}'.format(poliza.p_total),
            'prima_total_recibo': '$' + '{:,.2f}'.format(primaT),
            'fecha_recibo': fi,
            'files': json.dumps(files_data),
            'remitente': remitente,
            'subject': subject,
            'receiver': receiver,
            'fechaLimitePago':fechaLimitePago,
            'certificate_number': poliza.certificate_number,
            # 'cc': json.dumps(cc),
            'asegurado':asegurado,
            'direccion':direccion,
            'dato_cvigencia': orginfo[0].dato_cvigencia if orginfo else True,
            'dato_caseguradora': orginfo[0].dato_caseguradora if orginfo else True,
            'dato_csubramo': orginfo[0].dato_csubramo if orginfo else True,
            'dato_cmoneda': orginfo[0].dato_cmoneda if orginfo else True,
            'dato_cfrecuenciapago': orginfo[0].dato_cfrecuenciapago if orginfo else True,
            'dato_casegurado': orginfo[0].dato_casegurado if orginfo else True,
            'dato_cptotal': orginfo[0].dato_cptotal if orginfo else True,
            'dato_cpneta': orginfo[0].dato_cpneta if orginfo else True,
            'dato_cderecho': orginfo[0].dato_cderecho if orginfo else True,
            'dato_crpf': orginfo[0].dato_crpf if orginfo else True,
            'dato_civ': orginfo[0].dato_civ if orginfo else True,
            'dato_cnumcertificado': orginfo[0].dato_cnumcertificado if orginfo else True,
            'dato_ccontratante': orginfo[0].dato_ccontratante if orginfo else True,
        }
        if 'custom_email' in request.data  and request.data['custom_email']:
            first_comment = request.data['first_comment'] if 'first_comment' in request.data else '' 
            second_comment = request.data['second_comment'] if 'second_comment' in request.data else '' 
            data.update({'first_comment': first_comment,'second_comment':second_comment })
            body = render_to_string("share_certificateNV_custom.html", data)
            data.update({'body': body})
        url = host + "mails/share-policy-manual/"
        headers = {"user_agent": "mozilla", }
        req = requests.post(url, data=data, headers=headers)

        try:
            if str(req) == str('<Response [200]>'):
                # LOG 
                if poliza.document_type==3:
                    model = 18 
                    tipo = ' la colectividad: '
                    number = poliza.poliza_number
                elif poliza.document_type == 6:
                    model = 25
                    tipo = ' el certificado: '
                    number = poliza.certificate_number 
                    # crear registro en pendients report certificados
                    for emCert in request.data['emails']:
                        if not Pendients.objects.filter(poliza = poliza, email__iexact = emCert).exists():
                            obj = Pendients(
                                email = emCert,
                                poliza = poliza,
                                is_owner = False,
                                active = True
                                )
                            obj.save()
                elif poliza.document_type == 1:
                    model = 1
                    tipo = ' la póliza: '
                    number = poliza.poliza_number
                else:
                    model = 1
                    tipo = ' la póliza: '
                    number = poliza.poliza_number
                dataIdent = ' compartio' +str(tipo)+str(number)
                original = {}
                change= dataIdent                    
                try:
                    send_log_complete(request.user, poliza.org_name, 'POST', model, '%s' % str(dataIdent),'%s' % str(original),'%s' % str(change), poliza.id)
                except Exception as eee:
                    pass
                # LOG-------------
                if model_log:
                    if not request.data['custom_email']:
                        body = render_to_string("share_certificateNV.html", data)
                    comment = Comments(model=model_log, id_model=request.data['id'], content="Se ha compartido la póliza", org_name = request.GET.get('org'), user= request.user)
                    comment.save()
                    email_log = LogEmail(model=model_log, associated_id=request.data['id'], comment=comment, to=str(receiver).replace('[', '').replace(']', '').replace('"', ''), cc=request.user.email, subject=subject, body=body, files=files_data)
                    email_log.save()
                try:
                    for r in recibos:
                        if r.recibo_numero == 1:
                            comment = Comments(model=4, id_model=r.id, content="Se ha compartido la póliza", org_name = request.GET.get('org'), user= request.user)
                            comment.save()
                            email_log = LogEmail(model=4, associated_id=r.id, comment=comment, to=str(receiver).replace('[', '').replace(']', '').replace('"', ''), cc=request.user.email, subject=subject, body=body, files=files_data)
                            email_log.save()
                            r.track_bitacora = True
                            r.save()
                except Exception as e:
                    pass

                return Response({'response': 'sent'}, status=200, headers=headers)
            else:
                return Response({'response': 'Error'}, status=400,)
        except Exception as e:
            return Response({'response': 'Error!'}, status=400,)
    elif request.method == 'GET':
        plantillaSeleccionada=None
        try:
            plantilla =  request.GET.get('template_id')
            plantillaSeleccionada = EmailTemplate.objects.get(id=int(plantilla),org_name=org_name)
        except Exception as epl:
            print('no se reconocio idplantilla seleccionada',epl)
        try:
            body = ''
            try:
                poliza = Polizas.objects.get(pk=int(id))
            except:
                return Response({'error': 'No existe el Certificado'})
            if poliza.contractor:
                contratante = poliza.contractor.full_name
            else:
                contratante = ''
            if poliza.ramo:
                if poliza.ramo.ramo_code ==1:#vida
                    form = Life.objects.filter(policy = poliza.id)
                    tipo_poliza = 'VIDA'
                    if form:
                        if form[0]:
                            if form[0].personal:
                                asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                    if not asegurado:
                        form = Personal_Information.objects.filter(policy = poliza.id)
                        if form:
                            if form[0]:
                                if form[0]:
                                    asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                                else:
                                    asegurado = ''
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                elif poliza.ramo.ramo_code ==2:#acc
                    tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                    form = AccidentsDiseases.objects.filter(policy = poliza.id)
                    if form:
                        if form[0]:
                            if form[0].personal:
                                asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                            else:
                                asegurado = ''
                    else:
                        asegurado = ''
                elif poliza.ramo.ramo_code ==3 and poliza.subramo.subramo_code ==9:#aut
                    tipo_poliza = 'DAÑOS/AUTOS'
                    form = AutomobilesDamages.objects.filter(policy = poliza.id)
                    if form:
                        asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                    else:
                        asegurado = ''
                elif poliza.ramo.ramo_code ==3  and poliza.subramo.subramo_code !=9:#dañ
                    tipo_poliza = 'DAÑOS DIVERSOS'
                    form = Damages.objects.filter(policy = poliza.id)
                    if form:
                        asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
            else:
                asegurado = ''
            if poliza.document_type ==6:
                aseguradora = getattr(
                    poliza.parent.parent.parent.aseguradora, 'alias', 
                    getattr(poliza.parent.parent.parent.aseguradora, 'compania', None)
                )
            else:
                aseguradora=''
            status = status_poliza(poliza.status)
            remitente,logo, logo_mini = user_remitente(request)
            parCurrency = checkCurrency(poliza.f_currency)
            # subject = str(poliza.poliza_number)+';'+str(contratante)+';'+str(poliza.subramo)+';'+\
            #           str(poliza.start_of_validity.strftime("%d/%m/%Y"))+';'+str(poliza.get_forma_de_pago_display())
            subject = str(contratante)+'  te compartimos tu Certificado '+str(poliza.poliza_number)+\
                      ' - '+str(poliza.subramo.subramo_name if poliza.subramo else '')
            recibos = Recibos.objects.filter(isActive = True, isCopy = False, poliza = poliza.id,receipt_type=1).order_by('fecha_inicio')
            files_data = []
            if recibos:
                primaT = recibos[0].prima_total
                fi = recibos[0].fecha_inicio.strftime("%d/%m/%Y") if recibos and recibos[0] and recibos[0].fecha_inicio else ''
                if orginfo and orginfo[0].fecha_limite_email:
                    fechaLimitePago = recibos[0].vencimiento.strftime("%d/%m/%Y") if recibos and recibos[0] and recibos[0].vencimiento else ''
            else:
                primaT = 0
                fi = ''
            
            org_info = get_org_info(request)
            direccion =  org_info['address']
            data = {
                'logo':logo,
                'logo_mini':logo_mini,
                'certificate_number': poliza.certificate_number,
                'poliza_number': poliza.poliza_number,
                'contratante': contratante,
                'start_of_validity': poliza.start_of_validity.strftime("%d/%m/%Y"),
                'end_of_validity': poliza.end_of_validity.strftime("%d/%m/%Y"),
                'aseguradora': aseguradora,
                'ramo': poliza.ramo,
                'subramo': poliza.subramo,
                'moneda':parCurrency,
                'frecuencia_de_pago': poliza.get_forma_de_pago_display(),
                'prima_neta': '$' + '{:,.2f}'.format(poliza.p_neta),
                'rpf': '$' + '{:,.2f}'.format(poliza.rpf),
                'derecho': '$' + '{:,.2f}'.format(poliza.derecho),
                'iva': '$' + '{:,.2f}'.format(poliza.iva),
                'prima_total': '$' + '{:,.2f}'.format(poliza.p_total),
                'prima_total_recibo': '$' + '{:,.2f}'.format(primaT),
                'fecha_recibo': fi if fi else '',
                'fechaLimitePago':fechaLimitePago,
                'subject': subject,
                'asegurado':asegurado,
                'direccion':direccion,
                'dato_cvigencia': orginfo[0].dato_cvigencia if orginfo else True,
                'dato_caseguradora': orginfo[0].dato_caseguradora if orginfo else True,
                'dato_csubramo': orginfo[0].dato_csubramo if orginfo else True,
                'dato_cmoneda': orginfo[0].dato_cmoneda if orginfo else True,
                'dato_cfrecuenciapago': orginfo[0].dato_cfrecuenciapago if orginfo else True,
                'dato_casegurado': orginfo[0].dato_casegurado if orginfo else True,
                'dato_cptotal': orginfo[0].dato_cptotal if orginfo else True,
                'dato_cpneta': orginfo[0].dato_cpneta if orginfo else True,
                'dato_cderecho': orginfo[0].dato_cderecho if orginfo else True,
                'dato_crpf': orginfo[0].dato_crpf if orginfo else True,
                'dato_civ': orginfo[0].dato_civ if orginfo else True,
                'dato_cnumcertificado': orginfo[0].dato_cnumcertificado if orginfo else True,
                'dato_ccontratante': orginfo[0].dato_ccontratante if orginfo else True,
            }
            banner_file = BannerFile.objects.filter(org_name = request.GET.get('org')) 
            header = ''
            footer = ''
            if banner_file.exists():
                if banner_file[0].header:
                    header = get_url_file(banner_file[0].header)  
                if banner_file[0].footer:
                    footer = get_url_file(banner_file[0].footer)  
            data.update({'b_header': header,'b_footer': footer})
            body = render_to_string("share_certificateNV_body.html", data)
            head = render_to_string("share_certificateNV_head.html", data)
            footer = render_to_string("share_certificateNV_footer.html", data)
            return Response({'body':body, 'head':head, 'footer':footer,'subject_default':subject}, status=200)
        except Exception as e:
            return Response({'response': 'Error!', 'error': str(e)})


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def ShareSiniestroEmailNV(request, id=None):
    fechaLimitePago=''
    siniestro=None
    poliza=None
    org_name = request.GET.get('org')
    model_log = request.data['model'] if 'model' in request.data else None
    try:
        siniestro = Siniestros.objects.get(pk=int(request.data['id'] if request.data and 'id' in request.data else id),org_name=request.GET.get('org'))
        poliza = Polizas.objects.get(pk=siniestro.poliza.id,org_name=request.GET.get('org'))
    except:
        return Response({'error': 'No existe el siniestro con el ID: '+str(request.data['id'] if request.data and 'id' in request.data else id)})

    if request.method == 'POST':
        receiver =  json.dumps(request.data['emails']) #request.data['emails']
        try:
            r_files = request.data['files']
        except Exception as error_file:
            r_files = []
        if poliza.contractor:
            contratante = poliza.contractor.full_name
        else:
            contratante = ''

        try:
            sov = str(poliza.start_of_validity.strftime("%d/%m/%Y"))
        except:
            sov = ''

        try:
            eov = str(poliza.end_of_validity.strftime("%d/%m/%Y"))
        except:
            eov = ''
        if 'subject' in request.data and request.data['subject']:
            subject = request.data['subject']
        else:
            subject = str(contratante)+'  información del siniestro '+str(siniestro.numero_siniestro if siniestro.numero_siniestro else siniestro.folio_interno)+\
                      ' - '+str(poliza.subramo.subramo_name if poliza.subramo else '')
        remitente,logo,logo_mini = user_remitente(request)
        files = SiniestrosFile.objects.filter(id__in=list(r_files))

        files_data = []
        if poliza.ramo:
            try:
                if poliza.ramo.ramo_code ==1:#vida
                    tipo_poliza = 'VIDA'
                    form = Vida.objects.get(siniestro = siniestro.id,org_name=siniestro.org_name)
                    tipo_poliza=form.get_razon_siniestro_display()
                    asegurado = form.nombre_afectado if form and form.nombre_afectado else poliza.contractor.full_name if poliza and poliza.contractor else ''
                elif poliza.ramo.ramo_code ==2:#acc
                    tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                    accident = Accidentes.objects.get(siniestro = siniestro.id,org_name=siniestro.org_name)
                    tipo_poliza=accident.get_razon_siniestro_display()                    
                    if accident.dependiente:
                        asegurado = accident.dependiente.first_name + ' ' + accident.dependiente.last_name + ' ' + accident.dependiente.second_last_name
                    else:
                        asegurado = accident.titular.first_name + ' ' + accident.titular.last_name + ' ' + accident.titular.second_last_name
                    if not asegurado:
                        asegurado = poliza.contractor.full_name if poliza and poliza.contractor else ''
  
                elif poliza.ramo.ramo_code ==3 and poliza.subramo.subramo_code ==9:#aut
                    tipo_poliza = 'DAÑOS/AUTOS'
                    form = Autos.objects.get(siniestro = siniestro.id,org_name=siniestro.org_name)
                    tipo_poliza=form.get_tipo_siniestro_display()
                    asegurado = ''
                elif poliza.ramo.ramo_code ==3  and poliza.subramo.subramo_code !=9:#dañ
                    tipo_poliza = 'DAÑOS'
                    form = Danios.objects.get(siniestro = siniestro.id,org_name=siniestro.org_name)
                    asegurado = form.bien_asegurado if form and form.bien_asegurado else poliza.contractor.full_name if poliza and poliza.contractor else ''
                else:
                    asegurado =poliza.contractor.full_name if poliza and poliza.contractor else ''
            except Exception as c:
                asegurado = ''      
                tipo_poliza=poliza.subramo.subramo_name if poliza and poliza.subramo and poliza.subramo.subramo_name else ''
        else:
            asegurado = ''
        aseguradora=poliza.aseguradora.compania if poliza.aseguradora else ''
        if poliza.document_type ==3:                
            tipo_poliza = 'PÓLIZA DE GRUPO'
        if poliza.document_type ==8:                
            tipo_poliza = 'FIANZA DE GRUPO'
        if poliza.document_type ==6:  
            aseguradora=poliza.parent.parent.parent.aseguradora.compania if poliza.parent and poliza.parent.parent and poliza.parent.parent.parent and poliza.parent.parent.parent.aseguradora and poliza.parent.parent.parent.aseguradora.compania else ''              
            tipo_poliza = 'CERTIFICADO'
        if files:
            if admin_archivos(request):
                for file in files:                    
                    file.arch = get_presigned_url(folder+"/{url}".format(url=file.arch),28800)  
                    URL = str(file.arch).replace(" ", "+")
                    files_data.append({'url':URL,'name':file.nombre})
        status = status_poliza(poliza.status)
        parCurrency = checkCurrency(poliza.f_currency)
        cc = [request.user.email]
        org_info = get_org_info(request)
        direccion =  org_info['address']
        # acorde al ramo 
        personailinfo=''
        emailAsegurado=''
        asuntoAsegurado=''
        fullname=''

        if siniestro.tipo_siniestro_general == 2:
            formulario=AccidentsDiseases.objects.filter(policy=siniestro.poliza,org_name=siniestro.org_name)
            if formulario and formulario[0] and formulario[0].personal:
                personailinfo=formulario[0].personal
            else:
                personailinfo=None
            accident = Accidentes.objects.filter(siniestro=siniestro, org_name=org_name)
            if accident[0] and accident[0].titular:
                emailAsegurado=accident[0].titular.email
                fullname=accident[0].titular.first_name +' '+str(accident[0].titular.last_name)+' '+str(accident[0].titular.second_last_name)
                asuntoAsegurado= fullname
                asegurado=asuntoAsegurado
            elif accident[0] and accident[0].dependiente:
                emailAsegurado=personailinfo.email if personailinfo else email_to
                fullname=accident[0].dependiente.first_name +' '+str(accident[0].dependiente.last_name)+' '+str(accident[0].dependiente.second_last_name)
                asuntoAsegurado= fullname
                asegurado=asuntoAsegurado
            if accident and accident[0]:
                tipo_poliza = accident[0].get_razon_siniestro_display()
  
        elif siniestro.tipo_siniestro_general == 3 :
            automovil = AutomobilesDamages.objects.get(policy=siniestro.poliza,org_name=siniestro.org_name)
            asuntoAsegurado=' Asegurado(a)'               
            asegurado= str(automovil.brand if automovil.brand else '') +' '+str(automovil.model if automovil.model else '')+' '+str(automovil.year if automovil.year else '') +' / '+str(automovil.serial if automovil.serial else '') 

        elif siniestro.tipo_siniestro_general == 1 :
            vida = Vida.objects.filter(siniestro=siniestro, org_name=org_name)
            asuntoAsegurado=' Asegurado(a)'
            asegurado= vida[0].nombre_afectado if vida and vida[0] and vida[0].nombre_afectado else ''

            if not asegurado:
                form = Life.objects.filter(policy = poliza.id,org_name=org_name)
                tipo_poliza = 'VIDA'
                if form:
                    if form[0]:
                        if form[0].personal:
                            asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
            if asegurado:
                asuntoAsegurado=asegurado
            if vida and vida[0]:
                tipo_poliza = vida[0].get_razon_siniestro_display()
        elif siniestro.tipo_siniestro_general == 4 :
            damage = Danios.objects.filter(siniestro=siniestro, org_name=org_name)  
            asuntoAsegurado=' Asegurado(a)'  
            asegurado = damage[0].bien_asegurado if damage and damage[0] and damage[0].bien_asegurado else asegurado
        # --------------------------------
        data = {
            'solobody':False,
            'logo':logo,
            'logo_mini':logo_mini,
            'numero_siniestro': siniestro.numero_siniestro,
            'poliza_number': poliza.poliza_number,
            'tipo_siniestro': tipo_poliza,
            'contratante': contratante,
            'start_of_validity': sov,
            'end_of_validity': eov,
            'aseguradora': aseguradora,
            'ramo': poliza.ramo.ramo_name if poliza.ramo else '',
            'subramo': poliza.subramo.subramo_name if poliza.subramo else '',
            'moneda':parCurrency,
            'siniestro_estatus':siniestro.get_status_display(),
            'fecha':datetime.now().strftime("%d/%m/%y"),
            'files': json.dumps(files_data),
            'remitente': remitente,
            'subject': subject,
            'receiver': receiver,
            'cc': json.dumps(cc),
            'asegurado':asegurado if asegurado else poliza.contractor.full_name if poliza and poliza.contractor else '',
            'direccion':direccion,
            'estimado':asuntoAsegurado,
            'org':request.GET.get('org'),
        }
        first_comment = request.data['first_comment'] if 'first_comment' in request.data else '' 
        second_comment = request.data['second_comment'] if 'second_comment' in request.data else '' 
        try:
            textinitial =first_comment if first_comment else ''
            result = re.sub('\?[^"]+', '', textinitial)
            textinitial = result
            img_pattern = r'<img.*?src="data:image/(.*?);base64,(.*?)".*?>'
            images = re.findall(img_pattern, textinitial)
            # print('imagesimages',images)
            if images:
                for i, (img_type, img_data) in enumerate(images):
                    rnd =random.randint(1,10001)
                    img_name = 'image_'+str(i+1)+'_'+str(rnd)+'.'+str(img_type) 
                    s3_url = upload_to_s3_img_siniestros(img_data, img_name, img_type,img_name,org_name)
                    search_str = 'data:image/' + img_type + ';base64,' + img_data
                    width = 200
                    height = 200 
                    img_tag = s3_url + '" style="text-align:center;'
                    first_comment = first_comment.replace(search_str, img_tag)
            textinitial_2 =second_comment if second_comment else ''
            result = re.sub('\?[^"]+', '', textinitial_2)
            textinitial_2 = result
            img_pattern = r'<img.*?src="data:image/(.*?);base64,(.*?)".*?>'
            images_2 = re.findall(img_pattern, textinitial_2)
            # print('images_2images_2',images_2)
            if images_2:
                for i, (img_type, img_data) in enumerate(images_2):
                    rnd =random.randint(1,10001)
                    img_name = 'image_'+str(i+1)+'_'+str(rnd)+'.'+str(img_type) 
                    s3_url = upload_to_s3_img_siniestros(img_data, img_name, img_type,img_name,org_name)
                    search_str = 'data:image/' + img_type + ';base64,' + img_data
                    width = 200
                    height = 200 
                    img_tag = s3_url + '" style="text-align:center;'
                    second_comment = second_comment.replace(search_str, img_tag)
        except Exception as yimage:
            print('error imagen despacho****',yimage)
        data.update({'first_comment': first_comment,'second_comment':second_comment })
        body = render_to_string("correo_siniestro.html", data)
        data.update({'body': body})
        url = host + "mails/share-policy-manual/"
        headers = {"user_agent": "mozilla", }
        req = requests.post(url, data=data, headers=headers)
        try:
            if str(req) == str('<Response [200]>'):
                # LOG                
                model = 5
                dato_id = siniestro.numero_siniestro if siniestro and siniestro.numero_siniestro else siniestro.folio_interno
                dataIdent = ' envio información del siniestro' +str(dato_id)+' de la póliza: '+str(poliza.poliza_number if poliza and poliza.poliza_number else poliza.internal_number)
                original = {}
                change= dataIdent                    
                try:
                    send_log_complete(request.user, poliza.org_name, 'POST', model, '%s' % str(dataIdent),'%s' % str(original),'%s' % str(change), poliza.id)
                except Exception as eee:
                    pass
                # LOG-------------
                if model_log:
                    body = render_to_string("correo_siniestro.html", data)
                    comment = Comments(model=model_log, id_model=request.data['id'], content="Se ha compartido la póliza", org_name = request.GET.get('org'), user= request.user)
                    comment.save()
                    email_log = LogEmail(model=model_log, associated_id=request.data['id'], comment=comment, to=str(receiver).replace('[', '').replace(']', '').replace('"', ''), cc=request.user.email, subject=subject, body=body, files=files_data)
                    email_log.save()
                return Response({'response': 'sent'}, status=200, headers=headers)
            else:
                try:
                    data = json.loads(req.text)
                    return Response({'response': 'Error: '+str(data['info'])}, status=400,)
                except:
                    return Response({'response': 'Error'}, status=400,)
        except Exception as e:
            return Response({'response': 'Error!'}, status=400,)
    elif request.method == 'GET':
        org_name = request.GET.get('org')
        try:
            body = ''
            if poliza.contractor:
                contratante = poliza.contractor.full_name
            else:
                contratante = ''

            try:
                sov = str(poliza.start_of_validity.strftime("%d/%m/%Y"))
            except:
                sov = ''

            try:
                eov = str(poliza.end_of_validity.strftime("%d/%m/%Y"))
            except:
                eov = ''
            subject = str(contratante)+'  información del siniestro '+str(siniestro.numero_siniestro if siniestro.numero_siniestro else siniestro.folio_interno)+\
                        ' - '+str(poliza.subramo.subramo_name if poliza.subramo else '')
            remitente,logo,logo_mini = user_remitente(request)
            if poliza.ramo:
                try:
                    if poliza.ramo.ramo_code ==1:#vida
                        tipo_poliza = 'VIDA'
                        form = Vida.objects.get(siniestro = siniestro.id,org_name=siniestro.org_name)
                        tipo_poliza=form.get_razon_siniestro_display()
                        asegurado = ''
                    elif poliza.ramo.ramo_code ==2:#acc
                        tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                        form = Accidentes.objects.get(siniestro = siniestro.id,org_name=siniestro.org_name)
                        tipo_poliza=form.get_razon_siniestro_display()
                        asegurado = ''
                    elif poliza.ramo.ramo_code ==3 and poliza.subramo.subramo_code ==9:#aut
                        tipo_poliza = 'DAÑOS/AUTOS'
                        form = Autos.objects.get(siniestro = siniestro.id,org_name=siniestro.org_name)
                        tipo_poliza=form.get_tipo_siniestro_display()
                        asegurado = ''
                    elif poliza.ramo.ramo_code ==3  and poliza.subramo.subramo_code !=9:#dañ
                        tipo_poliza = 'DAÑOS'
                        form = Danios.objects.get(siniestro = siniestro.id,org_name=siniestro.org_name)
                        asegurado = ''
                    else:
                        asegurado = ''
                except:
                    tipo_poliza=poliza.subramo.subramo_name if poliza and poliza.subramo and poliza.subramo.subramo_name else ''
            else:
                asegurado = ''
            if poliza.document_type ==3:                
                tipo_poliza = 'PÓLIZA DE GRUPO'
            if poliza.document_type ==8:                
                tipo_poliza = 'FIANZA DE GRUPO'
            if poliza.document_type ==6:                
                tipo_poliza = 'CERTIFICADO'
            
            status = status_poliza(poliza.status)
            parCurrency = checkCurrency(poliza.f_currency)
            org_info = get_org_info(request)
            direccion =  org_info['address']
            aseguradora = poliza.aseguradora.compania if poliza.aseguradora else ''
            if siniestro.poliza.document_type==6:
                if siniestro and siniestro.poliza and siniestro.poliza.parent and siniestro.poliza.parent.parent and siniestro.poliza.parent.parent.parent and siniestro.poliza.parent.parent.parent.aseguradora:
                    aseguradora = siniestro.poliza.parent.parent.parent.aseguradora.compania
            # acorde al ramo 
            personailinfo=''
            emailAsegurado=''
            asuntoAsegurado=''
            fullname=''
            if siniestro.tipo_siniestro_general == 2:
                formulario=AccidentsDiseases.objects.filter(policy=siniestro.poliza,org_name=siniestro.org_name)
                if formulario and formulario[0] and formulario[0].personal:
                    personailinfo=formulario[0].personal
                else:
                    personailinfo=None
                accident = Accidentes.objects.filter(siniestro=siniestro, org_name=org_name)
                if accident[0] and accident[0].titular:
                    emailAsegurado=accident[0].titular.email
                    fullname=accident[0].titular.first_name +' '+str(accident[0].titular.last_name)+' '+str(accident[0].titular.second_last_name)
                    asuntoAsegurado= fullname
                    asegurado=asuntoAsegurado
                elif accident[0] and accident[0].dependiente:
                    emailAsegurado=personailinfo.email if personailinfo else email_to
                    fullname=accident[0].dependiente.first_name +' '+str(accident[0].dependiente.last_name)+' '+str(accident[0].dependiente.second_last_name)
                    asuntoAsegurado= fullname
                    asegurado=asuntoAsegurado
                if accident and accident[0]:
                    tipo_poliza = accident[0].get_razon_siniestro_display()
            elif siniestro.tipo_siniestro_general == 3 :
                automovil = AutomobilesDamages.objects.get(policy=siniestro.poliza,org_name=siniestro.org_name)
                asuntoAsegurado=' Asegurado(a)'               
                asegurado= str(automovil.brand if automovil.brand else '') +' '+str(automovil.model if automovil.model else '')+' '+str(automovil.year if automovil.year else '') +' / '+str(automovil.serial if automovil.serial else '') 

                print('asegurado',asegurado,asuntoAsegurado,automovil.serial)
            elif siniestro.tipo_siniestro_general == 1 :
                vida = Vida.objects.filter(siniestro=siniestro, org_name=org_name)
                asuntoAsegurado=' Asegurado(a)'
                asegurado= vida[0].nombre_afectado if vida and vida[0] and vida[0].nombre_afectado else asegurado
                if not asegurado:
                    form = Life.objects.filter(policy = poliza.id)
                    tipo_poliza = 'VIDA'
                    if form:
                        if form[0]:
                            if form[0].personal:
                                asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                            else:
                                asegurado = ''
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                if asegurado:
                    asuntoAsegurado=asegurado
                if vida and vida[0]:
                    tipo_poliza = vida[0].get_razon_siniestro_display()
            elif siniestro.tipo_siniestro_general == 4 :
                damage = Danios.objects.filter(siniestro=siniestro, org_name=org_name)  
                asuntoAsegurado=' Asegurado(a)'  
                asegurado = damage[0].bien_asegurado if damage and damage[0] and damage[0].bien_asegurado else asegurado
            # --------------------------------

            data = {
                'logo':logo,
                'solobody':True,
                'logo_mini':logo_mini,
                'numero_siniestro': siniestro.numero_siniestro,
                'poliza_number': poliza.poliza_number,
                'tipo_siniestro': tipo_poliza,
                'contratante': contratante,
                'start_of_validity': sov,
                'end_of_validity': eov,
                'aseguradora': aseguradora,
                'ramo': poliza.ramo.ramo_name if poliza.ramo else '',
                'subramo': poliza.subramo.subramo_name if poliza.subramo else '',
                'moneda':parCurrency,
                'siniestro_estatus':siniestro.get_status_display(),
                'fecha':datetime.now().strftime("%d/%m/%y"),
                'subject': subject,
                'asegurado':asegurado,
                'direccion':direccion,
                'org':request.GET.get('org'),
            }
            if poliza.document_type ==3:                
                tipo_poliza = 'PÓLIZA DE GRUPO'
            if poliza.document_type ==8:                
                tipo_poliza = 'FIANZA DE GRUPO'
            status = status_poliza(poliza.status)            
            body = render_to_string("correo_siniestro.html", data)
            return Response({'body':body, 'subject_default':subject}, status=200)
        except Exception as e:
            return Response({'response': 'Error!', 'error': str(e)})


# *********************** fin compartir certificado **************
def checkCurrency(request):
    switcher = {
        1: "Pesos",
        2: "Dólares",
        3: "UDI",
        4: "Euro",
    }
    return switcher.get(request, "Pesos")
def checkCurrency2(request):
    switcher = {
        1: "MXN",
        2: "USD",
        3: "UDI",
        3: "UDIS",
        4: "Euro",
        4: "Euros",
    }
    return switcher.get(request, "MXN")

    
def get_url_file(fileobj):
    if fileobj and hasattr(fileobj, 'url'):
        try:
            urloki = fileobj.url.replace('https://miurabox.s3.', 'https://miurabox-public.s3.')
        except Exception as e:
            # Log the exception if needed
            urloki = fileobj.url
    else:
        urloki = None
    return urloki
# extact base64
import re
def extract_base64_image(data_str):
    # Define the regex pattern to match base64 image data
    base64_pattern = r'data:image/[a-zA-Z]+;base64,([a-zA-Z0-9+/=]+)'
    # Search for the pattern in the input string
    match = re.search(base64_pattern, data_str)    
    if match:
        # Extract the base64 data (group 1 from the regex match)
        base64_image = match.group(1)
        return base64_image
    return None
def base64_to_image(base64_str, file_path):
    import base64
    image_data = base64.b64decode(base64_str)
    with open(file_path, 'wb') as file:
        file.write(image_data)

def upload_to_s3_img_siniestros(image_data, image_name, image_type,filename,org_name):
    import boto3    
    from boto3.s3.transfer import S3Transfer
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_STORAGE_BUCKET_NAME = "miurabox-public"
    AWS_ACCESS_KEY_ID = 'xxxxxxx'
    AWS_SECRET_ACCESS_KEY = 'xxxxxxx'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    MEDIA_URL = "https://%s/" % (AWS_S3_CUSTOM_DOMAIN)
    JWT_SECRET_KEY = 'CaS2.xxxxxxxx'
    JWT_ALGORITHM = 'HS256'
    image_data_bytes = base64.b64decode(image_data)
    # Upload image to S3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        BUCKET_FILE_NAME = "siniestros_imagenes%s/%s"%(org_name,filename)
        s3.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=BUCKET_FILE_NAME,
            Body=image_data_bytes,
            ContentType='image/'+str(image_type),
            ACL='public-read' 
        )
        url = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/' + BUCKET_FILE_NAME

        return url
    except FileNotFoundError:
        return "The file was not found"
    except NoCredentialsError:
        return "Credentials not available"
def upload_to_s3_img_recordatorios(image_data, image_name, image_type,filename,org_name):
    import boto3    
    from boto3.s3.transfer import S3Transfer
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_STORAGE_BUCKET_NAME = "miurabox-public"
    AWS_ACCESS_KEY_ID = 'x'
    AWS_SECRET_ACCESS_KEY = 'xxxxxxxxxxx'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    MEDIA_URL = "https://%s/" % (AWS_S3_CUSTOM_DOMAIN)
    JWT_SECRET_KEY = 'CaS2.xxxxxxxxxx'
    JWT_ALGORITHM = 'HS256'
    image_data_bytes = base64.b64decode(image_data)
    # Upload image to S3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        BUCKET_FILE_NAME = "cobranza_recordatorio%s/%s"%(org_name,filename)
        s3.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=BUCKET_FILE_NAME,
            Body=image_data_bytes,
            ContentType='image/'+str(image_type),
            ACL='public-read' 
        )
        url = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/' + BUCKET_FILE_NAME

        return url
    except FileNotFoundError:
        return "The file was not found"
    except NoCredentialsError:
        return "Credentials not available"
def upload_to_s3_img_rec_poliza(image_data, image_name, image_type,filename,org_name):
    import boto3    
    from boto3.s3.transfer import S3Transfer
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_STORAGE_BUCKET_NAME = "miurabox-public"
    AWS_ACCESS_KEY_ID = 'xxxxxx'
    AWS_SECRET_ACCESS_KEY = 'xxxxxxx'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    MEDIA_URL = "https://%s/" % (AWS_S3_CUSTOM_DOMAIN)
    JWT_SECRET_KEY = 'CaS2.xxxx'
    JWT_ALGORITHM = 'HS256'
    image_data_bytes = base64.b64decode(image_data)
    # Upload image to S3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        BUCKET_FILE_NAME = "poliza_recordatorio%s/%s"%(org_name,filename)
        s3.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=BUCKET_FILE_NAME,
            Body=image_data_bytes,
            ContentType='image/'+str(image_type),
            ACL='public-read' 
        )
        url = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/' + BUCKET_FILE_NAME

        return url
    except FileNotFoundError:
        return "The file was not found"
    except NoCredentialsError:
        return "Credentials not available"
