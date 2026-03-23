# -*- coding: utf-8 -*-
from urllib import response
from urllib.parse import urljoin
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.core.paginator import Paginator
from control.models import Session
from rest_framework import viewsets
from rest_framework import permissions, viewsets
from core.serializers import *
from core.models import *
from organizations.models import  DjangoGroupInfo
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.auth.models import Group as DjangoGroups 
from polizas.models import Assign, Polizas, Cotizacion, OldPolicies, Pendients
from archivos.models import LecturaFile, PolizasFile, RecibosFile, SiniestrosFile
from rest_framework import parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from rest_framework import status
from .models import Log, Graphics, ModelsPermissions, UserPermissions, LogEmail
import datetime
from .serializers import LogSerializer, GraphHyperSerializer
from django.db import models
from django.db.models import *
from operator import and_, or_
from operator import __or__ as OR
from operator import __and__ as AND
import operator
from functools import reduce
from collections import defaultdict
from PIL import Image
import requests
from organizations.views import get_org
from organizations.serializers import UserSerializer, UserInfoHyperSerializer
from claves.models import Claves
from datetime import datetime, timedelta, date
import arrow
# Importaciones para las tareas desde comentario
from endosos.models import Endorsement
from siniestros.models import Siniestros
from vendedores.models import AccountState
from .push_messages import send_push
import json
from decimal import Decimal
from contratantes.models import Contractor, Group, GroupingLevel
from paquetes.models import Package
from delivery.models import Tasks
from contratantes.serializers import ContractorCasSerializer, GruposCasSerializer, CelulaContractorCasSerializer, GroupingLevelCasSerializer
from claves.serializers import ClavesCasSerializer
from ramos.models import SubRamos, Ramos
from ramos.serializers import SubramosCasSerializer, RamosHyperSerializer
from recibos.models import Recibos
import pytz
import datetime
from endosos.models import *
from recibos.models import Bonos
from django.core.mail.backends.smtp import EmailBackend
import smtplib
from pytz import timezone
import time
#
from organizations.views import get_org_info
from django.core.serializers import serialize
from generics.models import Personal_Information
from forms.models import AutomobilesDamages
# from django.contrib.auth.models import UsersGroups as DjangoUserGroups 
from django.template.loader import render_to_string
from core.utils import decode_token, getDataForPerfilRestricted, is_perm_ver_referenciadores
from contratantes.serializers import GroupingLevelHyperSerializer, ContractorsResumeSerializer
from aseguradoras.serializers import ProviderReadListClaveSerializer
from aseguradoras.models import Provider
# imports necesary to cas2
from control.permissions import IsAuthenticatedV2, IsOrgMemberV2, KBIPermissionV2, AgendaPermissionsV2, FormatosPermissionsV2, EmailInfoPermissionsV2,ComisionesPermissionV2, TokenRevision, TokenRevisionDummy

from dateutil.relativedelta import relativedelta
from rest_framework.pagination import PageNumberPagination
from core.utils import upload_to_s3_signatures, extract_mentioned_users
import random
from polizas.serializers import CotizacionFullSerializer

# from openpyxl import Workbook
# from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
host = settings.MAILSERVICE

@api_view(['POST'])
def send_email_contact(request):
    name = request.data['name']
    email = request.data['email']
    phone = request.data['phone']
    mensaje = request.data['message']


    message=render_to_string("contact_email.html",{
        'name': name, 
        'email': email,
        'phone': phone,
        'mensaje': mensaje,
    })

    remitente = "<no-reply@miurabox.com>"
    subject = "Mensaje de contacto desde SAAM digital"
    email = EmailMultiAlternatives(subject, message, from_email=remitente, to=['contacto@miurabox.com'])
    # email = EmailMultiAlternatives(subject, message, from_email=remitente, to=['rafael.arellano@miurabox.com'])

    email.content_subtype="html"
    email.mixed_subtype = 'related'

    email.send()

    return JsonResponse({'status':'sent'}, safe = False)




@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, ))
def updateFirebaseToken(request):

    user = request.META['user']
    ui = UserInfo.objects.get(user= request.user)
    if request.data['action'] == 'save':
        ui.fcm_token = request.data['token']
        ui.save()
    else:
        ui.fcm_token = None
        ui.save()
    return Response({'task':'Done'})



@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def saveReminder(request):
    comment_id = request.data['mid']
    reminder_date = request.data['reminder_date']
    has_reminder = request.data['has_reminder']

    f = "%Y-%m-%dT%H:%M:%S.%fZ"
    reminder_date = datetime.datetime.strptime(reminder_date, f)

    comment = get_object_or_404(Comments, pk = comment_id)
    comment.reminder_date = reminder_date
    comment.has_reminder = has_reminder
    comment.save()
    serializer = CommentHyperSerializer(comment,context={'request':request}, many = False)
    return Response(serializer.data)




from firebase import firebase
@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def SendChatMessage(request):
    authentication = firebase.FirebaseAuthentication('p7tLbwTYqHdLOl55lx5ZfsbLNucvGk4R1dQgPCHv', 'rafael.arellano@miurabox.com', extra={'id': 123})
    fb = firebase.FirebaseApplication('https://saamnotificaciones.firebaseio.com', authentication=authentication)


    to = request.data['to']
    user_to = User.objects.get(id=to).username.lower()
    user_from = request.user.username.lower()

    if user_from < user_to:
        chat_id = user_from + '_' + user_to
    else:
        chat_id = user_to + '_' + user_from





    result = fb.post('/Chats/%s'%get_org(request.GET.get('org')).urlname,data = {
        'id':chat_id,
        'content':request.data['content'],
        'from': request.user.username,
        'to': user_to,
        'date': datetime.datetime.now(),
        'org': request.GET.get('org')
        })

    return Response({'Status':'Done'})



class GraphicsViewSet(viewsets.ModelViewSet):
    serializer_class = GraphHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        user= self.request.META['user']
        Graphics.objects.filter(org_name=self.request.GET.get('org'), type_graphic = self.request.data['type_graphic'], owner = self.request.user).delete()
        obj = serializer.save(owner=self.request.user, org_name=self.request.GET.get('org'))

    def get_queryset(self):
        if 'type_graphic' in self.request.GET:
            if int(self.request.GET['type_graphic']) ==2:
                config = Graphics.objects.filter(org_name=self.request.GET.get('org'),type_graphic = self.request.GET['type_graphic']).order_by('-created_at')
            else:
                config = Graphics.objects.filter(org_name=self.request.GET.get('org'),owner__username=self.request.user, type_graphic = self.request.GET['type_graphic']).order_by('-created_at')
        else:
            config = Graphics.objects.all()
        return config




@api_view(['POST', 'GET'])
@permission_classes((TokenRevision, IsAuthenticatedV2 ))
def GroupManagerView(request):
    if request.method == 'POST':
        users = request.data
        GroupManager.objects.filter(manager = request.user).delete()
        for user in users:
            user_ = User.objects.get(id = user)
            GroupManager.objects.create(manager = request.user, user = user_)
        return Response(status = status.HTTP_200_OK)
    else:
        query = GroupManager.objects.filter(manager = request.user)
        serializer = GroupManagerHyperSerializer(query, context={"request":request}, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def PerfilByUsuarioRestringidoNameView(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    username = token['data']['username_target']
    try:
        ui = UserInfo.objects.get(user__username = username, org_name = token['org'])
        if ui.perfil_restringido:
            id_perfil_restringido = ui.perfil_restringido.nombre
        else:
            id_perfil_restringido = ''
    except:
        id_perfil_restringido = ''
    return Response(id_perfil_restringido, status = status.HTTP_200_OK)




@api_view(['POST'])
@permission_classes((TokenRevisionDummy, permissions.AllowAny ))
def PerfilByUsuarioRestringidoArrayView(request):
    token_jwt = request.data['Authorization']
    usernames = request.data['usernames']
    token = decode_token(token_jwt.replace('Bearer ',''))
    perfiles = []
    for username in usernames:
        try:
            if token['org'] == 'all':
                ui = UserInfo.objects.get(user__username = username)
            else:
                ui = UserInfo.objects.get(user__username = username, org_name = token['org'])
            if ui.perfil_restringido:
                id_perfil_restringido = ui.perfil_restringido.nombre
                perfiles.append(ui.perfil_restringido.nombre)
            else:
                perfiles.append('Sin Perfil')
        except:
            perfiles.append('Sin Perfil')
            
    
    return Response(perfiles, status = status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def PerfilByUsuarioRestringidoView(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    username = token['data']['username_target']
    ui = UserInfo.objects.get(user__username = username, org_name = token['org'])
    if ui.perfil_restringido:
        id_perfil_restringido = ui.perfil_restringido.id
    else:
        id_perfil_restringido = None
    return Response(id_perfil_restringido, status = status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def PerfilUsuarioRestringidoView(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    perfiles = PerfilUsuarioRestringido.objects.filter(org_name = token['org'])
    serializer = PerfilUsuarioRestringidoTableSerializer(perfiles, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def ContratantesCas(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    contratantes = Contractor.objects.filter(org_name = token['org'], is_active=True)
    serializer = ContractorCasSerializer(contratantes, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def GruposCas(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    grupos = Group.objects.filter(org_name = token['org'])
    serializer = GruposCasSerializer(grupos, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)


from contratantes.models import CelulaContractor
@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def CelulasCas(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    grupos = CelulaContractor.objects.filter(org_name = token['org'])
    serializer = CelulaContractorCasSerializer(grupos, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def SucursalesCas(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    grupos = Sucursales.objects.filter(org_name = token['org'])
    serializer = SucursalCasSerializer(grupos, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)


from organizations.serializers import ReferenciadoresCasSerializer
@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def ReferenciadoresCas(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    grupos = UserInfo.objects.filter(org_name = token['org'], is_vendedor = True)
    serializer = ReferenciadoresCasSerializer(grupos, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def AgrupacionesCas(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    agrupaciones = GroupingLevel.objects.filter(org_name = token['org'])
    serializer = GroupingLevelCasSerializer(agrupaciones, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def AgentesCas(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    agentes = Claves.objects.filter(org_name = token['org'])
    serializer = ClavesCasSerializer(agentes, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def SubramosGeneralCas(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    subramos = SubRamos.objects.filter(org_name = token['org']).distinct('subramo_name')
    serializer = SubramosCasSerializer(subramos, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)




@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def ExistePerfilRestringido(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    existe = PerfilUsuarioRestringido.objects.filter(org_name = token['org'], nombre__icontains = token['data']['nombre']).exists()
    return Response(existe, status = status.HTTP_200_OK)




@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def GuardarPerfilRestringido(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    perfil = PerfilUsuarioRestringido.objects.create(org_name = token['org'],  **request.data['payload'])
    serializer = PerfilUsuarioRestringidoSerializer(perfil, context = {'request':request}, many = False)
    return Response(serializer.data, status = status.HTTP_200_OK)



from polizas.serializers import PolizasCasSerializer
@api_view(['POST'])
@permission_classes((TokenRevision, permissions.AllowAny ))
def PolizasListadoSaam(request):
    token_jwt = request.data['Authorization']
    token = decode_token(token_jwt.replace('Bearer ',''))
    policies = Polizas.objects.filter(document_type__in = [1, 3, 11], poliza_number__icontains = token['data']['numero_poliza'], org_name=token['org']).exclude(status = 0)[:50]
    serializer = PolizasCasSerializer(policies, context = {'request':request}, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)


class PerfilUsuarioRestringidoViewSet(viewsets.ModelViewSet):
    serializer_class = PerfilUsuarioRestringidoSerializer
    permission_classes = (TokenRevision, permissions.AllowAny )
    queryset = PerfilUsuarioRestringido.objects.all()
    
    # def partial_update(self, request, pk=None):
    #     a = str(request.data).replace('"','').replace('\'','"')
    #     a = json.loads(json.dumps(a))
    #     queryset = PerfilUsuarioRestringido.objects.all()
    #     cf = get_object_or_404(queryset, pk=pk)
    #     serializer = PerfilUsuarioRestringidoSerializer(cf, context={'request': request}, data=a, partial=False)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data)
    


class RepositorioPagoViewSet(viewsets.ModelViewSet):
    serializer_class = RepositorioPagoSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)   

    def get_queryset(self):        
        queryset = RepositorioPago.objects.filter(org_name=self.request.GET.get('org')).order_by('-id')
        return queryset

class ConfigProviderScrapperViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigProviderScrapperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)   

    def get_queryset(self):        
        queryset = ConfigProviderScrapper.objects.filter(org_name=self.request.GET.get('org')).order_by('-id')
        return queryset
    def perform_create(self, serializer):
        obj_complete = serializer.save(org_name = self.request.GET.get('org'), owner = self.request.user)  
        return obj_complete
 
class SignatureViewSet(viewsets.ModelViewSet):
    serializer_class = SignatureSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        user =  self.request.META['user']
        orgName = self.request.GET.get('org')
        Signature.objects.filter(user = self.request.user).delete()
        obj = serializer.save(user= self.request.user, signature=self.request.data['signature'])
        input_str =obj.signature
        base64_image = extract_base64_image(input_str)
        if base64_image:
            # data['firma']='data:image/png;base64,'+base64_image
            base64_image = extract_base64_image(input_str)
            if base64_image:
                image_file_path = 'image.png'
                base64_to_image(base64_image, image_file_path)
                nameimage=str(random.randint(1,10001))+'_signature_'+orgName+'.png'
                # S3 bucket details
                bucket_name = 'miurabox-public'
                s3_file_name =nameimage                        
                sign = upload_to_s3_signatures(image_file_path, bucket_name, s3_file_name,orgName)
                obj.image_amazon=sign
                obj.in_amazon = True
                obj.save()

    def get_queryset(self):
        user =  self.request.META['user']
        orgName = self.request.GET.get('org')
        config = Signature.objects.filter(user= self.request.user)
        if config:
            input_str =config[0].signature
            base64_image = extract_base64_image(input_str)
            if base64_image:
                # data['firma']='data:image/png;base64,'+base64_image
                base64_image = extract_base64_image(input_str)
                if base64_image:
                    if config[0].in_amazon==False:
                        image_file_path = 'image.png'
                        base64_to_image(base64_image, image_file_path)
                        nameimage=str(random.randint(1,10001))+'_signature_'+orgName+'.png'
                        # S3 bucket details
                        bucket_name = 'miurabox-public'
                        s3_file_name =nameimage                        
                        sign = upload_to_s3_signatures(image_file_path, bucket_name, s3_file_name,orgName)
                        config[0].image_amazon=sign
                        config[0].in_amazon = True
                        config[0].save()
        return config
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
class BirthdateTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = BirthdateTemplateSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    # def perform_create(self, serializer):
    def create(self, request, *args, **kwargs):
        BirthdateTemplate.objects.filter(org_name=self.request.GET.get('org')).delete()
        validate=False
        error=''
        try:
            remitente =self.request.data['remitente']
            domain=''
            if "@" in remitente:
                domain =remitente.split("@")[1]
            url = settings.MAILSERVICE + "smtpconfvalidate/validate_email"
            req = requests.get(url, params={'username':self.request.data['remitente'],'domain':domain}, headers={'Content-Type': 'application/json'} )
            validate = req.json()['success']
            error=req.json()['message']
            print("=> validate", str(req.json()),validate)
        except Exception as c:
            print('err bday templ remitente***',c)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(org_name=self.request.GET.get('org'))
        response_serializer = BirthdateTemplateSerializer(obj, context={'request': self.request})
   
        return Response(
            {"validate": validate, "error": error, "data": response_serializer.data},
            status=status.HTTP_201_CREATED
        )
    def get_queryset(self):
        config = BirthdateTemplate.objects.filter(org_name=self.request.GET.get('org'))
        return config


class LecturaArchivosGeneralViewSet(viewsets.ModelViewSet):
    serializer_class = LecturaArchivosGeneralSerializer
    permission_classes = (AllowAny, )
    pagination_class = None

    def get_queryset(self):
        aseguradora = self.request.GET.get('aseguradora', '')
        org = self.request.GET.get('org', '')
        ramo = self.request.GET.get('ramo', '')
        aut = False
        ramo_code = 3
        if ramo == 'life_policy':
            ramo_code = 1
        if ramo == 'accidents_policy':
            ramo_code = 2
        if ramo == 'vehicle_policy':
            ramo_code = 3
            aut = True
        if ramo == 'damages_policy':
            ramo_code = 3
            aut = False
        
        if org == '':
            return []
        subramos = None
        if aseguradora == 'todas' or aseguradora == '':
            la = LecturaArchivos.objects.filter(org_name = org).order_by('-id')
            if ramo and len(ramo) > 0:
                ramos = Ramos.objects.filter(ramo_code = ramo_code, org_name = org).values_list('pk', flat=True)
                if int(ramo_code)==3:
                    if aut:
                        subramos = SubRamos.objects.filter(ramo__in = ramos,org_name = org,subramo_code = 9).values_list('pk', flat=True)
                    else:
                        subramos = SubRamos.objects.filter(ramo__in = ramos,org_name = org).exclude(subramo_code = 9).values_list('pk', flat=True)
                    la = la.filter(subramo__in = list(subramos))
                la = la.filter(ramo__in = list(ramos))

        else:
            aseg = list(Provider.objects.filter(alias = aseguradora, org_name = org).values_list('pk', flat=True))
            if ramo and len(ramo) > 0:
                ramos = Ramos.objects.filter(org_name = org, ramo_code = ramo_code, provider__id__in = list(aseg)).values_list('pk', flat=True)
                if int(ramo_code)==3:
                    if aut:
                        subramos = SubRamos.objects.filter(ramo__in = ramos,org_name = org,subramo_code = 9).values_list('pk', flat=True)
                    else:
                        subramos = SubRamos.objects.filter(ramo__in = ramos,org_name = org).exclude(subramo_code = 9).values_list('pk', flat=True)
                la = LecturaArchivos.objects.filter(aseguradora__in = aseg, org_name = org, ramo__in = list(ramos)).order_by('-id')
                if subramos:
                    la = la.filter(subramo__in = list(subramos))
            else:
                la = LecturaArchivos.objects.filter(aseguradora__in = aseg, org_name = org).order_by('-id')
        return la

    def perform_create(self, serializer):
        obj = serializer.save(org_name=self.request.GET.get('org'), owner = self.request.user)
    


class LecturaArchivosViewSet(viewsets.ModelViewSet):
    serializer_class = LecturaArchivosSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)
    pagination_class = None

    def get_queryset(self):
        la = LecturaArchivos.objects.filter(org_name=self.request.GET.get('org')).order_by('-id')
        return la

    def perform_create(self, serializer):
        obj = serializer.save(org_name=self.request.GET.get('org'), owner = self.request.user)
    

class LecturaArchivosEditViewSet(viewsets.ModelViewSet):
    serializer_class = LecturaArchivosEditSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def get_queryset(self):
        la = LecturaArchivos.objects.filter(org_name=self.request.GET.get('org')).order_by('-id')
        return la

    def perform_create(self, serializer):
        obj = serializer.save(org_name=self.request.GET.get('org'), owner = self.request.user)
    


class TagsLecturaArchivosViewSet(viewsets.ModelViewSet):
    serializer_class = TagsLecturaArchivosSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def get_queryset(self):
        config = TagsLecturaArchivos.objects.filter(org_name=self.request.GET.get('org'))
        return config

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        # print(args,kwargs['pk'])
        la = TagsLecturaArchivos.objects.get(id = kwargs['pk']).delete()
        return Response(data='delete success')
    

    def partial_update(self, request, pk=None):
        queryset = TagsLecturaArchivos.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        serializer = TagsLecturaArchivosSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)



@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def LogViewSet(request):
    day = request.GET.get('day')
    if day:
        f = "%d/%m/%Y"
        today = datetime.datetime.strptime(day, f)
        tomorrow = today + datetime.timedelta(days=1)
    else:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    queryset = Log.objects.filter(org_name = request.GET.get('org'), created_at__gte = today, created_at__lte = tomorrow )
    response = []
    i = 0
    for log in queryset:
        response.append("%s: El usuario %s %s %s con identificador: %s" % (log.created_at.strftime("%d/%m/%Y-%H:%M:%S"), log.user.username, log.get_event_display(), log.get_model_display(), log.identifier) )
        i = i + 1
    return Response(response)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def LogEmailViewSet(request, log_id, type='0'):
    try:
        if type=='0':
            log_email = LogEmail.objects.get(log=log_id)
        elif type=='1':
            log_email = LogEmail.objects.get(comment=log_id)

        serializer = LogEmailSerializer(log_email)
        return Response(serializer.data)
    except Exception as e:
        return Response("Log no encontrado", status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def send_log_public(request):
    org  = request.GET.get('org','')
    serializer = LogSerializer(data = request.data)
    if not serializer.is_valid(raise_exception=True):
        return Response(serializer.errors)


    event  = request.data['event']
    target  = request.data['model']
    identifier = request.data['identifier']
    associate_id = request.data['associated_id'] if 'associated_id' in request.data else 0

    # if not method or not target or not identifier:
    #     return Response({'error':'method, target or identifier cannot be null'}, status = 400)

    if event == 'DELETE':
        evento = 2
    elif event == 'POST' or event == 'GET':
        evento = 1
    elif event == 'CANCEL':
        evento = 4
    elif event == 'PATCH' or event == 'PUT':
        evento = 3

    log = Log.objects.create(
        model = target,
        event = evento,
        identifier = identifier,
        user= request.user,
        associated_id = associate_id,
        org_name = org
        )
    try:
        if target in (1, 4) and 'save_logmail' in request.data and request.data['save_logmail']==1:
            log_email = LogEmail.objects.filter(associated_id=associate_id, model=target, log=None).order_by('-id')[0]
            log_email.log = log
            log_email.save()
    except Exception as e:
        pass

    return Response(status.HTTP_201_CREATED)
@api_view(['POST'])

@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def send_log_public_specific(request):
    user = request.META['user']
    org  = request.GET.get('org','')
    serializer = LogSerializer(data = request.data)
    if not serializer.is_valid(raise_exception=True):
        return Response(serializer.errors)


    event  = request.data['event']
    target  = request.data['model']
    identifier = request.data['identifier']
    associate_id = request.data['associated_id'] if 'associated_id' in request.data else 0
    try:
        change = request.data['change']
    except Exception as e:
        change = {}
    try:
        original = request.data['original']
    except Exception as e:
        original = {}
    
    if event == 'DELETE':
        evento = 2
    elif event == 'POST' or event == 'GET':
        evento = 1
    elif event == 'CANCEL':
        evento = 4
    elif event == 'PATCH' or event == 'PUT':
        evento = 3

    log = Log.objects.create(
        model = target,
        event = evento,
        identifier = identifier,
        user= request.user,
        associated_id = associate_id,
        change = change,
        original = original,
        org_name = org
        )  
    return Response(status.HTTP_201_CREATED)

def send_log(user, org, method, target, identifier, associate_id):
    if method == 'DELETE':
        event = 2
    elif method == 'POST':
        event = 1
    elif method == 'CANCEL':
        event = 4
    elif method == 'PATCH' or method == 'PUT':
        event = 3
    else:
        event =5 

    log = Log.objects.create(
        model = target,
        event = event,
        identifier = identifier,
        user = user,
        associated_id = associate_id,
        org_name = org
        )
    return log.id

def send_log_complete(user, org, method, target, identifier, original,change, associate_id):
    if method == 'DELETE':
        event = 2
    elif method == 'POST':
        event = 1
    elif method == 'CANCEL':
        event = 4
    elif method == 'PATCH' or method == 'PUT':
        event = 3

    log = Log.objects.create(
        model = target,
        event = event,
        identifier = identifier,
        user = user,
        associated_id = associate_id,
        org_name = org,
        original = original,
        change = change
        )
    return log.id
def find_users_by_names(names,org):
    users = []
    for full_name in names:
        try:
            first_name, last_name = full_name.split()
            if(User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists()):
                if (UserInfo.objects.filter(user = User.objects.filter(first_name__iexact=first_name, 
                    last_name__iexact=last_name)[0],org_name=org)).exists():
                    user = User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name)[0]
                    users.append(user)
            else:
                user =None
                continue
        except User.DoesNotExist:
            continue
    return users
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)


    def partial_update(self, request, pk=None):
        queryset = Comments.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        serializer = CommentHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


    def perform_create(self, serializer):
        user = self.request.META['user']
        user_ = User.objects.get(username  = user['username'])
        if user_:
            user_full=user_.first_name+' '+str(user_.last_name)
        else:
            user_full = ''
        try:
            int(self.request.data['parent'])
            self.request.data['parent']
            parent = Comments.objects.get(id=int(self.request.data['parent']))
        except:
            parent = None


        comentario = serializer.save(
            parent = parent,
            user= self.request.user,
            org_name = self.request.GET.get('org'))
        # ---------get user
        try:
            to_notificate_owners=[]
            to_notificate_in_mentionated=[]
            mentioned_user_names = extract_mentioned_users(comentario.content)
            mentioned_users = find_users_by_names(mentioned_user_names,self.request.GET.get('org'))
            comentario.mentioned_users.add(*mentioned_users)
            comentario.save()
            if comentario.is_child and comentario.parent:
                owner_list = Comments.objects.filter(parent=comentario.parent,is_child=True, org_name=comentario.org_name)
                for i in owner_list:
                    if not i.user in to_notificate_owners:
                        to_notificate_owners.append(i.user)
                    if i.mentioned_users.all():
                        for u in i.mentioned_users.all():
                            if not u in to_notificate_in_mentionated:
                                to_notificate_in_mentionated.append(u)                                

                owner_list_original = Comments.objects.get(id=comentario.parent.id, org_name=comentario.org_name)
                if not owner_list_original.user in to_notificate_owners:
                    to_notificate_owners.append(owner_list_original.user)
                if owner_list_original.mentioned_users.all():
                    for u in owner_list_original.mentioned_users.all():
                        if not u in to_notificate_in_mentionated:
                            to_notificate_in_mentionated.append(u) 
            if mentioned_users:
                for t in mentioned_users:
                    if not t in to_notificate_in_mentionated:
                        to_notificate_in_mentionated.append(t)
            if mentioned_users:
                for inv in to_notificate_in_mentionated:
                    if inv.id != self.request.user.id:
                        notification = Notifications.objects.create(
                            model = 15,#comentario
                            id_reference = comentario.id,
                            title = "El usuario %s te ha mencionado en un comentario "% user_full if user_full else user['username'] ,
                            description = comentario.content ,
                            assigned = inv,
                            involucrado = True,
                            owner= self.request.user,
                            org_name = comentario.org_name ,
                        )
                        notification.send_push_comment(self.request,inv,notification,self.request.user)
            # if not mentioned_users and to_notificate_in_mentionated:
            #     for inv in to_notificate_in_mentionated:
            #         if inv.id != self.request.user.id:
            #             notification = Notifications.objects.create(
            #                 model = 15,#comentario
            #                 id_reference = comentario.id,
            #                 title = "El usuario %s se ha respondido en un comentario donde te han mencionado anteriormente "% user_full if user_full else user['username'] ,
            #                 description = comentario.content ,
            #                 assigned = inv,
            #                 involucrado = True,
            #                 owner= self.request.user,
            #                 org_name = comentario.org_name ,
            #             )
            #             notification.send_push_comment(self.request,inv,notification,self.request.user)
            if to_notificate_owners:
                for inv_o in to_notificate_owners:
                    if inv_o.id != self.request.user.id:
                        notification = Notifications.objects.create(
                            model = 15,#comentario
                            id_reference = comentario.id,
                            title = "El usuario %s ha respondido en la conversación "% user_full if user_full else user['username'] ,
                            description = comentario.content ,
                            assigned = inv_o,
                            involucrado = True,
                            owner= self.request.user,
                            org_name = comentario.org_name ,
                        )
                        notification.send_push_comment(self.request,inv_o,notification,self.request.user)

        except Exception as e:
            print('no users----',e)
        # ------------end send notification
        if comentario.model == 22:
            tarea = Ticket.objects.get(id = comentario.id_model)
            if tarea.archived:
                tarea.archived = False
                tarea.save()
            if tarea.owner.id != self.request.user.id:
                notification = Notifications.objects.create(
                        model = 22,
                        id_reference = tarea.id,
                        title = "El usuario %s ha comentado una tarea que creaste" % user['username'] ,
                        description = comentario.content ,
                        assigned = tarea.owner,
                        involucrado = False,
                        owner= self.request.user,
                        org_name = comentario.org_name ,
                    )
                notification.send_push_generic(self.request)
            try:
                if tarea.assigned.id != self.request.user.id:
                    notification = Notifications.objects.create(
                        model = 22,
                        id_reference = tarea.id,
                        title = "El usuario %s ha comentado una tarea que te han asignado" % user['username'] ,
                        description = comentario.content ,
                        assigned = tarea.assigned,
                        involucrado = False,
                        owner= self.request.user,
                        org_name = comentario.org_name ,
                    )
                    notification.send_push_generic(self.request)
                invs = Involved.objects.filter(involved=tarea)

                for inv in invs:
                    if inv.person.id != self.request.user.id:
                        notification = Notifications.objects.create(
                            model = 22,
                            id_reference = tarea.id,
                            title = "El usuario %s ha comentado una tarea en la que estas involucrado"%user['username'] ,
                            description = comentario.content ,
                            assigned = inv.person,
                            involucrado = True,
                            owner= self.request.user,
                            org_name = comentario.org_name ,
                        )
                        notification.send_push_involucrado(self.request)
            except Exception as e:
                pass
        elif comentario.model == 4:
            receipt = Recibos.objects.get(id=comentario.id_model)
            receipt.track_bitacora = True
            receipt.save()
        elif comentario.model == 6:
            poliza = Polizas.objects.get(pk = comentario.id_model)
            poliza.track_bitacora = True
            poliza.save()
        ramo  = comentario.model
        if ramo == 22: #Si el modelo es el de tareas solo crea el comentario y se regresa
            return comentario
        areas_array  = [
            {'area': 'Clientes', 'modelos':[2,3,8]},
            {'area': 'Fianzas', 'modelos':[13, 21] },
            {'area': 'Cobranzas', 'modelos':[4,7,12] },
            {'area': 'Siniestros', 'modelos':[5] },
            {'area': 'Endosos', 'modelos':[10] },
            {'area': 'Emisiones', 'modelos':[1,18] },
            {'area': 'Renovaciones', 'modelos':[6] }
        ]
        area_ramo = []

        if ramo == 4:
            recibo = Recibos.objects.get(pk = comentario.id_model)
            try:
                if recibo.poliza:
                    if recibo.poliza.ramo.ramo_code in  [1,2]:
                        area_ramo = [3]
                    if recibo.poliza.ramo.ramo_code == 3:
                        if recibo.poliza.subramo.subramo_code == 9:
                            area_ramo = [4]
                        else:
                            area_ramo = [2]
                elif recibo.endorsement:
                    if recibo.endorsement.policy:
                        if recibo.endorsement.policy.ramo.ramo_code in  [1,2]:
                            area_ramo = [3]
                        if recibo.endorsement.policy.ramo.ramo_code == 3:
                            if recibo.endorsement.policy.subramo.subramo_code == 9:
                                area_ramo = [4]
                            else:
                                area_ramo = [2]
                    else:
                        area_ramo=[]
            except Exception as e:
                print('error--e',e)
                return comentario

        elif ramo == 1:
            poliza = Polizas.objects.get(pk = comentario.id_model)
            if poliza.ramo.ramo_code in  [1,2]:
                area_ramo = [3]
            if poliza.ramo.ramo_code == 3:
                if poliza.subramo.subramo_code == 9:
                    area_ramo = [4]
                else:
                    area_ramo = [2]


        elif ramo == 10:
            endoso = Endorsement.objects.get(pk = comentario.id_model)
            if endoso.policy.ramo.ramo_code in  [1,2]:
                area_ramo = [3]
            if endoso.policy.ramo.ramo_code == 3:
                if endoso.policy.subramo.subramo_code == 9:
                    area_ramo = [4]
                else:
                    area_ramo = [2]


        elif ramo == 5:
            siniestro = Siniestros.objects.get(pk = comentario.id_model)
            if siniestro.poliza.ramo.ramo_code in  [1,2]:
                area_ramo = [3]
            if siniestro.poliza.ramo.ramo_code == 3:
                if siniestro.poliza.subramo.subramo_code == 9:
                    area_ramo = [4]
                else:
                    area_ramo = [2]


        # Para estos modelos se involucrarán todos los responsables del area sin distinguir ramos
        elif ramo in [12,13]: # Fianzas y estados de cuenta
            area_ramo = [2,3,4]


        elif ramo in [2,3,8]: # Contratantes fisicos, morales y grupos
            area_ramo = [3]

        else:
            area_ramo = [1]


        # Filtramos los usuarios de las areas y ramos
        areas_usuarios = []
        for area in areas_array:
            if ramo in area['modelos']:
                get_area = Areas.objects.filter(area_name = area['area'], org_name = comentario.org_name)[0:1]
                for foo in AreasResponsability.objects.filter(area = get_area, ramo__in = area_ramo).distinct('user'): #, ramo__in = area_ramo):
                    areas_usuarios.append(foo.user) #Tenemos todos los usuarios del area del comentario


        convert_task = self.request.data['create_task']
        # Si se seleccionó la creación de tarea desde el comentario
        if convert_task == True:
            user_assigned = User.objects.get(id=self.request.data['user_assigned'])

            if comentario.model == 4:
                comentario.modelo_tareas = 1
                recibo = Recibos.objects.get(pk = comentario.id_model)
                comentario.id_model = recibo.poliza.id


            # levantamos el ticket
            ticket = Ticket.objects.create(
                    title = serializer.validated_data['content'][0:50] ,
                    descrip = serializer.validated_data['content'],
                    date = datetime.datetime.now(),
                    assigned = user_assigned,
                    owner= self.request.user,
                    org_name = self.request.GET.get('org'),
                    priority = 2,
                    concept = 7,
                    model = comentario.modelo_tareas,
                    associated = comentario.id_model,
                    comment = comentario,
                )
            ticket.identifier = self.request.GET.get('org').upper() + '%07d' % ticket.id
            ticket.save()
            # Creamos la notificacion principal del ticket

            notification = Notifications.objects.create(
                    model = 22,
                    id_reference = ticket.id,
                    title = ticket.title ,
                    description = ticket.descrip ,
                    assigned = ticket.assigned,
                    involucrado = False,
                    owner = ticket.owner,
                    org_name = ticket.org_name ,
                )
            notification.send_push(self.request)

            # Creamos las notificaciones secundarias para los usuarios involucrados
            # Es necesario obtener los involucrados del area dependiendo del ramo y subramo al que se le
            # hizo el comentario y crearlos para la notificacion:
            # Creamos el regristro de los involucrados
            for inv in areas_usuarios:
                involv = Involved.objects.create(
                        person = inv, #Persona que será involucrada
                        involved = ticket,
                        org_name = ticket.org_name,
                        owner= self.request.user,
                    )

                #Creamos el registro de la notificacion


                notification = Notifications.objects.create(
                    model = 22,
                    involucrado = True,
                    id_reference = ticket.id,
                    title = ticket.title ,
                    description = ticket.descrip ,
                    assigned = involv.person,
                    owner = ticket.owner,
                    org_name = ticket.org_name
                )
                # Enviamos la notificacion
                notification.send_push(self.request)


            notification.send_email(self.request, ticket)

        else:
            for inv in areas_usuarios:
                notification = Notifications.objects.create(
                    involucrado_por_area = True,
                    model = 22,
                    involucrado = True,
                    id_reference = serializer.validated_data['id_model'],
                    title = 'EL usuario %s ha comentado en %s: \"%s\"...'%(user['username'], comentario.get_model_display()  ,serializer.validated_data['content'][0:10] ),
                    description = "%s: %s"%(user['username'],serializer.validated_data['content']),
                    assigned = inv,
                    owner= self.request.user,
                    org_name = self.request.GET.get('org')
                )
                # Enviamos la notificacion
                notification.send_push_involucrado(self.request)

    def get_queryset(self):
        try:
            model = self.request.GET.get('model')
            id_model = self.request.GET.get('id_model')
            is_child = self.request.GET.get('is_child')
            return Comments.objects.filter(org_name=self.request.GET.get('org'), model = model, id_model = id_model).order_by('-created_at')
        except Exception as ec:
            print('cr/v 1028---',ec)
            return []
class CommentByIdViewSet(viewsets.ModelViewSet):
    serializer_class = CommentInfoSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)
    def get_queryset(self):
        return custom_get_queryset(self.request, Comments)
# @api_view(['GET'])
# @permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
# def export_comments_excel(request):
#     org = request.GET.get('org')
#     model = request.GET.get('model')
#     id_model = request.GET.get('id_model')
#     if not org or not model or not id_model:
#         return Response({'detail': 'Los parámetros org, model e id_model son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)
#     try:
#         model_value = int(model)
#         id_model_value = int(id_model)
#     except (ValueError, TypeError):
#         return Response({'detail': 'model e id_model deben ser enteros.'}, status=status.HTTP_400_BAD_REQUEST)

#     queryset = Comments.objects.filter(org_name=org, model=model_value, id_model=id_model_value).select_related('user').order_by('created_at')
#     comments = list(queryset)
#     comment_map = {comment.id: comment for comment in comments}
#     children_map = defaultdict(list)
#     roots = []
#     for comment in comments:
#         if comment.parent_id and comment.parent_id in comment_map:
#             children_map[comment.parent_id].append(comment)
#         else:
#             roots.append(comment)

#     roots.sort(key=lambda comment: comment.created_at or datetime.datetime.min)
#     for sibling_list in children_map.values():
#         sibling_list.sort(key=lambda comment: comment.created_at or datetime.datetime.min)

#     ordered_comments = []
#     visited = set()

#     def append_comment(entry, level=0):
#         if entry.id in visited:
#             return
#         visited.add(entry.id)
#         ordered_comments.append((entry, level))
#         for child in children_map.get(entry.id, []):
#             append_comment(child, level + 1)

#     for root in roots:
#         append_comment(root, 0)
#     for comment in comments:
#         if comment.id not in visited:
#             fallback_level = 1 if comment.parent_id else 0
#             append_comment(comment, fallback_level)

#     def get_target_info():
#         if model_value == 2 and id_model_value:
#             contractor = Contractor.objects.filter(pk=id_model_value).first()
#             if contractor:
#                 name = contractor.full_name or ' '.join(
#                     part
#                     for part in (
#                         contractor.first_name,
#                         contractor.last_name,
#                         contractor.second_last_name,
#                     )
#                     if part
#                 ).strip()
#                 return 'Contratante: {}'.format(name or 'Sin nombre')
#         elif model_value == 1 and id_model_value:
#             poliza = Polizas.objects.select_related('ramo').filter(pk=id_model_value).first()
#             if poliza:
#                 number = poliza.poliza_number or poliza.folio or poliza.internal_number or ''
#                 ramo_name = poliza.ramo.ramo_name if poliza.ramo else ''
#                 info = 'Póliza'
#                 if number:
#                     info = '{}: {}'.format(info, number)
#                 if ramo_name:
#                     info = '{} - {}'.format(info, ramo_name)
#                 return info
#         elif model_value == 13 and id_model_value:
#             fianza = Polizas.objects.select_related('ramo').filter(pk=id_model_value).first()
#             if fianza:
#                 number = fianza.poliza_number or fianza.folio or fianza.internal_number or ''
#                 ramo_name = fianza.ramo.ramo_name if fianza.ramo else ''
#                 info = 'Fianza'
#                 if number:
#                     info = '{}: {}'.format(info, number)
#                 if ramo_name:
#                     info = '{} - {}'.format(info, ramo_name)
#                 return info
#         elif model_value == 10 and id_model_value:
#             endorsement = Endorsement.objects.select_related('policy__ramo').filter(pk=id_model_value).first()
#             if endorsement:
#                 number = endorsement.number_endorsement or endorsement.internal_number or ''
#                 ramo_name = ''
#                 if endorsement.policy and endorsement.policy.ramo:
#                     ramo_name = endorsement.policy.ramo.ramo_name
#                 info = 'Endoso'
#                 if number:
#                     info = '{}: {}'.format(info, number)
#                 if ramo_name:
#                     info = '{} - {}'.format(info, ramo_name)
#                 return info
#         elif model_value == 5 and id_model_value:
#             siniestro = Siniestros.objects.select_related('poliza__ramo').filter(pk=id_model_value).first()
#             if siniestro:
#                 number = siniestro.numero_siniestro or siniestro.folio_interno or ''
#                 poliza = siniestro.poliza
#                 poliza_number = ''
#                 ramo_name = ''
#                 if poliza:
#                     poliza_number = poliza.poliza_number or poliza.folio or poliza.internal_number or ''
#                     if poliza.ramo:
#                         ramo_name = poliza.ramo.ramo_name
#                 info = 'Siniestro'
#                 if number:
#                     info = '{}: {}'.format(info, number)
#                 if poliza_number:
#                     info = '{} (Póliza: {}'.format(info, poliza_number)
#                     if ramo_name:
#                         info = '{} - {}'.format(info, ramo_name)
#                     info = '{})'.format(info)
#                 return info
#         elif model_value in (4, 7, 12) and id_model_value:
#             recibo = Recibos.objects.select_related('poliza__ramo').filter(pk=id_model_value).first()
#             if recibo:
#                 recibo_label = recibo.folio or str(recibo.recibo_numero or '')
#                 poliza = recibo.poliza
#                 poliza_number = ''
#                 ramo_name = ''
#                 if poliza:
#                     poliza_number = poliza.poliza_number or poliza.folio or poliza.internal_number or ''
#                     if poliza.ramo:
#                         ramo_name = poliza.ramo.ramo_name
#                 info = 'Cobranza'
#                 if recibo_label:
#                     info = '{}: {}'.format(info, recibo_label)
#                 if poliza_number:
#                     info = '{} (Póliza: {}'.format(info, poliza_number)
#                     if ramo_name:
#                         info = '{} - {}'.format(info, ramo_name)
#                     info = '{})'.format(info)
#                 return info
#         elif model_value == 9 and id_model_value:
#             package = Package.objects.select_related('ramo').filter(pk=id_model_value).first()
#             if package:
#                 info = 'Paquete: {}'.format(package.package_name or 'Sin nombre')
#                 ramo_name = package.ramo.ramo_name if package.ramo else ''
#                 if ramo_name:
#                     info = '{} - {}'.format(info, ramo_name)
#                 return info
#         elif model_value == 8 and id_model_value:
#             group = Group.objects.filter(pk=id_model_value).first()
#             if group:
#                 return 'Grupo: {}'.format(group.group_name or 'Sin nombre')
#         elif model_value == 11 and id_model_value:
#             provider = Provider.objects.filter(pk=id_model_value).first()
#             if provider:
#                 name = provider.compania or provider.alias
#                 return 'Proveedor: {}'.format(name or 'Sin nombre')
#         elif model_value == 22 and id_model_value:
#             task = Tasks.objects.filter(pk=id_model_value, org_name=org).first()
#             if task:
#                 info_parts = []
#                 if task.action:
#                     info_parts.append(task.action)
#                 if task.address:
#                     info_parts.append(task.address)
#                 if task.date:
#                     info_parts.append(task.date.strftime('%d/%m/%Y %H:%M'))
#                 info = ' - '.join(info_parts)
#                 return 'Tarea: {}'.format(info or 'Sin descripción')
#             return 'Tarea #{}'.format(id_model_value)
#         return ''

#     relation_note = get_target_info()

#     workbook = Workbook()
#     sheet = workbook.active
#     sheet.title = 'Comentarios'
#     header_font = Font(bold=True, color="FFFFFFFF")
#     header_fill = PatternFill(start_color="FF4F81BD", end_color="FF4F81BD", fill_type="solid")
#     thin_side = Side(border_style="thin", color="FF4F81BD")
#     border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
#     header_alignment = Alignment(horizontal="center", vertical="center")
#     body_alignment = Alignment(vertical="top", wrap_text=True)
#     header_row_index = 1
#     if relation_note:
#         sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=3)
#         title_cell = sheet.cell(row=1, column=1, value=relation_note)
#         title_cell.font = header_font
#         title_cell.fill = header_fill
#         title_cell.border = border
#         title_cell.alignment = header_alignment
#         header_row_index = 2

#     headers = ['Usuario', 'Fecha', 'Comentario']
#     for index, title in enumerate(headers, start=1):
#         cell = sheet.cell(row=header_row_index, column=index, value=title)
#         cell.font = header_font
#         cell.fill = header_fill
#         cell.border = border
#         cell.alignment = header_alignment

#     column_widths = [40, 20, 120]
#     for idx, width in enumerate(column_widths, start=1):
#         sheet.column_dimensions[sheet.cell(row=header_row_index, column=idx).column_letter].width = width

#     data_start_row = header_row_index + 1
#     for row_index, (comment, level) in enumerate(ordered_comments, start=data_start_row):
#         user = comment.user
#         user_name = "{} {}".format(user.first_name, user.last_name).strip() or user.username
#         created_at = comment.created_at.strftime('%d/%m/%Y %H:%M') if comment.created_at else ''
#         prefix = '    ' * min(level, 5)
#         content = (comment.content or '').strip()
#         row_values = [
#             user_name,
#             created_at,
#             "{}{}".format(prefix, content),
#         ]
#         for col_index, value in enumerate(row_values, start=1):
#             cell = sheet.cell(row=row_index, column=col_index, value=value)
#             cell.alignment = body_alignment
#             cell.border = border
#         # añadir altura extra para dar más espacio visual entre comentarios

#     output = BytesIO()
#     workbook.save(output)
#     output.seek(0)
#     safe_org = ''.join(ch if ch.isalnum() else '_' for ch in org)
#     file_name = 'comentarios_{}_{}_{}.xlsx'.format(safe_org, model_value, id_model_value)
#     response = HttpResponse(
#         output.getvalue(),
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )
#     response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
#     return response


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def export_comments_excel(request):
    payload = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
    payload.update(request.GET.dict())

    auth_header = request.META.get('HTTP_AUTHORIZATION')
    headers = {'Authorization': auth_header} if auth_header else {}

    payload['Authorization'] = auth_header
    payload['org'] = request.GET.get('org')
    try:
        user_info = UserInfo.objects.get(user=request.user)
    except UserInfo.DoesNotExist:
        user_info = None
    except Exception:
        user_info = None

    perfil_restringido_id = None
    if user_info and getattr(user_info, 'perfil_restringido', None):
        perfil_restringido_id = user_info.perfil_restringido.id
    payload['perfil_restringido_id'] = perfil_restringido_id
    payload['verReferenciadores'] = is_perm_ver_referenciadores(request)
    payload['user'] = request.user

    base_url = (
        settings.SERVICEEXCEL_ANCORA_URL
        if payload.get('org') == 'ancora'
        else settings.SERVICEEXCEL_2_URL
    )
    service_url = urljoin(base_url, 'comments-export/')

    try:
        service_response = requests.post(
            service_url,
            headers=headers,
            data=payload,
            stream=True,
        )
    except requests.RequestException:
        return Response(
            {'detail': 'No se pudo conectar con el servicio de reportes.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    streaming_response = StreamingHttpResponse(
        service_response.iter_content(chunk_size=8192),
        status=service_response.status_code,
        content_type=service_response.headers.get(
            'Content-Type', 'application/octet-stream'
        ),
    )
    for header in ('Content-Disposition', 'Content-Length'):
        value = service_response.headers.get(header)
        if value:
            streaming_response[header] = value

    return streaming_response


class StatesSuperViewSet(viewsets.ModelViewSet):
    queryset = States.objects.all()
    serializer_class = StateHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)


class CitiesSuperViewSet(viewsets.ModelViewSet):
    queryset = Cities.objects.all()
    serializer_class = CityHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)


@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def StatesViewSet(request):
    queryset = States.objects.all()
    serializer = StateHyperSerializer(queryset,context = {'request':request}, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def CitiesViewSet(request):
    queryset = Cities.objects.all()
    serializer = CityHyperSerializer(queryset,context = {'request':request}, many = True)
    return Response(serializer.data)



class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)# 

    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            obj = serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))

    def get_queryset(self):
        return custom_get_queryset(self.request, Address)

class PhonesViewSet(viewsets.ModelViewSet):
    serializer_class = PhonesSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data, many = isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(org_name = self.request.GET.get('org'))
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        return custom_get_queryset(self.request, Phones)

class EmailsViewSet(viewsets.ModelViewSet):
    serializer_class = EmailsSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data, many = isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(org_name = self.request.GET.get('org'))
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        return custom_get_queryset(self.request, Emails)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# from beneficios.rethink import Rethink_db_connection

from datetime import timedelta
def makeUreadTasksNotifications(user, org):
    yesterday = datetime.datetime.now() - timedelta(days=1)
    before_yesterday = datetime.datetime.now() - timedelta(days=2)
    before_before_yesterday = datetime.datetime.now() - timedelta(days=3)
    tareas_sin_leer = Ticket.objects.filter(
        owner = user,
        closed = False,
        date__lte = yesterday,
        org_name = org
    )
    for tarea in tareas_sin_leer:
        try:
            notify = Notifications.objects.get_or_create(
                model = 22,
                id_reference = tarea.id,
                title = 'La tarea "%s" con fecha del %s/%s/%s no ha sido cerrada'%(tarea.title, tarea.date.day, tarea.date.month, tarea.date.year),
                description = "Descripcion de la tarea: %s"%tarea.descrip,
                assigned = user,
                owner = tarea.owner,
                org_name = tarea.org_name
                )
        except:
            pass





'''
Change Token Auth by another like JWT
'''
class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.first_name = request.data['first_name']
        user.last_name = request.data['last_name']
        user.save()
        token, created = Token.objects.get_or_create(user=user)
        permisos = ModelsPermissions.objects.filter(user = user).order_by('model_name')
        serializer = ModelsPermissionSerializer(permisos, context={'request':request}, many = True)
        try:
            makeUreadTasksNotifications(user,request.data['org'])
        except:
            pass
        return Response({'token': token.key, 'user': token.user.id, 'permisos':serializer.data, 'staff':user.is_staff , 'superuser': user.is_superuser})


# from beneficios import settings
from organizations.views import get_org, local_env, get_default_org, get_org_by_env


def custom_get_queryset_last_to_first(request, model):
    if local_env(request.META):
        return model.objects.all().order_by('-id')
    else:
        return model.objects.filter(org_name=request.GET.get('org')).order_by('-id')



def custom_get_queryset(request, model):
    user = request.META['user']
    org_name = user['org']['name']
    if local_env(request.META):
        return model.objects.all()
    else:
        return model.objects.filter(org_name=org_name)

    # return model.objects.all() if local.DEBUG and local_env(request.META) else model.objects.filter(org=request.GET['org'])


def custom_org_create(request):
    if not local_env(request.META):
        request.GET.get('org')
    # return get_org(get_default_org()) if local.DEBUG and local_env(request.META) else get_org(request.GET['org'])


def file_get_queryset(request, model, owner):
    return model.objects.filter(owner=owner, org_name=request.GET.get('org'))


    # return model.objects.all() if local.DEBUG and local_env(request.META) else model.objects.filter(owner=owner, org=request.GET['org'])



def get_permisos_local():
    models = ['coverageinpolicy', 'deductible', 'suminsured', 'contactinfo', 'taskemail', 'oldpolicies', 'pendients' ,
    'forms', 'respform', 'accounts', 'bancos' , 'accidentes', 'autos' , 'contactoauto', 'padecimientos',
    'vida', 'ramos','address', 'cities', 'log', 'states', 'endorsementcerts']

    app_labels = ['Can add archivos sensibles', 'Can change archivos sensibles', 'Can delete archivos sensibles',
    'Can add recibos', 'Can delete recibos', 'Can change reports', 'Can delete reports', 'Can delete nota credito',
    'Can change comments', 'Can delete comments', 'Can change renovations', 'Can delete renovations',
    'Can delete renovations', 'Can view renovations', 'Can delete commissions',
    'Can change commissions', 'Can add commissions', 'Can add facturas', 'Can view facturas', 'Can add phone', 'Can change phone',
    'Can view phone', 'Can delete phone', 'Can add subramos vendedor', 'Can view subramos vendedor','Can change subramos vendedor',
    'Can delete subramos vendedor', 'Can view phones', 'Can add phones', 'Can change phones', 'Can delete phones', 'Can view emails',
    'Can add emails','Can change emails','Can delete emails', 'Can view internal', 'Can add internal','Can change internal',
    'Can delete internal', 'Can view contract', 'Can add contract','Can change contract','Can delete contract',
    'Can view beneficiaries contract', 'Can add beneficiaries contract','Can change beneficiaries contract', 'Can delete beneficiaries contract']

    content = list(ContentType.objects.exclude(model__in = list(models)).values_list('pk', flat=True))
    permisos = Permission.objects.exclude(name__in = list(app_labels)).filter(content_type__in = content)
    return permisos

@csrf_exempt
def get_permisos(request):
    try:
        user = User.objects.get(id = 1)
        permisos = ModelsPermissions.objects.filter(user = user).order_by('model_name')
        serializer = ModelsPermissionSerializer(permisos, context={'request':request}, many = True)
        return JsonResponse(serializer.data,safe=False)
    except Exception as e:
        pass




@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def get_areas(request, _id):
    try:
        area =  Areas.objects.get(pk = _id)
        serializer = AreasFullSerializer(area, context={'request':request}, many = False)
        return JsonResponse(serializer.data,safe=False)
    except Exception as e:
        return JsonResponse({'error':str(e)},safe=False)



@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def get_user_permisos(request):
    org = request.GET.get('org')
    username = request.GET.get('username')
    try:
        user = User.objects.get(username = username)
        permisos = ModelsPermissions.objects.filter(user = user).order_by('model_name')
        serializer = ModelsPermissionSerializer(permisos, context={'request':request}, many = True)
        # print(serializer.data)
        # permisos = get_permisos_local()       
        # serializer = PermissionSerializer(permisos, context={'request':request}, many = True)
        # response = []
        # for s in serializer.data:            
        #     permiso= Permission.objects.get(name = s['name'],content_type = s['content_type']['id'])
        #     has_perm = user.user_permissions.filter(id = permiso.id).exists()
        #     if has_perm:
        #         s['active_on_user'] = 'true'
        #     else:
        #         s['active_on_user'] = 'false'
        #     response.append(s)
        return JsonResponse(serializer.data,safe=False)
    except Exception as e:
        return JsonResponse({'error':str(e)},safe=False)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def get_user_areas(request):
    org_name = request.GET.get('org')
    username = request.GET.get('username')
    try:
        user = User.objects.get(username = username)
        areas_responsability = AreasResponsability.objects.filter(user=user,org_name=org_name)
        response = []
        queryset = AreasResponsability.objects.filter(user=user,org_name=org_name)
        serializer_area = AreasResponsabilityInfoSerializer(areas_responsability, context={'request':request}, many = True)
        return Response(serializer_area.data)
    except Exception as e:
        return JsonResponse({'error':str(e)},safe=False)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def get_areas_responsability(request):
    org_name= request.GET.get('org')
    type_area = int(request.GET.get('type_area'))
    if type_area == 1:
        area_name = 'Renovaciones'
    elif type_area == 2:
        area_name = 'Emisiones'
    elif type_area == 3:
        area_name = 'Endosos'
    elif type_area == 4:
        area_name = 'Siniestros'
    elif type_area == 5:
        area_name = 'Cobranzas'
    elif type_area == 6:
        area_name = 'Fianzas'
    elif type_area == 7:
        area_name = 'Clientes'
    elif type_area == 8:
        area_name = 'Danios'
    elif type_area == 9:
        area_name = 'Autos'
    elif type_area == 10:
        area_name = 'Personas'
    else:
        return JsonResponse({'error':'El area no existe'},safe=False)
    try:
        # user = User.objects.get(username = username)
        areas = Areas.objects.filter(org_name=org_name,area_name = area_name)
        queryset_areas = AreasResponsability.objects.filter(org_name=org_name,area = areas, is_active = True)
        serializer_area = AreasResponsabilityInfoSerializer(queryset_areas, context={'request':request}, many = True)
        return Response(serializer_area.data)
    except Exception as e:
        return JsonResponse({'error':str(e)},safe=False)

@api_view(['GET'])
@csrf_exempt 
def ValidateEmailSISS(request):
    response = False
    email = request.GET.get('email')
    pi = Personal_Information.objects.filter(email__iexact=email)
    aut = AutomobilesDamages.objects.filter(email__iexact=email)

    if pi.exists():
        response = True
        first_name = pi[0].first_name
        last_name = pi[0].last_name
        return JsonResponse({'response':response, 'first_name':first_name, 'last_name':last_name})

    if aut.exists():
        response = True
        first_name = aut[0].beneficiary_name
        last_name = ""
        return JsonResponse({'response':response, 'first_name':first_name, 'last_name':last_name})

    return JsonResponse({'response':response})



@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, ))
def no_assigned_get_user_areas(request):
    org_name = request.GET.get('org')
    username = request.GET.get('username')
    try:
        user = User.objects.get(username = username)
        areas_responsability = AreasResponsability.objects.filter(user=user,org_name=org_name)
        response = []
        queryset = AreasResponsability.objects.filter(user=user,org_name=org_name)
        serializer_area = AreasResponsabilityInfoSerializer(areas_responsability, context={'request':request}, many = True)
        area_inuser = []
        for r in serializer_area.data:
            area_inuser.append(r['area'])
        queryset_areas = Areas.objects.filter(org_name=org_name).exclude(area_name__in = (area_inuser))
        serializer_ar = AreasInfoSerializer(queryset_areas, context={'request':request}, many = True)
        return Response(serializer_ar.data)
    except Exception as e:
        return JsonResponse({'error':str(e)},safe=False)

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def change_permisos(request):
    if request.method == 'GET':
        try:

            permiso = Permission.objects.get(id = int(request.data['perm_id']))
            user = User.objects.get(username = request.data['username'])

            exist = user.user_permissions.filter(id = permiso.id).exists()

            return Response({'status': permiso.name + ' ' + str(exist), 'has_perm': str(exist),'user':user.username })

        except Exception as e:
            pass


    elif request.method == 'POST':
        try:
            active = request.data['active']
            permiso = UserPermissions.objects.get(id = int(request.data['perm_id']))
            # user =  User.objects.get(username = request.data['username'])  

            # exist = user.user_permissions.filter(id = permiso.id).exists()

            if active == 'true':
                permiso.checked = True
                # user.user_permissions.add(permiso)
            elif active == 'false':
                permiso.checked = False
                # user.user_permissions.remove(permiso)
            else:
                pass


            permiso.save()

            # user = User.objects.get(pk=user.id)       

            # exist = user.user_permissions.filter(id = permiso.id).exists()

            return Response({'status': '200 OK'})

        except Exception as e:
            return Response({'status': 'error'})


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, ))
def change_massive_permisos(request):
    if request.method == 'POST':
        try:
            perms = request.data['perms']
            user = User.objects.get(username = request.data['username'])
            models = ModelsPermissions.objects.filter(user = user).values_list('pk',flat=True)
            permissions = UserPermissions.objects.filter(model__in = list(models)).update(checked = False)
            # print(permissions)

            perms = perms.split(',')
            # print(perms)

            for permiso in perms:
                perm = UserPermissions.objects.get(id = int(permiso))
                perm.checked = True
                perm.save()
            return Response({'status': '201 CREATED' })

        except Exception as e:
            return Response({'status': 'error'})


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, ))
def deactivate_user(request):
    try:
        if request.method == 'POST':
            username = request.data['username']
            user = User.objects.get(username = username)

            user.is_active = False
            user.save()
            return Response({'status': 'deactivated'})
        elif request.method == 'GET':
            username = request.GET.get('username')
            user = User.objects.get(username = username)

            user.is_active = True
            user.save()
            return Response({'status': 'activated'})
    except Exception as e:
        pass

class CartaViewSet(viewsets.ModelViewSet):
    serializer_class = CartaFullSerializer
    permission_classes = (IsAuthenticatedV2, FormatosPermissionsV2, IsOrgMemberV2)


    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            obj = serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))

        if obj.id:
            send_log(self.request.user, self.request.GET.get('org'), 'POST', 17, 'creó la carta', obj.id)


    def get_queryset(self):
        return custom_get_queryset(self.request, Cartas)


class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = (IsAuthenticatedV2,  AgendaPermissionsV2, IsOrgMemberV2)

    def update(self, request, *args, **kwargs):
        user = request.META['user']
        utc = pytz.UTC
        local_tz = pytz.timezone('America/Monterrey')
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        notification = Notifications.objects.filter(model=24, id_reference=instance.id)
        notification.delete()
        participants = ScheduleParticipants.objects.filter(schedule_id=instance.id)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        for participant in participants:
            notification = Notifications.objects.create(
                model=24,
                id_reference=instance.id,
                title="{} ha actualizado el evento {} para el {} a las {} finaliza el {} a las {} ".format(request.user.first_name,
                    instance.title,
                    datetime.datetime.strptime(request.data['startsAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                        tzinfo=utc).astimezone(local_tz).date(),
                    datetime.datetime.strptime(request.data['startsAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                        tzinfo=utc).astimezone(local_tz).time()
                        .replace(microsecond=0, second=0),
                    datetime.datetime.strptime(request.data['endsAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                        tzinfo=utc).astimezone(local_tz).date(),
                    datetime.datetime.strptime(request.data['endsAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                        tzinfo=utc).astimezone(local_tz).time()
                        .replace(microsecond=0, second=0)
                ),
                description=serializer.data['title'],
                assigned=participant.user,
                involucrado=False,
                owner=participant.user,
                org_name=self.request.GET.get('org'),
            )
            notification.send_push_generic(self.request)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            notification = Notifications.objects.filter(model=24, id_reference=instance.id)
            notification.delete()
            self.perform_destroy(instance)
        except:
            pass
        return Response({'Response': 'The element as been destroyed'}, status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        utc = pytz.UTC
        local_tz = pytz.timezone('America/Monterrey')
        try:
            if type(request.data[0]['participants']) is str:
                participants = []
            else:
                participants = request.data[0]['participants']
        except:
            participants = []

        participants.append({"first_name": self.request.user.first_name,"last_name":self.request.user.last_name, "id": self.request.user.id})
        if participants:
            request.data[0].update({"participants": participants})
        serializer = self.get_serializer(data = request.data, many = isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        refer = Schedule.objects.latest('id')
        headers = self.get_success_headers(serializer.data)
        if participants:
            for participant in participants:
                user = User.objects.get(id=participant['id'])
                participant_model = ScheduleParticipants.objects.create(user_id=user.id, schedule=refer)
                notification = Notifications.objects.create(
                    model=24,
                    id_reference=refer.id,
                    title="Se ha generado un evento para el {} a las {} finaliza el {} a las {} ".format(
                        datetime.datetime.strptime(serializer.data[0]['startsAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                            tzinfo=utc).astimezone(local_tz).date(),
                        datetime.datetime.strptime(serializer.data[0]['startsAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                            tzinfo=utc).astimezone(local_tz).time()
                            .replace(microsecond=0, second=0),
                        datetime.datetime.strptime(serializer.data[0]['endsAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                            tzinfo=utc).astimezone(local_tz).date(),
                        datetime.datetime.strptime(serializer.data[0]['endsAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                            tzinfo=utc).astimezone(local_tz).time()
                            .replace(microsecond=0, second=0)
                    ),
                    description=serializer.data[0]['title'],
                    assigned=user,
                    involucrado=False,
                    owner=user,
                    org_name = self.request.GET.get('org'),
                )
                notification.send_push_generic(self.request)
                notification.send_email_calendar(self.request, user.email, refer )
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        utc = pytz.UTC
        local_tz = pytz.timezone('America/Monterrey')
        events = ScheduleParticipants.objects.filter(user_id=self.request.user.id)
        queryset = Schedule.objects.filter(id__in=events.values('schedule_id'),org_name = self.request.GET.get('org'))

        # for schedule in queryset:
        #     if schedule.endsAt.replace(tzinfo=utc).astimezone(local_tz).ctime() < datetime.datetime.now().replace(tzinfo=utc).ctime():
        #         try:
        #             notification = Notifications.objects.filter(model=24, id_reference=schedule.id)
        #             if notification:
        #                 notification.delete()
        #             if schedule:
        #                 schedule.delete()
        #         except:
        #             pass
        return queryset


@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def cartas_by_model(request):
    modelo = request.GET.get('model')

    cartas = Cartas.objects.filter(model = modelo, org_name = request.GET.get('org'))
    serializer = CartaFullSerializer(cartas, context = {'request': request}, many = True)

    return JsonResponse(serializer.data, safe = False)

class InternalNumber(viewsets.ModelViewSet):
    serializer_class = InternalHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        try:
            obj = serializer.save(org_name=self.request.GET.get('org'))
        except Exception as e:
            obj = serializer.save(org_name=self.request.POST.get('org'))

    def get_queryset(self):
        return custom_get_queryset(self.request, Internal)

class AreasViewset(viewsets.ModelViewSet):
    serializer_class = AreasSerializer
    permission_classes = (IsAuthenticatedV2,)

    def perform_create(self, serializer):
        try:
            # print('SERIALIZER DATA', serializer.validated_data['area_name'])
            # filtro = Areas.objects.filter(org_name = self.request.GET.get('org')), area_name = serializer.validated_data['area_name'])
            # if filtro.exists():

            # else:
            #     print('EL FILTRO NO EXISTE')
            obj = serializer.save(owner= self.request.user, org_name = self.request.GET.get('org'))
        except Exception as e:
            obj = serializer.save(org_name = self.request.POST.get('org'))

    def get_queryset(self):
        return custom_get_queryset(self.request, Areas)



class AreasResViewset(viewsets.ModelViewSet):
    serializer_class = AreasResponsabilitySerializer
    permission_classes = (IsAuthenticatedV2,)

    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner= self.request.user, org_name = self.request.GET.get('org'))
        except Exception as e:
            obj = serializer.save(owner= self.request.user, org_name = self.request.POST.get('org'))

    def get_queryset(self):
        return custom_get_queryset(self.request, AreasResponsability)



from polizas.models import Polizas
@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def get_polizas_count(request):
    polizas = Polizas.objects.filter(org_name = request.GET.get('org'), document_type = 1)
    caratulas = Polizas.objects.filter(org_name = request.GET.get('org'), document_type = 3)

    obj = {
        'polizas': len(polizas),
        'caratulas' : len(caratulas)
    }

    return JsonResponse(obj,status = 200)


from django.shortcuts import get_object_or_404
class EmailInfoViewSet(viewsets.ModelViewSet):
    serializer_class = EmailInfoSerializer
    permission_classes = (IsAuthenticatedV2, EmailInfoPermissionsV2, IsOrgMemberV2)

    def partial_update(self, request, pk=None):
        queryset = EmailInfo.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        serializer = EmailInfoSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = EmailInfo.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        serializer = EmailInfoSerializer(cf, context={'request': request}, many = False)
        return Response(serializer.data)

    def perform_create(self, serializer):
        try:
            EmailInfo.objects.filter(org_name = self.request.GET.get('org'), model = self.request.POST.get('model')).delete()
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except Exception as e:
            pass

    def get_queryset(self):
        model = self.request.GET.get('model')

        emailinfo = EmailInfo.objects.filter(org_name = self.request.GET.get('org'), model = model)

        return emailinfo


@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def get_specific_log(request):
    modelo = int(request.GET.get('model'))
    try:
        associated_id = int(request.GET.get('associated_id'))
    except:
        return JsonResponse([], safe = False)

    logs = []
    primitive = Log.objects.filter(model = modelo, associated_id = associated_id, org_name=request.GET.get('org')).order_by('created_at')
    if modelo ==18:
        primitive =  Log.objects.filter(model__in = [modelo,1], associated_id = associated_id, org_name=request.GET.get('org')).order_by('created_at')
    if int(modelo) ==2:#físico
        nats = list(Contractor.objects.filter(type_person =1, org_name = request.GET.get('org')).values_list('pk', flat = True))
        primitive = primitive.filter(model = 26, associated_id__in = nats)
    elif int(modelo) ==3:#moral
        morl = list(Contractor.objects.filter(type_person =2, org_name = request.GET.get('org')).values_list('pk', flat = True))       
        primitive = primitive.filter(model = 26, associated_id__in = morl)        
    else:
        primitive = primitive
    
    for reg in primitive:
        email_log = LogEmail.objects.filter(log=reg).exists()
        obj = {
            "id": reg.id, 
            "date": reg.created_at,
            "msj": "El usuario " + reg.user.first_name +' '+ reg.user.last_name + ' ' + reg.identifier,
            "email_log": email_log,
            "original": reg.original,
            "change": reg.change,
            "update":reg.updated_at,
            "associated_id":reg.associated_id
        }

        logs.append(obj)
    return JsonResponse(logs, safe = False)



@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, ))
def change_user_type_access(request):
    username = request.data['username']
    tipo = request.data['type']

    user = User.objects.get(username = username)
    try:
        ui = UserInfo.objects.get(user = user)
        ui.user_type_access = int(tipo)
        ui.save()
    except:
        pass
    return JsonResponse({'status':'Done'})


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def CompleteTask(request):
    modelo = int(request.data['id'])
    task = Ticket.objects.get(pk = modelo)
    involvedUsers = Involved.objects.filter(involved = modelo)
    user = User.objects.get(username =request.user)
    if not task.closed:
        task.close_day = today = datetime.datetime.now()
        task.closed = True
        task.closedBy = user
        task.save()

        notification = Notifications.objects.create(
            model = 22,
            id_reference = task.id,
            title = "El usuario %s ha cerrado una tarea que creaste"%request.user.username ,
            description = task.descrip ,
            assigned = task.owner,
            involucrado = False,
            owner = request.user,
            org_name = task.org_name ,
        )
        notification.send_push_generic(request)
        for inv in involvedUsers:
            notification = Notifications.objects.create(
                model = 22,
                id_reference = task.id,
                title = "El usuario %s ha cerrado una tarea  en la que usted esta involucrado "%request.user.username ,
                description = task.descrip ,
                assigned = inv.person,
                involucrado = False,
                owner = request.user,
                org_name = task.org_name,
            )
            notification.send_push_generic(request)

    return JsonResponse({'Completed': True})
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
from django.shortcuts import get_object_or_404
class EmailInfoReminderViewSet(viewsets.ModelViewSet):
    serializer_class = EmailInfoReminderSerializer
    permission_classes = (IsAuthenticatedV2, EmailInfoPermissionsV2, IsOrgMemberV2)
    pagination_class = StandardResultsSetPagination

    def partial_update(self, request, pk=None):
        validate=False
        error=''
        try:
            remitente =request.data['remitente']
            domain=''
            if "@" in remitente:
                domain =remitente.split("@")[1]
            url = settings.MAILSERVICE + "smtpconfvalidate/validate_email"
            req = requests.get(url, params={'username':request.data['remitente'],'domain':domain}, headers={'Content-Type': 'application/json'} )
            validate = req.json()['success']
            error=req.json()['message']
            print("=> validate", str(req.json()),validate)
        except Exception as c:
            print('errorrrrrr***',c)
        queryset = EmailInfoReminder.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        serializer = EmailInfoReminderSerializer(cf, context={'request': request}, data=request.data, partial=True)
        # serializer = EmailInfoSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # return Response(serializer.data)
        return Response({"validate": validate,'error':error,"data": serializer.data},status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = EmailInfoReminder.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        serializer = EmailInfoReminderSerializer(cf, context={'request': request}, many = False)
        # serializer = EmailInfoSerializer(cf, context={'request': request}, many = False)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        validate = False
        error = ''
        try:
            remitente = request.data.get('remitente', '')
            domain = remitente.split("@")[1] if "@" in remitente else ''
            url = settings.MAILSERVICE + "smtpconfvalidate/validate_email"    
            req = requests.get(url,
                params={'username': remitente, 'domain': domain},
                headers={'Content-Type': 'application/json'})
            validate = req.json().get('success', False)
            error = req.json().get('message', '')
        except Exception as e:
            print("Error during validation:", e)
            error = "No se pudo validar el correo."
        remitenteok = remitente
        if not validate:
            try:
                org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
                response_org = org_.text
                org_data = json.loads(response_org)
                org_info = org_data['data']['org']
                if org_info:
                    remitente = org_info['email']
                    remitenteok = remitente
                    domain = remitente.split("@")[1] if "@" in remitente else ''
                    url = settings.MAILSERVICE + "smtpconfvalidate/validate_email"    
                    req = requests.get(url,
                        params={'username': remitente, 'domain': domain},
                        headers={'Content-Type': 'application/json'})
                    validate = req.json().get('success', False)
                    error = req.json().get('message', '')
                    error = error +' se guardará el de la Organización: '+str(remitenteok)
            except Exception as r:
                print('errrrrrrr',r)
        try:
            try:
                if request.data['model'] ==10:
                    request.data['remitente'] = remitenteok
            except:
                pass
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            EmailInfoReminder.objects.filter(
                org_name=request.GET.get('org'), model=request.POST.get('model')
            ).delete()
            obj = serializer.save(owner=request.user, org_name=request.GET.get('org'))
            response_serializer = EmailInfoReminderSerializer(obj, context={'request': request})
            return Response(
                {"validate": validate, "error": error, "data": response_serializer.data},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"validate": validate, "error": "Error.", "data": None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_queryset(self):
        model = self.request.GET.get('model')
        ids = [1, 3, 2]
        order = Case(*[When(relative_time=relative_time, then=pos) for pos, relative_time in enumerate(ids)])
        emailinfo = EmailInfoReminder.objects.filter(
            org_name=self.request.GET.get('org'),
            model=model
        ).order_by(order, '-days')
        paginator = Paginator(emailinfo, 10)
        try:
            page = self.request.data['page']
            results = paginator.page(page)
        except:
            results = paginator.page(1)
        return emailinfo

    def destroy(self, request, *args, **kwargs):
        EmailInfoReminder.objects.filter(org_name = self.request.GET.get('org'), **kwargs).delete()
        return Response("Deleted")

def export_users_xls(request):

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="users.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Recibos')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Recibo','Prima Total', 'Fecha Inicio', 'Póliza',]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    rows = Recibos.objects.filter(recibo_numero = 12).values_list('recibo_numero','prima_total', 'fecha_inicio', 'poliza__poliza_number')

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            if col_num == 2:
                font_style.num_format_str = 'DD/MM/YYYY'
                value = (row[col_num].replace(tzinfo=None))
            elif col_num == 1:
                font_style.num_format_str = '"$"#,##0.00_);("$"#,##'
                value = row[col_num]
            else:
                font_style.num_format_str = 'general'
                value = row[col_num]

            ws.write(row_num, col_num, value, font_style)

    wb.save(response)
    return response

class CedulaViewSet(viewsets.ModelViewSet):
    serializer_class = CedulaHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        try:
            serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))

    def get_queryset(self):
        return custom_get_queryset(self.request, Cedula)

class SucursalViewSet(viewsets.ModelViewSet):
    serializer_class = SucursalHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        try:
            serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))

    def get_queryset(self):
        return custom_get_queryset(self.request, Sucursales)

class SucursalShowViewSet(viewsets.ModelViewSet):
    serializer_class = SucursalFullSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def get_queryset(self):
        queryset = Sucursales.objects.filter(org_name =self.request.GET.get('org'))
        try:
            dataToFilter = getDataForPerfilRestricted(self.request, self.request.GET.get('org'))
        except Exception as er:
            dataToFilter = {}
        if dataToFilter:
            if dataToFilter['cspr'] and not dataToFilter['pspr']:
                queryset = queryset.filter(pk__in = list(dataToFilter['cspr']))
            if not dataToFilter['cspr'] and dataToFilter['pspr']:
                queryset = queryset.filter(pk__in = list(dataToFilter['pspr']))
            if dataToFilter['cspr'] and dataToFilter['pspr']:
                queryset = queryset.filter(Q(pk__in = list(dataToFilter['pspr'])) | Q(pk__in = list(dataToFilter['cspr'])))
        return queryset


class SucursalShowUnpagViewSet(viewsets.ModelViewSet):
    serializer_class = SucursalFullSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)
    pagination_class = None

    def get_queryset(self):
        queryset = Sucursales.objects.filter(org_name =self.request.GET.get('org'))
        try:
            dataToFilter = getDataForPerfilRestricted(self.request, self.request.GET.get('org'))
        except Exception as er:
            dataToFilter = {}
        if dataToFilter:
            if dataToFilter['cspr'] and not dataToFilter['pspr']:
                queryset = queryset.filter(pk__in = list(dataToFilter['cspr']))
            if not dataToFilter['cspr'] and dataToFilter['pspr']:
                queryset = queryset.filter(pk__in = list(dataToFilter['pspr']))
            if dataToFilter['cspr'] and dataToFilter['pspr']:
                queryset = queryset.filter(Q(pk__in = list(dataToFilter['pspr'])) | Q(pk__in = list(dataToFilter['cspr'])))
        return queryset

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        try:
            serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))

    def get_queryset(self):
        return custom_get_queryset(self.request, Ticket)

class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        now = datetime.datetime.now()
        curr_year = now.year
        Goals.objects.filter(org_name = self.request.GET.get('org'), created_at__year = curr_year).delete()
        obj = serializer.save(org_name = self.request.GET.get('org'))
        return obj

    def get_queryset(self):
        goal = Goals.objects.filter(org_name = self.request.GET.get('org'), created_at__year = curr_year)

        return goal[0]

class ExpensesViewSet(viewsets.ModelViewSet):
    serializer_class = ExpensesSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data, many = isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(org_name = self.request.GET.get('org'))
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        expenses = Expenses.objects.filter(org_name = self.request.GET.get('org'))

        return expenses

class TicketSaveViewSet(viewsets.ModelViewSet):
    serializer_class = SaveTicketHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):

        def create_identifier(obj):
            identifier = self.request.GET.get('org') + '%07d' % obj.id
            obj.identifier = identifier
            obj.save()

        obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        create_identifier(obj)

    def get_queryset(self):
        return custom_get_queryset(self.request, Ticket)
    
class TicketSaveViewSetMc(viewsets.ModelViewSet):
    serializer_class = SaveTicketHyperSerializerMc
    permission_classes = (AllowAny,)

    def perform_create(self, serializer):
        def create_identifier(obj):
            identifier = 'gpi' + '%07d' % obj.id
            obj.identifier = identifier
            obj.save()
        obj = serializer.save(owner=User.objects.get(username ='superuser_gpi'), org_name = 'gpi')
        create_identifier(obj)

   

class GetTickets(viewsets.ModelViewSet):
    serializer_class = FullTicketHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)
    def get_queryset(self):
        try:
            priority = int(self.request.GET.get('priority'))
        except Exception as ree:
            priority = 0
        closed = self.request.GET.get('closed')
        created = self.request.GET.get('created')
        assigned = self.request.GET.get('assigned')
        chain = self.request.GET.get('chain')
        archived = self.request.GET.get('archived')
        order = int(self.request.GET.get('order'))
        asc = int(self.request.GET.get('asc'))
        ver = int(self.request.GET.get('ver'))
        status = int(self.request.GET.get('status'))

        users = self.request.GET.getlist('users',0)
        try:
            fechahoy = self.request.GET.get('fechahoy')
        except:
            fechahoy=False

        session = Session.objects.filter(username=self.request.user.username)
        if session.exists():
            session = session.first()
        else:
            session = None
        

        ticketsR = Ticket.objects.filter(org_name = self.request.GET.get('org'))
        if users and len(users) > 0 and users != ['0']:
            ticketsR = ticketsR.filter(assigned__in = list(users))
        
        # aqui empieza filtro de another_tasks
        if session and session.another_tasks: # validar si puede ver las tareas de otros
            
            users_list = list(GroupManager.objects.filter(manager = self.request.user).values_list('user__username',flat=True))
            users_list.append(self.request.user.username)
        else:
            users_list = [self.request.user.username]
        # ------------------Ver solo involucrados, creador, asignado----------
        userfilter = [
            Q(owner__username__in = users_list),
            Q(assigned__username__in = users_list)
        ]
        ticketsR_filter = ticketsR.filter(reduce(OR, userfilter)).values_list('pk', flat = True)
        
        involvedTask = Involved.objects.filter(involved__in = ticketsR)
        userfilterI = [Q(person__username__in = users_list)]
        involvedTask_Filter = involvedTask.filter(reduce(OR, userfilterI)).values_list('involved', flat = True)       
        tkt = list(ticketsR_filter) + list(involvedTask_Filter)
        ticketsR = ticketsR.filter(pk__in = tkt)
        
        
        # ------------------Ver solo involucrados, creador, asignado----------        
        if int(priority) ==0 and int(closed) ==0 and int(created) ==0 and int(assigned) ==0 and (chain) ==0 and int(archived) ==0:
            involved = Involved.objects.filter(person__in = users_list).values_list('involved',flat = True)
            # ticketsR = Ticket.objects.filter(pk__in = involved, org_name = self.request.GET.get('org')).exclude(archived = True).exclude(closed = True)
            ticketsR = Ticket.objects.filter(pk__in = involved, org_name = self.request.GET.get('org'))
            try:
                fechahoy = self.request.GET.get('fechahoy')
                if fechahoy ==True or fechahoy =='true':                    
                    aux_month = datetime.datetime.today().month
                    aux_day = datetime.datetime.today().day
                    aux_year = datetime.datetime.today().year
                    # date__month = aux_month, date__day = aux_day
                    ticketsR = ticketsR.filter(date__month = aux_month, date__day = aux_day,date__year=aux_year)
            except:
                fechahoy=False
            return ticketsR      

        
        # aqui termina filtro de another_tasks

        # Filtros combinables
        if priority != 0:
            # ticketsR = ticketsR.filter(org_name = self.request.GET.get('org'), priority = priority).exclude(archived = True).exclude(closed = True)
            ticketsR = ticketsR.filter( priority = priority)

        if status == 4:
            ticketsR = ticketsR.filter( closed = True)

        if status == 8:
            ticketsR = ticketsR.filter( archived = True)
        if int(status) == 11 or int(status) == 0:
            # ticketsR = ticketsR.filter(closed = False).exclude(archived = True)
            ticketsR = ticketsR.filter(closed = False)

        if int(ver) == 0:
            ticketsR = ticketsR

        if int(ver) == 5:
            # ticketsR = ticketsR.filter( assigned =  self.request.user).exclude(archived = True).exclude(closed = True)
            ticketsR = ticketsR.filter( assigned__username__in =  users_list) # aqui va un filtro de another_tasks

        if int(ver) == 6:
            # ticketsR = ticketsR.filter( owner= users_list).exclude(archived = True).exclude(closed = True)
            ticketsR = ticketsR.filter( owner__username__in= users_list)  # aqui va un filtro de another_tasks

        # if int(ver) == 10:
        #     # ticketsR = ticketsR.filter(closed = False).exclude(archived = True)
        #     ticketsR = ticketsR.filter(closed = False)
        if chain:
            if not chain == '0':
                contains_filter = [Q(identifier__icontains = chain),
                                   Q(descrip__icontains = chain),
                                   Q(title__icontains = chain),
                                   Q(owner__first_name__icontains = chain),
                                   Q(owner__last_name__icontains = chain)]
                # ticketsR = ticketsR.filter(reduce(OR, contains_filter), org_name = self.request.GET.get('org')).exclude(archived = True)
                ticketsR = ticketsR.filter(reduce(OR, contains_filter))

        if order == 1:
            if asc == 1:
                ticketsR = ticketsR.order_by('identifier')
            else:
                ticketsR = ticketsR.order_by('-identifier')
        elif order == 2:
            if asc == 1:
                ticketsR = ticketsR.order_by('title')
            else:
                ticketsR = ticketsR.order_by('-title')
        elif order == 3:
            if asc == 1:
                ticketsR = ticketsR.order_by('date')
            else:
                ticketsR = ticketsR.order_by('-date')
        elif order == 4:
            if asc == 1:
                ticketsR = ticketsR.order_by('priority')
            else:
                ticketsR = ticketsR.order_by('-priority')
        elif order == 5:
            if asc == 1:
                ticketsR = ticketsR.order_by('assigned__last_name','assigned__first_name')
            else:
                ticketsR = ticketsR.order_by('-assigned__last_name','-assigned__first_name')
        elif order == 6:
            if asc == 1:
                ticketsR = ticketsR.order_by('owner__last_name','owner__first_name')
            else:
                ticketsR = ticketsR.order_by('-owner__last_name','owner__first_name')
        else:
            ticketsR = ticketsR
        try:
            fechahoy = self.request.GET.get('fechahoy')
            if fechahoy ==True or fechahoy =='true':                    
                aux_month = datetime.datetime.today().month
                aux_day = datetime.datetime.today().day
                aux_year = datetime.datetime.today().year
                # date__month = aux_month, date__day = aux_day
                ticketsR = ticketsR.filter(date__month = aux_month, date__day = aux_day,date__year=aux_year)
        except:
            fechahoy=False
        return ticketsR



@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def getEmailsUsers(request):
    userinfo = UserInfo.objects.filter(org_name = request.GET.get('org'))
    receiver = []
    for user in userinfo:
        if user.user.email and user.user.is_superuser == False and user.user.is_active == True:
            receiver.append(user.user.email)

    return JsonResponse({'emails':receiver})



from email.mime.image import MIMEImage
import os
from django.template.loader import render_to_string
from django.core.mail import EmailMessage,EmailMultiAlternatives
@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def sendHistoricEmail(request):
    id_tarea = request.data['id_tarea']
    email = request.data['email']
    email_x = request.data['type_email']
    if email_x == 2:
        email_multiples = request.data['emails_selected']
    else:
        email_multiples = []

    tarea = Ticket.objects.get(pk = int(id_tarea))
    comentarios = Comments.objects.filter(model = 22, id_model = tarea.id, parent__isnull = True)

    comentarios_serialized = CommentHyperSerializer(comentarios, context = {'request':request}, many = True)
    tarea_serialized = TicketSerializer(tarea, context = {'request':request}, many = False)
    from_email= '<no-reply@miurabox.com>'
    subject='Historico de tarea \"%s\"'%tarea.title

    message=render_to_string("send_historic_email.html",{'comentarios':comentarios_serialized.data, 'tarea':tarea})

    # GET ORG INFO
    org_info = get_org_info(request)
    # Sendgrit Piloto test
    if request.user.email:
        remitente = "{} <{}>".format(org_info['name'], request.user.email)
    elif org_info['email']:
        remitente = "{} <{}>".format(org_info['name'], org_info['email'])
    else:
        remitente = "{} <no-reply@miurabox.com>".format(org_info['name'])

    if email_x == 1:
        email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email, cc=[request.user.email])
    elif email_x == 2:
        email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_multiples, cc=[request.user.email])



    email.content_subtype="html"
    email.mixed_subtype = 'related'
    # print(tarea_serialized.data['archivos_ticket'])


    for f in tarea_serialized.data['archivos_ticket']:
        response = requests.get(f['arch'])
        if response.status_code == 200:
            with open(f['nombre'], 'wb') as file:
                file.write(response.content)
                fp = open(os.path.join(os.path.dirname('..'), f['nombre'] ), 'rb')
                fp.close()
                email.attach_file(os.path.join(os.path.dirname('..'), f['nombre'] ))
                os.remove(f['nombre'])
    email.send()

    # if files:
    #     for file in files:
    #         os.remove(file.nombre)
    return JsonResponse({'status':'send'})

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def ReporteTaskToExcel(request):

    # priority = request.data['priority']
    priority = int(request.data['priority'])
    closed = request.data['closed']
    created = request.data['created']
    assigned = request.data['assigned']
    try:
        chain = request.data['chain']
    except Exception as r:
        chain = '0'
    archived = request.data['archived']
    order = int(request.data['order'])
    asc = int(request.data['asc'])
    ver = int(request.data['ver'])
    status = int(request.data['status'])
    ticketsR = Ticket.objects.filter(org_name = request.GET.get('org'))

    # ------------------Ver solo involucrados, creador, asignado----------
    userfilter = [Q(owner__username = request.user),
                   Q(assigned__username = request.user),]
    ticketsR_filter = ticketsR.filter(reduce(OR, userfilter), org_name = request.GET.get('org')).values_list('pk', flat = True)
    involvedTask = Involved.objects.filter(involved__in = ticketsR)
    userfilterI = [Q(person__username = request.user)]
    involvedTask_Filter = involvedTask.filter(reduce(OR, userfilterI)).values_list('involved', flat = True)       
    tkt = list(ticketsR_filter) + list(involvedTask_Filter)
    ticketsR = ticketsR.filter(pk__in = tkt)
    # ------------------Ver solo involucrados, creador, asignado---------- 
    # Filtros combinables
    if priority != 0:
        # ticketsR = ticketsR.filter(org_name = request.GET.get('org'), priority = priority).exclude(archived = True).exclude(closed = True)
        ticketsR = ticketsR.filter(org_name = request.GET.get('org'), priority = priority)


    if status == 4:
        ticketsR = ticketsR.filter(org_name = request.GET.get('org'), closed = True)

    if status == 8:
        ticketsR = ticketsR.filter(org_name = request.GET.get('org'), archived = True)
    if int(status) == 11 or int(status) == 0:
        ticketsR = ticketsR.filter(org_name = request.GET.get('org'),closed = False)


    if int(ver) == 0:
        ticketsR = ticketsR

    if int(ver) == 5:
        # ticketsR = ticketsR.filter(org_name = request.GET.get('org'), assigned =  request.user).exclude(archived = True).exclude(closed = True)
        ticketsR = ticketsR.filter(org_name = request.GET.get('org'), assigned =  request.user)

    if int(ver) == 6:
        # ticketsR = ticketsR.filter(org_name = request.GET.get('org'), owner = request.user).exclude(archived = True).exclude(closed = True)
        ticketsR = ticketsR.filter(org_name = request.GET.get('org'), owner = request.user)

    # if int(ver) == 10:
    #     # ticketsR = ticketsR.filter(org_name = request.GET.get('org'),closed = False).exclude(archived = True)
    #     ticketsR = ticketsR.filter(org_name = request.GET.get('org'),closed = False)
    if chain:
        if not chain == '0':
            contains_filter = [Q(identifier__icontains = chain),
                               Q(descrip__icontains = chain),
                               Q(title__icontains = chain),
                               Q(owner__first_name__icontains = chain),
                               Q(owner__last_name__icontains = chain)]
            # ticketsR = ticketsR.filter(reduce(OR, contains_filter), org_name = request.GET.get('org')).exclude(archived = True)
            ticketsR = ticketsR.filter(reduce(OR, contains_filter), org_name = request.GET.get('org'))

    tickets = ticketsR
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Tareas.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reporte Tareas')
    info_org = getInfoOrg(request)

    if len(info_org['logo']) != 0:
      archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + info_org['logo']
    else:
      archivo_imagen = 'saam.jpg'
    if info_org['urlname'] != 'basanez':
        try:
            img = Image.open(requests.get(archivo_imagen, stream=True).raw)
            r, g, b = img.split()
            img = Image.merge("RGB", (r, g, b))
            img = img.resize((130,150),Image.ANTIALIAS)
            name_logo = info_org['urlname']+'_logo.bmp'
            img.save(name_logo)
            ws.insert_bitmap(name_logo, 0, 0)
        except Exception as e:
            img = Image.open("saam.jpg")
            r, g, b = img.split()
            img = Image.merge("RGB", (r, g, b))
            img.save('imagetoadd.bmp')
            ws.insert_bitmap('imagetoadd.bmp', 0, 0)
            # print(info_org)

    # info_org = getInfoOrg(request)
    # print(info_org)

    company_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    company_style.pattern = pattern
    company_style = xlwt.easyxf('font: bold on, color black, height 380;\
                   pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(0, 5, info_org['name'], company_style)

    text_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    text_style.pattern = pattern
    text_style = xlwt.easyxf('font: bold off, color black;\
                   pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(1, 5, info_org['address'], text_style)
    ws.write(3, 5, "Tel." + info_org['phone'], text_style)
    ws.write(4, 5, info_org['email'], text_style)
    ws.write(5, 5, info_org['webpage'], text_style)

    title_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    title_style.pattern = pattern
    title_style = xlwt.easyxf('font: bold on, color black, height 280;\
                   pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(8, 5,"Reporte de tareas ", title_style)
    row_num = 10
    font_style = xlwt.XFStyle()
    font_style.font.bold = True


    columns = ['Identificador','Titulo','Fecha','Prioridad','Concepto','Descripción','Asignada a','Creada por','Estatus','Antiguedad']

    for col_num in range(len(columns)):
        style = xlwt.XFStyle()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        # print( xlwt.Style.colour_map)
        style = xlwt.easyxf('font: bold on, color black;\
                       borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;\
                       pattern: pattern solid, fore_color ice_blue; align: horiz center')
        ws.write(row_num, col_num, columns[col_num], style)

    rows = tickets.values_list('identifier', 'title', 'date','priority','concept','descrip','assigned__first_name',
        'assigned__last_name','owner__first_name','owner__last_name','created_at','closed')


    for row in rows:
        row_num += 1
        for col_num in range(10):
            font_style.font.bold = False
            if col_num == 0:
                font_style.num_format_str = 'general'
                value = row[col_num]
            elif col_num == 1:
                value = (row[col_num])
            elif col_num == 2:
                try:
                    font_style.num_format_str = 'DD/MM/YYYY'
                    value = (row[col_num].replace(tzinfo=None))
                except:
                    value = row[col_num]
            elif col_num == 3:
                value = checkPriority(row[col_num])
            elif col_num == 4:
                value = checkConcept(row[col_num])
            elif col_num == 5:
                value = row[col_num]
            elif col_num == 6:
                value = row[col_num] + ' ' + row[7]
            elif col_num == 7:
                value = row[8] + ' '+row[9]
            elif col_num == 8:
                if row[11]:
                    value = 'Cerrada'
                else:
                    value = 'Activa'
            elif col_num == 9:
                font_style.num_format_str = 'general'
                today = date.today()
                a = arrow.get(today)
                aux_date = row[10]
                b = arrow.get(aux_date)
                antiguedad = (a-b).days
                antiguedad = int(antiguedad)+1
                value = antiguedad

            else:
                font_style.num_format_str = 'general'
                value = row[col_num]

            try:
                ws.write(row_num, col_num, value, font_style)
            except Exception as e:
                value = (row[col_num])
                ws.write(row_num, col_num, value, font_style)

    final_row = int(row_num) + 2
    title = "Total: " + str(len(rows)) + " Registros"
    font_style = xlwt.easyxf('font: bold off, color black;\
                     pattern: pattern solid, fore_color white;')
    ws.write(final_row, 0, title, font_style)

    wb.save(response)
    return response
def checkPriority(request):
    switcher = {
        1: "Alta",
        2: "Media",
        3: "Baja",
    }
    return switcher.get(request, "")
def checkConcept(request):
    switcher = {
        1: "Cotización",
        2: "Emisión",
        4: "Corrección",
        5: "Cancelación",
        6: "Renovación",
        7: "Otro",
    }
    return switcher.get(request, "")


def getInfoOrg(request):
    org_ = requests.get(settings.CAS2_URL + 'get-org-info/'+request.META['user']['org']['name'],verify=False)
    response_org= org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    return org_info

class NotificationsViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationstHyperSerializer
    queryset = Notifications.objects.all()
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        if self.request.data['model'] == 26:
            obj = serializer.save(org_name = self.request.GET.get('org'), assigned = self.request.user, owner = self.request.user)   
        else:
            obj = serializer.save(org_name = self.request.GET.get('org'), owner = self.request.user)  
        if  self.request.data['model'] == 27 and obj.type_notification ==1:
            users_to_notification = getUserNotification(obj, self.request)
            imagen = NotificationFile.objects.filter(owner = obj, org_name = obj.org_name)
            if users_to_notification:
                import firebase_admin
                from firebase_admin import credentials
                from firebase_admin import messaging 
                for usnot in users_to_notification:              
                    if not firebase_admin._apps:
                        cred = credentials.Certificate("core/ancora-bb4dd-firebase-adminsdk-uz4n7-ff6aa3d29b.json")
                        firebase_admin.initialize_app(cred)
                    # The topic name can be optionally prefixed with "/topics/".
                    # See documentation on defining a message payload.
                    # solo notificacion si promocion en archivos notifications
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=obj.title,
                            body=obj.description,
                            image= ''
                        ),
                        data={
                            "title":"notification_to_app",
                            "message":obj.description,
                            "there_is_notify":'true'
                        },
                        topic=usnot.username
                    )
                    # Send a message to the devices subscribed to the provided topic.
                    response = messaging.send(message)
                    # Response is a message ID string.

            # return Response(response)


    def get_queryset(self):
        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(1)
        today_start = datetime.datetime.combine(today, datetime.time())
        today_end = datetime.datetime.combine(tomorrow, datetime.time())

        return Notifications.objects.filter(org_name = self.request.GET.get('org'),assigned = self.request.user, created_at__gte = today_start, created_at__lte = today_end).order_by('-id')

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def NotificationsCount(request):
    today = datetime.datetime.now().date()
    tomorrow = today + datetime.timedelta(1)
    today_start = datetime.datetime.combine(today, datetime.time())
    today_end = datetime.datetime.combine(tomorrow, datetime.time())
    count =len(Notifications.objects.filter(org_name = request.GET.get('org'),seen = False, assigned = request.user, created_at__gte = today_start, created_at__lte = today_end).order_by('-id'))
    count_rec =len(Notifications.objects.filter(org_name = request.GET.get('org'),model =31,seen = False, assigned = request.user, created_at__gte = today_start, created_at__lte = today_end).order_by('-id'))
    datos =Notifications.objects.filter(model =31,org_name = request.GET.get('org'), assigned = request.user, created_at__gte = today_start, created_at__lte = today_end).order_by('-id')
    count31 =len(Notifications.objects.filter(org_name = request.GET.get('org'),seen = False, assigned = request.user, created_at__gte = today_start, created_at__lte = today_end).order_by('-id'))
    nots = []
    if datos:
        serializer = NotificationsAppHyperSerializer(datos, context = {'request':request}, many = True)
        nots = serializer.data
    # return Response(len(Notifications.objects.filter(org_name = request.GET.get('org'),seen = False, assigned = request.user, created_at__gte = today_start, created_at__lte = today_end).order_by('-id')))
    return JsonResponse({'data':count, 'datos':nots,'count31':count31,'recordatorios':count_rec})

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def NotificationsTest(request):
    today = datetime.datetime.now().date()
    tomorrow = today + datetime.timedelta(1)
    today_start = datetime.datetime.combine(today, datetime.time())
    today_end = datetime.datetime.combine(tomorrow, datetime.time())
    nots = Notifications.objects.filter(
        org_name = request.GET.get('org'),
        # seen = False, 
        assigned = request.user, 
        created_at__gte = today_start, 
        created_at__lte = today_end
    ).order_by('-id')
    nots_recordatorios = Notifications.objects.filter(
        org_name = request.GET.get('org'),
        model=31, 
        assigned = request.user, 
        created_at__gte = today_start, 
        created_at__lte = today_end
    ).order_by('-id')
    try:
        serializer = NotificationsAppHyperSerializer(nots, context = {'request':request}, many = True)
        return JsonResponse({'results': serializer.data, 'count': len(nots), 'recordatorios': len(nots_recordatorios)})
    except Exception as e:
        return Response({'error': 321})

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def NotificationsApp(request):
    today = datetime.datetime.now().date()
    tomorrow = today + datetime.timedelta(1)
    today_start = datetime.datetime.combine(today, datetime.time())
    today_end = datetime.datetime.combine(tomorrow, datetime.time())
    org_name = request.GET.get('org')
    if org_name == 'ancora' or org_name == 'pruebas':        
        # nots =Notifications.objects.filter(org_name = request.GET.get('org'), created_at__gte = today_start, created_at__lte = today_end, owner__in = list(usersapp)).order_by('-id')
        nots = Notifications.objects.filter(org_name = request.GET.get('org'), model = 27).order_by('-id')
        try:
            serializer = NotificationsAppHyperSerializer(nots, context = {'request':request}, many = True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': 321})
    else:        
        return Response({'error': 321})
    # return Response(len(Notifications.objects.filter(org_name = request.GET.get('org'),seen = False, assigned = request.user, created_at__gte = today_start, created_at__lte = today_end).order_by('-id')))

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, KBIPermissionV2  ))
def KBI(request):
    now = datetime.datetime.now()
    try:
        now = int(request.data['until_year'])
        curr_year = int(request.data['until_year'])
        dic31 = '31/12/'+str(now)+' 23:59:59'
        f = "%d/%m/%Y %H:%M:%S"     
        date31 = datetime.datetime.strptime(dic31 , f)
        ene01_c_eh = '01/01/'+str(now)+' 00:00:00'
        date01_ehoy = datetime.datetime.strptime(ene01_c_eh , f)
        #anterior     
        anterior_dic31 = '31/12/'+str(int(now)-1)+' 23:59:59'   
        anterior_date31 = datetime.datetime.strptime(anterior_dic31 , f)
        anterior_ene01_c_eh = '01/01/'+str(int(now)-1)+' 00:00:00'
        anterior_date01_ehoy = datetime.datetime.strptime(anterior_ene01_c_eh , f)
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year
        dic31 = '31/12/'+str(now.year)+' 23:59:59'
        f = "%d/%m/%Y %H:%M:%S"     
        date31 = datetime.datetime.strptime(dic31 , f)
        ene01_c_eh = '01/01/'+str(now.year)+' 00:00:00'
        date01_ehoy = datetime.datetime.strptime(ene01_c_eh , f)
        #anterior
        anterior_dic31 = '31/12/'+str(now.year-1)+' 23:59:59'        
        anterior_date31 = datetime.datetime.strptime(anterior_dic31 , f)
        anterior_ene01_c_eh = '01/01/'+str(now.year-1)+' 00:00:00'
        anterior_date01_ehoy = datetime.datetime.strptime(anterior_ene01_c_eh , f)
    anio_anterior = curr_year -1   
    # Comisones de enero (año actual) a la fecha
    #**********************----------------************************
    org = request.GET.get('org')
    users = list(User.objects.values_list('pk', flat=True))
    providers = list(Provider.objects.filter(org_name = org).values_list('pk', flat=True))
    cves = list(Claves.objects.filter(org_name = org).values_list('pk', flat=True))
    bonos = Bonos.objects.filter(org_name = org, 
                                     aseguradora__in = providers,
                                     clave__in = cves,
                                     owner__in = users)
    ramos = list(Ramos.objects.filter(org_name = org, provider__in = providers).values_list('pk', flat=True))
    subramos = list(SubRamos.objects.filter(org_name = org, ramo__in = ramos).values_list('pk', flat=True))
    polizas = Polizas.objects.filter(org_name = org,
                                         aseguradora__in = providers,
                                         ramo__in = ramos,
                                         subramo__in = subramos,
                                         clave__in = cves,
                                         owner__in = users).exclude(status__in = [1,2,0]).exclude(document_type__in = [2,6,10])
    parents = polizas.filter(document_type = 3)
    subgrupos = Polizas.objects.filter(parent__id__in = parents.values_list('pk', flat = True), document_type = 4, org_name = org).values_list('id', flat = True)
    recibos1 = Recibos.objects.filter(Q(poliza__id__in = polizas) | Q(bono__id__in = bonos) | Q(poliza__in = subgrupos),
                                         isActive = True, 
                                         isCopy = False,
                                         org_name = request.GET.get('org')).exclude(status__in = [0,7,2]).filter(receipt_type__in = [1,2,3,4])
    recibos_solo = Recibos.objects.filter(Q(poliza__id__in = polizas) | Q(bono__id__in = bonos) | Q(poliza__in = subgrupos),
                                         isActive = True, 
                                         isCopy = False,
                                         org_name = request.GET.get('org')).exclude(status__in = [0]).filter(receipt_type__in = [1,2,3,4])
        
    #                       ***********************----------------************************
    st = [1,2,4,10,11,12,13,14,15]
    policies = Polizas.objects.filter(status__in = st, 
        org_name = request.GET.get('org'),
        ramo__in = ramos, 
        subramo__in = subramos, 
        aseguradora__in = providers,
        clave__in = cves,
        owner__in = users,start_of_validity__year = curr_year)
    anterior_policies = Polizas.objects.filter(status__in = st, 
        org_name = request.GET.get('org'),
        ramo__in = ramos, 
        subramo__in = subramos, 
        aseguradora__in = providers,
        clave__in = cves,
        owner__in = users,start_of_validity__year = anio_anterior)
    recibos_actual = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__year = curr_year).filter(poliza__f_currency =1)
    new_recibos_actual = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = date01_ehoy, fecha_inicio__lte = date31).exclude(poliza__document_type = 2).exclude(poliza__status = 0).filter(poliza__f_currency =1)
    new_rec_all_enero_hoy = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = date01_ehoy, fecha_inicio__lte = date31).filter(poliza__f_currency =1).exclude(poliza__status = 0)
    #ANTERIOR
    anterior_recibos_actual = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__year = anio_anterior).filter(poliza__f_currency =1)
    anterior_new_recibos_actual = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = anterior_date01_ehoy, fecha_inicio__lte = anterior_date31).exclude(poliza__document_type = 2).exclude(poliza__status = 0).filter(poliza__f_currency =1)
    anterior_new_rec_all_enero_hoy = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = anterior_date01_ehoy, fecha_inicio__lte = anterior_date31).filter(poliza__f_currency =1).exclude(poliza__status = 0)
    try:
        your_date_string = request.data['until_day']
        format_string = "%d/%m/%Y"
        datetime_object = datetime.datetime.strptime(your_date_string, format_string).date()
        new_date = datetime_object - relativedelta(years=1)
        anterior_untilDay = datetime.datetime.strftime(new_date, format_string).replace(' 0', ' ')
        antsinceDay = request.data['since_day']
        antsinceDay = datetime.datetime.strptime(antsinceDay, format_string).date()
        antsinceDay = antsinceDay - relativedelta(years=1)
        anterior_sinceDay = datetime.datetime.strftime(antsinceDay, format_string).replace(' 0', ' ')
        f1 = "%d/%m/%Y %H:%M:%S"     
        anterior_untilDay = str(anterior_untilDay)+' 23:59:59'
        anterior_untilDay = datetime.datetime.strptime(anterior_untilDay , f)
        anterior_sinceDay = str(anterior_sinceDay)+' 00:00:00'
        anterior_sinceDay = datetime.datetime.strptime(anterior_sinceDay , f)
        anterior_recibosProduccion = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = anterior_sinceDay, fecha_inicio__lte = anterior_untilDay).filter(poliza__f_currency =1).exclude(poliza__status = 0)
        anterior_log_actual = Log.objects.filter(org_name = request.GET.get('org'), created_at__gte = anterior_sinceDay, created_at__lte = anterior_untilDay)
    except Exception as et:
        anterior_recibosProduccion = anterior_new_rec_all_enero_hoy
        anterior_log_actual = Log.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)
        print('et----error fechas ant--',et)
        anterior_untilDay = ''
        anterior_sinceDay = ''
    # fecha inicio
    try:
        until_day = request.data['until_day']
        since_day = request.data['since_day']
        f1 = "%d/%m/%Y %H:%M:%S"     
        untilDay = str(until_day)+' 23:59:59'
        untilDay = datetime.datetime.strptime(untilDay , f)
        sinceDay = str(since_day)+' 00:00:00'
        sinceDay = datetime.datetime.strptime(sinceDay , f)
        recibosProduccion = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = sinceDay, fecha_inicio__lte = untilDay).filter(poliza__f_currency =1).exclude(poliza__status = 0)
        log_actual = Log.objects.filter(org_name = request.GET.get('org'), created_at__gte = sinceDay, created_at__lte = untilDay)
    except Exception as err:
        recibosProduccion = new_rec_all_enero_hoy
        log_actual = Log.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)
    # Aseguradoras y Subramos
    policies1 = Polizas.objects.filter(status__in = st, org_name = request.GET.get('org'),ramo__in = ramos, subramo__in = subramos, aseguradora__in = providers,
        clave__in = cves, owner__in = users, f_currency = 1)
    polizasProduccion = policies1.filter(Q(start_of_validity__gte=sinceDay),Q(start_of_validity__lte = untilDay), f_currency = 1, document_type__in =[1,3,11,12])
    anterior_polizasProduccion = policies1.filter(Q(start_of_validity__gte=anterior_sinceDay),Q(start_of_validity__lte = anterior_untilDay), f_currency = 1, document_type__in =[1,3,11,12])
    new_serializer_aseg = polizasProduccion.values('aseguradora__alias').annotate(Sum('p_neta')).order_by('aseguradora__alias')
    new_serializer_aseg_pagado = recibosProduccion.filter(status__in=[1,5,6]).values('poliza__aseguradora__alias').annotate(Sum('prima_neta')).order_by('poliza__aseguradora__alias')
    anterior_new_serializer_aseg = anterior_polizasProduccion.values('aseguradora__alias').annotate(Sum('p_neta')).order_by('aseguradora__alias')
    anterior_new_serializer_aseg_pagado = anterior_recibosProduccion.filter(status__in=[1,5,6]).values('poliza__aseguradora__alias').annotate(Sum('prima_neta')).order_by('poliza__aseguradora__alias')
    for t in anterior_new_serializer_aseg:
        for y in anterior_new_serializer_aseg_pagado:
            if t['aseguradora__alias'] == y['poliza__aseguradora__alias']:
                t['pagado'] = y['prima_neta__sum']
    for t in new_serializer_aseg:
        for y in new_serializer_aseg_pagado:
            if t['aseguradora__alias'] == y['poliza__aseguradora__alias']:
                t['pagado'] = y['prima_neta__sum']
    new_serializer_subramos = recibosProduccion.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    new_serializer_subramos = recibosProduccion.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    anterior_new_serializer_subramos = anterior_recibosProduccion.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    anterior_new_serializer_subramos = anterior_recibosProduccion.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    
    new_serializer_subramos = polizasProduccion.values('subramo__subramo_name').annotate(Sum('p_neta')).order_by('subramo__subramo_code')
    new_serializer_subramos_pagado = recibosProduccion.filter(status__in=[1,5,6]).values('poliza__subramo__subramo_name').annotate(Sum('prima_neta')).order_by('poliza__subramo__subramo_code')
    for t in new_serializer_subramos:
        for y in new_serializer_subramos_pagado:
            if t['subramo__subramo_name'] == y['poliza__subramo__subramo_name']:
                t['pagado'] = y['prima_neta__sum']
    
    anterior_new_serializer_subramos = anterior_polizasProduccion.values('subramo__subramo_name').annotate(Sum('p_neta')).order_by('subramo__subramo_code')
    anterior_new_serializer_subramos_pagado = anterior_recibosProduccion.filter(status__in=[1,5,6]).values('poliza__subramo__subramo_name').annotate(Sum('prima_neta')).order_by('poliza__subramo__subramo_code')
    for t in anterior_new_serializer_subramos:
        for y in anterior_new_serializer_subramos_pagado:
            if t['subramo__subramo_name'] == y['poliza__subramo__subramo_name']:
                t['pagado'] = y['prima_neta__sum']
    
    # Ejecutivos
    serializer_ejecutivos = log_actual.values('user__first_name', 'user__last_name').annotate(Count('user'))
    anterior_serializer_ejecutivos = anterior_log_actual.values('user__first_name', 'user__last_name').annotate(Count('user'))
    # Bateo y cotización
    total_cotizaciones = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year).count()
    bateadas = Cotizacion.objects.filter(org_name = request.GET.get('org'), status = 3, created_at__year = curr_year).count()
    anterior_total_cotizaciones = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = int(curr_year)-1).count()
    anterior_bateadas = Cotizacion.objects.filter(org_name = request.GET.get('org'), status = 3, created_at__year = int(curr_year)-1).count()
    if total_cotizaciones:
        serializer_bateo = (bateadas * 100) / total_cotizaciones
    else:
        serializer_bateo = 0
    if anterior_total_cotizaciones:
        anterior_serializer_bateo = (anterior_bateadas * 100) / anterior_total_cotizaciones
    else:
        anterior_serializer_bateo = 0
    # Comisiones
    try:
        now = int(request.data['until_year'])
        dic31_com = '31/12/'+str(now)+' 23:59:59'
        ene01_com = '01/01/'+str(now)+' 00:00:00'
        anterior_dic31_com = '31/12/'+str(now-1)+' 23:59:59'
        anterior_ene01_com = '01/01/'+str(now-1)+' 00:00:00'
    except Exception as e:
        dic31_com = '31/12/'+str(now.year)+' 23:59:59'
        ene01_com = '01/01/'+str(now.year)+' 00:00:00'
        anterior_dic31_com = '31/12/'+str(now.year-1)+' 23:59:59'
        anterior_ene01_com = '01/01/'+str(now.year-1)+' 00:00:00'
    f = "%d/%m/%Y %H:%M:%S"     
    date31_com = datetime.datetime.strptime(dic31_com , f)
    date01_com = datetime.datetime.strptime(ene01_com , f)
    anterior_date31_com = datetime.datetime.strptime(anterior_dic31_com , f)
    anterior_date01_com = datetime.datetime.strptime(anterior_ene01_com , f)
    new_recibos_enero_hoy = recibos1.filter(org_name = request.GET.get('org'),status__in = [1,5,6], fecha_inicio__gte = date01_com, fecha_inicio__lte = date31_com).filter(poliza__f_currency =1).exclude(poliza__status = 0)
    new_comision_neta = new_recibos_enero_hoy.exclude(receipt_type=3).aggregate(Sum('comision'))
    #anterior
    anterior_new_recibos_enero_hoy = recibos1.filter(org_name = request.GET.get('org'),status__in = [1,5,6], fecha_inicio__gte = anterior_date01_com, fecha_inicio__lte = anterior_date31_com).filter(poliza__f_currency =1).exclude(poliza__status = 0)
    anterior_new_comision_neta = anterior_new_recibos_enero_hoy.exclude(receipt_type=3).aggregate(Sum('comision'))

    comision_perdida = recibos_solo.filter(status__in =[2,8] ,receipt_type = 3, poliza__f_currency =1, fecha_inicio__gte = date01_ehoy, fecha_inicio__lte = date31).aggregate(Sum('comision'))
    anterior_comision_perdida = recibos_solo.filter(status__in =[2,8] ,receipt_type = 3, poliza__f_currency =1, fecha_inicio__gte = anterior_date01_ehoy, fecha_inicio__lte = anterior_date31).aggregate(Sum('comision'))
    new1 = new_recibos_actual.filter(receipt_type = 3).exclude(status = 0).aggregate(Sum('prima_total'))
    notas_total = recibos_actual.filter(receipt_type = 3).exclude(status = 0).aggregate(Sum('prima_total'))
    new_total_recibir = new_recibos_actual.filter(status__in = [4,3]).exclude(receipt_type =3).aggregate(Sum('comision'))

    anterior_new1 = anterior_new_recibos_actual.filter(receipt_type = 3).exclude(status = 0).aggregate(Sum('prima_total'))
    anterior_notas_total = anterior_recibos_actual.filter(receipt_type = 3).exclude(status = 0).aggregate(Sum('prima_total'))
    anterior_new_total_recibir = anterior_new_recibos_actual.filter(status__in = [4,3]).exclude(receipt_type =3).aggregate(Sum('comision'))
    # Primas
    new_pagados_total = new_recibos_enero_hoy.filter(status__in = [1,5,6]).aggregate(Sum('prima_neta'))
    new_pendientes_total = new_recibos_actual.filter(status__in = [4,3]).exclude(receipt_type = 3).aggregate(Sum('prima_total'))
    emitidas_cancel = policies.filter(status__in = [11,4], f_currency = 1).aggregate(Sum('p_neta'))
    total_total = recibos_actual.aggregate(Sum('prima_neta'))
    new_total_total = new_recibos_enero_hoy.aggregate(Sum('prima_neta'))    
    
    anterior_new_pagados_total = anterior_new_recibos_enero_hoy.filter(status__in = [1,5,6]).aggregate(Sum('prima_neta'))
    anterior_new_pendientes_total = anterior_new_recibos_actual.filter(status__in = [4,3]).exclude(receipt_type = 3).aggregate(Sum('prima_total'))
    anterior_emitidas_cancel = anterior_policies.filter(status__in = [11,4], f_currency = 1).aggregate(Sum('p_neta'))
    anterior_total_total = anterior_recibos_actual.aggregate(Sum('prima_neta'))
    anterior_new_total_total = anterior_new_recibos_enero_hoy.aggregate(Sum('prima_neta'))    

    meta = Goals.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)
    anterior_meta = Goals.objects.filter(org_name = request.GET.get('org'), created_at__year = int(curr_year)-1)
    # Meta
    if meta:
        if new_total_total['prima_neta__sum']:
            new_total_total['prima_neta__sum'] = new_total_total['prima_neta__sum']
        else:
            new_total_total['prima_neta__sum'] = 0
        new_metas = {
            'value': float(meta[0].goal) if meta[0].goal else 0,
            'progress': float(new_total_total['prima_neta__sum']),
            'remain': str(meta[0].goal - new_total_total['prima_neta__sum']),
            'currency': "MXN",
            'percentajeGoal': float((new_total_total['prima_neta__sum'] * 100) / meta[0].goal)
        }
    else:
        new_metas = {
            'value': 0,
            'progress': 0,
            'remain': 0,
            'currency': "MXN",
            'percentajeGoal': 0
        }
    if anterior_meta:
        if anterior_new_total_total['prima_neta__sum']:
            anterior_new_total_total['prima_neta__sum'] = anterior_new_total_total['prima_neta__sum']
        else:
            anterior_new_total_total['prima_neta__sum'] = 0
        anterior_new_metas = {
            'value': float(anterior_meta[0].goal) if anterior_meta[0].goal else 0,
            'progress': float( anterior_new_total_total['prima_neta__sum']),
            'remain': str(anterior_meta[0].goal - anterior_new_total_total['prima_neta__sum']),
            'currency': "MXN",
            'percentajeGoal': float( (anterior_new_total_total['prima_neta__sum'] * 100) / anterior_meta[0].goal)
        }
    else:
        anterior_new_metas = {
            'value': 0,
            'progress': 0,
            'remain': 0,
            'currency': "MXN",
            'percentajeGoal': 0
        }
    # ***************DOLARES----------
    recibos_actualDolar = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__year = curr_year).filter(poliza__f_currency =2)
    new_recibos_actualDolar = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = date01_ehoy, fecha_inicio__lte = date31).exclude(poliza__document_type = 2).exclude(poliza__status = 0).filter(poliza__f_currency =2)
    new_rec_all_enero_hoyDolar = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = date01_ehoy, fecha_inicio__lte = date31).filter(poliza__f_currency =2).exclude(poliza__status = 0)
    #ANTERIOR
    anterior_recibos_actualDolar = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__year = anio_anterior).filter(poliza__f_currency =2)
    anterior_new_recibos_actualDolar = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = anterior_date01_ehoy, fecha_inicio__lte = anterior_date31).exclude(poliza__document_type = 2).exclude(poliza__status = 0).filter(poliza__f_currency =2)
    anterior_new_rec_all_enero_hoyDolar = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = anterior_date01_ehoy, fecha_inicio__lte = anterior_date31).filter(poliza__f_currency =2).exclude(poliza__status = 0)
    try:
        your_date_string = request.data['until_day']
        format_string = "%d/%m/%Y"
        datetime_object = datetime.datetime.strptime(your_date_string, format_string).date()
        new_date = datetime_object - relativedelta(years=1)
        anterior_untilDay = datetime.datetime.strftime(new_date, format_string).replace(' 0', ' ')
        antsinceDay = request.data['since_day']
        antsinceDay = datetime.datetime.strptime(antsinceDay, format_string).date()
        antsinceDay = antsinceDay - relativedelta(years=1)
        anterior_sinceDay = datetime.datetime.strftime(antsinceDay, format_string).replace(' 0', ' ')
        f1 = "%d/%m/%Y %H:%M:%S"     
        anterior_untilDay = str(anterior_untilDay)+' 23:59:59'
        anterior_untilDay = datetime.datetime.strptime(anterior_untilDay , f)
        anterior_sinceDay = str(anterior_sinceDay)+' 00:00:00'
        anterior_sinceDay = datetime.datetime.strptime(anterior_sinceDay , f)
        anterior_recibosProduccionDolar = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = anterior_sinceDay, fecha_inicio__lte = anterior_untilDay).filter(poliza__f_currency =2).exclude(poliza__status = 0)
        anterior_log_actualDolar = Log.objects.filter(org_name = request.GET.get('org'), created_at__gte = anterior_sinceDay, created_at__lte = anterior_untilDay)
    except Exception as et:
        anterior_recibosProduccionDolar = anterior_new_rec_all_enero_hoy
        anterior_log_actualDolar = Log.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)
       
        anterior_untilDay = ''
        anterior_sinceDay = ''
    # fecha inicio
    try:
        until_day = request.data['until_day']
        since_day = request.data['since_day']
        f1 = "%d/%m/%Y %H:%M:%S"     
        untilDay = str(until_day)+' 23:59:59'
        untilDay = datetime.datetime.strptime(untilDay , f)
        sinceDay = str(since_day)+' 00:00:00'
        sinceDay = datetime.datetime.strptime(sinceDay , f)
        recibosProduccionDolar = recibos1.filter(org_name = request.GET.get('org'), fecha_inicio__gte = sinceDay, fecha_inicio__lte = untilDay).filter(poliza__f_currency =2).exclude(poliza__status = 0)
        log_actualDolar = Log.objects.filter(org_name = request.GET.get('org'), created_at__gte = sinceDay, created_at__lte = untilDay)
    except Exception as err:
        recibosProduccionDolar = new_rec_all_enero_hoyDolar
        log_actualDolar = Log.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)
    # Aseguradoras y Subramos
    policies2 = Polizas.objects.filter(status__in = st, org_name = request.GET.get('org'),ramo__in = ramos, subramo__in = subramos, aseguradora__in = providers,
        clave__in = cves, owner__in = users, f_currency = 2)
    polizasProduccionDolar = policies2.filter(Q(start_of_validity__gte=sinceDay),Q(start_of_validity__lte = untilDay), f_currency = 2, document_type__in =[1,3,11,12])
    anterior_polizasProduccionDolar = policies2.filter(Q(start_of_validity__gte=anterior_sinceDay),Q(start_of_validity__lte = anterior_untilDay), f_currency = 2, document_type__in =[1,3,11,12])
    new_serializer_asegDolar = polizasProduccionDolar.values('aseguradora__alias').annotate(Sum('p_neta')).order_by('aseguradora__alias')
    new_serializer_aseg_pagadoDolar = recibosProduccion.filter(status__in=[1,5,6]).values('poliza__aseguradora__alias').annotate(Sum('prima_neta')).order_by('poliza__aseguradora__alias')
    anterior_new_serializer_asegDolar = anterior_polizasProduccionDolar.values('aseguradora__alias').annotate(Sum('p_neta')).order_by('aseguradora__alias')
    anterior_new_serializer_aseg_pagadoDolar = anterior_recibosProduccionDolar.filter(status__in=[1,5,6]).values('poliza__aseguradora__alias').annotate(Sum('prima_neta')).order_by('poliza__aseguradora__alias')
    for t in anterior_new_serializer_asegDolar:
        for y in anterior_new_serializer_aseg_pagadoDolar:
            if t['aseguradora__alias'] == y['poliza__aseguradora__alias']:
                t['pagado'] = y['prima_neta__sum']
    for t in new_serializer_asegDolar:
        for y in new_serializer_aseg_pagadoDolar:
            if t['aseguradora__alias'] == y['poliza__aseguradora__alias']:
                t['pagado'] = y['prima_neta__sum']
    new_serializer_subramosDolar = recibosProduccionDolar.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    new_serializer_subramosDolar = recibosProduccionDolar.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    anterior_new_serializer_subramosDolar = anterior_recibosProduccionDolar.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    anterior_new_serializer_subramosDolar = anterior_recibosProduccionDolar.values('poliza__subramo__subramo_name').annotate(Sum('poliza__p_neta')).annotate(pagado = Sum(Case(When(status__in = [1,5,6], then = 'prima_neta'), output_field=CharField()))).order_by('poliza__subramo__subramo_name')
    
    new_serializer_subramosDolar = polizasProduccionDolar.values('subramo__subramo_name').annotate(Sum('p_neta')).order_by('subramo__subramo_code')
    new_serializer_subramos_pagadoDolar = recibosProduccionDolar.filter(status__in=[1,5,6]).values('poliza__subramo__subramo_name').annotate(Sum('prima_neta')).order_by('poliza__subramo__subramo_code')
    for t in new_serializer_subramosDolar:
        for y in new_serializer_subramos_pagadoDolar:
            if t['subramo__subramo_name'] == y['poliza__subramo__subramo_name']:
                t['pagado'] = y['prima_neta__sum']
    
    anterior_new_serializer_subramosDolar = anterior_polizasProduccionDolar.values('subramo__subramo_name').annotate(Sum('p_neta')).order_by('subramo__subramo_code')
    anterior_new_serializer_subramos_pagadoDolar = anterior_recibosProduccionDolar.filter(status__in=[1,5,6]).values('poliza__subramo__subramo_name').annotate(Sum('prima_neta')).order_by('poliza__subramo__subramo_code')
    for t in anterior_new_serializer_subramosDolar:
        for y in anterior_new_serializer_subramos_pagadoDolar:
            if t['subramo__subramo_name'] == y['poliza__subramo__subramo_name']:
                t['pagado'] = y['prima_neta__sum']
    
    # Ejecutivos
    serializer_ejecutivosDolar = log_actualDolar.values('user__first_name', 'user__last_name').annotate(Count('user'))
    anterior_serializer_ejecutivosDolar = anterior_log_actualDolar.values('user__first_name', 'user__last_name').annotate(Count('user'))
    # Bateo y cotización
    total_cotizacionesDolar = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year).count()
    bateadasDolar = Cotizacion.objects.filter(org_name = request.GET.get('org'), status = 3, created_at__year = curr_year).count()
    anterior_total_cotizacionesDolar = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = int(curr_year)-1).count()
    anterior_bateadasDolar = Cotizacion.objects.filter(org_name = request.GET.get('org'), status = 3, created_at__year = int(curr_year)-1).count()
    if total_cotizacionesDolar:
        serializer_bateoDolar = (bateadasDolar * 100) / total_cotizacionesDolar
    else:
        serializer_bateoDolar = 0
    if anterior_total_cotizacionesDolar:
        anterior_serializer_bateoDolar = (anterior_bateadasDolar * 100) / anterior_total_cotizacionesDolar
    else:
        anterior_serializer_bateoDolar = 0
    # Comisiones
    try:
        now = int(request.data['until_year'])
        dic31_com = '31/12/'+str(now)+' 23:59:59'
        ene01_com = '01/01/'+str(now)+' 00:00:00'
        anterior_dic31_com = '31/12/'+str(now-1)+' 23:59:59'
        anterior_ene01_com = '01/01/'+str(now-1)+' 00:00:00'
    except Exception as e:
        dic31_com = '31/12/'+str(now.year)+' 23:59:59'
        ene01_com = '01/01/'+str(now.year)+' 00:00:00'
        anterior_dic31_com = '31/12/'+str(now.year-1)+' 23:59:59'
        anterior_ene01_com = '01/01/'+str(now.year-1)+' 00:00:00'
    f = "%d/%m/%Y %H:%M:%S"     
    date31_com = datetime.datetime.strptime(dic31_com , f)
    date01_com = datetime.datetime.strptime(ene01_com , f)
    anterior_date31_com = datetime.datetime.strptime(anterior_dic31_com , f)
    anterior_date01_com = datetime.datetime.strptime(anterior_ene01_com , f)
    new_recibos_enero_hoyDolar = recibos1.filter(org_name = request.GET.get('org'),status__in = [1,5,6], fecha_inicio__gte = date01_com, fecha_inicio__lte = date31_com).filter(poliza__f_currency =2).exclude(poliza__status = 0)
    new_comision_netaDolar = new_recibos_enero_hoyDolar.exclude(receipt_type=3).aggregate(Sum('comision'))
    #anterior
    anterior_new_recibos_enero_hoyDolar = recibos1.filter(org_name = request.GET.get('org'),status__in = [1,5,6], fecha_inicio__gte = anterior_date01_com, fecha_inicio__lte = anterior_date31_com).filter(poliza__f_currency =2).exclude(poliza__status = 0)
    anterior_new_comision_netaDolar = anterior_new_recibos_enero_hoyDolar.exclude(receipt_type=3).aggregate(Sum('comision'))

    comision_perdidaDolar = recibos_solo.filter(status__in =[2,8] ,receipt_type = 3, poliza__f_currency =2, fecha_inicio__gte = date01_ehoy, fecha_inicio__lte = date31).aggregate(Sum('comision'))
    anterior_comision_perdidaDolar = recibos_solo.filter(status__in =[2,8] ,receipt_type = 3, poliza__f_currency =2, fecha_inicio__gte = anterior_date01_ehoy, fecha_inicio__lte = anterior_date31).aggregate(Sum('comision'))
    new1Dolar = new_recibos_actualDolar.filter(receipt_type = 3).exclude(status = 0).aggregate(Sum('prima_total'))
    notas_totalDolar = recibos_actualDolar.filter(receipt_type = 3).exclude(status = 0).aggregate(Sum('prima_total'))
    new_total_recibirDolar = new_recibos_actualDolar.filter(status__in = [4,3]).exclude(receipt_type =3).aggregate(Sum('comision'))

    anterior_new1Dolar = anterior_new_recibos_actualDolar.filter(receipt_type = 3).exclude(status = 0).aggregate(Sum('prima_total'))
    anterior_notas_totalDolar = anterior_recibos_actualDolar.filter(receipt_type = 3).exclude(status = 0).aggregate(Sum('prima_total'))
    anterior_new_total_recibirDolar = anterior_new_recibos_actualDolar.filter(status__in = [4,3]).exclude(receipt_type =3).aggregate(Sum('comision'))
    # Primas
    new_pagados_totalDolar = new_recibos_enero_hoyDolar.filter(status__in = [1,5,6]).aggregate(Sum('prima_neta'))
    new_pendientes_totalDolar = new_recibos_actualDolar.filter(status__in = [4,3]).exclude(receipt_type = 3).aggregate(Sum('prima_total'))
    emitidas_cancelDolar = policies2.filter(status__in = [11,4], f_currency = 2).aggregate(Sum('p_neta'))
    total_totalDolar = recibos_actualDolar.aggregate(Sum('prima_neta'))
    new_total_totalDolarDolar = new_recibos_enero_hoyDolar.aggregate(Sum('prima_neta'))    
    
    anterior_new_pagados_totalDolar = anterior_new_recibos_enero_hoyDolar.filter(status__in = [1,5,6]).aggregate(Sum('prima_neta'))
    anterior_new_pendientes_totalDolar = anterior_new_recibos_actualDolar.filter(status__in = [4,3]).exclude(receipt_type = 3).aggregate(Sum('prima_total'))
    anterior_emitidas_cancelDolar = policies2.filter(status__in = [11,4], f_currency = 2).aggregate(Sum('p_neta'))
    anterior_total_totalDolar = anterior_recibos_actualDolar.aggregate(Sum('prima_neta'))
    anterior_new_total_totalDolar = anterior_new_recibos_enero_hoyDolar.aggregate(Sum('prima_neta'))    
        
    contractors = len(Contractor.objects.filter(org_name = request.GET.get('org'), is_active = True))
    anterior_polizascontractors = len(Contractor.objects.filter(org_name = request.GET.get('org'), created_at__year = (curr_year-1), is_active = True))

    recibos_2x = Recibos.objects.filter(org_name = request.GET.get('org')).exclude(fecha_inicio = None).exclude(status = 0)
    re = recibos_2x.order_by('fecha_inicio').first()
    re2 = recibos_2x.order_by('fecha_inicio').last()
    años = rango_fechas(re.fecha_inicio,re2.fecha_inicio)
    # DOLARES**************************************
    data = {
        'aseguradoras': json.dumps(list(new_serializer_aseg), default=decimal_default),
        'anterior_aseguradoras': json.dumps(list(anterior_new_serializer_aseg), default=decimal_default),
        'aseguradoras_pagado': json.dumps(list(new_serializer_aseg_pagado), default=decimal_default),
        'anterior_aseguradoras_pagado': json.dumps(list(anterior_new_serializer_aseg_pagado), default=decimal_default),
        'subramos': json.dumps(list(new_serializer_subramos), default=decimal_default),
        'anterior_subramos': json.dumps(list(anterior_new_serializer_subramos), default=decimal_default),
        'ejecutivos': json.dumps(list(serializer_ejecutivos), default=decimal_default),
        'anterior_ejecutivos': json.dumps(list(anterior_serializer_ejecutivos), default=decimal_default),
        'bateo': serializer_bateo,
        'anterior_bateo': anterior_serializer_bateo,
        'cotizaciones': total_cotizaciones,
        'anterior_cotizaciones': anterior_total_cotizaciones,
        'comision': float(new_comision_neta['comision__sum']) if new_comision_neta['comision__sum'] else 0,
        'anterior_comision': float(anterior_new_comision_neta['comision__sum']) if anterior_new_comision_neta['comision__sum'] else 0,
        'comision_perdida': float(comision_perdida['comision__sum']) if comision_perdida['comision__sum']  else 0,
        'anterior_comision_perdida': float(anterior_comision_perdida['comision__sum']) if anterior_comision_perdida['comision__sum']  else 0,
        'recibos_pagados': float(new_pagados_total['prima_neta__sum']) if new_pagados_total['prima_neta__sum']  else 0,
        'anterior_recibos_pagados': float(anterior_new_pagados_total['prima_neta__sum']) if anterior_new_pagados_total['prima_neta__sum']  else 0,
        'prima_cobrar': float( new_pendientes_total['prima_total__sum']) if new_pendientes_total['prima_total__sum'] else 0,
        'anterior_prima_cobrar': float(anterior_new_pendientes_total['prima_total__sum']) if anterior_new_pendientes_total['prima_total__sum'] else 0,
        'prima_recibir': float(new_total_recibir['comision__sum']) if new_total_recibir['comision__sum'] else 0,
        'anterior_prima_recibir': float(anterior_new_total_recibir['comision__sum']) if anterior_new_total_recibir['comision__sum'] else 0,
        'primas_canceladas': float(emitidas_cancel['p_neta__sum'] )if emitidas_cancel['p_neta__sum'] else 0,
        'anterior_primas_canceladas': float(anterior_emitidas_cancel['p_neta__sum']) if anterior_emitidas_cancel['p_neta__sum'] else 0,
        'goal': new_metas,
        'anterior_goal': anterior_new_metas,
        'contratantes': contractors,
        'anterior_contratantes': anterior_polizascontractors,
        #'endosos': Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__gte = date01_com, init_date__lte = date31).exclude(status = 0).count(),
        'endosos': Endorsement.objects.filter(org_name = request.GET.get('org')).exclude(status = 0).count(),
        'anterior_endosos': Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__gte = anterior_date01_com, init_date__lte = anterior_date31).exclude(status = 0).count(),
        #'siniestros': Siniestros.objects.filter(org_name = request.GET.get('org'), fecha_ingreso__gte = date01_com, fecha_ingreso__lte = date31).exclude(status = 0).count(),
        'siniestros': Siniestros.objects.filter(org_name = request.GET.get('org')).exclude(status = 0).count(),
        'anterior_siniestros': Siniestros.objects.filter(org_name = request.GET.get('org'), fecha_ingreso__gte = anterior_date01_com, fecha_ingreso__lte = anterior_date31).exclude(status = 0).count(),
        'notas_credito': float(notas_total['prima_total__sum']) if notas_total and 'prima_total__sum' in notas_total and notas_total['prima_total__sum'] else 0,
        'anterior_notas_credito': float(anterior_notas_total['prima_total__sum']) if anterior_notas_total and 'prima_total__sum' in anterior_notas_total and anterior_notas_total['prima_total__sum'] else 0,
        #'ot': (Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__gte = date01_com, init_date__lte = date31, status__in = [1,5]).count() + Polizas.objects.filter(document_type__in=list([1,3]),org_name = request.GET.get('org'), start_of_validity__gte = date01_com, start_of_validity__lte = date31, status = 1).count()),
        'ot': (Endorsement.objects.filter(org_name = request.GET.get('org'), status__in = [1,5]).count() + Polizas.objects.filter(document_type__in=list([1,3]),org_name = request.GET.get('org'), status = 1).count()),
        'anterior_ot': (Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__gte = anterior_date01_com, init_date__lte = anterior_date31, status__in = [1,5]).count() + Polizas.objects.filter(document_type__in=list([1,3]),org_name = request.GET.get('org'), start_of_validity__gte = anterior_date01_com, start_of_validity__lte = anterior_date31, status = 1).count()),
        #'polizas': Polizas.objects.filter(org_name = request.GET.get('org'), start_of_validity__year = curr_year, document_type__in=[1,3,7,8,11,12]).exclude(status = 0).count(),
        'polizas': Polizas.objects.filter(org_name = request.GET.get('org'), document_type__in=[1,3,7,8,11,12]).exclude(status = 0).count(),
        'anterior_polizas': Polizas.objects.filter(org_name = request.GET.get('org'), start_of_validity__year = int(curr_year-1), document_type__in=[1,3,7,8,11,12]).exclude(status = 0).count(),
        #'renovaciones': Polizas.objects.filter(org_name = request.GET.get('org'), end_of_validity__gte=date01_com, end_of_validity__lte = date31, renewed_status=1, is_renewable = 1, document_type__in = [1,3,11,12], status__in = [12,10,14]).exclude(status = 0).exclude(status = 15).count(),
        'renovaciones': Polizas.objects.filter(org_name = request.GET.get('org'), renewed_status=1, is_renewable = 1, document_type__in = [1,3,11,12], status__in = [12,10,14]).exclude(status = 0).exclude(status = 15).count(),
        'anterior_renovaciones': Polizas.objects.filter(org_name = request.GET.get('org'), end_of_validity__gte=anterior_date01_com, end_of_validity__lte = anterior_date31, renewed_status=1, is_renewable = 1, document_type__in = [1,3,11,12], status__in = [12,10,14]).exclude(status = 0).exclude(status = 15).count(),
        'chartDataFinancial': getChartDataFinancial(request,1,1),
        'chartDataFinancial_anterior': getChartDataFinancial(request,1,2),
        'barDataFinancial': getBarDataFinancial(request,1,1),
        'barDataFinancial_anterior': getBarDataFinancial(request,1,2),
        'polarDataFinancial': getPolarDataFinancial(request,1,1),
        'polarDataFinancial_anterior': getPolarDataFinancial(request,1,2),
        'barDataProduction': getBarDataProduction(request,1,1),
        'barDataProduction_anterior': getBarDataProduction(request,1,2),
        'barDataCotization': getBarDataCotizacion(request,1,1),
        'barDataCotization_anterior': getBarDataCotizacion(request,1,2),
        'monthsBateo': getMonthsBateo(request,1,1),
        'monthsBateo_anterior': getMonthsBateo(request,1,2),
        'chartDataCotization': getChartDataCotizacion(request,1,1),
        'chartDataCotization_anterior': getChartDataCotizacion(request,1,2),
        'barDataGastos': getBarDataGastos(request, recibos_actual,1,recibos_actualDolar,1),
        'barDataGastos_anterior': getBarDataGastos(request, anterior_recibos_actual,1,anterior_recibos_actualDolar,2),
        'monthsUtilidad': getMonthsUtilidad(request, recibos_actual,1, recibos_actualDolar,1),
        'monthsUtilidad_anterior': getMonthsUtilidad(request, anterior_recibos_actual,1, anterior_recibos_actualDolar,2),
        # Dolares
        'aseguradorasDolar': json.dumps(list(new_serializer_asegDolar), default=decimal_default),
        'anterior_aseguradorasDolar': json.dumps(list(anterior_new_serializer_asegDolar), default=decimal_default),
        'subramosDolar': json.dumps(list(new_serializer_subramosDolar), default=decimal_default),
        'anterior_subramosDolar': json.dumps(list(anterior_new_serializer_subramosDolar), default=decimal_default),
        'ejecutivosDolar': json.dumps(list(serializer_ejecutivosDolar), default=decimal_default),
        'anterior_ejecutivosDolar': json.dumps(list(anterior_serializer_ejecutivosDolar), default=decimal_default),
        'bateoDolar': serializer_bateoDolar,
        'anterior_bateoDolar': anterior_serializer_bateoDolar,
        'cotizacionesDolar': total_cotizacionesDolar,
        'anterior_cotizacionesDolar': anterior_total_cotizacionesDolar,

        'comisionDolar': float(new_comision_netaDolar['comision__sum']) if new_comision_netaDolar['comision__sum'] else 0,
        'anterior_comisionDolar': float(anterior_new_comision_netaDolar['comision__sum']) if anterior_new_comision_netaDolar['comision__sum'] else 0,
        'comision_perdidaDolar': comision_perdidaDolar['comision__sum'] if  comision_perdidaDolar['comision__sum'] else 0,
        'anterior_comision_perdidaDolar': anterior_comision_perdidaDolar['comision__sum'] if  anterior_comision_perdidaDolar['comision__sum'] else 0,
        'recibos_pagadosDolar': float(new_pagados_totalDolar['prima_neta__sum']) if new_pagados_totalDolar['prima_neta__sum'] else 0,
        'anterior_recibos_pagadosDolar': float(anterior_new_pagados_totalDolar['prima_neta__sum']) if anterior_new_pagados_totalDolar['prima_neta__sum'] else 0,
        'prima_cobrarDolar': float(new_pendientes_totalDolar['prima_total__sum']) if new_pendientes_totalDolar['prima_total__sum'] else 0,
        'anterior_prima_cobrarDolar': float(anterior_new_pendientes_totalDolar['prima_total__sum'] )if anterior_new_pendientes_totalDolar['prima_total__sum'] else 0,
        'prima_recibirDolar': float(new_total_recibirDolar['comision__sum']) if new_total_recibirDolar['comision__sum'] else 0,
        'anterior_prima_recibirDolar': float(anterior_new_total_recibirDolar['comision__sum']) if anterior_new_total_recibirDolar['comision__sum'] else 0,
        'primas_canceladasDolar': float(emitidas_cancelDolar['p_neta__sum']) if emitidas_cancelDolar['p_neta__sum'] else 0,
        'anterior_primas_canceladasDolar': float(anterior_emitidas_cancelDolar['p_neta__sum']) if anterior_emitidas_cancelDolar['p_neta__sum'] else 0,

        'contratantesDolar': (Contractor.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year, is_active = True).count()),
        'endososDolar': Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__gte = date01_com, init_date__lte = date31).exclude(status = 0).count(),
        'siniestrosDolar': Siniestros.objects.filter(org_name = request.GET.get('org'), fecha_ingreso__gte = date01_com, fecha_ingreso__lte = date31).exclude(status = 0).count(),
        'notas_creditoDolar': notas_totalDolar['prima_total__sum'],
        'otDolar': (Endorsement.objects.filter(org_name = request.GET.get('org'), init_date__gte = date01_com, init_date__lte = date31, status__in = [1,5]).count() + Polizas.objects.filter(document_type__in=list([1,3]),org_name = request.GET.get('org'), start_of_validity__gte = date01_com, start_of_validity__lte = date31, status = 1).count()),
        'polizasDolar': Polizas.objects.filter(org_name = request.GET.get('org'), start_of_validity__year = curr_year, document_type__in=[1,3,7,8,11,12]).exclude(status = 0).count(),
        'renovacionesDolar': Polizas.objects.filter(org_name = request.GET.get('org'), end_of_validity__gte=date01_com, end_of_validity__lte = date31, renewed_status=1, is_renewable = 1, document_type__in = [1,3,11,12], status__in = [12,10,14]).exclude(status = 0).exclude(status = 15).count(),
        'chartDataFinancialDolar': getChartDataFinancial(request,2,1),
        'chartDataFinancialDolar_anterior': getChartDataFinancial(request,2,2),
        'barDataFinancialDolar': getBarDataFinancial(request,2,1),
        'barDataFinancialDolar_anterior': getBarDataFinancial(request,2,2),
        'polarDataFinancialDolar': getPolarDataFinancial(request,2,1),
        'polarDataFinancialDolar_anterior': getPolarDataFinancial(request,2,2),
        'barDataCotizacionSubramo': getBarDataCotizacionSubramo(request,2,1),
        'barDataCotizacionSubramo_anterior': getBarDataCotizacionSubramo(request,2,2),
        'barDataCotizationRamo': getBarDataCotizacionRamo(request,2,1),
        'barDataCotizationRamo_anterior': getBarDataCotizacionRamo(request,2,2),
        'barDataProductionDolar': getBarDataProduction(request,2,1),
        'barDataProductionDolar_anterior': getBarDataProduction(request,2,2),
        'barDataCotizationDolar': getBarDataCotizacion(request,2,1),
        'barDataCotizationDolar_anterior': getBarDataCotizacion(request,2,2),
        'monthsBateoDolar': getMonthsBateo(request,2,1),
        'monthsBateoDolar_anterior': getMonthsBateo(request,2,2),
        'chartDataCotizationDolar': getChartDataCotizacion(request,2,1),
        'chartDataCotizationDolar_anterior': getChartDataCotizacion(request,2,2),
        'barDataGastosDolar': getBarDataGastos(request, recibos_actualDolar,2,recibos_actual,1),
        'barDataGastosDolar_anterior': getBarDataGastos(request, anterior_recibos_actualDolar,2,anterior_recibos_actual,2),
        'monthsUtilidadDolar': getMonthsUtilidad(request, recibos_actualDolar,2, recibos_actual,1),
        'monthsUtilidadDolar_anterior': getMonthsUtilidad(request, anterior_recibos_actualDolar,2, anterior_recibos_actual,2),
        'anios': años
        }
    return JsonResponse(data)

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, KBIPermissionV2  ))
def kbisubramos(request):
    now = datetime.datetime.now()
    try:
        now = int(request.data['until_year'])
        curr_year = int(request.data['until_year'])
        dic31 = '31/12/'+str(now)+' 23:59:59'
        f = "%d/%m/%Y %H:%M:%S"     
        date31 = datetime.datetime.strptime(dic31 , f)
        ene01_c_eh = '01/01/'+str(now)+' 00:00:00'
        date01_ehoy = datetime.datetime.strptime(ene01_c_eh , f)
        #anterior     
        anterior_dic31 = '31/12/'+str(int(now)-1)+' 23:59:59'   
        anterior_date31 = datetime.datetime.strptime(anterior_dic31 , f)
        anterior_ene01_c_eh = '01/01/'+str(int(now)-1)+' 00:00:00'
        anterior_date01_ehoy = datetime.datetime.strptime(anterior_ene01_c_eh , f)
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year
        dic31 = '31/12/'+str(now.year)+' 23:59:59'
        f = "%d/%m/%Y %H:%M:%S"     
        date31 = datetime.datetime.strptime(dic31 , f)
        ene01_c_eh = '01/01/'+str(now.year)+' 00:00:00'
        date01_ehoy = datetime.datetime.strptime(ene01_c_eh , f)
        #anteruir
        anterior_dic31 = '31/12/'+str(now.year-1)+' 23:59:59'        
        anterior_date31 = datetime.datetime.strptime(anterior_dic31 , f)
        anterior_ene01_c_eh = '01/01/'+str(now.year-1)+' 00:00:00'
        anterior_date01_ehoy = datetime.datetime.strptime(anterior_ene01_c_eh , f)
    
    data = {
        'polarDataFinancialDolar': getPolarDataFinancialSubs(request,2,1),
        'polarDataFinancial': getPolarDataFinancialSubs(request,1,1),      
        }
    return JsonResponse(data)

# Subramos OK
def getPolarDataFinancialSubs(request, currency,anio):
    org = request.GET.get('org')
    month1 = request.data['month']
    month2 = request.data['month']
    year1 = request.data['year']
    year2 = request.data['year_c']
    lst = [0] * 12
    try:
        now = request.data['until_year']
        curr_year = now
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year
    try:
        now = int(request.data['until_year'])
        curr_year =now
        dic31 = '31/12/'+str(now)+' 23:59:59'
        ene01 = '01/01/'+str(now)+' 00:00:00'
    except Exception as err:
        now = datetime.datetime.now()
        curr_year = now.year
        dic31 = '31/12/'+str(now.year)+' 23:59:59'
        ene01 = '01/01/'+str(now.year)+' 00:00:00'

    f = "%d/%m/%Y %H:%M:%S"     
    date31 = datetime.datetime.strptime(dic31 , f)
    date01 = datetime.datetime.strptime(ene01 , f)
    users = list(User.objects.values_list('pk', flat=True))
    providers = list(Provider.objects.filter(org_name = org).values_list('pk', flat=True))
    cves = list(Claves.objects.filter(org_name = org).values_list('pk', flat=True))
    bonos = Bonos.objects.filter(org_name = org, 
                                     aseguradora__in = providers,
                                     clave__in = cves,
                                     owner__in = users)
    ramos = list(Ramos.objects.filter(org_name = org, provider__in = providers).values_list('pk', flat=True))
    subramos = list(SubRamos.objects.filter(org_name = org, ramo__in = ramos).values_list('pk', flat=True))
    st = [1,2,4,10,11,12,13,14,15]
    currency =currency if currency else 1
    p_a = Polizas.objects.filter(status__in = st, 
        org_name = request.GET.get('org'),
        ramo__in = ramos, 
        subramo__in = subramos, 
        aseguradora__in = providers,
        clave__in = cves,
        owner__in = users,start_of_validity__year = year1, start_of_validity__month = month1,document_type__in = list([1,3,11,12]), f_currency = currency)
    subramos_1 = p_a.values('subramo__subramo_code').annotate(Sum('p_neta')).order_by('subramo__subramo_name')
    anterior1 = Polizas.objects.filter(status__in = st, 
        org_name = request.GET.get('org'),
        ramo__in = ramos, 
        subramo__in = subramos, 
        aseguradora__in = providers,
        clave__in = cves,
        owner__in = users,start_of_validity__year = year2,start_of_validity__month = month2,document_type__in = list([1,3,11,12]), f_currency = currency)

    antsubramos = anterior1.values('subramo__subramo_code').annotate(Sum('p_neta')).order_by('subramo__subramo_name')
     
    data = {'labels':["Vida", "GM", "Salud", "AP", "Autos", 'RC', 'Marítimo y Transportes', 'Incendio', 'Agrícola', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Riesgos Catastróficos'],
         'series': ["Vida", "Gastos Médicos", "Salud", "Accidentes y Enfermedades", "Automóviles", 'Responsabilidad Civil y Riesgos Profesionales', 'Marítimo y Transportes', 'Incendio', 'Agrícola y de Animales', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Terremoto y Otros Riesgos Catastróficos'],
         'data':[[searchDataSubramos(1, subramos_1), 
                searchDataSubramos(3, subramos_1), 
                searchDataSubramos(4, subramos_1), 
                searchDataSubramos(2, subramos_1), 
                searchDataSubramos(9, subramos_1), 
                searchDataSubramos(5, subramos_1), 
                searchDataSubramos(6, subramos_1), 
                searchDataSubramos(7, subramos_1), 
                searchDataSubramos(8, subramos_1), 
                searchDataSubramos(10, subramos_1), 
                searchDataSubramos(11, subramos_1), 
                searchDataSubramos(12, subramos_1), 
                searchDataSubramos(13, subramos_1), 
                searchDataSubramos(14, subramos_1)],
                [searchDataSubramos(1, antsubramos), 
                searchDataSubramos(3, antsubramos), 
                searchDataSubramos(4, antsubramos), 
                searchDataSubramos(2, antsubramos), 
                searchDataSubramos(9, antsubramos), 
                searchDataSubramos(5, antsubramos), 
                searchDataSubramos(6, antsubramos), 
                searchDataSubramos(7, antsubramos), 
                searchDataSubramos(8, antsubramos), 
                searchDataSubramos(10, antsubramos), 
                searchDataSubramos(11, antsubramos), 
                searchDataSubramos(12, antsubramos), 
                searchDataSubramos(13, antsubramos), 
                searchDataSubramos(14, antsubramos)]                   
            ],
         'colours': ['#9B59B6', '#D4D4D4', '#2980B9', '#01A9DB', '#1ABC9C', '#61380B', '#00FF80', '#F7819F', '#F1C40F', '#F39C12', '#E67E22', '#D35400', '#C0392B', '#E74C3C'] }

    return data

def rango_fechas(desde, hasta):
    rango = []
    # Calculamos la diferencia de los años
    dias_totales = (hasta.year - desde.year)
    for year in range(dias_totales + 1): 
        fecha = (desde + relativedelta(year=year)).year
        if desde.year == fecha:
            d = desde.year 
        else:
            d = desde.year + fecha
        # if int(d)
            rango.append(d)
    return rango
# traer los meses de un query
class Month(Func):
    function = 'EXTRACT'
    template = '%(function)s(MONTH from %(expressions)s)'
    output_field = models.IntegerField()
# regresa total (enviar un mes(#) y la info (object) )
import math
def searchData(month, data):
    concidence = [element for element in data if element['month'] == month]
    if concidence:
        if math.isnan(concidence[0]['total']):
            return 0 
        else:
            return float(concidence[0]['total']) if float(concidence[0]['total']) else 0 
    else:
        return 0
# regresa suma (enviar un mes(#) y la info (onject) )
def searchDataSum(month, data):
    concidence = [element for element in data if element['month'] == month]
    if concidence:
        return float(concidence[0]['cantidad__sum'])
    else:
        return 0

def searchDataSubramos(month, data):
    concidence = [element for element in data if element['subramo__subramo_code'] == month]
    if concidence:
        return float(concidence[0]['p_neta__sum'])
    else:
        return 0
def searchDataSubramosCode(month, data):
    concidence = [element for element in data if element['subramo_code'] == month]
    if concidence:
        return concidence[0]['subramo_code__count']
    else:
        return 0
def getBarDataCotizacionSubramo(request, currency,anio):
    try:
        now = datetime.datetime.now()
        curr_year = int(request.data['until_year'])
    except Exception as er:
        now = datetime.datetime.now()
        curr_year = now.year
    total_cotizacionesD = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year).count()

    lst = [0] * 12

    p_a = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)
    anterior_p_a = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year-1)
    subramos = p_a.values('subramo_code').annotate(Count('subramo_code')).order_by('subramo_code')
    subramos_anterior = anterior_p_a.values('subramo_code').annotate(Count('subramo_code')).order_by('subramo_code')
    if anio ==1:
        data = {'labels':["Vida", "GM", "Salud", "AP", "Autos", 'RC', 'Marítimo y Transportes', 'Incendio', 'Agrícola', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Riesgos Catastróficos'],
                             'series': ["Vida", "Gastos Médicos", "Salud", "Accidentes y Enfermedades", "Automóviles", 'Responsabilidad Civil y Riesgos Profesionales', 'Marítimo y Transportes', 'Incendio', 'Agrícola y de Animales', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Terremoto y Otros Riesgos Catastróficos'],
                             'data': [[searchDataSubramosCode(1, subramos), searchDataSubramosCode(3, subramos), searchDataSubramosCode(4, subramos), searchDataSubramosCode(2, subramos), searchDataSubramosCode(9, subramos), searchDataSubramosCode(5, subramos), searchDataSubramosCode(6, subramos), searchDataSubramosCode(7, subramos), searchDataSubramosCode(8, subramos), searchDataSubramosCode(10, subramos), searchDataSubramosCode(11, subramos), searchDataSubramosCode(12, subramos), searchDataSubramosCode(13, subramos), searchDataSubramosCode(14, subramos)]],
                             'colours': ['#9B59B6', '#DF01A5', '#2980B9', '#01A9DB', '#1ABC9C', '#61380B', '#00FF80', '#F7819F', '#F1C40F', '#F39C12', '#E67E22', '#D35400', '#C0392B', '#E74C3C'] }
    elif anio ==2:
        data = {'labels':["Vida", "GM", "Salud", "AP", "Autos", 'RC', 'Marítimo y Transportes', 'Incendio', 'Agrícola', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Riesgos Catastróficos'],
                             'series': ["Vida", "Gastos Médicos", "Salud", "Accidentes y Enfermedades", "Automóviles", 'Responsabilidad Civil y Riesgos Profesionales', 'Marítimo y Transportes', 'Incendio', 'Agrícola y de Animales', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Terremoto y Otros Riesgos Catastróficos'],
                             'data': [[searchDataSubramosCode(1, subramos_anterior), searchDataSubramosCode(3, subramos_anterior), searchDataSubramosCode(4, subramos_anterior), searchDataSubramosCode(2, subramos_anterior), searchDataSubramosCode(9, subramos_anterior), searchDataSubramosCode(5, subramos_anterior), searchDataSubramosCode(6, subramos_anterior), searchDataSubramosCode(7, subramos_anterior), searchDataSubramosCode(8, subramos_anterior), searchDataSubramosCode(10, subramos_anterior), searchDataSubramosCode(11, subramos_anterior), searchDataSubramosCode(12, subramos_anterior), searchDataSubramosCode(13, subramos_anterior), searchDataSubramosCode(14, subramos_anterior)]],
                             'colours': ['#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4'] }
    else:
        data = {'labels':["Vida", "GM", "Salud", "AP", "Autos", 'RC', 'Marítimo y Transportes', 'Incendio', 'Agrícola', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Riesgos Catastróficos'],
                             'series': ["Vida", "Gastos Médicos", "Salud", "Accidentes y Enfermedades", "Automóviles", 'Responsabilidad Civil y Riesgos Profesionales', 'Marítimo y Transportes', 'Incendio', 'Agrícola y de Animales', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Terremoto y Otros Riesgos Catastróficos'],
                             'data': [[searchDataSubramosCode(1, subramos), searchDataSubramosCode(3, subramos), searchDataSubramosCode(4, subramos), searchDataSubramosCode(2, subramos), searchDataSubramosCode(9, subramos), searchDataSubramosCode(5, subramos), searchDataSubramosCode(6, subramos), searchDataSubramosCode(7, subramos), searchDataSubramosCode(8, subramos), searchDataSubramosCode(10, subramos), searchDataSubramosCode(11, subramos), searchDataSubramosCode(12, subramos), searchDataSubramosCode(13, subramos), searchDataSubramosCode(14, subramos)]],
                             'colours': ['#9B59B6', '#DF01A5', '#2980B9', '#01A9DB', '#1ABC9C', '#61380B', '#00FF80', '#F7819F', '#F1C40F', '#F39C12', '#E67E22', '#D35400', '#C0392B', '#E74C3C'] }

    return data
def searchDataRamosCode(month, data):
    concidence = [element for element in data if element['ramo_code'] == month]
    if concidence:
        return concidence[0]['ramo_code__count']
    else:
        return 0
def getBarDataCotizacionRamo(request, currency,anio):
    try:
        now = datetime.datetime.now()
        curr_year = int(request.data['until_year'])
    except Exception as er:
        now = datetime.datetime.now()
        curr_year = now.year
    total_cotizacionesD = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year).count()
    total_cotizacionesD_ant = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year-1).count()

    lst = [0] * 12

    p_a = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year)
    anterior_p_a = Cotizacion.objects.filter(org_name = request.GET.get('org'), created_at__year = curr_year-1)
    subramos = p_a.values('ramo_code').annotate(Count('ramo_code')).order_by('ramo_code')
    anterior_subramos = anterior_p_a.values('ramo_code').annotate(Count('ramo_code')).order_by('ramo_code')
    if anio ==1:
        data = {'labels':["Vida","Accidentes y Enfermedades", "Daños"],
                             'series': ["Vida","Accidentes y Enfermedades", "Daños"],
                             'data': [[searchDataRamosCode(1, subramos), searchDataRamosCode(2, subramos), searchDataRamosCode(3, subramos)]],
                             'colours': ['#5DADE2', '#DF01A5', '#2980B9']}
    elif anio ==2:        
        data = {'labels':["Vida","Accidentes y Enfermedades", "Daños"],
                             'series': ["Vida","Accidentes y Enfermedades", "Daños"],
                             'data': [[searchDataRamosCode(1, anterior_subramos), searchDataRamosCode(2, anterior_subramos), searchDataRamosCode(3, anterior_subramos)]],
                             'colours': ['#D4D4D4', '#D4D4D4', '#D4D4D4']}
    else:        
        data = {'labels':["Vida","Accidentes y Enfermedades", "Daños"],
                             'series': ["Vida","Accidentes y Enfermedades", "Daños"],
                             'data': [[searchDataRamosCode(1, subramos), searchDataRamosCode(2, subramos), searchDataRamosCode(3, subramos)]],
                             'colours': ['#5DADE2', '#DF01A5', '#2980B9']}
    return data
# puntos comparión
def getChartDataFinancial(request, currency,anio):
    # lst = [0] * 12
    try:
        now = int(request.data['until_year'])
        curr_year =now
        dic31 = '31/12/'+str(now)+' 23:59:59'
        ene01 = '01/01/'+str(now)+' 00:00:00'
        anterior_dic31 = '31/12/'+str(now-1)+' 23:59:59'
        anterior_ene01 = '01/01/'+str(now-1)+' 00:00:00'
    except Exception as err:
        now = datetime.datetime.now()
        curr_year = now.year
        dic31 = '31/12/'+str(now.year)+' 23:59:59'
        ene01 = '01/01/'+str(now.year)+' 00:00:00'
        anterior_dic31 = '31/12/'+str(now.year-1)+' 23:59:59'
        anterior_ene01 = '01/01/'+str(now.year-1)+' 00:00:00'

    f = "%d/%m/%Y %H:%M:%S"     
    date31 = datetime.datetime.strptime(dic31 , f)
    date01 = datetime.datetime.strptime(ene01 , f)
    anteriordate31 = datetime.datetime.strptime(anterior_dic31 , f)
    anteriordate01 = datetime.datetime.strptime(anterior_ene01 , f)
    # Sum o count es lo que se modifican por atributo,fecha o x
    new_p_a = Recibos.objects.filter(fecha_inicio__gte = date01,fecha_inicio__lte = date31, org_name = request.GET.get('org'), status__in = [1,5,6], poliza__f_currency = currency).exclude(poliza__status = 0).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('prima_neta')).order_by('month')
    new_p_l = Recibos.objects.filter(fecha_inicio__year = (curr_year- 1), org_name = request.GET.get('org'),status__in = [1,5,6], poliza__f_currency = currency).exclude(poliza__status = 0).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('prima_neta')).order_by('month')
    #                       -----------------------****************------------------------
    org = request.GET.get('org')
    users = list(User.objects.values_list('pk', flat=True))
    providers = list(Provider.objects.filter(org_name = org).values_list('pk', flat=True))
    cves = list(Claves.objects.filter(org_name = org).values_list('pk', flat=True))
    bonos = Bonos.objects.filter(org_name = org, 
                                     aseguradora__in = providers,
                                     clave__in = cves,
                                     owner__in = users)
    ramos = list(Ramos.objects.filter(org_name = org, provider__in = providers).values_list('pk', flat=True))
    subramos = list(SubRamos.objects.filter(org_name = org, ramo__in = ramos).values_list('pk', flat=True))
    polizas = Polizas.objects.filter(org_name = org,
                                         aseguradora__in = providers,
                                         ramo__in = ramos,
                                         subramo__in = subramos,
                                         clave__in = cves,
                                         owner__in = users).exclude(status__in = [1,2,0]).exclude(document_type__in = [2,6,10])
    parents = polizas.filter(document_type = 3)
    subgrupos = Polizas.objects.filter(parent__id__in = parents.values_list('pk', flat = True), document_type = 4, org_name = org).values_list('id', flat = True)
    recibos = Recibos.objects.filter(Q(poliza__in = polizas) | Q(poliza__in = subgrupos) | Q(bono__in = bonos),
                                     isActive = True, 
                                     isCopy = False,
                                     org_name = org).exclude(status__in =  [0,7,2]).filter(receipt_type__in = [1,2,3,4])
    new_p_a = recibos.filter(fecha_inicio__gte = date01,fecha_inicio__lte = date31, org_name = request.GET.get('org'), status__in = [1,5,6], poliza__f_currency = currency).exclude(poliza__status = 0).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('prima_neta')).order_by('month')
    new_p_l = recibos.filter(fecha_inicio__year = (curr_year- 1), org_name = request.GET.get('org'),status__in = [1,5,6], poliza__f_currency = currency).exclude(poliza__status = 0).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('prima_neta')).order_by('month')
 
    #                       ***********************----------------************************
    print('new_p_a',len(new_p_a),anio,date01,date31)
    if anio ==1:
        new_data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': [curr_year ],
              'data': [[searchData(1, new_p_a), searchData(2, new_p_a), searchData(3, new_p_a), searchData(4, new_p_a), searchData(5, new_p_a), searchData(6, new_p_a), searchData(7, new_p_a), searchData(8, new_p_a), searchData(9, new_p_a), searchData(10, new_p_a), searchData(11, new_p_a), searchData(12, new_p_a)]],
              'colours': ['#F1C40F'] }
    elif anio ==2:#anterior
        new_data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': [(curr_year - 1)],
              'data': [[searchData(1, new_p_l), searchData(2, new_p_l), searchData(3, new_p_l), searchData(4, new_p_l), searchData(5, new_p_l), searchData(6, new_p_l), searchData(7, new_p_l), searchData(8, new_p_l), searchData(9, new_p_l), searchData(10, new_p_l), searchData(11, new_p_l), searchData(12, new_p_l)]],
              'colours': ['#D4D4D4'] }
    else:#orignal
        new_data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': [(curr_year - 1), curr_year ],
              'data': [[searchData(1, new_p_l), searchData(2, new_p_l), searchData(3, new_p_l), searchData(4, new_p_l), searchData(5, new_p_l), searchData(6, new_p_l), searchData(7, new_p_l), searchData(8, new_p_l), searchData(9, new_p_l), searchData(10, new_p_l), searchData(11, new_p_l), searchData(12, new_p_l)],
                       [searchData(1, new_p_a), searchData(2, new_p_a), searchData(3, new_p_a), searchData(4, new_p_a), searchData(5, new_p_a), searchData(6, new_p_a), searchData(7, new_p_a), searchData(8, new_p_a), searchData(9, new_p_a), searchData(10, new_p_a), searchData(11, new_p_a), searchData(12, new_p_a)]],
              'colours': ['#D4D4D4', '#F1C40F'] }
    return new_data

def getBarDataFinancial(request, currency,anio):
    lst = [0] * 12
    try:
        now = datetime.datetime.now()
        curr_year = int(request.data['until_year'])
    except Exception as er:
        now = datetime.datetime.now()
        curr_year = now.year

    p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org'), f_currency = currency).exclude(status = 0).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('p_total')).order_by('month')
    new_p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org'), f_currency = currency).exclude(status = 0).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('p_total')).order_by('month')
    ant_p_a = Polizas.objects.filter(start_of_validity__year = curr_year-1, org_name = request.GET.get('org'), f_currency = currency).exclude(status = 0).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('p_total')).order_by('month')
    ant_new_p_a = Polizas.objects.filter(start_of_validity__year = curr_year-1, org_name = request.GET.get('org'), f_currency = currency).exclude(status = 0).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('p_total')).order_by('month')
    if anio ==1:
         data = {'labels':["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
            'series': ["Prima Total Actual "+str(curr_year)],
            'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)]],
            }
    elif anio ==2:
        data = {'labels':["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
            'series': ["Prima Total Año Anterior "+str(curr_year-1)],
            'data': [[searchData(1, ant_p_a), searchData(2, ant_p_a), searchData(3, ant_p_a), searchData(4, ant_p_a), searchData(5, ant_p_a), searchData(6, ant_p_a), searchData(7, ant_p_a), searchData(8, ant_p_a), searchData(9, ant_p_a), searchData(10, ant_p_a), searchData(11, ant_p_a), searchData(12, ant_p_a)]],
            }
    else:
        data = {'labels':["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
            'series': ["Prima Total Actual "+str(curr_year),"Prima Total Año Anterior "+str(curr_year-1)],
            'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)],
            [searchData(1, ant_p_a), searchData(2, ant_p_a), searchData(3, ant_p_a), searchData(4, ant_p_a), searchData(5, ant_p_a), searchData(6, ant_p_a), searchData(7, ant_p_a), searchData(8, ant_p_a), searchData(9, ant_p_a), searchData(10, ant_p_a), searchData(11, ant_p_a), searchData(12, ant_p_a)]],
            }

    return data
# Subramos OK
def getPolarDataFinancial(request, currency,anio):
    lst = [0] * 12
    try:
        now = request.data['until_year']
        curr_year = now
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year
    try:
        now = int(request.data['until_year'])
        curr_year =now
        dic31 = '31/12/'+str(now)+' 23:59:59'
        ene01 = '01/01/'+str(now)+' 00:00:00'
    except Exception as err:
        now = datetime.datetime.now()
        curr_year = now.year
        dic31 = '31/12/'+str(now.year)+' 23:59:59'
        ene01 = '01/01/'+str(now.year)+' 00:00:00'

    f = "%d/%m/%Y %H:%M:%S"     
    date31 = datetime.datetime.strptime(dic31 , f)
    date01 = datetime.datetime.strptime(ene01 , f)
    # p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org'), f_currency = currency).exclude(status = 0)
    new_p_a = Recibos.objects.filter(fecha_inicio__gte = date01,fecha_inicio__lte = date31, org_name = request.GET.get('org'), status__in = [1,5,6], poliza__f_currency = currency).exclude(poliza__status = 0)
    #                       ***********************----------------************************
    org = request.GET.get('org')
    users = list(User.objects.values_list('pk', flat=True))
    providers = list(Provider.objects.filter(org_name = org).values_list('pk', flat=True))
    cves = list(Claves.objects.filter(org_name = org).values_list('pk', flat=True))
    bonos = Bonos.objects.filter(org_name = org, 
                                     aseguradora__in = providers,
                                     clave__in = cves,
                                     owner__in = users)
    ramos = list(Ramos.objects.filter(org_name = org, provider__in = providers).values_list('pk', flat=True))
    subramos = list(SubRamos.objects.filter(org_name = org, ramo__in = ramos).values_list('pk', flat=True))
    polizas = Polizas.objects.filter(org_name = org,
                                         aseguradora__in = providers,
                                         ramo__in = ramos,
                                         subramo__in = subramos,
                                         clave__in = cves,
                                         owner__in = users).exclude(status__in = [1,2,0]).exclude(document_type__in = [2,6,10])
    parents = polizas.filter(document_type = 3)
    subgrupos = Polizas.objects.filter(parent__id__in = parents.values_list('pk', flat = True), document_type = 4, org_name = org).values_list('id', flat = True)
    recibos1 = Recibos.objects.filter(Q(poliza__in = polizas) | Q(poliza__in = subgrupos) | Q(bono__in = bonos),
                                     isActive = True, 
                                     isCopy = False,
                                     org_name = org).exclude(status__in =  [0,7,2]).filter(receipt_type__in = [1,2,3,4])
    new_p_a = recibos1.filter(fecha_inicio__gte = date01,fecha_inicio__lte = date31, org_name = request.GET.get('org'), status__in = [1,5,6], poliza__f_currency = currency).exclude(poliza__status = 0)
    #                       ***********************----------------************************

    st = [1,2,4,10,11,12,13,14,15]
    currency =currency if currency else 1
    p_a = Polizas.objects.filter(status__in = st, 
        org_name = request.GET.get('org'),
        ramo__in = ramos, 
        subramo__in = subramos, 
        aseguradora__in = providers,
        clave__in = cves,
        owner__in = users,start_of_validity__year = curr_year,document_type__in = list([1,3,11,12]), f_currency = currency)
    subramos_1 = p_a.values('subramo__subramo_code').annotate(Sum('p_neta')).order_by('subramo__subramo_name')
    anterior1 = Polizas.objects.filter(status__in = st, 
        org_name = request.GET.get('org'),
        ramo__in = ramos, 
        subramo__in = subramos, 
        aseguradora__in = providers,
        clave__in = cves,
        owner__in = users,start_of_validity__year = (int(curr_year-1)),document_type__in = list([1,3,11,12]), f_currency = currency)

    antsubramos = anterior1.values('subramo__subramo_code').annotate(Sum('p_neta')).order_by('subramo__subramo_name')

    if anio ==1:        
        data = {'labels':["Vida", "GM", "Salud", "AP", "Autos", 'RC', 'Marítimo y Transportes', 'Incendio', 'Agrícola', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Riesgos Catastróficos'],
                             'series': ["Vida", "Gastos Médicos", "Salud", "Accidentes y Enfermedades", "Automóviles", 'Responsabilidad Civil y Riesgos Profesionales', 'Marítimo y Transportes', 'Incendio', 'Agrícola y de Animales', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Terremoto y Otros Riesgos Catastróficos'],
                             'data':[[searchDataSubramos(1, subramos_1), 
                                    searchDataSubramos(3, subramos_1), 
                                    searchDataSubramos(4, subramos_1), 
                                    searchDataSubramos(2, subramos_1), 
                                    searchDataSubramos(9, subramos_1), 
                                    searchDataSubramos(5, subramos_1), 
                                    searchDataSubramos(6, subramos_1), 
                                    searchDataSubramos(7, subramos_1), 
                                    searchDataSubramos(8, subramos_1), 
                                    searchDataSubramos(10, subramos_1), 
                                    searchDataSubramos(11, subramos_1), 
                                    searchDataSubramos(12, subramos_1), 
                                    searchDataSubramos(13, subramos_1), 
                                    searchDataSubramos(14, subramos_1)],
                                    [searchDataSubramos(1, antsubramos), 
                                    searchDataSubramos(3, antsubramos), 
                                    searchDataSubramos(4, antsubramos), 
                                    searchDataSubramos(2, antsubramos), 
                                    searchDataSubramos(9, antsubramos), 
                                    searchDataSubramos(5, antsubramos), 
                                    searchDataSubramos(6, antsubramos), 
                                    searchDataSubramos(7, antsubramos), 
                                    searchDataSubramos(8, antsubramos), 
                                    searchDataSubramos(10, antsubramos), 
                                    searchDataSubramos(11, antsubramos), 
                                    searchDataSubramos(12, antsubramos), 
                                    searchDataSubramos(13, antsubramos), 
                                    searchDataSubramos(14, antsubramos)]                   
                                ],
                             'colours': ['#9B59B6', '#D4D4D4', '#2980B9', '#01A9DB', '#1ABC9C', '#61380B', '#00FF80', '#F7819F', '#F1C40F', '#F39C12', '#E67E22', '#D35400', '#C0392B', '#E74C3C'] }
    
    elif anio ==2:
        data = {'labels':["Vida", "GM", "Salud", "AP", "Autos", 'RC', 'Marítimo y Transportes', 'Incendio', 'Agrícola', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Riesgos Catastróficos'],
                             'series': ["Vida", "Gastos Médicos", "Salud", "Accidentes y Enfermedades", "Automóviles", 'Responsabilidad Civil y Riesgos Profesionales', 'Marítimo y Transportes', 'Incendio', 'Agrícola y de Animales', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Terremoto y Otros Riesgos Catastróficos'],
                             'data': [[searchDataSubramos(1, antsubramos), 
                                    searchDataSubramos(3, antsubramos), 
                                    searchDataSubramos(4, antsubramos), 
                                    searchDataSubramos(2, antsubramos), 
                                    searchDataSubramos(9, antsubramos), 
                                    searchDataSubramos(5, antsubramos), 
                                    searchDataSubramos(6, antsubramos), 
                                    searchDataSubramos(7, antsubramos), 
                                    searchDataSubramos(8, antsubramos), 
                                    searchDataSubramos(10, antsubramos), 
                                    searchDataSubramos(11, antsubramos), 
                                    searchDataSubramos(12, antsubramos), 
                                    searchDataSubramos(13, antsubramos), 
                                    searchDataSubramos(14, antsubramos)]],
                             'colours': ['#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4', '#D4D4D4'] }
    else:
        data = {'labels':["Vida", "GM", "Salud", "AP", "Autos", 'RC', 'Marítimo y Transportes', 'Incendio', 'Agrícola', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Riesgos Catastróficos'],
                             'series': ["Vida", "Gastos Médicos", "Salud", "Accidentes y Enfermedades", "Automóviles", 'Responsabilidad Civil y Riesgos Profesionales', 'Marítimo y Transportes', 'Incendio', 'Agrícola y de Animales', 'Crédito', 'Crédito a la Vivienda', 'Garantía Financiera' , 'Diversos', 'Terremoto y Otros Riesgos Catastróficos'],
                             'data': [[searchDataSubramos(1, subramos_1), 
                                    searchDataSubramos(3, subramos_1), 
                                    searchDataSubramos(4, subramos_1), 
                                    searchDataSubramos(2, subramos_1), 
                                    searchDataSubramos(9, subramos_1), 
                                    searchDataSubramos(5, subramos_1), 
                                    searchDataSubramos(6, subramos_1), 
                                    searchDataSubramos(7, subramos_1), 
                                    searchDataSubramos(8, subramos_1), 
                                    searchDataSubramos(10, subramos_1), 
                                    searchDataSubramos(11, subramos_1), 
                                    searchDataSubramos(12, subramos_1), 
                                    searchDataSubramos(13, subramos_1), 
                                    searchDataSubramos(14, subramos_1)]],
                             'colours': ['#9B59B6', '#DF01A5', '#2980B9', '#01A9DB', '#1ABC9C', '#61380B', '#00FF80', '#F7819F', '#F1C40F', '#F39C12', '#E67E22', '#D35400', '#C0392B', '#E74C3C'] }

    return data

def getBarDataProduction(request, currency,anio):
    lst = [0] * 12
    try:
        now = int(request.data['until_year'])
        curr_year =now
        dic31 = '31/12/'+str(now)+' 23:59:59'
        ene01 = '01/01/'+str(now)+' 00:00:00'
        anterior_dic31 = '31/12/'+str(now-1)+' 23:59:59'
        anterior_ene01 = '01/01/'+str(now-1)+' 00:00:00'
    except Exception as err:
        now = datetime.datetime.now()
        curr_year = now.year
        dic31 = '31/12/'+str(now.year)+' 23:59:59'
        ene01 = '01/01/'+str(now.year)+' 00:00:00'
        anterior_dic31 = '31/12/'+str(now.year-1)+' 23:59:59'
        anterior_ene01 = '01/01/'+str(now.year-1)+' 00:00:00'

    f = "%d/%m/%Y %H:%M:%S"     
    date31 = datetime.datetime.strptime(dic31 , f)
    date01 = datetime.datetime.strptime(ene01 , f)
    anteriordate31 = datetime.datetime.strptime(anterior_dic31 , f)
    anteriordate01 = datetime.datetime.strptime(anterior_ene01 , f)
    p_a = Polizas.objects.filter(start_of_validity__year = curr_year, org_name = request.GET.get('org'), f_currency = currency).exclude(status = 0).annotate(month = Month('start_of_validity')).values('month').annotate(total = Sum('comision')).order_by('month')
    new_p_a = Recibos.objects.filter(fecha_inicio__gte = date01, fecha_inicio__lte = date31, status__in = [1,5,6], org_name = request.GET.get('org')).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    #                       ***********************----------------************************
    org = request.GET.get('org')
    users = list(User.objects.values_list('pk', flat=True))
    providers = list(Provider.objects.filter(org_name = org).values_list('pk', flat=True))
    cves = list(Claves.objects.filter(org_name = org).values_list('pk', flat=True))
    bonos = Bonos.objects.filter(org_name = org, 
                                     aseguradora__in = providers,
                                     clave__in = cves,
                                     owner__in = users)
    ramos = list(Ramos.objects.filter(org_name = org, provider__in = providers).values_list('pk', flat=True))
    subramos = list(SubRamos.objects.filter(org_name = org, ramo__in = ramos).values_list('pk', flat=True))
    polizas = Polizas.objects.filter(org_name = org,
                                         aseguradora__in = providers,
                                         ramo__in = ramos,
                                         subramo__in = subramos,
                                         clave__in = cves,
                                         owner__in = users).exclude(status__in = [1,2,0]).exclude(document_type__in = [2,6,10])
    parents = polizas.filter(document_type = 3)
    subgrupos = Polizas.objects.filter(parent__id__in = parents.values_list('pk', flat = True), document_type = 4, org_name = org).values_list('id', flat = True)
    recibos1 = Recibos.objects.filter(Q(poliza__in = polizas) | Q(poliza__in = subgrupos) | Q(bono__in = bonos),
                                     isActive = True, 
                                     isCopy = False,
                                     org_name = org).exclude(status__in =  [0,7,2]).filter(receipt_type__in = [1,2,3,4])
    new_p_a = recibos1.filter(fecha_inicio__gte = date01, fecha_inicio__lte = date31, status__in = [1,5,6], org_name = request.GET.get('org')).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    anterior_new_p_a = recibos1.filter(fecha_inicio__gte = anteriordate01, fecha_inicio__lte = anteriordate31, status__in = [1,5,6], org_name = request.GET.get('org')).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    #                       ***********************----------------************************
    if anio ==1:
        new_data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Comisión"],
          'data': [[searchData(1, new_p_a), searchData(2, new_p_a), searchData(3, new_p_a), searchData(4, new_p_a), searchData(5, new_p_a), searchData(6, new_p_a), searchData(7, new_p_a), searchData(8, new_p_a), searchData(9, new_p_a), searchData(10, new_p_a), searchData(11, new_p_a), searchData(12, new_p_a)]],
          'colours': ['#E67E22'] }
    elif anio ==2:
        new_data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Comisión"],
          'data': [[searchData(1, anterior_new_p_a), searchData(2, anterior_new_p_a), searchData(3, anterior_new_p_a), searchData(4, anterior_new_p_a), searchData(5, anterior_new_p_a), searchData(6, anterior_new_p_a), searchData(7, anterior_new_p_a), searchData(8, anterior_new_p_a), searchData(9, anterior_new_p_a), searchData(10, anterior_new_p_a), searchData(11, anterior_new_p_a), searchData(12, anterior_new_p_a)]],
          'colours': ['#D4D4D4'] }
    else:
        new_data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Comisión"],
          'data': [[searchData(1, new_p_a), searchData(2, new_p_a), searchData(3, new_p_a), searchData(4, new_p_a), searchData(5, new_p_a), searchData(6, new_p_a), searchData(7, new_p_a), searchData(8, new_p_a), searchData(9, new_p_a), searchData(10, new_p_a), searchData(11, new_p_a), searchData(12, new_p_a)]],
          'colours': ['#E67E22'] }

    # return data
    return new_data

def getBarDataCotizacion(request, currency,anio):
    lst = [0] * 12
    try:
        now = int(request.data['until_year'])
        curr_year = now
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year        

    p_a = Cotizacion.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')
    anterior_p_a = Cotizacion.objects.filter(created_at__year = (curr_year-1), org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')
    if anio ==1:
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Cotizacion"],
          'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)]],
          'colours': ['#E67E22'] }
    elif anio ==2:
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Cotizacion"],
          'data': [[searchData(1, anterior_p_a), searchData(2, anterior_p_a), searchData(3, anterior_p_a), searchData(4, anterior_p_a), searchData(5, anterior_p_a), searchData(6, anterior_p_a), searchData(7, anterior_p_a), searchData(8, anterior_p_a), searchData(9, anterior_p_a), searchData(10, anterior_p_a), searchData(11, anterior_p_a), searchData(12, anterior_p_a)]],
          'colours': ['#D4D4D4'] }
    else:
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ["Cotizacion"],
          'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)]],
          'colours': ['#E67E22'] }

    return data

def getMonthsBateo(request,currency,anio):
    lst = [0] * 12
    try:
        now = int(request.data['until_year'])
        curr_year = now
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year

    p_a = Cotizacion.objects.filter(status = 3, created_at__year = curr_year, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')
    anteriorp_a = Cotizacion.objects.filter(status = 3, created_at__year = (curr_year-1), org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')

    if anio ==1:
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
    elif anio ==2:

        data = [{'month': 'Enero', 'value': searchData(1, anteriorp_a)},
          {'month': 'Febrero', 'value': searchData(2, anteriorp_a)},
          {'month': 'Marzo', 'value': searchData(3, anteriorp_a)},
          {'month': 'Abril', 'value': searchData(4, anteriorp_a)},
          {'month': 'Mayo', 'value': searchData(5, anteriorp_a)},
          {'month': 'Junio', 'value': searchData(6, anteriorp_a)},
          {'month': 'Julio', 'value': searchData(7, anteriorp_a)},
          {'month': 'Agosto', 'value': searchData(8, anteriorp_a)},
          {'month': 'Septiembre', 'value': searchData(9, anteriorp_a)},
          {'month': 'Octubre', 'value': searchData(10, anteriorp_a)},
          {'month': 'Noviembre', 'value': searchData(11, anteriorp_a)},
          {'month': 'Diciembre', 'value': searchData(12, anteriorp_a)} ]
    else:        
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

def getMonthsUtilidad(request, recibos, currency, recibos2,anio):
    lst = [0] * 12
    try: 
        tipocambio = request.data['tipocambio']
        try:
            tipocambio = ConfigKbi.objects.filter(owner = request.user,org_name = request.GET.get('org'))
            tipocambio = float(tipocambio[0].tipocambio)
        except ConfigKbi.DoesNotExist:
            tipocambio = request.data['tipocambio']
    except:
        tipocambio = 20
    try:
        now = int(request.data['until_year'])
        curr_year = now
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year

    p_a = Expenses.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).values('month').annotate(Sum('cantidad'))
    recibos_mes = recibos.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org'), poliza__f_currency = currency).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    recibos_mes_dolar = recibos2.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org'), poliza__f_currency = 2).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    for r2 in recibos_mes_dolar:
        r2['total'] = float(r2['total']) * float(tipocambio)
        for r1 in recibos_mes:
            if r2['month'] == r1['month']:
                r1['total'] = float(r1['total'])+float(r2['total'])
    anterior_p_a = Expenses.objects.filter(created_at__year = curr_year-1, org_name = request.GET.get('org')).values('month').annotate(Sum('cantidad'))
    anterior_recibos_mes = recibos.filter(fecha_inicio__year = (curr_year-1), org_name = request.GET.get('org'), poliza__f_currency = currency).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    anterior_recibos_mes_dolar = recibos2.filter(fecha_inicio__year = (curr_year-1), org_name = request.GET.get('org'), poliza__f_currency = 2).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    for r3 in anterior_recibos_mes_dolar:
        r3['total'] = float(r3['total']) * float(tipocambio)
        for r4 in anterior_recibos_mes:
            if r3['month'] == r4['month']:
                r4['total'] = float(r4['total'])+float(r3['total'])
    if anio ==1:
        data = [{'month': 'Enero', 'value': (searchData(1, recibos_mes) - searchDataSum(1, p_a))},
          {'month': 'Febrero', 'value': (searchData(2, recibos_mes) - searchDataSum(2, p_a))},
          {'month': 'Marzo', 'value': (searchData(3, recibos_mes) - searchDataSum(3, p_a))},
          {'month': 'Abril', 'value': (searchData(4, recibos_mes) - searchDataSum(4, p_a))},
          {'month': 'Mayo', 'value': (searchData(5, recibos_mes) - searchDataSum(5, p_a))},
          {'month': 'Junio', 'value': (searchData(6, recibos_mes) - searchDataSum(6, p_a))},
          {'month': 'Julio', 'value': (searchData(7, recibos_mes) - searchDataSum(7, p_a))},
          {'month': 'Agosto', 'value': (searchData(8, recibos_mes) - searchDataSum(8, p_a))},
          {'month': 'Septiembre', 'value': (searchData(9, recibos_mes) - searchDataSum(9, p_a))},
          {'month': 'Octubre', 'value': (searchData(10, recibos_mes) - searchDataSum(10, p_a))},
          {'month': 'Noviembre', 'value': (searchData(11, recibos_mes) - searchDataSum(11, p_a))},
          {'month': 'Diciembre', 'value': (searchData(12, recibos_mes) - searchDataSum(12, p_a))} ]
    elif anio ==2:
        data = [{'month': 'Enero', 'value': (searchData(1, anterior_recibos_mes) - searchDataSum(1, anterior_p_a))},
          {'month': 'Febrero', 'value': (searchData(2, anterior_recibos_mes) - searchDataSum(2, anterior_p_a))},
          {'month': 'Marzo', 'value': (searchData(3, anterior_recibos_mes) - searchDataSum(3, anterior_p_a))},
          {'month': 'Abril', 'value': (searchData(4, anterior_recibos_mes) - searchDataSum(4, anterior_p_a))},
          {'month': 'Mayo', 'value': (searchData(5, anterior_recibos_mes) - searchDataSum(5, anterior_p_a))},
          {'month': 'Junio', 'value': (searchData(6, anterior_recibos_mes) - searchDataSum(6, anterior_p_a))},
          {'month': 'Julio', 'value': (searchData(7, anterior_recibos_mes) - searchDataSum(7, anterior_p_a))},
          {'month': 'Agosto', 'value': (searchData(8, anterior_recibos_mes) - searchDataSum(8, anterior_p_a))},
          {'month': 'Septiembre', 'value': (searchData(9, anterior_recibos_mes) - searchDataSum(9, anterior_p_a))},
          {'month': 'Octubre', 'value': (searchData(10, anterior_recibos_mes) - searchDataSum(10, anterior_p_a))},
          {'month': 'Noviembre', 'value': (searchData(11, anterior_recibos_mes) - searchDataSum(11, anterior_p_a))},
          {'month': 'Diciembre', 'value': (searchData(12, anterior_recibos_mes) - searchDataSum(12, anterior_p_a))} ]
    else:
        data = [{'month': 'Enero', 'value': (searchData(1, recibos_mes) - searchDataSum(1, p_a)), 'value_dolar': (searchData(1, recibos_mes_dolar) - searchDataSum(1, p_a))},
          {'month': 'Febrero', 'value': (searchData(2, recibos_mes) - searchDataSum(2, p_a)), 'value_dolar': (searchData(2, recibos_mes_dolar) - searchDataSum(2, p_a))},
          {'month': 'Marzo', 'value': (searchData(3, recibos_mes) - searchDataSum(3, p_a)), 'value_dolar': (searchData(3, recibos_mes_dolar) - searchDataSum(3, p_a))},
          {'month': 'Abril', 'value': (searchData(4, recibos_mes) - searchDataSum(4, p_a)), 'value_dolar': (searchData(4, recibos_mes_dolar) - searchDataSum(4, p_a))},
          {'month': 'Mayo', 'value': (searchData(5, recibos_mes) - searchDataSum(5, p_a)), 'value_dolar': (searchData(5, recibos_mes_dolar) - searchDataSum(5, p_a))},
          {'month': 'Junio', 'value': (searchData(6, recibos_mes) - searchDataSum(6, p_a)), 'value_dolar': (searchData(6, recibos_mes_dolar) - searchDataSum(6, p_a))},
          {'month': 'Julio', 'value': (searchData(7, recibos_mes) - searchDataSum(7, p_a)), 'value_dolar': (searchData(7, recibos_mes_dolar) - searchDataSum(7, p_a))},
          {'month': 'Agosto', 'value': (searchData(8, recibos_mes) - searchDataSum(8, p_a)), 'value_dolar': (searchData(8, recibos_mes_dolar) - searchDataSum(8, p_a))},
          {'month': 'Septiembre', 'value': (searchData(9, recibos_mes) - searchDataSum(9, p_a)), 'value_dolar': (searchData(9, recibos_mes_dolar) - searchDataSum(9, p_a))},
          {'month': 'Octubre', 'value': (searchData(10, recibos_mes) - searchDataSum(10, p_a)), 'value_dolar': (searchData(10, recibos_mes_dolar) - searchDataSum(10, p_a))},
          {'month': 'Noviembre', 'value': (searchData(11, recibos_mes) - searchDataSum(11, p_a)), 'value_dolar': (searchData(11, recibos_mes_dolar) - searchDataSum(11, p_a))},
          {'month': 'Diciembre', 'value': (searchData(12, recibos_mes) - searchDataSum(12, p_a)), 'value_dolar': (searchData(12, recibos_mes_dolar) - searchDataSum(12, p_a))} ]

    return data

def getBarDataGastos(request, recibos, currency, recibos2,anio):
    lst = [0] * 12
    try:
        now = int(request.data['until_year'])
        curr_year = now
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year
    try: 
        tipocambio = request.data['tipocambio']
        try:
            tipocambio = ConfigKbi.objects.filter(owner = request.user,org_name = request.GET.get('org'))
            tipocambio = float(tipocambio[0].tipocambio)
        except ConfigKbi.DoesNotExist:
            tipocambio = 20
    except:
        tipocambio = 20        

    p_a = Expenses.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).values('month').annotate(Sum('cantidad'))
    p_a_serializer = Expenses.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org'))
    ser_expenses = ExpensesInfoSerializer(p_a_serializer,context={'request':request}, many= True)
    recibos_mes = recibos.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org'), poliza__f_currency = currency).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    recibos_mes_dolar = recibos2.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org'), poliza__f_currency = 2).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    for r2 in recibos_mes_dolar:
        r2['total'] = float(r2['total']) * float(tipocambio)
        for r1 in recibos_mes:
            if r2['month'] == r1['month']:
                r1['total'] = float(r1['total'])+float(r2['total'])
    #anterior
    antp_a = Expenses.objects.filter(created_at__year = curr_year-1, org_name = request.GET.get('org')).values('month').annotate(Sum('cantidad'))
    antp_a_serializer = Expenses.objects.filter(created_at__year = curr_year-1, org_name = request.GET.get('org'))
    antser_expenses = ExpensesInfoSerializer(antp_a_serializer,context={'request':request}, many= True)
    antrecibos_mes = recibos.filter(fecha_inicio__year = (curr_year-1), org_name = request.GET.get('org'), poliza__f_currency = currency).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    antrecibos_mes_dolar = recibos2.filter(fecha_inicio__year = (curr_year-1), org_name = request.GET.get('org'), poliza__f_currency = 2).annotate(month = Month('fecha_inicio')).values('month').annotate(total = Sum('comision')).order_by('month')
    for r2 in antrecibos_mes_dolar:
        r2['total'] = float(r2['total']) * float(tipocambio)
        for r1 in antrecibos_mes:
            if r2['month'] == r1['month']:
                r1['total'] = float(r1['total'])+float(r2['total'])
    if anio ==1:
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ['Gastos', 'Comisiones MXN','Comisiones USD'],
          'data': [[searchDataSum(1, p_a), searchDataSum(2, p_a), searchDataSum(3, p_a), searchDataSum(4, p_a), searchDataSum(5, p_a), searchDataSum(6, p_a), searchDataSum(7, p_a), searchDataSum(8, p_a), searchDataSum(9, p_a), searchDataSum(10, p_a), searchDataSum(11, p_a), searchDataSum(12, p_a)],
                   [searchData(1, recibos_mes), searchData(2, recibos_mes), searchData(3, recibos_mes), searchData(4, recibos_mes), searchData(5, recibos_mes), searchData(6, recibos_mes), searchData(7, recibos_mes), searchData(8, recibos_mes), searchData(9, recibos_mes), searchData(10, recibos_mes), searchData(11, recibos_mes), searchData(12, recibos_mes)]                   
                   ],
          'colours': ['#E74C3C', '#949FB1'],
          'concepts': ser_expenses.data }

        comSumRecs = recibos.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('comision'))
        comSumRecs_dolar = recibos2.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('comision'))
        sumGastos = Expenses.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('cantidad'))
        comSumRecs_dolar['comision__sum'] = float(comSumRecs_dolar['comision__sum']) if comSumRecs_dolar['comision__sum'] else 0 * float(tipocambio)
        comSumRecs['comision__sum'] = float(comSumRecs['comision__sum']) if comSumRecs['comision__sum'] else 0 +float(comSumRecs_dolar['comision__sum'])
        try:
            utilidadneta = float(comSumRecs['comision__sum']) - float(sumGastos['cantidad__sum'])
            utilidadneta_dolar = float(comSumRecs_dolar['comision__sum']) - float(sumGastos['cantidad__sum'])
        except Exception as er:
            utilidadneta = 0
            utilidadneta_dolar = 0
        data['utilidadneta'] = utilidadneta
        data['utilidadneta_dolar'] = utilidadneta_dolar
    elif anio ==2:
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ['Gastos', 'Comisiones MXN','Comisiones USD'],
          'data': [[searchDataSum(1, antp_a), searchDataSum(2, antp_a), searchDataSum(3, antp_a), searchDataSum(4, antp_a), searchDataSum(5, antp_a), searchDataSum(6, antp_a), searchDataSum(7, antp_a), searchDataSum(8, antp_a), searchDataSum(9, antp_a), searchDataSum(10, antp_a), searchDataSum(11, antp_a), searchDataSum(12, antp_a)],
                   [searchData(1, antrecibos_mes), searchData(2, antrecibos_mes), searchData(3, antrecibos_mes), searchData(4, antrecibos_mes), searchData(5, antrecibos_mes), searchData(6, antrecibos_mes), searchData(7, antrecibos_mes), searchData(8, antrecibos_mes), searchData(9, antrecibos_mes), searchData(10, antrecibos_mes), searchData(11, antrecibos_mes), searchData(12, antrecibos_mes)]                   
                   ],
          'colours': ['#D4D4D4', '#64696A'],
          'concepts': antser_expenses.data }

        comSumRecs = recibos.filter(fecha_inicio__year = (curr_year-1), org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('comision'))
        comSumRecs_dolar = recibos2.filter(fecha_inicio__year = (curr_year-1), org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('comision'))
        sumGastos = Expenses.objects.filter(created_at__year = curr_year-1, org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('cantidad'))
        comSumRecs_dolar['comision__sum'] = float(comSumRecs_dolar['comision__sum']) if comSumRecs_dolar['comision__sum'] else 0 * float(tipocambio)
        comSumRecs['comision__sum'] = float(comSumRecs['comision__sum'] if comSumRecs['comision__sum'] else 0)+float(comSumRecs_dolar['comision__sum'])
        try:
            utilidadneta = float(comSumRecs['comision__sum']) - float(sumGastos['cantidad__sum'])
            utilidadneta_dolar = float(comSumRecs_dolar['comision__sum']) - float(sumGastos['cantidad__sum'])
        except Exception as er:
            utilidadneta = 0
            utilidadneta_dolar = 0
        data['utilidadneta'] = utilidadneta
        data['utilidadneta_dolar'] = utilidadneta_dolar
    else:
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
          'series': ['Gastos', 'Comisiones MXN','Comisiones USD'],
          'data': [[searchDataSum(1, p_a), searchDataSum(2, p_a), searchDataSum(3, p_a), searchDataSum(4, p_a), searchDataSum(5, p_a), searchDataSum(6, p_a), searchDataSum(7, p_a), searchDataSum(8, p_a), searchDataSum(9, p_a), searchDataSum(10, p_a), searchDataSum(11, p_a), searchDataSum(12, p_a)],
                   [searchData(1, recibos_mes), searchData(2, recibos_mes), searchData(3, recibos_mes), searchData(4, recibos_mes), searchData(5, recibos_mes), searchData(6, recibos_mes), searchData(7, recibos_mes), searchData(8, recibos_mes), searchData(9, recibos_mes), searchData(10, recibos_mes), searchData(11, recibos_mes), searchData(12, recibos_mes)],
                   [searchData(1, recibos_mes_dolar), searchData(2, recibos_mes_dolar), searchData(3, recibos_mes_dolar), searchData(4, recibos_mes_dolar), searchData(5, recibos_mes_dolar), searchData(6, recibos_mes_dolar), searchData(7, recibos_mes_dolar), searchData(8, recibos_mes_dolar), searchData(9, recibos_mes_dolar), searchData(10, recibos_mes_dolar), searchData(11, recibos_mes_dolar), searchData(12, recibos_mes_dolar)]
                   ],
          'colours': ['#E74C3C', '#949FB1', '#EA6AF7'],
          'concepts': ser_expenses.data }

        comSumRecs = recibos.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('comision'))
        comSumRecs_dolar = recibos2.filter(fecha_inicio__year = (curr_year), org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('comision'))
        sumGastos = Expenses.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).values('org_name').annotate(Count('org_name')).aggregate(Sum('cantidad'))
        comSumRecs_dolar['comision__sum'] = float(comSumRecs_dolar['comision__sum'] if comSumRecs_dolar['comision__sum'] else 0) * tipocambio
        comSumRecs['comision__sum'] = float(comSumRecs['comision__sum'] if comSumRecs['comision__sum'] else 0)+float(comSumRecs_dolar['comision__sum'])
        try:
            utilidadneta = float(comSumRecs['comision__sum']) - float(sumGastos['cantidad__sum'])
            utilidadneta_dolar = float(comSumRecs_dolar['comision__sum']) - float(sumGastos['cantidad__sum'])
        except Exception as er:
            utilidadneta = 0
            utilidadneta_dolar = 0
        data['utilidadneta'] = utilidadneta
        data['utilidadneta_dolar'] = utilidadneta_dolar
    return data

def getChartDataCotizacion(request, currency,anio):
    lst = [0] * 12
    try:
        now = int(request.data['until_year'])
        curr_year = now
    except Exception as e:
        now = datetime.datetime.now()
        curr_year = now.year

    p_a = Cotizacion.objects.filter(created_at__year = curr_year, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')
    p_l = Cotizacion.objects.filter(status = 2, created_at__year = curr_year, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')
    anterior_p_a = Cotizacion.objects.filter(created_at__year = curr_year-1, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')
    anterior_p_l = Cotizacion.objects.filter(status = 2, created_at__year = curr_year-1, org_name = request.GET.get('org')).annotate(month = Month('created_at')).values('month').annotate(total = Count('id')).order_by('month')

    if anio ==1:
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': ['Cotización', 'Emisión'],
              'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)],
                       [searchData(1, p_l), searchData(2, p_l), searchData(3, p_l), searchData(4, p_l), searchData(5, p_l), searchData(6, p_l), searchData(7, p_l), searchData(8, p_l), searchData(9, p_l), searchData(10, p_l), searchData(11, p_l), searchData(12, p_l)]],
              'colours': ['#27AE60', '#884EA0'] }
    elif anio ==2:        
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': ['Cotización', 'Emisión'],
              'data': [[searchData(1, anterior_p_a), searchData(2, anterior_p_a), searchData(3, anterior_p_a), searchData(4, anterior_p_a), searchData(5, anterior_p_a), searchData(6, anterior_p_a), searchData(7, anterior_p_a), searchData(8, anterior_p_a), searchData(9, anterior_p_a), searchData(10, anterior_p_a), searchData(11, anterior_p_a), searchData(12, anterior_p_a)],
                       [searchData(1, anterior_p_l), searchData(2, anterior_p_l), searchData(3, anterior_p_l), searchData(4, anterior_p_l), searchData(5, anterior_p_l), searchData(6, anterior_p_l), searchData(7, anterior_p_l), searchData(8, anterior_p_l), searchData(9, anterior_p_l), searchData(10, anterior_p_l), searchData(11, anterior_p_l), searchData(12, anterior_p_l)]],
              'colours': ['#D4D4D4', '#64696A'] }
    else:
        data = {'labels': ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
              'series': ['Cotización', 'Emisión'],
              'data': [[searchData(1, p_a), searchData(2, p_a), searchData(3, p_a), searchData(4, p_a), searchData(5, p_a), searchData(6, p_a), searchData(7, p_a), searchData(8, p_a), searchData(9, p_a), searchData(10, p_a), searchData(11, p_a), searchData(12, p_a)],
                       [searchData(1, p_l), searchData(2, p_l), searchData(3, p_l), searchData(4, p_l), searchData(5, p_l), searchData(6, p_l), searchData(7, p_l), searchData(8, p_l), searchData(9, p_l), searchData(10, p_l), searchData(11, p_l), searchData(12, p_l)]],
              'colours': ['#27AE60', '#884EA0'] }

    return data

class ResponsablesViewSet(viewsets.ModelViewSet):
    serializer_class = RespInvolvedHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data, many = isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(org_name = self.request.GET.get('org'))
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        return custom_get_queryset(self.request, ResponsablesInvolved)

class ReferenciadoresViewSet(viewsets.ModelViewSet):
    serializer_class = RefInvolvedHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data, many = isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(org_name=self.request.GET.get('org'))
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        return custom_get_queryset(self.request, ReferenciadoresInvolved)
@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def GetReportLog(request):
    # Parameters
    start_time=time.perf_counter()
    usuarios = request.data['users']
    model = request.data['model']
    since = request.data['since']
    until = request.data['until']
    group_by = request.data['groupBy']
    # Multiples users
    if usuarios:
        users = list(User.objects.filter(pk__in = usuarios).values_list('pk', flat=True))
    else:
        users = list(User.objects.values_list('pk', flat=True))
    # Filtro de fechas
    try:
        f = "%d/%m/%Y %H:%M:%S"
        since = datetime.datetime.strptime(since , f)
        until = datetime.datetime.strptime(until , f)
    except:
        f = "%m/%d/%Y %H:%M:%S"
        since = datetime.datetime.strptime(since , f)
        until = datetime.datetime.strptime(until , f)
    date_filters = [Q(created_at__gte=since),Q(created_at__lte = until)]

    logs = Log.objects.filter(reduce(operator.and_, date_filters)).filter(org_name = request.GET.get('org')).exclude(model=32)
    # Filtro de model
    if int(model) == 0:
        logs = logs
    else:
        if int(model) ==2:#físico
            nats = list(Contractor.objects.filter(type_person =1, org_name = request.GET.get('org')).values_list('pk', flat = True))
            logs = logs.filter(model = 26, associated_id__in = nats)
        elif int(model) ==3:#moral
            morl = list(Contractor.objects.filter(type_person =2, org_name = request.GET.get('org')).values_list('pk', flat = True))       
            logs = logs.filter(model = 26, associated_id__in = morl)        
        else:
            logs = logs.filter(model = int(model))
    # Filtro de ususarios selected
    if usuarios:
        logs = logs.filter(Q(user__in = users))
    # Agrupación no
    if int(group_by) == 0:
        logs = logs
        # serializer = LogReportSerializer(logs, context={'request':request}, many = True)
        # Paginación
        paginator = Paginator(logs, 10)
        try:
            page = request.data['page']
            results = paginator.page(page)
        except:
            results = paginator.page(1)

        serializer = LogReportSerializer(results, context={'request':request}, many = True)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        try:
            logsystem = {'data':'Reporte logs vista','conteo':len(logs),'org_name':request.GET.get('org'),
                        'user': request.user.id, 'inicio':start_time,'fin':end_time,'total':total_time}
            logs_ =send_log(request.user, request.GET.get('org'), 'GET', 32,json.dumps(logsystem),None)
        except Exception as j:
            print('--------',j)
        return JsonResponse({'results': serializer.data, 'count': len(logs)})
    else:
        try:
            if group_by == 1:
                prueba = {}
                prueba = logs.values('user__first_name','user__last_name').annotate(Sum('model')).annotate(Sum('event')).annotate(Count('user__id')).order_by('user__id')
                return Response({'results': prueba})
        except Exception as e:
            return Response({'error': 321})


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def GetReportExcelLog(request):
    # Parameters
    usuarios = request.data['users']
    model = request.data['model']
    since = request.data['since']
    until = request.data['until']
    group_by = request.data['groupBy']
    export = request.data['export_type']
    # Multiples users
    if usuarios:
        users = list(User.objects.filter(pk__in = usuarios).values_list('pk', flat=True))
    else:
        users = list(User.objects.values_list('pk', flat=True))
    # Filtro de fechas
    try:
        f = "%d/%m/%Y %H:%M:%S"
        since = datetime.datetime.strptime(since , f)
        until = datetime.datetime.strptime(until , f)
    except:
        f = "%m/%d/%Y %H:%M:%S"
        since = datetime.datetime.strptime(since , f)
        until = datetime.datetime.strptime(until , f)
    date_filters = [Q(created_at__gte=since),Q(created_at__lte = until)]

    logs = Log.objects.filter(reduce(operator.and_, date_filters)).filter(org_name = request.GET.get('org'))
    # Filtro de model
    if int(model) == 0:
        logs = logs
    else:
        logs = logs.filter(model = int(model))
    # Filtro de ususarios selected
    if usuarios:
        logs = logs.filter(Q(user__in = users))
    # Agrupación no
    if int(group_by) == 0:
        logs = logs

    else:
        try:
            if group_by == 1:
                prueba = {}
                prueba = logs.values('user__first_name','user__last_name').annotate(Count('model')).annotate(Sum('event')).annotate(Count('user__id')).order_by('user__id')
        except Exception as e:
            pass

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Reporte Transacciones.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Paquetes')

    # Empieza insertado de imagen
    info_org = getInfoOrg(request)
    if len(info_org['logo']) != 0:
        archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + info_org['logo']
    else:
        archivo_imagen = 'saam.jpg'

    if info_org['urlname'] != 'basanez':
        try:
            img = Image.open(requests.get(archivo_imagen, stream=True).raw)
            r, g, b = img.split()
            img = Image.merge("RGB", (r, g, b))
            img = img.resize((130,150),Image.ANTIALIAS)
            name_logo = info_org['urlname']+'_logo.bmp'
            img.save(name_logo)
            ws.insert_bitmap(name_logo, 0, 0)
        except Exception as e:
            img = Image.open("saam.jpg")
            r, g, b = img.split()
            img = Image.merge("RGB", (r, g, b))
            img.save('imagetoadd.bmp')
            ws.insert_bitmap('imagetoadd.bmp', 0, 0)

    company_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    company_style.pattern = pattern
    company_style = xlwt.easyxf('font: bold on, color black, height 380;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(0, 5, info_org['name'], company_style)

    text_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    text_style.pattern = pattern
    text_style = xlwt.easyxf('font: bold off, color black;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(1, 5, info_org['address'], text_style)
    ws.write(3, 5, "Tel." + info_org['phone'], text_style)
    ws.write(4, 5, info_org['email'], text_style)
    ws.write(5, 5, info_org['webpage'], text_style)

    title_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    title_style.pattern = pattern
    title_style = xlwt.easyxf('font: bold on, color black, height 280;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    row_num = 10
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    # Totales dela agrupación
    if int(export) == 1:
        font_style.font.bold = True
        columns = ['Usuario', 'Registros']

        for col_num in range(len(columns)):
            style = xlwt.XFStyle()
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            # print( xlwt.Style.colour_map)
            style = xlwt.easyxf('font: bold on, color black;\
                         borders: top_color black, bottom_color black, right_color black, left_color black,\
                                  left thin, right thin, top thin, bottom thin;\
                         pattern: pattern solid, fore_color ice_blue; align: horiz center')
            ws.write(row_num, col_num, columns[col_num], style)
        rows = prueba.values_list('user__first_name','user__last_name','user__id__count')

        for row in rows:
            row_num += 1
            for col_num in range(2):
                font_style.font.bold = False
                if col_num == 0:
                    font_style.num_format_str = 'general'
                    value = (row[col_num]) + ' '+ str(row[1])
                elif col_num == 1:
                    font_style.num_format_str = 'general'
                    value = row[2]
                else:
                    font_style.num_format_str = 'general'
                    value = row[col_num]

                try:
                    ws.write(row_num, col_num, value, font_style)
                except Exception as e:
                    value = (row[col_num].replace(tzinfo=None))
                    ws.write(row_num, col_num, value, font_style)
        final_row = int(row_num) + 2
        title = "Total: " + str(len(rows)) + " Registros"
        font_style = xlwt.easyxf('font: bold off, color black;\
                         pattern: pattern solid, fore_color white;')
        ws.write(final_row, 0, title, font_style)
        wb.save(response)
        return response

    # Desglose
    elif int(export) == 2:
        font_style.font.bold = True
        columns = ['Usuario','Acción','Modelo','Fecha Creación']

        for col_num in range(len(columns)):
            style = xlwt.XFStyle()
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            # print( xlwt.Style.colour_map)
            style = xlwt.easyxf('font: bold on, color black;\
                         borders: top_color black, bottom_color black, right_color black, left_color black,\
                                  left thin, right thin, top thin, bottom thin;\
                         pattern: pattern solid, fore_color ice_blue; align: horiz center')
            ws.write(row_num, col_num, columns[col_num], style)

        rows = logs.values_list('user__first_name','event','identifier','model','created_at','user__last_name')

        for row in rows:
            row_num += 1
            for col_num in range(4):
                font_style.font.bold = False
                if col_num == 0:
                    font_style.num_format_str = 'general'
                    value = (row[col_num]) + ' '+ str(row[5])
                elif col_num == 1:
                    font_style.num_format_str = 'general'
                    value = row[2]
                elif col_num == 2:
                    font_style.num_format_str = 'general'
                    if row[3] :
                        value = modelCheck(row[3])
                    else:
                        value = ''
                elif col_num == 3:
                    try:
                        font_style.num_format_str = 'DD/MM/YYYY'
                        value = (row[4].replace(tzinfo=None))
                    except:
                        value = row[4]
                else:
                    font_style.num_format_str = 'general'
                    value = row[col_num]

                try:
                    ws.write(row_num, col_num, value, font_style)
                except Exception as e:
                    value = (row[col_num].replace(tzinfo=None))
                    ws.write(row_num, col_num, value, font_style)
        final_row = int(row_num) + 2
        title = "Total: " + str(len(rows)) + " Registros"
        font_style = xlwt.easyxf('font: bold off, color black;\
                         pattern: pattern solid, fore_color white;')
        ws.write(final_row, 0, title, font_style)
        wb.save(response)
        return response

def modelCheck(request):
    switcher = {
        1 :'Pólizas',
        2 :'Contratantes Fisicos',
        3 :'Contratantes Morales',
        4 :'Recibos',
        5 :'Siniestros',
        6 :'Renovaciones',
        7 :'Recibos-Comisiones',
        8 :'Grupos',
        9 :'Paquetes',
        10 :'Endosos',
        11 :'Aseguradoras',
        12 : 'Estados de Cuenta',
        13 :'Fianzas',
        14 :'Afianzadoras',
        15 :'Comentarios',
        16 :'Logs',
        17 :'Cartas',
        18 :'Colectividades',
        19 :'Graphs',
        20 :'Notes',
        21 :'Fianzas Reclamaciones',
        22 :'Task'
    }
    return switcher.get(request, "No aplica")

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def get_user_by_username(request):
    org = request.GET.get('org')
    username = request.GET.get('username')
    try:
        serializer = UserSerializer(User.objects.get(username = username), context = {'request':request}, many = False)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': 321})

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def SendEmailAdmins(request):
    model = int(request.data['model'])
    id_info = int(request.data['id'])
    type_person = int(request.data['type_person'])

    email_to = []
    org = request.GET.get('org')
    if model == 1:
        type_elim = 'Endoso'
    elif model == 2:
        type_elim = 'Póliza'
    elif model == 3:
        type_elim = 'Contratante'
    elif model == 4:
        type_elim = 'Fianza'
    elif model == 5:
        type_elim = 'Siniestros'
    elif model == 6:
        type_elim = 'Archivos de Póliza'
    elif model == 7:
        type_elim = 'Archivos de Siniestros'
    elif model == 8:
        type_elim = 'Recibos'

    subject = 'Eliminación de '+str(type_elim)
    emails_admins = requests.get(settings.CAS_URL + 'get-emails/?org_id='+str(org))
    response_emails= emails_admins.text
    response = json.loads(response_emails)
    users = response['data']
    for email in users:
        if email['email']:
            email_to.append(email['email'])
    user = User.objects.get(username= request.user)
    user = user.first_name +' '+ str(user.last_name)
    fecha =  datetime.datetime.today()
    if model == 1:
        try:
            informacion = Endorsement.objects.get(id = id_info, org_name = request.GET.get('org'))
            info_type = str(informacion.internal_number) 
        except Exception as e:
            return Response({'error':'No existe el endoso'})
    elif model == 2:
        try:
            informacion = Polizas.objects.get(id = id_info, org_name = request.GET.get('org'))
            if informacion.document_type == 1 or informacion.document_type == 3:
                info_type = str(informacion.internal_number) 
            elif informacion.document_type == 4:
                try:
                    type_elim='Subgrupo'
                    info_type = str(informacion.name) +' de la póliza: '+str(informacion.parent.poliza_number) 
                except Exception as e:
                    info_type = '<strong>Eliminación del subgrupo: </strong>'+ str(informacion.name)
            elif informacion.document_type == 5:
                type_elim='Categoría'
                try:
                    info_type = str(informacion.name) +'del subgrupo: '+ str(informacion.parent.name)
                except Exception as e:
                    info_type = str(informacion.name) 
            elif informacion.document_type == 6:
                type_elim='Certificado'
                try:
                    info_type = str(informacion.certificate_number) +'de la categoría '+ str(informacion.parent.name)
                except Exception as e:
                    info_type =str(informacion.certificate_number) 
        except Exception as e:
            return Response({'error':'No existe la póliza'})
    elif model == 3:
        try:
            informacion = Contractor.objects.get(id = id_info, org_name = request.GET.get('org'))
            info_type = str(informacion.full_name) 
        except Exception as e:
            return Response({'error':'No existe el contratante'})
    elif model == 4:
        try:
            informacion = Polizas.objects.get(id = id_info, org_name = request.GET.get('org'))
            type_elim='Fianza'
            info_type = ' Folio: '+ str(informacion.internal_number) 
        except Exception as e:
            return Response({'error':'No existe la fianza'})
    elif model == 5:
        try:
            informacion = Siniestros.objects.get(id = id_info, org_name = request.GET.get('org'))
            info_type ='Folio '+ str(informacion.internal_number) 
        except Exception as e:
            return Response({'error':'No existe el siniestro'})
    elif model == 6:
        try:
            try:
                informacion =  PolizasFile.objects.get(id = id_info, org_name = request.GET.get('org'))
                info_type = str(informacion.nombre) 
            except Exception as e:
                id_poliza = int(request.data['id_poliza'])
                informacion =  Polizas.objects.get(id = id_poliza, org_name = request.GET.get('org'))
                info_type = str(informacion.poliza_number) +' folio '+str(informacion.internal_number)
                # return Response({'error':'No existe el archivo'})
        except Exception as e:
            pass
    elif model == 7:
        try:
            try:
                informacion =  SiniestrosFile.objects.get(id = id_info, org_name = request.GET.get('org'))
                info_type = str(informacion.nombre) 
            except Exception as e:
                id_sin = int(request.data['id_siniestro'])
                informacion =  Siniestros.objects.get(id = id_sin, org_name = request.GET.get('org'))
                info_type = str(informacion.numero_siniestro) +' de la póliza '+str(informacion.poliza.poliza_number)
                # return Response({'error':'No existe el archivo'})
        except Exception as e:
            pass
    elif model == 8:
        try:
            try:
                informacion =  Recibos.objects.get(id = id_info, org_name = request.GET.get('org'))
                info_type = str(informacion.recibo_numero) 
            except Exception as e:
                id_sin = int(request.data['id_poliza'])
                informacion =  Polizas.objects.get(id = id_sin, org_name = request.GET.get('org'))
                info_type = str(informacion.poliza_number) 
                # return Response({'error':'No existe el archivo'})
        except Exception as e:
            pass
    
    usuario_accion =  '<strong>Usuario que realizo la acción: </strong>'+str(user)
    message=render_to_string("correo_admins.html",{
            'concepto':type_elim,
            'fecha':fecha,
            'usuario': user,
            'org_name': request.GET.get('org'),
            'info_type': info_type,
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
    # email_to=['guadalupe.becerril@miurabox.com']
    email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_to, cc=[request.user.email])

    email.content_subtype="html"
    email.mixed_subtype = 'related'

    try:
        email.send()
        val={'status':'sent'}
        return JsonResponse(val, status=200)

        if smtplib.SMTPAuthenticationError:
            val = {'status':'Credenciales de correo mal configuradas. Comuniquese con su administrador'}
            return JsonResponse(val, status=400)

    except Exception as e:
        val = {'status':'Error al enviar el Email'}
        try:
            from_email = '<no-reply@miurabox.com>'
            email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_to, cc=[request.user.email])
            val = {'status':'sent'}
            return JsonResponse(val, status=200)
        except Exception as e:
            return JsonResponse(val, status=400)



@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def GetTasksReporte(request):
    # Parameters
    start_time=time.perf_counter()
    createdBy = request.data['createdBy'] #
    closedBy = request.data['closedBy'] #
    involved = request.data['involvedUsers']
    since = request.data['since']
    until = request.data['until']
    reportBy = request.data['reportBy']
    priority = int(request.data['priority'])
    archived = request.data['archived']
    closed = request.data['closed']
    opened = request.data['opened']

    todos = request.data['todos']

    # Creado por
    if createdBy:
        created_by = list(User.objects.filter(pk__in = createdBy).values_list('pk', flat=True))
    else:
        created_by = list(User.objects.values_list('pk', flat=True))
    # Cerrado por
    if closedBy:
        closed_by = list(User.objects.filter(pk__in = closedBy).values_list('pk', flat=True))
    else:
        closed_by = list(User.objects.values_list('pk', flat=True))

    # Involucrados
    if involved:
        involved_users = list(User.objects.filter(pk__in = involved).values_list('pk', flat=True))
    else:
        involved_users = list(User.objects.values_list('pk', flat=True))
    # Estatus
    if archived:
        archived_task = True
    else:
        archived_task = False

    if closed:
        closed_task = True
    elif opened:
        closed_task = False
    else:
        closed_task = False

    # Filtro de fechas
    try:
        f = "%d/%m/%Y %H:%M:%S"
        since = datetime.datetime.strptime(since , f)
        until = datetime.datetime.strptime(until , f)
    except:
        f = "%m/%d/%Y %H:%M:%S"
        since = datetime.datetime.strptime(since , f)
        until = datetime.datetime.strptime(until , f)

    date_filters = []
    if reportBy == 1:
        date_filters = [Q(close_day__gte=since),Q(close_day__lte = until)]
    elif reportBy == 2:
        date_filters = [Q(date__gte=since),Q(date__lte = until)]

    if date_filters:
        if priority != 0:
            tickets = Ticket.objects.filter(reduce(operator.and_, date_filters)).filter(priority = priority, org_name = request.GET.get('org'))
        else:
            tickets = Ticket.objects.filter(reduce(operator.and_, date_filters)).filter(org_name = request.GET.get('org'))
    else:
        if priority != 0:
            tickets = Ticket.objects.filter(org_name = request.GET.get('org'), priority = priority)
        else:
            tickets = Ticket.objects.filter(org_name = request.GET.get('org'))
    
    
    # Creado por
    if createdBy:
        tickets = tickets.filter(Q(owner__in = created_by))
    # Cerrado por
    if closedBy:
        tickets = tickets.filter(Q(closedBy__in = closed_by))
    # Tareas cerradas
    if todos:
        tickets = tickets
    else:
        if closed_task:
            tickets = tickets.filter(closed = True)
        else:
            tickets = tickets.filter(closed = False)
        # Tareas archivadas
        if archived_task:
            tickets = tickets.filter(archived = True)
        else:
            tickets = tickets.filter(archived = False)

    if involved:
        involvedTasks = Involved.objects.filter(person__in = involved_users, org_name = request.GET.get('org'))
        tareas = involvedTasks.filter(involved__in = list(tickets)).values_list('involved', flat = True)
        tickets = tickets.filter(id__in = tareas)
    else:
        tickets = tickets
    # ------------------Ver solo involucrados, creador, asignado----------

    session = Session.objects.filter(username=request.user.username)
    if session.exists():
        session = session.first()
    else:
        session = None

    if session and session.another_tasks: # validar si puede ver las tareas de otros
        users_list = list(GroupManager.objects.filter(manager = request.user).values_list('user__username',flat=True))
        users_list.append(request.user.username)
    else:
        users_list = [request.user.username]


    userfilter = [Q(owner__username__in = users_list),
                   Q(assigned__username__in = users_list),]
    ticketsR_filter = tickets.filter(reduce(OR, userfilter), org_name = request.GET.get('org')).values_list('pk', flat = True)
    involvedTask = Involved.objects.filter(involved__in = tickets)
    userfilterI = [Q(person__username__in = users_list)]
    involvedTask_Filter = involvedTask.filter(reduce(OR, userfilterI)).values_list('involved', flat = True)       
    tkt = list(ticketsR_filter) + list(involvedTask_Filter)
    tickets = tickets.filter(pk__in = tkt)
    # ------------------Ver solo involucrados, creador, asignado---------- 


    # Paginación
    paginator = Paginator(tickets, 10)
    try:
        page = request.data['page']
        results = paginator.page(page)
    except:
        results = paginator.page(1)
    serializer = FullTicketHyperSerializer(results, context={'request':request}, many = True)    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    try:
        logsystem = {'data':'Reporte tareas vista','conteo':len(tickets),'org_name':request.GET.get('org'),
                    'user': request.user.id, 'inicio':start_time,'fin':end_time,'total':total_time}
        logs_ =send_log(request.user, request.GET.get('org'), 'GET', 32,json.dumps(logsystem),None)
    except Exception as j:
        print('--------',j)
    return JsonResponse({'results': serializer.data, 'count': len(tickets)})

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def GetTasksReporteExcel(request):
    # Parameters
    createdBy = request.data['createdBy'] #
    closedBy = request.data['closedBy'] #
    involved = request.data['involvedUsers']
    since = request.data['since']
    until = request.data['until']
    reportBy = request.data['reportBy']
    priority = int(request.data['priority'])
    archived = request.data['archived']
    closed = request.data['closed']
    todos = request.data['todos']

    # Creado por
    if createdBy:
        created_by = list(User.objects.filter(pk__in = createdBy).values_list('pk', flat=True))
    else:
        created_by = list(User.objects.values_list('pk', flat=True))
    # Cerrado por
    if closedBy:
        closed_by = list(User.objects.filter(pk__in = closedBy).values_list('pk', flat=True))
    else:
        closed_by = list(User.objects.values_list('pk', flat=True))

    # Involucrados
    if involved:
        involved_users = list(User.objects.filter(pk__in = involved).values_list('pk', flat=True))
    else:
        involved_users = list(User.objects.values_list('pk', flat=True))
    # Estatus
    if archived:
        archived_task = True
    else:
        archived_task = False

    if closed:
        closed_task = True
    else:
        closed_task = False

    # Filtro de fechas
    try:
        f = "%d/%m/%Y %H:%M:%S"
        since = datetime.datetime.strptime(since , f)
        until = datetime.datetime.strptime(until , f)
    except:
        f = "%m/%d/%Y %H:%M:%S"
        since = datetime.datetime.strptime(since , f)
        until = datetime.datetime.strptime(until , f)

    date_filters = []
    if reportBy == 1:
        date_filters = [Q(close_day__gte=since),Q(close_day__lte = until)]
    elif reportBy == 2:
        date_filters = [Q(date__gte=since),Q(date__lte = until)]

    if date_filters:
        if priority != 0:
            tickets = Ticket.objects.filter(reduce(operator.and_, date_filters)).filter(priority = priority, org_name = request.GET.get('org'))
        else:
            tickets = Ticket.objects.filter(reduce(operator.and_, date_filters)).filter(org_name = request.GET.get('org'))
    else:
        if priority != 0:
            tickets = Ticket.objects.filter(org_name = request.GET.get('org'), priority = priority)
        else:
            tickets = Ticket.objects.filter(org_name = request.GET.get('org'))
    # Creado por
    if createdBy:
        tickets = tickets.filter(Q(owner__in = created_by))
    # Cerrado por
    if closedBy:
        tickets = tickets.filter(Q(closedBy__in = closed_by))
    # Tareas cerradas
    if todos:
        tickets = tickets
    else:
        if closed_task:
            tickets = tickets.filter(closed = True)
        else:
            tickets = tickets.filter(closed = False)
        # Tareas archivadas
        if archived_task:
            tickets = tickets.filter(archived = True)
        else:
            tickets = tickets.filter(archived = False)

    if involved:
        involvedTasks = Involved.objects.filter(person__in = involved_users, org_name = request.GET.get('org'))
        tareas = involvedTasks.filter(involved__in = list(tickets)).values_list('involved', flat = True)
        tickets = tickets.filter(id__in = tareas)
    else:
        tickets = tickets
    # ------------------Ver solo involucrados, creador, asignado----------
    userfilter = [Q(owner__username = request.user),
                   Q(assigned__username = request.user),]
    ticketsR_filter = tickets.filter(reduce(OR, userfilter), org_name = request.GET.get('org')).values_list('pk', flat = True)
    involvedTask = Involved.objects.filter(involved__in = tickets)
    userfilterI = [Q(person__username = request.user)]
    involvedTask_Filter = involvedTask.filter(reduce(OR, userfilterI)).values_list('involved', flat = True)       
    tkt = list(ticketsR_filter) + list(involvedTask_Filter)
    tickets = tickets.filter(pk__in = tkt)
    # ------------------Ver solo involucrados, creador, asignado---------- 
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Reporte Tareas.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Tareas')

    # Empieza insertado de imagen
    info_org = getInfoOrg(request)
    if len(info_org['logo']) != 0:
        archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + info_org['logo']
    else:
        archivo_imagen = 'saam.jpg'

    if info_org['urlname'] != 'basanez':
        try:
            img = Image.open(requests.get(archivo_imagen, stream=True).raw)
            r, g, b = img.split()
            img = Image.merge("RGB", (r, g, b))
            img = img.resize((130,150),Image.ANTIALIAS)
            name_logo = info_org['urlname']+'_logo.bmp'
            img.save(name_logo)
            ws.insert_bitmap(name_logo, 0, 0)
        except Exception as e:
            img = Image.open("saam.jpg")
            r, g, b = img.split()
            img = Image.merge("RGB", (r, g, b))
            img.save('imagetoadd.bmp')
            ws.insert_bitmap('imagetoadd.bmp', 0, 0)

    company_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    company_style.pattern = pattern
    company_style = xlwt.easyxf('font: bold on, color black, height 380;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(0, 5, info_org['name'], company_style)

    text_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    text_style.pattern = pattern
    text_style = xlwt.easyxf('font: bold off, color black;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(1, 5, info_org['address'], text_style)
    ws.write(3, 5, "Tel." + info_org['phone'], text_style)
    ws.write(4, 5, info_org['email'], text_style)
    ws.write(5, 5, info_org['webpage'], text_style)

    title_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    title_style.pattern = pattern
    title_style = xlwt.easyxf('font: bold on, color black, height 280;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    row_num = 10
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['Estatus','Identificador','Título','Fecha','Prioridad','Concepto','Descripción','Asignada a','Creada por','Antigüedad','Cerrado por ','Involucrados']

    for col_num in range(len(columns)):
        style = xlwt.XFStyle()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        # print( xlwt.Style.colour_map)
        style = xlwt.easyxf('font: bold on, color black;\
                       borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;\
                       pattern: pattern solid, fore_color ice_blue; align: horiz center')
        ws.write(row_num, col_num, columns[col_num], style)

    rows = tickets.values_list('closed','identifier', 'title', 'date','priority','concept','descrip','assigned__first_name',
        'assigned__last_name','owner__first_name','owner__last_name','created_at','closedBy__first_name','closedBy__last_name','id','archived')


    for row in rows:
        row_num += 1
        for col_num in range(12):
            font_style.font.bold = False
            col_width = 256 * 20
            if col_num == 0:
                font_style.num_format_str = 'general'
                if row[col_num]:
                    value = 'Completada'
                    if row[15]:
                        value = value + ' (archivada)'
                else:
                    value = 'Vigente'
                    if row[15]:
                        value = value + ' (archivada)'
            elif col_num == 1:
                value = (row[col_num])
            elif col_num == 2:
                value = row[col_num]
            elif col_num == 3:
                try:
                    font_style.num_format_str = 'DD/MM/YYYY'
                    value = (row[col_num].replace(tzinfo=None))
                except:
                    value = row[col_num]
            elif col_num == 4:
                value = checkPriority(row[col_num])
            elif col_num == 5:
                value = checkConcept(row[col_num])
            elif col_num == 6:
                value = row[col_num]
            elif col_num == 7:
                value = row[col_num] + ' ' + row[8]
            elif col_num ==8:
                value = row[9] + ' '+row[10]
            elif col_num == 9:
                font_style.num_format_str = 'general'
                today = date.today()
                a = arrow.get(today)
                aux_date = row[11]
                b = arrow.get(aux_date)
                antiguedad = (a-b).days
                antiguedad = int(antiguedad)+1
                value = antiguedad
            elif col_num == 10:
                font_style.num_format_str = 'general'
                if row[12]:
                    value = row[12] +' '+str(row[13])
                else:
                    value = ''
            elif col_num == 11:
                invTask = Involved.objects.filter(involved = int(row[14]), org_name = request.GET.get('org')).values_list('person__first_name','person__last_name')
                v = []
                try:
                    for it in invTask:
                        v.append(it[0] +' '+ str(it[1])+str(', '))
                    value = v
                except Exception as e:
                    if invTask[0][0]:
                        value = invTask[0][0]
                    else:
                        value = ''
            else:
                font_style.num_format_str = 'general'
                value = row[col_num]

            try:
                ws.write(row_num, col_num, value, font_style)
            except Exception as e:
                value = (row[col_num])
                ws.write(row_num, col_num, value, font_style)

    final_row = int(row_num) + 2
    title = "Total: " + str(len(rows)) + " Registros"
    font_style = xlwt.easyxf('font: bold off, color black;\
                     pattern: pattern solid, fore_color white;')
    ws.write(final_row, 0, title, font_style)

    wb.save(response)
    return response


@api_view(['POST'])
# @permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
@permission_classes((IsAuthenticatedV2,))
def contactEmailIBIS(request):
    
    message1 = request.data['message']
    name = request.data['name']
    poliza = int(request.data['pol_id'])
    user = int(request.data['user_id'])
    # email_to = request.data['to_email']
    # email_to = 'maavalos@prevex.com.mx'
    email_to = ['comercial@prevex.com.mx']
    org = request.data['org']
    # 

    subject = 'SICS  (Sistema de Información para clientes SAAM)'

    user = User.objects.get(username= request.user)
    user = user.first_name +' '+ str(user.last_name)
    fecha =  datetime.datetime.today()
    celula = None
    try:
        try:
            informacion =  Polizas.objects.get(id = poliza, org_name = org)
            info_type = 'Certificado: '+ str(informacion.poliza_number) 
            # Obetenr Célula y enviar a correo definido
            if org == 'ancora':
                email_to = ['guadalupe.becerril@miurabox.com']
                if informacion.document_type == 6:
                    if informacion.parent.parent.parent:
                        if informacion.parent.parent.parent.celula:
                            celula = informacion.parent.parent.parent.celula
                        else:
                            celula = None
                elif informacion.document_type == 12:
                    if informacion.parent:
                        if informacion.parent.celula:
                            celula = informacion.parent.celula
                        else:
                            celula = None
                elif informacion.document_type == 1 or informacion.document_type == 3:
                    if informacion.celula:
                        celula = informacion.celula
                    else:
                        celula = None
                else:
                    celula = None
            elif org == 'prevex':
                email_to = email_to
            elif org == 'gpi':
                email_to = ['contacto@grupogpi.mx','guadalupe.becerril@miurabox.com'] 
            else:
                email_to = ['guadalupe.becerril@miurabox.com']
        except Exception as e:
            info_type = 'Certificado: error'
            celula = None
            # return Response({'error':'No existe el archivo'})
    except Exception as e:
        pass
    # Sacar la célula, adjuntar email a enviar
    info_type = str(info_type)+'\n\n'+str(message1)+'\n'
    if org == 'ancora':
        if celula:
            if celula.id == 37 or celula.celula_name == 'Célula uno':
                email_to = ['fundador@ancora.com.mx','sgmm@teleton.org.mx','bal@ancora.com.mx','profuturo@ancora.com.mx']
            elif celula.id == 39 or celula.celula_name == 'Célula dos':
                email_to = ['ancora@up.edu.mx','ancora.ags@up.edu.mx','ancoragdl@up.edu.mx']
            elif celula.id == 40 or celula.celula_name == 'Célula tres':
                email_to = ['segurosmls@ancora.com.mx','ipade@ancora.com.mx','elililly@ancora.com.mx']
            elif celula.id == 36 or celula.celula_name == 'Célula cuatro':
                email_to = ['cen4a@ancora.com.mx', 'cen4b@ancora.com.mx']
            elif celula.id == 41 or celula.celula_name == 'Célula cinco':
                email_to = ['mhernandez@ancora.com.mx']
            elif celula.id == 35 or celula.celula_name == 'Célula LP':
                email_to = ['guadalupe.becerril@miurabox.com']
            elif celula.id == 42 or celula.celula_name == 'Otros':
                email_to = ['guadalupe.becerril@miurabox.com']
            else:
                email_to = ['guadalupe.becerril@miurabox.com']

    message=render_to_string("correo_ibis.html",{
            'concepto':subject,
            'fecha':fecha,
            'usuario': user,
            'name': name,
            'org_name': org,
            'info_type': info_type,
            'email': request.data['to_email'],
            'user': user,
            })

    # print('-----email_to-----',email_to,type_person,request.user.email)
    # GET ORG INFO
    org_info = org
    # Sendgrit Piloto test
    try:
        remitente = "{} <no-reply@miurabox.com>".format(org_info.name)
    except Exception as orerror:
        remitente = "{} <no-reply@miurabox.com>".format(org_info)
    email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_to)

    email.content_subtype="html"
    email.mixed_subtype = 'related'

    val = {'status':'Error al enviar el Email'}
    try:
        from_email = '<no-reply@miurabox.com>'
        # email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_to, cc=[request.user.email])
        email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_to)
        email.content_subtype="html"
        email.mixed_subtype = 'related'
        email.send()
        val = {'status':'sent'}
        return JsonResponse(val, status=200)
    except Exception as e:
        return JsonResponse(val, status=400)

@api_view(['POST'])
# @permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
@permission_classes((IsAuthenticatedV2,))
def contactEmailIBISGeneral(request):
    
    message1 = request.data['message']
    name = request.data['name']
    poliza = int(request.data['pol_id'])
    user = int(request.data['user_id'])
    email_to = ['contacto@miurabox.com']
    # email_to = ['guadalupe.becerril@miurabox.com']
    # org = request.data['org']
    subject = 'SICS  (Sistema de Información para clientes SAAM)'
    try:
        polizaInfo = Polizas.objects.get(pk = int(request.data['pol_id']))
        org = polizaInfo.org_name
    except Exception as f:
        print('fffffffff',f)
        org = None
    if polizaInfo and org:
        # email_to = []
        try:
            org_ = requests.get(settings.CAS2_URL + 'get-org-info/'+org,verify=False)
            response_org= org_.text
            org_data = json.loads(response_org)
            org_info = org_data['data']['org']
            email_to = [org_info['email']]
        except Exception as xd:
            print('xd---------',xd)
    else:
        print('error sin poliza...')
    user = User.objects.get(username= request.user)
    user = user.first_name +' '+ str(user.last_name)
    fecha =  datetime.datetime.today()
    # Sacar la célula, adjuntar email a enviar
    info_type = str('')+'\n\n'+str(message1)+'\n'
    final_time = fecha - timedelta(hours=6)
    fecha = final_time.strftime("%d/%m/%Y") 
    message=render_to_string("correo_ibis_general.html",{
            'concepto':subject,
            'fecha':fecha,
            'usuario': user,
            'name': name,
            'message':message1,
            'poliza': polizaInfo.poliza_number if polizaInfo else '',
            'info_type': info_type,
            'email': request.data['to_email'],
            'user': user,
            })
    # GET ORG INFO
    # org_info = org
    org_info = 'Contacto Miurabox'
    # Sendgrit Piloto test
    try:
        remitente = "{} <no-reply@miurabox.com>".format(org_info.name)
    except Exception as orerror:
        remitente = "{} <no-reply@miurabox.com>".format(org_info)
    email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_to)

    email.content_subtype="html"
    email.mixed_subtype = 'related'

    val = {'status':'Error al enviar el Email'}
    try:
        from_email = '<no-reply@miurabox.com>'
        # email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_to, cc=[request.user.email])
        email = EmailMultiAlternatives(subject, message, from_email=remitente, to=email_to)
        email.content_subtype="html"
        email.mixed_subtype = 'related'
        email.send()
        val = {'status':'sent'}
        return JsonResponse(val, status=200)
    except Exception as e:
        return JsonResponse(val, status=400)

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def ReporteCedulaExcel(request):
    # Parameters
    cedula_ = Cedula.objects.filter(org_name = request.GET.get('org'))
     
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Reporte Cédula(s).xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Cédula(s)')

    # Empieza insertado de imagen
    info_org = getInfoOrg(request)
    if len(info_org['logo']) != 0:
        archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + info_org['logo']
    else:
        archivo_imagen = 'saam.jpg'

    if info_org['urlname'] != 'basanez':
        try:
            img = Image.open(requests.get(archivo_imagen, stream=True).raw)
            r, g, b = img.split()
            img = Image.merge("RGB", (r, g, b))
            img = img.resize((130,150),Image.ANTIALIAS)
            name_logo = info_org['urlname']+'_logo.bmp'
            img.save(name_logo)
            ws.insert_bitmap(name_logo, 0, 0)
        except Exception as e:
            img = Image.open("saam.jpg")
            r, g, b = img.split()
            img = Image.merge("RGB", (r, g, b))
            img.save('imagetoadd.bmp')
            ws.insert_bitmap('imagetoadd.bmp', 0, 0)

    company_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    company_style.pattern = pattern
    company_style = xlwt.easyxf('font: bold on, color black, height 380;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(0, 5, info_org['name'], company_style)

    text_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    text_style.pattern = pattern
    text_style = xlwt.easyxf('font: bold off, color black;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    ws.write(1, 5, info_org['address'], text_style)
    ws.write(3, 5, "Tel." + info_org['phone'], text_style)
    ws.write(4, 5, info_org['email'], text_style)
    ws.write(5, 5, info_org['webpage'], text_style)

    title_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    title_style.pattern = pattern
    title_style = xlwt.easyxf('font: bold on, color black, height 280;\
                     pattern: pattern solid, fore_color white; align: horiz center')
    row_num = 10
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['No.Cédula','Fecha Expiración','Observaciones','Creada por','Fecha Creación']

    for col_num in range(len(columns)):
        style = xlwt.XFStyle()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        style = xlwt.easyxf('font: bold on, color black;\
                       borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;\
                       pattern: pattern solid, fore_color ice_blue; align: horiz center')
        ws.write(row_num, col_num, columns[col_num], style)

    rows = cedula_.values_list('cedula','expiracion','observaciones','owner__first_name','created_at','owner__last_name')


    for row in rows:
        row_num += 1
        for col_num in range(5):
            font_style.font.bold = False
            col_width = 256 * 20
            if col_num == 0:
                font_style.num_format_str = 'general'
                value = row[col_num]
            elif col_num == 1:
                try:
                    font_style.num_format_str = 'DD/MM/YYYY'
                    value = (row[col_num].replace(tzinfo=None))
                except Exception as r:
                    value = row[col_num]  
            elif col_num == 2:
                value = row[col_num]
            elif col_num == 3:
                value = row[col_num] + ' '+ str(row[5])
            elif col_num == 4:
                try:
                    font_style.num_format_str = 'DD/MM/YYYY'
                    value = (row[col_num].replace(tzinfo=None))
                except Exception as r:
                    value = row[col_num]            
            else:
                font_style.num_format_str = 'general'
                value = row[col_num]

            try:
                ws.write(row_num, col_num, value, font_style)
            except Exception as e:
                value = (row[col_num])
                ws.write(row_num, col_num, value, font_style)

    final_row = int(row_num) + 2
    title = "Total: " + str(len(rows)) + " Registros"
    font_style = xlwt.easyxf('font: bold off, color black;\
                     pattern: pattern solid, fore_color white;')
    ws.write(final_row, 0, title, font_style)

    wb.save(response)
    return response

class SharedApiViewSet(viewsets.ModelViewSet):
    serializer_class = SharedApiHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)
    def partial_update(self, request, pk=None):
        queryset = Shared.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        try:
            serializer = SharedApiHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)   

        except:
            serializer = SharedApiHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)   
  
    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except Exception as e:
            try:
                obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
            except Exception as r:
                obj = serializer.save(owner=self.request.user, org_name=self.request.POST.get('org'))      

    def get_queryset(self):
        return custom_get_queryset(self.request, Shared)

#----------- INFO SHARED
@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ComisionesPermissionV2))
def GetSharedGroupUser(request):
    user = int(request.GET.get('user'))
    groupUsers = int(request.GET.get('group'))
    shared = {}
    shared_gral = Shared.objects.filter( org_name = request.GET.get('org'))
    if user != 0:
        compartidos =  Shared.objects.filter(usuario = user)    
    elif groupUsers != 0:
        compartidos =  Shared.objects.filter(grupo = groupUsers)   
    else:
        compartidos = shared_gral    
    try:
        shared['aseguradoras'] = compartidos.values('aseguradora__compania','aseguradora').annotate(Count('aseguradora')).annotate(Sum('aseguradora')).order_by('aseguradora')
        shared['contratante_fisico'] = compartidos.values('contratante_fisico__full_name','contratante_fisico').annotate(Count('contratante_fisico')).order_by('contratante_fisico')
        shared['contratante_moral'] = compartidos.values('contratante_moral__j_name','contratante_moral').annotate(Count('contratante_moral')).order_by('contratante_moral')
        shared['fianza'] = compartidos.values('fianza__fianza_number','fianza__internal_number','fianza').annotate(Count('fianza')).order_by('fianza')
        shared['grupo_de_contratantes'] = compartidos.values('grupo_de_contratantes__group_name','grupo_de_contratantes').annotate(Count('grupo_de_contratantes')).order_by('grupo_de_contratantes')
        shared['poliza'] = compartidos.values('poliza__poliza_number','poliza').annotate(Count('poliza')).order_by('poliza')
        shared['usuarios'] = shared_gral.values('usuario__first_name','usuario__last_name','usuario').annotate(Count('usuario')).order_by('usuario')
        shared['grupos'] = shared_gral.values('grupo__name','grupo').annotate(Count('grupo')).order_by('grupo')
            
        response = {
            'registros_creados': len(compartidos),
            'info': shared
        }
        return Response(response)
    except Exception as e:
        return Response(0)


# Group users
class DjangoGroupsViewSet(viewsets.ModelViewSet):
    serializer_class = DjangoGroupsHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)


    def partial_update(self, request, pk=None):
        queryset = DjangoGroups.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        try:
            serializer = DjangoGroupsHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            # serializer.save()
            serializer.save(owner=self.request.user)
            return Response(serializer.data)   

        except:
            serializer = DjangoGroupsHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            # serializer.save()
            serializer.save(owner=self.request.user)
            return Response(serializer.data)   
  
    def perform_create(self, serializer):
        try:
            obj = serializer.save(name = self.request.GET.get('name'))
        except Exception as e:
            try:
                obj = serializer.save(name = self.request.POST.get('name'))
            except Exception as r:
                obj = serializer.save(name = self.request.data['name'])
                val = DjangoGroupInfo.objects.get_or_create(group=obj, org= self.request.GET.get('org'), owner= self.request.user)
    def get_queryset(self):
        return custom_get_queryset(self.request, DjangoGroups)

#----------- INFO SHARED
@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ComisionesPermissionV2))
def GetGroupUser(request):
    request.request = request
    group_users = {}
    group_user_gral = DjangoGroups.objects.all()
    groups_1 = DjangoGroupInfo.objects.filter(group__in = list(group_user_gral), org_name = request.GET.get('org')).values_list('group', flat = True)
    group_user_gral = DjangoGroups.objects.filter(pk__in = groups_1)
    try:
        serializer = DjangoGroupsHyperSerializer(group_user_gral,context={'request':request},many=True)
        # DjangoGroupInfoHyperSerializer
        return JsonResponse({'results': serializer.data})
    except Exception as e:
        return Response(0)
#users in groups
# Group users

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def DjangoUserGroupsViewSet(request):
    action = request.data['action']
    id_group = request.data['group']
    id_user = request.data['user']
    if action == 1:
        try:
            g = DjangoGroups.objects.get(id = id_group) 
            g.user_set.add(id_user)
            # serializer = DjangoGroupsHyperSerializer(g, context={'request':request}, many =True)#error to save
            return Response("Éxito: usuarios añadidos del grupo: "+str(g.name)) 
        except Exception as e:
            # obj = serializer.save(group = id_group, user = user)
            return Response('Error al añadir usuarios al Grupo')
    elif action == 2:
        try:            
            g = DjangoGroups.objects.get(id = id_group) 
            g.user_set.remove(id_user)
            # serializer = DjangoGroupsHyperSerializer(g, context={'request':request}, many =True)#error to save
            return Response("Éxito: usuarios eliminados al grupo: "+str(g.name)) 
        except Exception as e:
            # obj = serializer.save(group = id_group, user = user)
            return Response('Error al eliminar usuarios al Grupo')
    elif action == 3:
        try:
            group = DjangoGroups.objects.get(id = id_group)
            groupInfo = DjangoGroupInfo.objects.get(group = group, org_name = request.GET.get('org'))
            bgroup = User.objects.get(username = request.user)
            bpm = UserInfoHyperSerializer(request.user)
            if request.user == groupInfo.owner:
                try:
                    group.delete()
                    return Response('Grupo eliminado',status=204)
                except Exception as rty:
                    return Response('Error al eliminar el Grupo', status = 400)
            else:
                return Response('Error al eliminar el Grupo', status = 400)
        except DjangoGroups.DoesNotExist:
            return Response('Group Not Found', status = 400) 

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def GetDjangoUserGroupsViewSet(request):
    try:
        id_group = request.GET.get('group')
        g = DjangoGroups.objects.get(id = id_group) 
        users = User.objects.filter(groups__name=g.name)
        serializer = UserSerializer(users, context={'request':request}, many =True)
        return Response(serializer.data) 
    except Exception as e:
        # obj = serializer.save(group = id_group, user = user)
        return Response(0)

class seekerDjangoGroups(viewsets.ModelViewSet):
    serializer_class = DjangoGroupsHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def get_queryset(self):
        try:
            groups = DjangoGroups.objects.filter(name__icontains = str(self.request.GET.get('word')),).values_list('pk', flat = True)
            groups_1 = DjangoGroupInfo.objects.filter(group__in = list(groups), org_name = self.request.GET.get('org')).values_list('group', flat = True)
            groups = DjangoGroups.objects.filter(pk__in = groups_1)
        except Exception as e:
            groups = None
        return groups

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def DelSharedUserAndGroup(request):
    try:
        try:
            if request.data['group']:
                id_group = request.data['group']
                id_user = 0
            elif request.data['user']:
                id_group = 0
                id_user = request.data['user']
        except Exception as rte:
            if request.data['group']:
                id_group = request.data['group']
                id_user = 0
            elif request.data['user']:
                id_group = 0
                id_user = request.data['user']
        if id_group:
            g = DjangoGroupInfo.objects.get(group = id_group, org_name = request.GET.get('org')) 
            groups_1 = DjangoGroupInfo.objects.filter(group = id_group, org_name = request.GET.get('org')).values_list('group', flat = True)
            groups = DjangoGroups.objects.filter(pk__in = groups_1)
            if groups:
                try:
                    cf = request.data['contratante_fisico']
                    shrd = Shared.objects.filter(grupo=g.group, contratante_fisico__id = cf)
                    serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                    for sd in shrd:
                        sd.contratante_fisico = None
                        sd.save()
                    return Response(serializer.data) 
                except Exception as n_cf:
                    try:
                        cm = request.data['contratante_moral']
                        shrd = Shared.objects.filter(grupo=g.group, contratante_moral__id = cm)
                        serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                        for sd in shrd:
                            sd.contratante_moral = None
                            sd.save()
                        return Response(serializer.data) 
                    except Exception as n_cm:
                        try:
                            ase = request.data['aseguradora']
                            shrd = Shared.objects.filter(grupo=g.group, aseguradora__id = ase)
                            serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                            for sd in shrd:
                                sd.aseguradora = None
                                sd.save()
                            return Response(serializer.data) 
                        except Exception as n_a:
                            try:
                                fi = request.data['fianza']
                                shrd = Shared.objects.filter(grupo=g.group, fianza__id = fi)
                                serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                                for sd in shrd:
                                    sd.fianza = None
                                    sd.save()
                                return Response(serializer.data) 
                            except Exception as n_f:
                                try:
                                    pol = request.data['poliza']
                                    shrd = Shared.objects.filter(grupo=g.group, poliza__id = pol)
                                    serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                                    for sd in shrd:
                                        sd.poliza = None
                                        sd.save()
                                    return Response(serializer.data) 
                                except Exception as n_p:
                                    try:
                                        gc = request.data['grupo_de_contratantes']
                                        shrd = Shared.objects.filter(grupo=g.group, grupo_de_contratantes__id = gc)
                                        serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                                        for sd in shrd:
                                            sd.grupo_de_contratantes = None
                                            sd.save()
                                        return Response(serializer.data) 
                                    except Exception as n_gc:
                                        pass        
                return Response('OK') 
        elif id_user:
            user = User.objects.get(id = id_user)
            try:
                cf = request.data['contratante_fisico']
                shrd = Shared.objects.filter(usuario = id_user, contratante_fisico__id = cf)
                serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                for sd in shrd:
                    sd.contratante_fisico = None
                    sd.save()
                return Response(serializer.data) 
            except Exception as n_cf:
                try:
                    cm = request.data['contratante_moral']
                    shrd = Shared.objects.filter(usuario = id_user, contratante_moral__id = cm)
                    serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                    for sd in shrd:
                        sd.contratante_moral = None
                        sd.save()
                    return Response(serializer.data) 
                except Exception as n_cm:
                    try:
                        ase = request.data['aseguradora']
                        shrd = Shared.objects.filter(usuario = id_user, aseguradora__id = ase)
                        serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                        for sd in shrd:
                            sd.aseguradora = None
                            sd.save()
                        return Response(serializer.data) 
                    except Exception as n_a:
                        try:
                            fi = request.data['fianza']
                            shrd = Shared.objects.filter(usuario = id_user, fianza__id = fi)
                            serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                            for sd in shrd:
                                sd.fianza = None
                                sd.save()
                            return Response(serializer.data) 
                        except Exception as n_f:
                            try:
                                pol = request.data['poliza']
                                shrd = Shared.objects.filter(usuario = id_user, poliza__id = pol)
                                serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                                for sd in shrd:
                                    sd.poliza = None
                                    sd.save()
                                return Response(serializer.data) 
                            except Exception as n_p:
                                try:
                                    gc = request.data['grupo_de_contratantes']
                                    shrd = Shared.objects.filter(usuario=id_user, grupo_de_contratantes__id = gc)
                                    serializer = SharedApiHyperSerializer(shrd, context={'request':request}, many =True)
                                    for sd in shrd:
                                        sd.grupo_de_contratantes = None
                                        sd.save()
                                    return Response(serializer.data) 
                                except Exception as n_gc:
                                    pass      
            return Response('OK')  
    except Exception as e:
        # obj = serializer.save(group = id_group, user = user)
        return Response(0)

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, ))
def config_smtp(request):
    status = 200
    response  =  {
        'success': False,
        'username': '',
        'name': '',
        'host': '',
        'port': '',
        'message': ''
    }
    try:
        response['username'] =  request.user.email
        response['name'] =  request.user.first_name
        if request.method == 'POST':
            url = host + "smtpconf/?username={}".format(request.user.email)
            url_post= host + "smtpconf/"
            headers = {"user_agent": "mozilla", }
            req = requests.get(url, headers=headers)
            if req.status_code == 200:
                data  = {
                    'org': request.user.user_info.org_name,
                    'name': request.data['name'],
                    'username': request.user.email,
                    'password': request.data['password'],
                    'host': request.data['host'],
                    'port': request.data['port']
                }
                if req.json():
                    req = requests.patch(url_post+str(req.json()[0]['id'])+'/', headers=headers, data=data)
                else:
                    req = requests.post(url_post, headers=headers, data=data)
                if req.status_code  in (200, 201):
                    result =  req.json()
                    response['name'] =  result['name']
                    response['host'] =  result['host']
                    response['port'] =  result['port']
                    response['success'] =  True
                else:
                    response['message'] =  req.json()
                    status = 400
        elif request.method == 'GET':
            url = host + "smtpconf/?username={}".format(request.user.email)
            headers = {"user_agent": "mozilla", }
            req = requests.get(url, headers=headers)
            if req.status_code == 200:
                if req.json():
                    result =  req.json()[0]
                    response['name'] =  result['name']
                    response['host'] =  result['host']
                    response['port'] =  result['port']
                    response['success'] =  True

        return Response(response, status=status)
    except Exception as e:
        return Response({'message': str(e)}, status=400)

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticatedV2, ))
def config_smtp_org(request):
    status = 200
    response  =  {
        'success': False,
        'username': '',
        'name': '',
        'host': '',
        'port': '',
        'message': '',
        'signature': ''
    }
    try:
        #response['username'] =  request.user.email
        #response['name'] =  request.user.first_name
        if request.method == 'POST':
            url = host + "orgsmtpconf/?org={}".format(request.user.user_info.org_name)
            url_post= host + "orgsmtpconf/"
            req = requests.get(url)
            if req.status_code == 200:
                data  = {
                    'org': request.user.user_info.org_name,
                    'name': request.data['name'],
                    'username': request.data['username'].lower(),
                    'password': request.data['password'],
                    'host': request.data['host'],
                    'port': request.data['port'],
                    'signature': request.data['signature'],
                }
                if req.json():
                    req = requests.patch(url_post+str(req.json()[0]['id'])+'/', data=data)
                else:
                    req = requests.post(url_post, data=data)
                if req.status_code  in (200, 201):
                    result =  req.json()
                    response['name'] =  result['name']
                    response['host'] =  result['host']
                    response['port'] =  result['port']
                    response['username'] =  result['username']
                    response['signature'] =  result['signature']
                    response['success'] =  True
                else:
                    response['message'] =  req.json()
                    status = 400
        elif request.method == 'GET':
            url = host + "orgsmtpconf/?org={}".format(request.user.user_info.org_name)
            req = requests.get(url)
            if req.status_code == 200:
                if req.json():
                    result =  req.json()[0]
                    response['name'] =  result['name']
                    response['host'] =  result['host']
                    response['port'] =  result['port']
                    response['username'] =  result['username']
                    response['signature'] =  result['signature']
                    response['success'] =  True
                    response['id'] = result['id']
                    response['url'] = result['url']

        return Response(response, status=status)
    except Exception as e:
        return Response({'message': str(e)}, status=400)



@api_view(['POST'])
@permission_classes((IsAuthenticatedV2,))
def get_info_org(request):
    data = {}
    try:
        org = request.user.user_info.org_name
        org_ = requests.get(settings.CAS_URL + 'get-org-info/'+org.urlname,verify=False)
        response_org= org_.text
        org_data = json.loads(response_org)
        info_org = org_data['data']['org']
        if len(info_org['logo']) != 0:
            archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + info_org['logo']
        else:
            archivo_imagen = 'https://miurabox.s3.amazonaws.com/cas/pruebas/logos/saam.jpeg'
        data = {
            'email_org':info_org['email'],
            'phone_org':info_org['phone'],
            'webpage_org':info_org['webpage'],
            'address_org':info_org['address'],
            'urlname_org':info_org['name'],
            'logo': archivo_imagen, 
            'banner': 'https://miurabox.s3.amazonaws.com/cas/' + info_org['banner'] if info_org['banner'] else ''

        }

    except Exception as e:
        return Response(str(e), status=status.HTTP_404_NOT_FOUND)
    return Response(data, status= status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def tasks_initial(request):
    time_inicial = time.time()
    labelGreen = 'En tiempo'
    labelYellow = 'Atención'
    labelOrange = 'Atención urgente'
    labelRed = 'Urgente'

    session = Session.objects.filter(username=request.user.username)
    if session.exists():
        session = session.first()
    else:
        session = None
    

    if session and session.another_tasks: # validar si puede ver las tareas de otros
        users_list = list(GroupManager.objects.filter(manager = request.user).values_list('user',flat=True))
        users_list.append(request.user)
        
    else:
        users_list = [request.user]
    org = request.GET.get('org')
    ui = UserInfo.objects.get(user= request.user)
    try:
        try:
            config_chart = Graphics.objects.get(owner=request.user, org_name=org, type_graphic = 5)
        except:
            config_chart = Graphics.objects.get(org_name=org, type_graphic = 5)
        days_green = config_chart.green if config_chart.green else 45
        days_yellow = config_chart.yellow if config_chart.yellow else 30
        days_orange = config_chart.orange if config_chart.orange else 15
        days_red = config_chart.red if config_chart.red else 1000
        filter_graphs =  config_chart.option_filter
    except Exception as e:
        config_chart = None
        days_green = 45
        days_yellow = 30
        days_orange = 15
        days_red = 1000
        filter_graphs = 3

    today = datetime.datetime.today()
    orange_days = timedelta(days = days_orange)
    yellow_days = timedelta(days = days_yellow)
    green_days = timedelta(days = days_green)
    red_days = timedelta(days = days_red)

    diasO = today + orange_days
    diasY = today + yellow_days
    diasG = today + green_days

    # query_g = (Q(created_at__lt = diasG) & Q(created_at__gte = diasY))
    # query_y = (Q(created_at__lt = diasY) & Q(created_at__gte = diasO))
    # query_o = (Q(created_at__lt = diasO) & Q(created_at__gte = today))
    ## query_r = (Q(fecha_inicio__lt = today))*
    # query_r = (Q(created_at__lte = diasO))
    # query = (Q(created_at__lte = diasG))
    # option_filter: 1 creadas, 2 asignadas, 3 ambas
    involved = Involved.objects.filter(org_name=org, person__in=users_list).values_list('involved',flat=True)
    if int(filter_graphs) ==1:
        pk = list(Ticket.objects.filter(org_name=org, owner__in = users_list, closed = False).values_list('pk', flat=True))  
    elif int(filter_graphs) ==2: 
        pk = list(Ticket.objects.filter((Q(assigned__in = users_list) | Q(id__in = involved)), org_name=org, closed = False).values_list('pk', flat=True))  
    elif int(filter_graphs) == 3:
        pk = list(Ticket.objects.filter((Q(assigned__in = users_list) | Q(owner__in = users_list) | Q(id__in = involved)), org_name=org, closed = False).values_list('pk', flat=True))  
    else:
        pk = list(Ticket.objects.filter((Q(assigned__in = users_list) | Q(owner__in = users_list) | Q(id__in = involved)), org_name=org, closed = False).values_list('pk', flat=True))  
    # *************************************
    diasO = today - orange_days
    diasY = today - yellow_days
    diasG = today - green_days
    # diasR = today - red_days        

    pendingGreen = Ticket.objects.filter(pk__in = pk, org_name =  request.GET.get('org'), created_at__lte = today, created_at__gt = diasG)
    pendingYellow = Ticket.objects.filter(pk__in = pk, org_name =  request.GET.get('org'), created_at__lte = diasG, created_at__gt = diasY)
    pendingOrange = Ticket.objects.filter(pk__in = pk, org_name =  request.GET.get('org'), created_at__lte = diasY, created_at__gt = diasO)
    pendingRed = Ticket.objects.filter(pk__in = pk, org_name =  request.GET.get('org'), created_at__lte = diasO)

    # ***********************************+**
    green = pendingGreen.count()
    yellow = pendingYellow.count()
    orange = pendingOrange.count()
    red = pendingRed.count()   


    pendingGreen = pendingGreen.values('org_name').annotate(Count('org_name')).order_by('org_name')
    pendingYellow = pendingYellow.values('org_name').annotate(Count('org_name')).order_by('org_name')
    pendingOrange = pendingOrange.values('org_name').annotate(Count('org_name')).order_by('org_name')
    pendingRed = pendingRed.values('org_name').annotate(Count('org_name')).order_by('org_name')
    # prioridad ALTA
    pendingGreen1 = Ticket.objects.filter(pk__in = pk, priority = 1).filter(created_at__lte = today, created_at__gt = diasG).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingYellow1 = Ticket.objects.filter(pk__in = pk, priority = 1).filter(created_at__lte = diasG, created_at__gt = diasY).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingOrange1 = Ticket.objects.filter(pk__in = pk, priority = 1).filter(created_at__lte = diasY, created_at__gt = diasO).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingRed1 = Ticket.objects.filter(pk__in = pk, priority =1).filter(created_at__lte = diasO).values('priority').annotate(Count('priority')).order_by('org_name')
    # prioridad Media
    pendingGreen2 = Ticket.objects.filter(pk__in = pk, priority =2).filter(created_at__lte = today, created_at__gt = diasG).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingYellow2 = Ticket.objects.filter(pk__in = pk, priority =2).filter(created_at__lte = diasG, created_at__gt = diasY).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingOrange2 = Ticket.objects.filter(pk__in = pk, priority =2).filter(created_at__lte = diasY, created_at__gt = diasO).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingRed2 = Ticket.objects.filter(pk__in = pk, priority =2).filter(created_at__lte = diasO).values('priority').annotate(Count('priority')).order_by('org_name')
    # prioridad Baja
    pendingGreen3 = Ticket.objects.filter(pk__in = pk, priority =3).filter(created_at__lte = today, created_at__gt = diasG).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingYellow3 = Ticket.objects.filter(pk__in = pk, priority =3).filter(created_at__lte = diasG, created_at__gt = diasY).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingOrange3 = Ticket.objects.filter(pk__in = pk, priority =3).filter(created_at__lte = diasY, created_at__gt = diasO).values('priority').annotate(Count('priority')).order_by('org_name')
    pendingRed3 = Ticket.objects.filter(pk__in = pk, priority =3).filter(created_at__lte = diasO).values('priority').annotate(Count('priority')).order_by('org_name')

    if len(pendingGreen):
        green = pendingGreen[0]['org_name__count']
    else:
        green = 0
    if len(pendingYellow):
        yellow = pendingYellow[0]['org_name__count']
    else:
        yellow = 0

    if len(pendingOrange):
        orange = pendingOrange[0]['org_name__count']
    else:
        orange = 0
    if len(pendingRed):
        red = pendingRed[0]['org_name__count']
    else:
        red = 0
    # Green
    if len(pendingGreen1):
        greenAlta = pendingGreen1[0]['priority__count']
    else:
        greenAlta = 0
    if len(pendingGreen2):
        greenMedia = pendingGreen2[0]['priority__count']
    else:
        greenMedia = 0
    if len(pendingGreen3):
        greenBaja = pendingGreen3[0]['priority__count']
    else:
        greenBaja = 0
    # Yellow
    if len(pendingYellow1):
        yellowAlta = pendingYellow1[0]['priority__count']
    else:
        yellowAlta = 0
    if len(pendingYellow2):
        yellowMedia = pendingYellow2[0]['priority__count']
    else:
        yellowMedia = 0
    if len(pendingYellow3):
        yellowBaja = pendingYellow3[0]['priority__count']
    else:
        yellowBaja = 0
    # Orange
    if len(pendingOrange1):
        orangeAlta = pendingOrange1[0]['priority__count']
    else:
        orangeAlta = 0
    if len(pendingOrange2):
        orangeMedia = pendingOrange2[0]['priority__count']
    else:
        orangeMedia = 0
    if len(pendingOrange3):
        orangeBaja = pendingOrange3[0]['priority__count']
    else:
        orangeBaja = 0
    # Red
    if len(pendingRed1):
        redAlta = pendingRed1[0]['priority__count']
    else:
        redAlta = 0
    if len(pendingRed2):
        redMedia = pendingRed2[0]['priority__count']
    else:
        redMedia = 0
    if len(pendingRed3):
        redBaja = pendingRed3[0]['priority__count']
    else:
        redBaja = 0

    total = green + yellow + orange + red

    if green > 0:
        greenPercent = (green / total) * 100
    else:
        greenPercent = 0

    if yellow > 0:
        yellowPercent = (yellow / total) * 100
    else:
        yellowPercent = 0

    if orange > 0:
        orangePercent = (orange / total) * 100
    else:
        orangePercent = 0

    if red > 0:
        redPercent = (red / total) * 100
    else:
        redPercent = 0

    data = {'green': {'title': 'Restan entre ' + str(days_green) + ' y ' + str(0) + ' días',  
                    'percent': greenPercent, 
                    'Alta': str(greenAlta), 
                    'Media': str(greenMedia), 
                    'Baja': str(greenBaja), 
                    'label': labelGreen, 
                    'status': str(green) + '/' + str(total)},
            'yellow': {'title': 'Restan entre ' + str(days_yellow) + ' y ' + str(days_green) + ' días',  
                    'percent': yellowPercent, 
                    'Alta': str(yellowAlta), 
                    'Media': str(yellowMedia), 
                    'Baja': str(yellowBaja), 
                    'label': labelYellow, 
                    'status': str(yellow) + '/' + str(total)}, 
            'orange': {'title': 'Restan entre ' + str(days_orange) + ' y ' + str(days_yellow) + ' días',  
                    'percent': orangePercent, 
                    'Alta': str(orangeAlta), 
                    'Media': str(orangeMedia), 
                    'Baja': str(orangeBaja),
                    'label': labelOrange, 
                    'status': str(orange) + '/' + str(total)}, 
            'red': {'title': 'Sin días restantes',  
                    'percent': redPercent, 
                    'Alta': str(redAlta), 
                    'Media': str(redMedia), 
                    'Baja': str(redBaja),                    
                    'label': labelRed, 
                    'status': str(red) + '/' + str(total)}
            }
    return JsonResponse(data)

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def tasks_graphic(request):
        tipo = request.data['tipo']
        request = request

        session = Session.objects.filter(username=request.user.username)
        if session.exists():
            session = session.first()
        else:
            session = None
        

        if session and session.another_tasks: # validar si puede ver las tareas de otros
            users_list = list(GroupManager.objects.filter(manager = request.user).values_list('user',flat=True))
            users_list.append(request.user)
            
        else:
            users_list = [request.user]
        org_name = request.GET.get('org')
        
        try:
            try:
                config_chart = Graphics.objects.get(owner=request.user, org_name=org_name, type_graphic = 5)
            except:
                config_chart = Graphics.objects.get(org_name=org_name, type_graphic = 5)
            days_green = config_chart.green if config_chart.green else 45
            days_yellow = config_chart.yellow if config_chart.yellow else 30
            days_orange = config_chart.orange if config_chart.orange else 15
            days_red = config_chart.red if config_chart.red else 1000
            filter_graphs =  config_chart.option_filter
        except:
            config_chart = None
            days_green = 45
            days_yellow = 30
            days_orange = 15
            days_red = 1000
            filter_graphs = 3

        today = datetime.datetime.today()
        orange_days = timedelta(days = days_orange)
        yellow_days = timedelta(days = days_yellow)
        green_days = timedelta(days = days_green)
        red_days = timedelta(days = days_red)

        diasO = today + orange_days
        diasY = today + yellow_days
        diasG = today + green_days

        # query_g = (Q(created_at__lt = diasG) & Q(created_at__gte = diasY))
        # query_y = (Q(created_at__lt = diasY) & Q(created_at__gte = diasO))
        # query_o = (Q(created_at__lt = diasO) & Q(created_at__gte = today))
        # query_r = (Q(created_at__lte = today))
        # query = (Q(created_at__lte = diasG))
        involved = Involved.objects.filter(org_name=org_name, person__in=users_list).values_list('involved',flat=True)
        
        if int(filter_graphs) ==1:
            pk = list(Ticket.objects.filter(org_name=org_name, owner__in = users_list, closed = False).values_list('pk', flat=True))  
        elif int(filter_graphs) ==2: 
            pk = list(Ticket.objects.filter((Q(assigned__in = users_list) | Q(id__in = involved)), org_name=org_name, closed = False).values_list('pk', flat=True))  
        elif int(filter_graphs) == 3:
            pk = list(Ticket.objects.filter((Q(assigned__in = users_list) | Q(owner__in = users_list) | Q(id__in = involved)), org_name=org_name, closed = False).values_list('pk', flat=True))  
        else:
            pk = list(Ticket.objects.filter((Q(assigned__in = users_list) | Q(owner__in = users_list) | Q(id__in = involved)), org_name=org_name, closed = False).values_list('pk', flat=True)) 
        # ------------------------------------
        diasO = today - orange_days
        diasY = today - yellow_days
        diasG = today - green_days
        diasR = today - red_days     
        pendingGreen = Ticket.objects.filter(pk__in = pk, org_name =  request.GET.get('org'), created_at__lte = today, created_at__gt = diasG)
        pendingYellow = Ticket.objects.filter(pk__in = pk, org_name =  request.GET.get('org'), created_at__lte = diasG, created_at__gt = diasY)
        pendingOrange = Ticket.objects.filter(pk__in = pk, org_name =  request.GET.get('org'), created_at__lte = diasY, created_at__gt = diasO)
        pendingRed = Ticket.objects.filter(pk__in = pk, org_name =  request.GET.get('org'), created_at__lte = diasO)
        # *************************************+
        # green = pendingGreen.count()
        # yellow = pendingYellow.count()
        # orange = pendingOrange.count()
        red = pendingRed.count() 
        # -----------------------------
        # total_neto = 0

        if tipo == 'green':
            pendingGreen = pendingGreen
            serializer =TicketHyperSerializer(pendingGreen,context={'request':request},many=True)        
            return JsonResponse({'results': serializer.data, 'count': len(pendingGreen)})
            # return pendingGreen
        elif tipo == 'yellow':
            pendingYellow = pendingYellow
            serializer =TicketHyperSerializer(pendingYellow,context={'request':request},many=True)        
            return JsonResponse({'results': serializer.data, 'count': len(pendingYellow)})
            # return pendingYellow
        elif tipo == 'orange':
            pendingOrange = pendingOrange
            serializer =TicketHyperSerializer(pendingOrange,context={'request':request},many=True)        
            return JsonResponse({'results': serializer.data, 'count': len(pendingOrange)})
            # return pendingOrange
        elif tipo == 'red':
            pendingRed = pendingRed
            serializer =TicketHyperSerializer(pendingRed,context={'request':request},many=True)        
            return JsonResponse({'results': serializer.data, 'count': len(pendingRed)})
            # return pendingRed
        else:
            tickets = pendingGreen | pendingYellow | pendingOrange | pendingRed            
            serializer =TicketHyperSerializer(tickets,context={'request':request},many=True)        
            return JsonResponse({'results': serializer.data, 'count': len(tickets)})
            # return tickets
@api_view(['GET'])
@permission_classes((IsAuthenticatedV2,))
def obtenerDataNotsSpecificUsuarioApp(request,username):
    try:
        user = User.objects.get(username=username)
    except:
        return Response({'error':'No existe el usuario'})
    # ------------------
    # Solo las de hoy todo el dia
    today = datetime.datetime.now().date()
    today_start = datetime.datetime.combine(today, datetime.time())
    tomorrow = today + timedelta(1)#todo el dia
    today_end = datetime.datetime.combine(tomorrow, datetime.time())
    # Actual hoy hace 7 dias
    ahora = datetime.datetime.now()
    hace_una_semana = ahora - timedelta(days=7)
    today_start = datetime.datetime.combine(ahora, datetime.time())
    tomorrow = today_start - timedelta(days = 7)# desde hace 7 días
    today_end = datetime.datetime.combine(tomorrow, datetime.time())
    today_start = today_start + timedelta(days=3)
    # ------****------
    queryset = Assign.objects.filter(user = user).exclude(poliza__status = 15)
    if user.email:
        queryset_ = Pendients.objects.filter(email__iexact = user.email)
    else:
        queryset_ = []    

    if not queryset.exists() and not queryset_.exists():
        return Response({'error':'No existen polizas asignadas a ese usuario'})
   
    polizasUser = Polizas.objects.filter(Q(pk__in = list(queryset.values_list('poliza__id',flat= True))) | Q(pk__in = list(queryset_.values_list('poliza__id',flat= True))))
    polizasGrales = polizasUser
    user_to_send_notification = {}        
    # ntslist =Notifications.objects.filter(seen = False, startsAt__gte = today_start, startsAt__lte = today_end, model = 27).order_by('-id')
    # ntslist =Notifications.objects.filter(seen = False, startsAt__gte = today_end, startsAt__lte = today_start,model = 27).order_by('-id')
    ntslist =Notifications.objects.filter(created_at__gte = today_end, created_at__lte = today_start,model = 27).order_by('-id')

    org_name = 'ancora'
    if user:
        if user.user_info.org_name:
            ntslist = ntslist.filter(org_name = user.user_info.org_name)
            org_name = user.user_info.org_name
        else:
            ntslist = ntslist.filter(org_name = org_name)
    notificaciones_user = []
    glevels = GroupingLevel.objects.filter(org_name = org_name, type_grouping = 1).values_list('pk',flat = True)
    x = 0
    for nts in ntslist:
        x = x+1
        polizasGrales = polizasUser
        # acorde a filtros sacar assign corresponde y, pendients corresponden with users
        if nts.poliza_groupinglevel:
            contractor = Contractor.objects.filter(Q(groupinglevel__id = nts.poliza_groupinglevel) |
                    Q(groupinglevel__parent__id = nts.poliza_groupinglevel) |
                    Q(groupinglevel__parent__parent__id = nts.poliza_groupinglevel) |
                    Q(groupinglevel__parent__parent__id = nts.poliza_groupinglevel), org_name = org_name, is_active = True)
        else:
            contractor = Contractor.objects.filter(Q(groupinglevel__id__in = glevels) |
                    Q(groupinglevel__parent__id__in = glevels) |
                    Q(groupinglevel__parent__parent__id__in = glevels) |
                    Q(groupinglevel__parent__parent__id__in = glevels), org_name = org_name, is_active = True)
        polizasGrales = polizasGrales.filter(Q(contractor__id__in = contractor.values_list('pk',flat =True)) |
            Q(parent__contractor__id__in = contractor.values_list('pk',flat =True)) | 
            Q(parent__parent__contractor__id__in = contractor.values_list('pk',flat =True)) | 
            Q(parent__parent__parent__contractor__id__in = contractor.values_list('pk',flat =True)))
        if nts.poliza_contractor:
            polizasGrales = polizasGrales.filter(Q(contractor__id__in = nts.poliza_contractor) |
                Q(parent__contractor__id__in = nts.poliza_contractor) | 
                Q(parent__parent__contractor__id__in = nts.poliza_contractor) | 
                Q(parent__parent__parent__contractor__id__in = nts.poliza_contractor)).exclude(status = 0)
        if nts.poliza_provider:
            polizasGrales = polizasGrales.filter(Q(aseguradora__id__in = nts.poliza_provider) |
                Q(parent__aseguradora__id__in = nts.poliza_provider) | 
                Q(parent__parent__aseguradora__id__in = nts.poliza_provider) | 
                Q(parent__parent__parent__aseguradora__id__in = nts.poliza_provider)).exclude(status = 0)   
        if nts.poliza_ramo:
            polizasGrales = polizasGrales.filter(Q(ramo__ramo_code__in = nts.poliza_ramo) |
                Q(parent__ramo__ramo_code__in = nts.poliza_ramo) | 
                Q(parent__parent__ramo__ramo_code__in = nts.poliza_ramo) | 
                Q(parent__parent__parent__ramo__ramo_code__in = nts.poliza_ramo)).exclude(status = 0)  
        if polizasGrales:
            notificaciones_user.append(nts)
    # ****************
    serializer = NotificationsAppHyperSerializer(notificaciones_user, context = {'request':request}, many = True)
    data = {'data':serializer.data}
    return Response(data)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def delete_notification_app(request):
    try:
        obj = Notifications.objects.get(pk = request.GET.get('id'),model = 27)
        obj.delete()
        return Response({'status': 'Objeto eliminado'})
    except Exception as e:
        return Response(status=status.HTTP_404_NOT_FOUND)


import logging
import boto3
import random
from botocore.exceptions import ClientError
from django.conf import settings

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def create_presigned_post(request):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """
    org = request.GET.get('org')
    filename = request.GET.get('filename')
    base = 'miurabox/media/{org}/{type}/' + time.strftime("%Y/%m/%d") + '/{file_id}_{img}'
    # Generate a presigned S3 POST URL
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY
    )
    try:
        bucket_name = base.format(
            org=org, 
            type='polizas', 
            img=filename,  
            file_id = random.randint(1,10001)
        ) 
        object_name = 'test'
        fields = {}
        conditions = []
        expiration = 3600

        response = s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    return Response(response)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def update_notification_app(request):
    try:
        obj = Notifications.objects.get(pk = request.GET.get('id'),model = 27)
        obj.seen = True
        obj.save()
        return Response({'status': 'Objeto actualizado*'})
    except Exception as e:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def cotizaciones_graphql(request):
    from gql import gql, Client
    from gql.transport.aiohttp import AIOHTTPTransport

    transport = AIOHTTPTransport(url="https://gateway.staging.ixuapis.com/graphql/")

    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql(
        """
        query listQuotes2
        {
        listQuotes(projectId: "d91c9789-9f66-4d7a-b8d2-5eb150b5851a")
        {
            firstName
            lastName
            frecuency
            packageName
            zipCode
            packageName
            frecuency
            typeFrecuency
            status
            email 
            description
            brand
            year
            phone
            id
            address
            startValidity
            endValidity
            quoteServices{
                insurerService {
                    name
                    quotationCoverages {
                        name
                        code
                            sumAssured
                            deductible
                    }
                }
            }
        }
        }
        """
    )

    # Execute the query on the transport
    result = client.execute(query)

    response = result['listQuotes']
    return JsonResponse(response, safe = False)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def aseguradoras_lectura_documentos(request):
    lecturas = LecturaArchivos.objects.filter(
        org_name = request.GET.get('org')
    )
    response = list(Provider.objects.filter(id__in = list(lecturas.values_list('aseguradora', flat=True))).values_list('alias', flat=True))
    return JsonResponse(response, status = 200, safe=False)


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, ))
def lectura_documentos(request):
    from pdf2image import convert_from_bytes
    lectura = LecturaArchivos.objects.create(
        nombre = request.data['nombre_entrenamiento'],
        tipo_poliza = request.data['tipo_poliza'],
        aseguradora = request.data['aseguradora'],
        ramo = request.data['ramo'],
        subramo = request.data['subramo' ],
        org_name = request.GET.get('org'),
        owner = request.user
    )

    pageNumber = request.data['pageNumber' ]
    if pageNumber:
        pageNumber = int(pageNumber) - 1 
    else:
        pageNumber = 1

    images = convert_from_bytes(request.FILES['arch'].read())
    # for i in range(len(images)):
    #     nombre_imagen = str(lectura.id) + '_page'+ str(i + 1) +'.jpg'
    #     images[i].save(nombre_imagen, 'JPEG')
    #     file_object  = open(nombre_imagen, 'rb')
    #     file_object = File(file_object)
    #     file =  LecturaFile.objects.create(
    #         owner = lectura,
    #         arch =  file_object, 
    #         nombre = nombre_imagen, 
    #         org_name = request.GET.get('org')
    #     )
    #     os.remove(nombre_imagen)
    nombre_imagen = str(lectura.id) + '_page'+ str(pageNumber) +'.jpg'
    try:
        width, height = images[pageNumber].size
        images[pageNumber].save(nombre_imagen, 'JPEG')
    except:
        images[0].save(nombre_imagen, 'JPEG')
    file_object  = open(nombre_imagen, 'rb')
    file_object = File(file_object)
    file =  LecturaFile.objects.create(
        owner = lectura,
        arch =  file_object, 
        nombre = nombre_imagen, 
        org_name = request.GET.get('org'),
        width = width,
        height = height
    )
    os.remove(nombre_imagen)
    serializer = LecturaArchivosSerializer(lectura, context={'request':request}, many = False)
    return Response(serializer.data)


def getUserNotification(notification,request):
    user_to_send_notification = {}
    queryset = Assign.objects.filter(poliza__org_name = request.GET.get('org')).exclude(poliza__status = 15).exclude(user = None)
    users = User.objects.filter(user_info__org_name = request.GET.get('org')).exclude(email = None)
    queryset_ = Pendients.objects.filter(poliza__org_name = request.GET.get('org'), email__in = (users.values_list('email', flat = True)))    
    polizasGrales = Polizas.objects.filter(Q(pk__in = list(queryset.values_list('poliza__pk',flat = True))) | Q(pk__in = list(queryset_.values_list('poliza__pk',flat = True))))
    #perfil restringido aplicar el de user logueado que creo la notificación
    try:
        dataToFilter = getDataForPerfilRestricted(request, request.GET.get('org'))      
    except Exception as er:
        dataToFilter = {}
    if dataToFilter:
        # Contratantes***
        if dataToFilter['ccpr']:
            polizasGrales = polizasGrales.filter(contractor__in = list(dataToFilter['ccpr']))
        if dataToFilter['cgpr']:
            polizasGrales = polizasGrales.filter(contractor__group__in = list(dataToFilter['cgpr']))
        if dataToFilter['ccepr']:
            polizasGrales = polizasGrales.filter(contractor__cellule__in = list(dataToFilter['ccepr']))
        if dataToFilter['crpr']:
            polizasGrales = polizasGrales.filter(contractor__vendor__in = list(dataToFilter['crpr']))
        if dataToFilter['cspr']:
            polizasGrales = polizasGrales.filter(contractor__sucursal__in = list(dataToFilter['cspr']))
        # Pólizas ****
        if dataToFilter['pppr']:
            polizasGrales = polizasGrales.filter(pk__in = list(dataToFilter['pppr']))
        if dataToFilter['pgpr']:
            polizasGrales = polizasGrales.filter(contractor__group__in = list(dataToFilter['pgpr']))
        if dataToFilter['pcepr']:
            polizasGrales = polizasGrales.filter(celula__in = list(dataToFilter['pcepr']))
        if dataToFilter['prpr']:
            polizasGrales = polizasGrales.filter(ref_policy__referenciador__in = list(dataToFilter['prpr']))
        if dataToFilter['pspr']:
            polizasGrales = polizasGrales.filter(sucursal__in = list(dataToFilter['pspr']))
        if dataToFilter['papr']:
            polizasGrales = polizasGrales.filter(groupinglevel__in = list(dataToFilter['papr']))
        if dataToFilter['pcapr']:
            polizasGrales = polizasGrales.filter(clave__in = list(dataToFilter['pcapr']))
        if dataToFilter['psrpr']:
            polizasGrales = polizasGrales.filter(subramo__subramo_code__in = list(dataToFilter['psrpr']))
        if dataToFilter['paspr']:
            polizasGrales = polizasGrales.filter(aseguradora__in = list(dataToFilter['paspr']))
        if dataToFilter['pstpr']:
            polizasGrales = polizasGrales.filter(status__in = list(dataToFilter['pstpr']))
    # notificación creada 
    nts=notification
    glevels = GroupingLevel.objects.filter(org_name = request.GET.get('org'), type_grouping = 1).values_list('pk',flat = True)
    # acorde a filtros sacar assign corresponde y, pendients corresponden with users
    if nts.poliza_groupinglevel !=None:
        contractor = Contractor.objects.filter(Q(groupinglevel__id = nts.poliza_groupinglevel) |
                Q(groupinglevel__parent__id = nts.poliza_groupinglevel) |
                Q(groupinglevel__parent__parent__id = nts.poliza_groupinglevel) |
                Q(groupinglevel__parent__parent__id = nts.poliza_groupinglevel), org_name = request.GET.get('org'), is_active = True)
    else:
        contractor = Contractor.objects.filter(Q(groupinglevel__id__in = glevels) |
                Q(groupinglevel__parent__id__in = glevels) |
                Q(groupinglevel__parent__parent__id__in = glevels) |
                Q(groupinglevel__parent__parent__id__in = glevels), org_name = request.GET.get('org'), is_active = True)
    polizasGrales = polizasGrales.filter(Q(contractor__id__in = contractor.values_list('pk',flat =True)) |
        Q(parent__contractor__id__in = contractor.values_list('pk',flat =True)) | 
        Q(parent__parent__contractor__id__in = contractor.values_list('pk',flat =True)) | 
        Q(parent__parent__parent__contractor__id__in = contractor.values_list('pk',flat =True)))

    if nts.poliza_contractor:
        polizasGrales = polizasGrales.filter(Q(contractor__id__in = nts.poliza_contractor) |
            Q(parent__contractor__id__in = nts.poliza_contractor) | 
            Q(parent__parent__contractor__id__in = nts.poliza_contractor) | 
            Q(parent__parent__parent__contractor__id__in = nts.poliza_contractor)).exclude(status = 0)
    if nts.poliza_provider:
        polizasGrales = polizasGrales.filter(Q(aseguradora__id__in = nts.poliza_provider) |
            Q(parent__aseguradora__id__in = nts.poliza_provider) | 
            Q(parent__parent__aseguradora__id__in = nts.poliza_provider) | 
            Q(parent__parent__parent__aseguradora__id__in = nts.poliza_provider)).exclude(status = 0) 
    if nts.poliza_ramo:
        polizasGrales = polizasGrales.filter(Q(ramo__ramo_code__in = nts.poliza_ramo) |
            Q(parent__ramo__ramo_code__in = nts.poliza_ramo) | 
            Q(parent__parent__ramo__ramo_code__in = nts.poliza_ramo) | 
            Q(parent__parent__parent__ramo__ramo_code__in = nts.poliza_ramo)).exclude(status = 0)        

    if polizasGrales:
        queryset = Assign.objects.filter(poliza__org_name = request.GET.get('org'), poliza__id__in = list(polizasGrales.values_list('pk',flat = True))).exclude(poliza__status = 15).exclude(user = None)
        users = User.objects.filter(user_info__org_name = request.GET.get('org')).exclude(email = None)
        queryset_ = Pendients.objects.filter(poliza__id__in = list(polizasGrales.values_list('pk',flat = True)), poliza__org_name = request.GET.get('org'), email__in = (users.values_list('email', flat = True)))    
        user1 = queryset.values_list('user',flat = True)
        user2 = User.objects.filter(user_info__org_name = request.GET.get('org'), email__in = list(queryset_.values_list('pk',flat = True)))
        user_nots = list(user1) + list(user2)
        user_to_send_notification = User.objects.filter(pk__in = list(user_nots))
    return  user_to_send_notification

class EmailTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = EmailTemplateFullSerializer
    permission_classes = (IsAuthenticatedV2, FormatosPermissionsV2, IsOrgMemberV2)


    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            obj = serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))

        if obj.id:
            send_log(self.request.user, self.request.GET.get('org'), 'POST', 29, 'creó la plantilla de correos', obj.id)


    def get_queryset(self):
        queryset = custom_get_queryset(self.request, EmailTemplate)
        templatemodel = self.request.GET.get('template_model', None)
        if templatemodel:
            queryset = queryset.filter(template_model=templatemodel)
        return queryset
        # return custom_get_queryset(self.request, EmailTemplate)

class EmailTemplateUnpagViewSet(viewsets.ModelViewSet):
    serializer_class = EmailTemplateFullSerializer
    permission_classes = (IsAuthenticatedV2, FormatosPermissionsV2, IsOrgMemberV2)
    pagination_class = None
    def get_queryset(self):
        code=[]
        queryset = custom_get_queryset(self.request, EmailTemplate)
        templatemodel = self.request.GET.get('template_model', None)
        idpoliza = self.request.GET.get('id_policy', 0)
        if idpoliza !=0:
            code_ = Polizas.objects.get(org_name=self.request.GET.get('org'),id=idpoliza)
            code = [code_.ramo.ramo_code,code_.subramo.subramo_code]
        if templatemodel:
            queryset = queryset.filter(template_model=templatemodel)
        if code:
            queryset = queryset.filter(Q(ramo_code__overlap=code) | Q(ramo_code=[]))
            if code_.subramo and code_.subramo.subramo_code ==9:
                queryset = queryset.filter(Q(ramo_code__overlap=[code_.subramo.subramo_code]) | Q(ramo_code=[]))

        return queryset
    
class ConfigKbiViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigKbiFullSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)
    def perform_create(self, serializer):
        self.request.data['tipocambio'] = float(self.request.data['tipocambio'])
        user= self.request.META['user'] if 'user' in self.request.META else self.request.user
        #ConfigKbi.objects.filter(org_name=self.request.GET.get('org'),owner = self.request.user).delete()
        if(ConfigKbi.objects.filter(org_name=self.request.GET.get('org'),owner = self.request.user).exists()):
            query =ConfigKbi.objects.filter(org_name=self.request.GET.get('org'),owner = self.request.user).update(tipocambio = self.request.data['tipocambio'])
        else:
            try:
                obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
            except:
                obj = serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))
    def get_queryset(self):
        #return custom_get_queryset(self.request, ConfigKbi)
        queryset = ConfigKbi.objects.filter(owner=self.request.user,org_name = self.request.GET.get('org'))
        return queryset

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def getRepositorioPago(request):
    # Parameters
    rp = RepositorioPago.objects.filter(org_name=request.GET.get('org')).order_by('-id')
    # serializer = LogReportSerializer(logs, context={'request':request}, many = True)
    # Paginación
    paginator = Paginator(rp, 10)
    try:
        page = request.data['page']
        results = paginator.page(page)
    except:
        results = paginator.page(1)

    serializer = RepositorioPagoSerializer(results, context={'request':request}, many = True)
    return JsonResponse({'results': serializer.data, 'count': len(rp)})

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2, ))
def getConfigsProviderScrapper(request):
    # Parameters
    rp = ConfigProviderScrapper.objects.filter(org_name=request.GET.get('org')).order_by('-id')
    # Paginación
    paginator = Paginator(rp, 10)
    try:
        page = request.data['page']
        results = paginator.page(page)
    except:
        results = paginator.page(1)

    serializer = ConfigProviderScrapperInfoSerializer(results, context={'request':request}, many = True)
    return JsonResponse({'results': serializer.data, 'count': len(rp)})

class PromotoriaTableroViewSet(viewsets.ModelViewSet):
    serializer_class = PromotoriaTableroSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)  
    def get_queryset(self):  
        queryset = PromotoriaTablero.objects.filter(org_name=self.request.GET.get('org')).order_by('-id')
        return queryset
    def perform_create(self, serializer):
        obj_complete = serializer.save(org_name = self.request.GET.get('org'), owner = self.request.user)  
        return obj_complete
    
    def destroy(self, request, *args, **kwargs):
        # print(args,kwargs['pk'])
        la = PromotoriaTablero.objects.filter(id = kwargs['pk']).update(is_active=False)
        return Response(data=kwargs['pk']+str(self.request.GET.get('org')))
@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def getPromotoriaOTsByRamos(request):
    ramos_sel = (request.data['ramos'] if 'ramos' in request.data else [1,2,3,4,5,6,7,8,9,10])
    asegs_sel = request.data['aseguradoras'] if 'aseguradoras' in request.data else []
    type_ots = request.data['type_ots'] if 'type_ots' in request.data else 0
    principal = (request.data['principal'] if 'principal' in request.data else '')

    try:
        prom = PromotoriaTablero.objects.get(pk = int(principal),org_name=request.GET.get('org'),is_active=True)
    except:
        return JsonResponse({'results': [],'original':{},'count': 0})
    ots =Polizas.objects.filter(status=1, org_name = request.GET.get('org'),subramo__subramo_code__in=ramos_sel,document_type__in=[1,3,12])
    endosos =Endorsement.objects.filter(status=5, org_name = request.GET.get('org'),policy__subramo__subramo_code__in=ramos_sel,policy__document_type__in=[1,3,12])
    if asegs_sel:
        ots = ots.filter(aseguradora__in = asegs_sel)
        endosos = endosos.filter(policy__aseguradora__in = asegs_sel)
    # ---------------
    try:
        dataToFilter = getDataForPerfilRestricted(request, request.GET.get('org'))
    except Exception as er:
        dataToFilter = {}
    if dataToFilter:
        # Contratantes***
        polizasCl = Polizas.objects.filter(document_type__in = [1,3,11,7,8,12,6,4], org_name = request.GET.get('org')).exclude(status = 0)
        polizasToF = Polizas.objects.filter(document_type__in = [1,3,11,7,8], org_name = request.GET.get('org')).exclude(status = 0)
        if dataToFilter['ccpr']:
            polizasToF = polizasToF.filter(contractor__in = list(dataToFilter['ccpr']))
        if dataToFilter['cgpr']:
            polizasToF = polizasToF.filter(contractor__group__in = list(dataToFilter['cgpr']))
        if dataToFilter['ccepr']:
            polizasToF = polizasToF.filter(contractor__cellule__in = list(dataToFilter['ccepr']))
        if dataToFilter['crpr']:
            polizasToF = polizasToF.filter(contractor__vendor__id__in = list(dataToFilter['crpr']))
        if dataToFilter['cspr']:
            polizasToF = polizasToF.filter(contractor__sucursal__in = list(dataToFilter['cspr']))
        # Pólizas ****
        if dataToFilter['pppr']:
            polizasToF = polizasToF.filter(pk__in = list(dataToFilter['pppr']))
        if dataToFilter['pgpr']:
            polizasToF = polizasToF.filter(contractor__group__in = list(dataToFilter['pgpr']))
        if dataToFilter['pcepr']:
            polizasToF = polizasToF.filter(celula__in = list(dataToFilter['pcepr']))
        if dataToFilter['prpr']:
            polizasToF = polizasToF.filter(ref_policy__referenciador__id__in = list(dataToFilter['prpr']))
        if dataToFilter['pspr']:
            polizasToF = polizasToF.filter(sucursal__in = list(dataToFilter['pspr']))
        if dataToFilter['papr']:
            polizasToF = polizasToF.filter(groupinglevel__in = list(dataToFilter['papr']))
        if dataToFilter['pcapr']:
            polizasToF = polizasToF.filter(clave__in = list(dataToFilter['pcapr']))
        if dataToFilter['psrpr']:
            polizasToF = polizasToF.filter(subramo__subramo_code__in = list(dataToFilter['psrpr']))
        if dataToFilter['paspr']:
            polizasToF = polizasToF.filter(aseguradora__in = list(dataToFilter['paspr']))
        if dataToFilter['pstpr']:
            polizasToF = polizasToF.filter(status__in = list(dataToFilter['pstpr']))
        
        polizasCT = polizasCl.filter(document_type = 12, parent__in = list(polizasToF))
        polizasGT = polizasCl.filter(Q(parent__parent__parent__in = list(polizasToF)) | Q(parent__parent__in = list(polizasToF)),document_type__in = [6,4])
        polizasFin = list(polizasToF.values_list('pk', flat = True)) + list(polizasCT.values_list('pk', flat = True)) + list(polizasGT.values_list('pk', flat = True))
        ots = ots.filter(pk__in = list(polizasFin))  
        endosos = endosos.filter(policy__id__in = list(polizasFin)) 
    # ******************
    ots_=[]
    # -----------------
    # otsprom = json.loads(prom.config)
    data_filter=[]
    try:
        otsprom = json.loads(prom.polizas_ots)
    except Exception as eee:
        otsprom = prom.polizas_ots
        try:
            otsprom = eval(otsprom)
        except Exception as e:
            pass
    data_filter=[]
    for index,ot in enumerate(otsprom):
        try:
            ot = json.loads(ot)
        except Exception as eee:
            print('errrr',eee)
        if ot and 'tablero' in ot and ot['tablero']:
            data_={
                'tablero': ot['tablero'] if ot and 'tablero' in ot else '',
                'color':ot['color'] if ot and 'color' in ot else '',
                'polizas':[],
                'endoso':[]
            }
            if 'polizas' in ot:
                for ind,pks in enumerate(ot['polizas']):
                    if (type_ots)==1:
                        data_['endoso']=[]
                        if pks in ots_:
                            data_['polizas'].append(pks)
                    elif (type_ots)==2:
                        data_['polizas']=[]
                    elif (type_ots)==0:
                        if pks in ots_:
                            data_['polizas'].append(pks)
                    else:
                        if pks in ots_:
                            data_['polizas'].append(pks)
            
            if 'endoso' in ot:
                for ind,pkse in enumerate(ot['endoso']):
                    if (type_ots)==1:
                        data_['endoso'] = []
                    elif (type_ots)==2:
                        data_['polizas']=[]
                        if pkse in endosos.values_list('pk',flat=True):
                            data_['endoso'].append(pkse)
                    elif (type_ots)==0:
                        if pkse in endosos.values_list('pk',flat=True):
                            data_['endoso'].append(pkse)
                    else:
                        if pkse in endosos.values_list('pk',flat=True):
                            data_['endoso'].append(pkse)                        
            if data_['polizas']:
                listap = Polizas.objects.filter(pk__in = data_['polizas'], org_name=request.GET.get('org'),status=1).order_by('-id')
                data_['details_polizas'] = PolizaHyperPromotoriaSerializer(instance = listap, context={'request':request}, many = True).data
                
            if data_['endoso']:
                listae = Endorsement.objects.filter(pk__in = data_['endoso'], org_name=request.GET.get('org'),status=5).order_by('-id')
                data_['details_endoso'] = EndorsementHyperPromotoriaSerializer(instance = listae, context={'request':request}, many = True).data
            data_filter.append(data_)
    valores_filtrados = (data_filter)   

    serializer = PromotoriaTableroSerializer(prom,context={'request':request},many=False)        
    return JsonResponse({'results': valores_filtrados,'original':serializer.data,'count': len(ots)})

@api_view(['POST','GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def fsubramos_tablero(request):
    org_name = request.GET.get('org')
    user = request.user
    ui = UserInfo.objects.filter(user = user)
    if ui.exists():
        ui = ui.first()
    else:
        ui = None
    if request.method == 'POST':
        if ui:
            ui.subramos_tablero = request.data['subramos'] if 'subramos' in request.data else []
            ui.aseguradoras_tablero = request.data['aseguradoras'] if 'aseguradoras' in request.data else []
            ui.type_ots = request.data['type_ots'] if 'type_ots' in request.data else 0
            ui.save()
            return JsonResponse({'status':'done'}, status = 200)
        else:
            return JsonResponse({'error':'not found'}, status = 404)
    if request.method == 'GET':
        if ui:
            return JsonResponse({'data':ui.subramos_tablero,'aseguradoras':ui.aseguradoras_tablero,'type_ots':ui.type_ots}, status = 200)
        else:
            return JsonResponse({'error':'not found'}, status = 404)

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def getPromotoriaOTsInitial(request):
    try:
        prom = PromotoriaTablero.objects.filter(org_name=request.GET.get('org'),is_active=True).order_by('-id')[0]
    except:
        prom = {}
    ots =Polizas.objects.filter(status=1, org_name = request.GET.get('org'),document_type__in=[1,3,12]).order_by('id')
    endosos =Endorsement.objects.filter(status__in=[5,1], org_name = request.GET.get('org'),policy__document_type__in=[1,3,12]).order_by('id')
    # ---------------
    user = request.user
    ui = UserInfo.objects.filter(user = user)
    if ui.exists():
        ui = ui.first()
    else:
        ui = None
    config = False
    ramos_sel = [1,2,3,4,5,6,7,8,9,10]
    if ui:
        if ui.subramos_tablero:
            ramos_sel = ui.subramos_tablero
            ots =ots.filter(subramo__subramo_code__in=ramos_sel)
            endosos =endosos.filter(policy__subramo__subramo_code__in=ramos_sel)
            config = True
        if ui.aseguradoras_tablero:
            asegs_sel = ui.aseguradoras_tablero
            ots =ots.filter(aseguradora__id__in=asegs_sel)
            endosos =endosos.filter(policy__aseguradora__id__in=asegs_sel)
            config = True
        
    principal = (request.data['principal'] if 'principal' in request.data else '')
    try:
        prom = PromotoriaTablero.objects.get(pk = int(principal),org_name=request.GET.get('org'),is_active=True)
    except Exception as er:
        print('error -',er)
        try:
            prom = PromotoriaTablero.objects.filter(org_name=request.GET.get('org'),is_active=True).order_by('updated_at')[0]
        except Exception as x:
            return JsonResponse({'results': [],'original':[],'count': 0,'perfilRestringido':'','config':[]})
        # return JsonResponse({'results': [],'original':{},'count': 0})

    # ----------------
    perfilRestringido = False
    try:
        dataToFilter = getDataForPerfilRestricted(request, request.GET.get('org'))
    except Exception as er:
        dataToFilter = {}
    if dataToFilter:
        perfilRestringido = True
        # Contratantes***
        polizasCl = Polizas.objects.filter(document_type__in = [1,3,11,7,8,12,6,4], org_name = request.GET.get('org')).exclude(status = 0)
        polizasToF = Polizas.objects.filter(document_type__in = [1,3,11,7,8], org_name = request.GET.get('org')).exclude(status = 0)
        if dataToFilter['ccpr']:
            polizasToF = polizasToF.filter(contractor__in = list(dataToFilter['ccpr']))
        if dataToFilter['cgpr']:
            polizasToF = polizasToF.filter(contractor__group__in = list(dataToFilter['cgpr']))
        if dataToFilter['ccepr']:
            polizasToF = polizasToF.filter(contractor__cellule__in = list(dataToFilter['ccepr']))
        if dataToFilter['crpr']:
            polizasToF = polizasToF.filter(contractor__vendor__in = list(dataToFilter['crpr']))
        if dataToFilter['cspr']:
            polizasToF = polizasToF.filter(contractor__sucursal__in = list(dataToFilter['cspr']))
        # Pólizas ****
        if dataToFilter['pppr']:
            polizasToF = polizasToF.filter(pk__in = list(dataToFilter['pppr']))
        if dataToFilter['pgpr']:
            polizasToF = polizasToF.filter(contractor__group__in = list(dataToFilter['pgpr']))
        if dataToFilter['pcepr']:
            polizasToF = polizasToF.filter(celula__in = list(dataToFilter['pcepr']))
        if dataToFilter['prpr']:
            polizasToF = polizasToF.filter(ref_policy__referenciador__in = list(dataToFilter['prpr']))
        if dataToFilter['pspr']:
            polizasToF = polizasToF.filter(sucursal__in = list(dataToFilter['pspr']))
        if dataToFilter['papr']:
            polizasToF = polizasToF.filter(groupinglevel__in = list(dataToFilter['papr']))
        if dataToFilter['pcapr']:
            polizasToF = polizasToF.filter(clave__in = list(dataToFilter['pcapr']))
        if dataToFilter['psrpr']:
            polizasToF = polizasToF.filter(subramo__subramo_code__in = list(dataToFilter['psrpr']))
        if dataToFilter['paspr']:
            polizasToF = polizasToF.filter(aseguradora__in = list(dataToFilter['paspr']))
        if dataToFilter['pstpr']:
            polizasToF = polizasToF.filter(status__in = list(dataToFilter['pstpr']))
        
        polizasCT = polizasCl.filter(document_type = 12, parent__in = list(polizasToF))
        polizasGT = polizasCl.filter(Q(parent__parent__parent__in = list(polizasToF)) | Q(parent__parent__in = list(polizasToF)),document_type__in = [6,4])
        polizasFin = list(polizasToF.values_list('pk', flat = True)) + list(polizasCT.values_list('pk', flat = True)) + list(polizasGT.values_list('pk', flat = True))
        ots = ots.filter(pk__in = list(polizasFin))  
        endosos = endosos.filter(policy__id__in = list(polizasFin)) 

    # ******************
    ots_ =(ots).values_list('id',flat=True)
    endosos_ =(endosos).values_list('id',flat=True)
    try:
        otsprom = json.loads(prom.polizas_ots)
    except Exception as eee:
        otsprom = prom.polizas_ots
        try:
            otsprom = eval(otsprom)
        except Exception as e:
            pass
    data_filter=[]
    for index,ot in enumerate(otsprom):
        try:
            ot = json.loads(ot)
        except Exception as eee:
            print('errrr',eee)
        if ot and 'tablero' in ot and ot['tablero']:
            data_={
                'tipo': ot['tipo'] if ot and 'tipo' in ot else 1,
                'tablero': ot['tablero'] if ot and 'tablero' in ot else '',
                'color':ot['color'] if ot and 'color' in ot else '',
                'polizas':[],
                'endoso':[]
            }
            if 'polizas' in ot:
                for ind,pks in enumerate(ot['polizas']):
                    if ui and ui.type_ots and int(ui.type_ots)==1:
                        data_['endoso']=[]
                        if pks in ots_:
                            data_['polizas'].append(pks)
                    elif ui and ui.type_ots and int(ui.type_ots)==2:
                        data_['polizas']=[]
                    elif ui and ui.type_ots and int(ui.type_ots)==0:
                        if pks in ots_:
                            data_['polizas'].append(pks)
                    else:
                        if pks in ots_:
                            data_['polizas'].append(pks)
            
            if 'endoso' in ot:
                for ind,pkse in enumerate(ot['endoso']):
                    if ui and ui.type_ots and int(ui.type_ots)==1:
                        data_['endoso'] = []
                    elif ui and ui.type_ots and int(ui.type_ots)==2:
                        data_['polizas']=[]
                        if pkse in endosos.values_list('pk',flat=True):
                            data_['endoso'].append(pkse)
                    elif ui and ui.type_ots and int(ui.type_ots)==0:
                        if pkse in endosos.values_list('pk',flat=True):
                            data_['endoso'].append(pkse)
                    else:
                        if pkse in endosos.values_list('pk',flat=True):
                            data_['endoso'].append(pkse)
                        
            if data_['polizas']:
                listap = Polizas.objects.filter(pk__in = data_['polizas'], org_name=request.GET.get('org'),status=1)
                data_['details_polizas'] = PolizaHyperPromotoriaSerializer(instance = listap, context={'request':request}, many = True).data
                
            if data_['endoso']:
                listae = Endorsement.objects.filter(pk__in = data_['endoso'], org_name=request.GET.get('org'),status__in=[5,1])
                data_['details_endoso'] = EndorsementHyperPromotoriaSerializer(instance = listae, context={'request':request}, many = True).data
            data_filter.append(data_)
    if data_filter:
        valores_filtrados = (data_filter)      
        serializer = PromotoriaTableroDetailSerializer(prom,context={'request':request},many=False)  
        return JsonResponse({'results': valores_filtrados,'original':serializer.data,'count': len(ots),'perfilRestringido':perfilRestringido,'config':config})
    else:
        return JsonResponse({'results': [],'original':[],'count': 0,'perfilRestringido':perfilRestringido})

@api_view(['POST'])
@permission_classes((IsAuthenticatedV2,))
def get_log_system(request):
    data_ok = {}
    try:
        logs = Log.objects.filter(org_name = request.GET.get('org'), model =32)
        data = LogInfoSerializer(logs,context={'request':request},many=True)
        data_ok = data.data 
    except Exception as e:
        return Response(str(e), status=status.HTTP_404_NOT_FOUND)
    return Response(data_ok, status= status.HTTP_200_OK)

class SmsTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = SmsTemplateFullSerializer
    permission_classes = (IsAuthenticatedV2, FormatosPermissionsV2, IsOrgMemberV2)


    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            obj = serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))

        if obj.id:
            send_log(self.request.user, self.request.GET.get('org'), 'POST', 33, 'creó la plantilla de sms', obj.id)


    def get_queryset(self):
        return custom_get_queryset(self.request, SmsTemplate)
    

class whatsappwebtemplateViewSet(viewsets.ModelViewSet):
    serializer_class = SmsTemplateFullSerializer
    permission_classes = (IsAuthenticatedV2, FormatosPermissionsV2, IsOrgMemberV2)
    pagination_class = StandardResultsSetPagination  # habilita paginación

    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            obj = serializer.save(owner=self.request.user, org_name = self.request.POST.get('org'))

        if obj.id:
            send_log(self.request.user, self.request.GET.get('org'), 'POST', 33, 'creó la plantilla de whatsapp', obj.id)


    def get_queryset(self):
            """
            🔹 Devuelve solo plantillas tipo WhatsApp Web (type_message=2)
            🔹 Filtra por organización
            🔹 Incluye paginación
            """
            org = self.request.GET.get('org')
            typem = self.request.GET.get('type_message')
            queryset = custom_get_queryset(self.request, SmsTemplate)

            if org:
                queryset = queryset.filter(org_name=org)
            # 🔹 Solo plantillas WhatsApp Web
            if typem:
                queryset = queryset.filter(type_message=typem).order_by('-created_at')
            else:
                queryset = queryset.filter(type_message=2).order_by('-created_at')

            return queryset


class whatsappwebtemplateUnpagViewSet(viewsets.ModelViewSet):
    serializer_class = SmsTemplateFullSerializer
    permission_classes = (IsAuthenticatedV2, FormatosPermissionsV2, IsOrgMemberV2)
    pagination_class = None
    def get_queryset(self):
        org = self.request.GET.get('org')
        queryset = custom_get_queryset(self.request, SmsTemplate)
        typem = self.request.GET.get('type_message')

        if org:
            queryset = queryset.filter(org_name=org)
        if typem:
            queryset = queryset.filter(type_message=typem).order_by('-created_at')
        else:
            queryset = queryset.filter(type_message=2).order_by('-created_at')

        return queryset

class SmsTemplateUnpagViewSet(viewsets.ModelViewSet):
    serializer_class = SmsTemplateFullSerializer
    permission_classes = (IsAuthenticatedV2, FormatosPermissionsV2, IsOrgMemberV2)
    pagination_class = None
    def get_queryset(self):
        return custom_get_queryset(self.request, SmsTemplate)

@api_view(['POST','GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def GetTemplatesList(request):
    templates = SmsTemplate.objects.filter(org_name = request.GET.get('org'),type_message=1)
    paginator = Paginator(templates, 10)
    try:
        page = request.data['page']
        results = paginator.page(page)
    except: 
        results = paginator.page(1)
    
    serializer = SmsTemplateFullSerializer(results,context={'request':request},many=True)     

    return JsonResponse({'results': serializer.data, 'count': len(templates)})


@api_view(['POST'])
@permission_classes((AllowAny,))
def crear_notificacion_reportes(request):
    data = {}
    try:
        user = User.objects.get(username = request.data['assigned'])
        notificacion = {
            'seen':False,
            'owner':user,
            'id_reference':request.data['id_reference'],
            'assigned':user,
            'org_name':request.data['org_name'],
            'description':request.data['description'],
            'model':26,
            'title':request.data['title'],
        }
        notificacion,crear_not = Notifications.objects.get_or_create(**notificacion)    

        return Response({'status': 'Objeto creado*','id':notificacion.id,'creado':crear_not})
    except Exception as e:
        return Response(str(e), status=status.HTTP_204_NO_CONTENT)
    
# @api_view(['GET'])
# @permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
# def GetCarouselFromCas(request):
#     carousel = requests.get(settings.CAS_URL + 'get-carousel-items/' + request.GET.get('org'))
#     response_org = carousel.text
#     carouseldata = json.loads(response_org)
#     carouselinfo = carouseldata['data']
#     return JsonResponse({'data': carouselinfo})
import json
import logging
import requests
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def GetCarouselFromCas(request):
    org = request.GET.get('org', '').strip()
    if not org:
        return JsonResponse({'data': []}, status=200)
    url = settings.CAS_URL.rstrip('/') + '/get-carousel-items/{}'.format(org)
    try:
        # timeout corto para no “congelar” tu login/home
        r = requests.get(url, timeout=5,verify=False)
        # si CAS responde 4xx/5xx
        if r.status_code != 200:
            logger.warning("CAS carousel HTTP %s url=%s body=%s", r.status_code, url, r.text[:300])
            return JsonResponse({'data': []}, status=200)
        # CAS te está mandando HTML a veces; esto evita json.loads() tronando
        try:
            payload = r.json()
        except ValueError:
            logger.warning("CAS carousel non-JSON url=%s content_type=%s body=%s",
                           url, r.headers.get('content-type'), r.text[:300])
            return JsonResponse({'data': []}, status=200)
        # valida estructura
        data = payload.get('data', [])
        if not isinstance(data, list):
            # si viene dict u otra cosa, lo normalizamos
            data = []
        return JsonResponse({'data': data}, status=200)
    except requests.exceptions.SSLError as e:
        logger.exception("CAS SSL error url=%s err=%s", url, e)
        return JsonResponse({'data': []}, status=200)
    except requests.exceptions.Timeout:
        logger.warning("CAS timeout url=%s", url)
        return JsonResponse({'data': []}, status=200)
    except requests.exceptions.RequestException as e:
        # incluye ConnectionError, etc.
        logger.exception("CAS request error url=%s err=%s", url, e)
        return JsonResponse({'data': []}, status=200)
    except Exception as e:
        # por si algo inesperado ocurre
        logger.exception("Unexpected error in GetCarouselFromCas url=%s err=%s", url, e)
        return JsonResponse({'data': []}, status=200)

@api_view(['GET'])
# @permission_classes((IsOrgMemberV2))
@permission_classes((AllowAny,))
def authenticateInSaamFromMC(request):
    token  = request.META['HTTP_AUTHORIZATION'].replace('Bearer ', '')
    # Obtener token y hacer la validacion con la tabla de sessiones   
    if Session.objects.filter(jwt_token=token).exists():        
        session = Session.objects.filter(jwt_token=token).first()
    else:
        session=None
    if session:     
        return Response({'status': True}, status = status.HTTP_200_OK)
    else:
        return Response({'status': False}, status = status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def quotations_initial(request):
    time_inicial = time.time()
    labelGreen = 'En tiempo'
    labelYellow = 'Atención'
    labelOrange = 'Atención urgente'
    labelRed = 'Urgente'

    org = request.GET.get('org')
    try:
        try:
            config_chart = Graphics.objects.get(owner=request.user, org_name=org, type_graphic = 6)
        except:
            config_chart = Graphics.objects.get(org_name=org, type_graphic = 6)
        days_green = config_chart.green if config_chart.green else 45
        days_yellow = config_chart.yellow if config_chart.yellow else 30
        days_orange = config_chart.orange if config_chart.orange else 15
        days_red = config_chart.red if config_chart.red else 1000
        filter_graphs =  config_chart.option_filter
    except Exception as e:
        config_chart = None
        days_green = 45
        days_yellow = 30
        days_orange = 15
        days_red = 1000
        filter_graphs = 3

    today = datetime.datetime.today()
    orange_days = timedelta(days = days_orange)
    yellow_days = timedelta(days = days_yellow)
    green_days = timedelta(days = days_green)
    red_days = timedelta(days = days_red)

    diasO = today + orange_days
    diasY = today + yellow_days
    diasG = today + green_days
    # option_filter: Default todas(except eliminadas y emitida), 1 en trámite, 2 bateada
    if int(filter_graphs) ==1:
        lista = Cotizacion.objects.filter(org_name=org,status=1)
    elif int(filter_graphs) ==2: 
        lista = Cotizacion.objects.filter(org_name=org,status=3)
    else:
        lista = Cotizacion.objects.filter(org_name=org,status__in=[1,3]).exclude(status=0)
    lista = lista.exclude(status=3)
    # *************************************
    diasO = today - orange_days
    diasY = today - yellow_days
    diasG = today - green_days
    # diasR = today - red_days        

    pendingGreen = lista.filter(created_at__lte = today, created_at__gt = diasG)
    pendingYellow = lista.filter(created_at__lte = diasG, created_at__gt = diasY)
    pendingOrange = lista.filter(created_at__lte = diasY, created_at__gt = diasO)
    pendingRed = lista.filter(created_at__lte = diasO)

    # ***********************************+**
    green = pendingGreen.count()
    yellow = pendingYellow.count()
    orange = pendingOrange.count()
    red = pendingRed.count()   


    pendingGreen = pendingGreen.values('org_name').annotate(Count('org_name')).order_by('org_name')
    pendingYellow = pendingYellow.values('org_name').annotate(Count('org_name')).order_by('org_name')
    pendingOrange = pendingOrange.values('org_name').annotate(Count('org_name')).order_by('org_name')
    pendingRed = pendingRed.values('org_name').annotate(Count('org_name')).order_by('org_name')
    # prioridad ALTA
    pendingGreen1 = lista.filter(created_at__lte = today, created_at__gt = diasG).values('status').annotate(Count('status')).order_by('org_name')
    pendingYellow1 = lista.filter(created_at__lte = diasG, created_at__gt = diasY).values('status').annotate(Count('status')).order_by('org_name')
    pendingOrange1 = lista.filter(created_at__lte = diasY, created_at__gt = diasO).values('status').annotate(Count('status')).order_by('org_name')
    pendingRed1 = lista.filter(created_at__lte = diasO).values('status').annotate(Count('status')).order_by('org_name')
    # prioridad Media
    pendingGreen2 = lista.filter(created_at__lte = today, created_at__gt = diasG).values('status').annotate(Count('status')).order_by('org_name')
    pendingYellow2 = lista.filter(created_at__lte = diasG, created_at__gt = diasY).values('status').annotate(Count('status')).order_by('org_name')
    pendingOrange2 = lista.filter(created_at__lte = diasY, created_at__gt = diasO).values('status').annotate(Count('status')).order_by('org_name')
    pendingRed2 = lista.filter(created_at__lte = diasO).values('status').annotate(Count('status')).order_by('org_name')
    # prioridad Baja
    pendingGreen3 =lista.filter(created_at__lte = today, created_at__gt = diasG).values('status').annotate(Count('status')).order_by('org_name')
    pendingYellow3 =lista.filter(created_at__lte = diasG, created_at__gt = diasY).values('status').annotate(Count('status')).order_by('org_name')
    pendingOrange3 =lista.filter(created_at__lte = diasY, created_at__gt = diasO).values('status').annotate(Count('status')).order_by('org_name')
    pendingRed3 =lista.filter(created_at__lte = diasO).values('status').annotate(Count('status')).order_by('org_name')

    if len(pendingGreen):
        green = pendingGreen[0]['org_name__count']
    else:
        green = 0
    if len(pendingYellow):
        yellow = pendingYellow[0]['org_name__count']
    else:
        yellow = 0

    if len(pendingOrange):
        orange = pendingOrange[0]['org_name__count']
    else:
        orange = 0
    if len(pendingRed):
        red = pendingRed[0]['org_name__count']
    else:
        red = 0
    # Green
    if len(pendingGreen1):
        greenAlta = pendingGreen1[0]['status__count']
    else:
        greenAlta = 0
    if len(pendingGreen2):
        greenMedia = pendingGreen2[0]['status__count']
    else:
        greenMedia = 0
    if len(pendingGreen3):
        greenBaja = pendingGreen3[0]['status__count']
    else:
        greenBaja = 0
    # Yellow
    if len(pendingYellow1):
        yellowAlta = pendingYellow1[0]['status__count']
    else:
        yellowAlta = 0
    if len(pendingYellow2):
        yellowMedia = pendingYellow2[0]['status__count']
    else:
        yellowMedia = 0
    if len(pendingYellow3):
        yellowBaja = pendingYellow3[0]['status__count']
    else:
        yellowBaja = 0
    # Orange
    if len(pendingOrange1):
        orangeAlta = pendingOrange1[0]['status__count']
    else:
        orangeAlta = 0
    if len(pendingOrange2):
        orangeMedia = pendingOrange2[0]['status__count']
    else:
        orangeMedia = 0
    if len(pendingOrange3):
        orangeBaja = pendingOrange3[0]['status__count']
    else:
        orangeBaja = 0
    # Red
    if len(pendingRed1):
        redAlta = pendingRed1[0]['status__count']
    else:
        redAlta = 0
    if len(pendingRed2):
        redMedia = pendingRed2[0]['status__count']
    else:
        redMedia = 0
    if len(pendingRed3):
        redBaja = pendingRed3[0]['status__count']
    else:
        redBaja = 0

    total = green + yellow + orange + red

    if green > 0:
        greenPercent = (green / total) * 100
    else:
        greenPercent = 0

    if yellow > 0:
        yellowPercent = (yellow / total) * 100
    else:
        yellowPercent = 0

    if orange > 0:
        orangePercent = (orange / total) * 100
    else:
        orangePercent = 0

    if red > 0:
        redPercent = (red / total) * 100
    else:
        redPercent = 0

    data = {'green': {'title': 'Restan entre ' + str(days_green) + ' y ' + str(0) + ' días',  
                    'percent': greenPercent, 
                    'Alta': str(greenAlta), 
                    'Media': str(greenMedia), 
                    'Baja': str(greenBaja), 
                    'label': labelGreen, 
                    'status': str(green) + '/' + str(total)},
            'yellow': {'title': 'Restan entre ' + str(days_yellow) + ' y ' + str(days_green) + ' días',  
                    'percent': yellowPercent, 
                    'Alta': str(yellowAlta), 
                    'Media': str(yellowMedia), 
                    'Baja': str(yellowBaja), 
                    'label': labelYellow, 
                    'status': str(yellow) + '/' + str(total)}, 
            'orange': {'title': 'Restan entre ' + str(days_orange) + ' y ' + str(days_yellow) + ' días',  
                    'percent': orangePercent, 
                    'Alta': str(orangeAlta), 
                    'Media': str(orangeMedia), 
                    'Baja': str(orangeBaja),
                    'label': labelOrange, 
                    'status': str(orange) + '/' + str(total)}, 
            'red': {'title': 'Sin días restantes',  
                    'percent': redPercent, 
                    'Alta': str(redAlta), 
                    'Media': str(redMedia), 
                    'Baja': str(redBaja),                    
                    'label': labelRed, 
                    'status': str(red) + '/' + str(total)}
            }
    return JsonResponse(data)
@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def quotations_graphic(request):
    tipo = request.data['tipo']
    request = request
    org_name=request.GET.get('org')
    try:
        try:
            config_chart = Graphics.objects.get(owner=request.user, org_name=org_name, type_graphic = 6)
        except:
            config_chart = Graphics.objects.get(org_name=org_name, type_graphic = 6)
        days_green = config_chart.green if config_chart.green else 45
        days_yellow = config_chart.yellow if config_chart.yellow else 30
        days_orange = config_chart.orange if config_chart.orange else 15
        days_red = config_chart.red if config_chart.red else 1000
        filter_graphs =  config_chart.option_filter
    except:
        config_chart = None
        days_green = 45
        days_yellow = 30
        days_orange = 15
        days_red = 1000
        filter_graphs = 3

    today = datetime.datetime.today()
    orange_days = timedelta(days = days_orange)
    yellow_days = timedelta(days = days_yellow)
    green_days = timedelta(days = days_green)
    red_days = timedelta(days = days_red)

    diasO = today + orange_days
    diasY = today + yellow_days
    diasG = today + green_days

    if int(filter_graphs) ==1:
        lista = Cotizacion.objects.filter(org_name=org_name,status=1).distinct('id').order_by('id')
    elif int(filter_graphs) ==2: 
        lista = Cotizacion.objects.filter(org_name=org_name,status=3).distinct('id').order_by('id')
    else:
        lista = Cotizacion.objects.filter(org_name=org_name,status__in=[1,3]).exclude(status=0).distinct('id').order_by('id')
    lista = lista.exclude(status=3)
    # ------------------------------------
    diasO = today - orange_days
    diasY = today - yellow_days
    diasG = today - green_days
    diasR = today - red_days     
    pendingGreen = lista.filter(created_at__lte = today, created_at__gt = diasG).distinct('id').order_by('id')
    pendingYellow = lista.filter(created_at__lte = diasG, created_at__gt = diasY).distinct('id').order_by('id')
    pendingOrange = lista.filter(created_at__lte = diasY, created_at__gt = diasO).distinct('id').order_by('id')
    pendingRed = lista.filter(created_at__lte = diasO).distinct('id').order_by('id')
    # *************************************+
    # green = pendingGreen.count()
    # yellow = pendingYellow.count()
    # orange = pendingOrange.count()
    red = pendingRed.count() 
    # -----------------------------
    # total_neto = 0
    if tipo == 'green':
        pendingGreen = pendingGreen
        paginator = Paginator(pendingGreen, 10)
        try:
            page = request.data['page']
            results = paginator.page(page)
        except:
                results = paginator.page(1)
        serializer =CotizacionFullSerializer(results,context={'request':request},many=True)        
        return JsonResponse({'results': serializer.data, 'count': len(pendingGreen)})
        # return pendingGreen
    elif tipo == 'yellow':
        pendingYellow = pendingYellow
        paginator = Paginator(pendingYellow, 10)
        try:
            page = request.data['page']
            results = paginator.page(page)
        except:
                results = paginator.page(1)
        serializer =CotizacionFullSerializer(results,context={'request':request},many=True)         
        return JsonResponse({'results': serializer.data, 'count': len(pendingYellow)})
        # return pendingYellow
    elif tipo == 'orange':
        pendingOrange = pendingOrange
        paginator = Paginator(pendingOrange, 10)
        try:
            page = request.data['page']
            results = paginator.page(page)
        except:
                results = paginator.page(1)
        serializer =CotizacionFullSerializer(results,context={'request':request},many=True)        
        return JsonResponse({'results': serializer.data, 'count': len(pendingOrange)})
        # return pendingOrange
    elif tipo == 'red':
        pendingRed = pendingRed
        paginator = Paginator(pendingRed, 10)
        try:
            page = request.data['page']
            results = paginator.page(page)
        except:
                results = paginator.page(1)
        serializer =CotizacionFullSerializer(results,context={'request':request},many=True)          
        return JsonResponse({'results': serializer.data, 'count': len(pendingRed)})
        # return pendingRed
    else:
        quotations = pendingGreen | pendingYellow | pendingOrange | pendingRed     
        paginator = Paginator(quotations, 10)
        try:
            page = request.data['page']
            results = paginator.page(page)
        except:
                results = paginator.page(1)
        serializer =CotizacionFullSerializer(results,context={'request':request},many=True)             
        return JsonResponse({'results': serializer.data, 'count': len(quotations)})

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def BuscarReferenciadorLista(request):
    abuscar = request.GET.get('abuscar', '')
    org = request.GET.get('org')
    if not abuscar or not org:
        return Response([])
    userinfo_qs = UserInfo.objects.select_related('user').filter(
        org_name=org,
        user__is_superuser=False
    ).filter(
        Q(user__first_name__icontains=abuscar) |
        Q(user__last_name__icontains=abuscar) |
        Q(user__username__icontains=abuscar) |
        Q(user__email__icontains=abuscar)
    ).order_by('user__first_name')
    userinfo_qs = User.objects.filter(id__in=userinfo_qs.values_list('user__id',flat=True))
    serializer = UserInfoVendedoresSerializer(userinfo_qs, context={'request': request}, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes((AllowAny,))
def check_user_name_exists(request):
    data = {}
    try:
        first = request.data.get("first_name")
        last  = request.data.get("last_name")
        org   = request.data.get("org")
        usersaam=UserInfo.objects.filter(
            user__first_name__iexact=first,
            user__last_name__iexact=last,
            org_name=org
        ).values_list('id','user__id')
        existe = UserInfo.objects.filter(
            user__first_name__iexact=first,
            user__last_name__iexact=last,
            org_name=org
        ).exists()
        return Response({"existe": existe,"user_saam":usersaam if existe else {}}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(str(e), status=status.HTTP_204_NO_CONTENT)

# upload file public
# -*- coding: utf-8 -*-
import re
import uuid
import mimetypes

import boto3
from botocore.exceptions import ClientError

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


def safe_filename(name):
    # Limpia nombre (espacios -> _, y quita raros)
    if not name:
        return "file"
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    if not name:
        name = "file"
    return name


@csrf_exempt  # quítalo si ya envías CSRF token desde tu front
@require_POST
def uploadPublicFile(request):
    """
    POST multipart/form-data:
      - file: el archivo
      - (opcional) folder: si no quieres permitirlo, lo forzamos a 'layouts'
    Respuesta:
      { ok: true, url: "...", key: "layouts/..." }
    """
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"ok": False, "error": "Falta el archivo en el campo 'file'."}, status=400)

    # Fuerza carpeta a layouts (recomendado)
    folder = (request.POST.get("folder") or "layouts").strip().strip("/")
    if folder != "layouts":
        folder = "layouts"

    original_name = safe_filename(getattr(f, "name", "file"))
    unique_name = "{}_{}".format(uuid.uuid4().hex, original_name)
    key = "{}/{}".format(folder, original_name)

    # Content-Type
    content_type = getattr(f, "content_type", None)
    if not content_type:
        guessed = mimetypes.guess_type(original_name)[0]
        content_type = guessed or "application/octet-stream"

    bucket = getattr(settings, "AWS_PUBLIC_BUCKET", "miurabox-public")
    base_url = getattr(
        settings,
        "AWS_PUBLIC_BASE_URL",
        "https://miurabox-public.s3.us-east-1.amazonaws.com/"
    )

    # Si estás en EC2/ECS con IAM Role, puedes omitir access_key/secret_key
    s3 = boto3.client(
        "s3",
        region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
        aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
        aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
    )

    extra_args = {
        "ContentType": content_type,
        "CacheControl": "public, max-age=31536000",
    }

    # Intento 1: con ACL public-read (solo si tu bucket lo permite)
    try:
        extra_acl = dict(extra_args)
        extra_acl["ACL"] = "public-read"
        s3.upload_fileobj(f, bucket, key, ExtraArgs=extra_acl)

    except ClientError as e:
        code = None
        try:
            code = e.response.get("Error", {}).get("Code")
        except Exception:
            code = None

        # Si el bucket tiene ACLs deshabilitadas (Bucket owner enforced),
        # reintenta SIN ACL y confía en Bucket Policy para hacerlo público.
        if code in ("AccessControlListNotSupported", "InvalidRequest"):
            try:
                s3.upload_fileobj(f, bucket, key, ExtraArgs=extra_args)
            except ClientError as e2:
                return JsonResponse({
                    "ok": False,
                    "error": "No se pudo subir a S3 (sin ACL).",
                    "detail": str(e2)
                }, status=500)
        else:
            return JsonResponse({
                "ok": False,
                "error": "No se pudo subir a S3.",
                "detail": str(e)
            }, status=500)

    public_url = "{}{}".format(base_url, key)

    return JsonResponse({
        "ok": True,
        "url": public_url,
        "key": key,
        "content_type": content_type,
        "original_name": original_name,
    })
