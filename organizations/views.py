import organizations.signals.handlers
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.http import JsonResponse, HttpResponse
from .serializers import *
from organizations.models import UserInfo
from django.contrib.auth.models import User
from pprint import pprint
from beneficios import settings
import yaml
from paquetes.models import Package
from ramos.models import Ramos, SubRamos
from aseguradoras.models import Provider
from coberturas.models import Coverage, SumInsured, Deductible
from polizas.models import Pendients, Assign
from rest_framework.authtoken.models import Token
import requests
import json

from core.push_messages import send_push
from core.models import ModelsPermissions, PerfilUsuarioRestringido, UserPermissions
from core.models import Areas, AreasResponsability,Log
from django.core import serializers
from core.serializers import AreasSerializer, AreasResponsabilitySerializer,AreasResponsabilityInfoSerializer,AreasInfoSerializer
from django.shortcuts import get_object_or_404
from django.conf import settings

from control.permissions import IsAuthenticatedV2, IsOrgMemberV2, IsCasOrigin
from  control.permission_functions import show_mails


def get_org_info(req):
    org_ = requests.get(settings.CAS_URL + 'get-org-info/' + req.GET.get('org'),verify=False)
    response_org = org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    return org_info

def get_org_info_2(orgname):
    org_ = requests.get(settings.CAS_URL + 'get-org-info/' + orgname,verify=False)
    response_org = org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    return org_info


def get_org(org_id):
    try:
        org_id = int(org_id)         
        try:
            o =  Organization.objects.get(id=org_id)
            return o
        except Organization.DoesNotExist:
            return {'error':'organization does not exist'}

    except:
        try:
            o =  Organization.objects.get(urlname=org_id)
            return o
        except :
            try:
                aux =''
                index = str(org_id).find('orgs')
                if index >=0:
                    index = index + 4
                    for i in range(index,len(org_id)):
                        aux = aux+ org_id[i]
                else:
                    return {'error':'organization does not exist'}
                o =  Organization.objects.get(id=only_numerics(aux))
                return o
            except Organization.DoesNotExist:
                return {'error':'organization does not exist'}
                





    #     o =  Organization.objects.get(id=org_id)
    #     return o
    # except Organization.DoesNotExist:
    #     raise Organization.DoesNotExist



class UsersViewSet(viewsets.ModelViewSet):
    queryset = UserInfo.objects.all()
    serializer_class = UserInfoHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def get_queryset(self):
        return UserInfo.objects.all()


class UserInfoViewSet(viewsets.ModelViewSet):
    queryset = UserInfo.objects.all()
    serializer_class = UserInfoVendedorHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def get_queryset(self):
        return UserInfo.objects.all()



# class VendedorViewSet(viewsets.ModelViewSet):
#     serializer_class = VendedorHyperSerializer
#     permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

#     def get_queryset(self):
#         return Vendedor.objects.all()

#     def perform_create(self, serializer):
#         obj =serializer.save()

"""
class OrganizationsViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationsHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def get_queryset(self):
        return Organization.objects.all()
"""

@api_view(('POST',))
def app_datavalidate(request, format=None):
    try:
        created = False
        try:
            user = User.objects.get(
                username=request.data['user_username'],
            )

            if (request.data['user_email']!= user.email):
                user.email = request.data['user_email']
                user.save()

            if (request.data['user_password'] != user.password):
                user.password = request.data['user_password']
                user.save()

            if (request.data['user_first_name'] != user.first_name):
                user.first_name = request.data['user_first_name']
                user.save()

            if (request.data['user_last_name'] != user.last_name):
                user.last_name = request.data['user_last_name']
                user.save()

        except User.DoesNotExist:
            user = User(
                username=request.data['user_username'],
                email=request.data['user_email'],
                password=request.data['user_password'],
                first_name = request.data['user_first_name'],
                last_name = request.data['user_last_name']
            )
            user.save()
            created = True
            pendients = Pendients.objects.filter(email=request.data['user_email'])
            if pendients:
                for pendiente in pendients:
                    to_assign = Assign(
                        user = user,
                        poliza= pendiente.poliza,
                        is_owner = pendiente.is_owner,
                        active = pendiente.active
                        )
                    to_assign.save()
                    pendiente.delete()

        if created:
            uinfo = UserInfo(user=user)
            uinfo.save()

        token = ['']

        return Response({'token': str(token[0])})
    except Exception as e:
        print(e)

def readYaml(fileName):
    with open(fileName, 'r') as f:
        try:
            doc = yaml.load(f)
        except yaml.YAMLError as exc:
            pass
    return doc


@api_view(('POST',))
# @permission_classes((IsAuthenticated, IsOrgMemberV2))
def data_validate(request, format=None):
    created = False
    user_created = False
    try:
        created = False
        print('request.data***2***1***+',request.data)

        try:
            user = User.objects.get(
                username=request.data['user_username'],
            )

            if (request.data['user_email']!= user.email):
                user.email = request.data['user_email']
                user.save()

            if (request.data['user_first_name'] != user.first_name):
                user.first_name = request.data['user_first_name']
                user.save()

            if (request.data['user_last_name'] != user.last_name):
                user.last_name = request.data['user_last_name']
                user.save()

        except User.DoesNotExist:
            print('request.user doesnotexist***2***1***+',request.data)
            user = User(
                username=request.data['user_username'],
                email=request.data['user_email'],
                first_name = request.data['user_first_name'],
                last_name = request.data['user_last_name']
            )
            user_created = True
            user.save()

            # add permisos
            # permisos_data = readYaml('scripts/default_permissions.yaml')
            
            # for m in permisos_data:
            #     model, model_created =  ModelsPermissions.objects.get_or_create(
            #         user = user,
            #         model_name = m['model'] 
            #     )
            #     for p in m['permisos']:
            #         UserPermissions.objects.get_or_create(
            #             model = model,
            #             permission_name = p
            #         )

            # end permisos

            created = True
            pendients = Pendients.objects.filter(email=request.data['user_email'])
            if pendients:
                for pendiente in pendients:
                    to_assign = Assign(
                        user = user,
                        poliza= pendiente.poliza,
                        is_owner = pendiente.is_owner,
                        active = pendiente.active
                        )
                    to_assign.save()
                    pendiente.delete()

        uinfo, uinfo_created = UserInfo.objects.get_or_create(user=user, org_name=request.data['org_urlname']) 
        print('requ***2***1***+',request.data,uinfo,uinfo_created)

        areas = ['Clientes', 'Fianzas', 'Cobranzas', 'Siniestros', 'Endosos', 'Emisiones', 'Renovaciones']
        for area in areas:
            try:
                area = Areas.objects.get_or_create(area_name = area, org_name = request.data['org_urlname'], owner = user)
            except:
                pass
        if user_created:
            print('user created')
        else:
            print('user already exist')
       
        if uinfo_created:
            print('user info created')
        else:
            print('user info already exist')



        providers_ = Provider.objects.filter(org_name= request.data['org_urlname'])
        if not providers_.exists():
            print('No existen aseguradoras, agregando...')

            def provider_save(prov,org_name):
                provider = Provider(compania=prov['company_name'], rfc=prov['rfc'],alias=prov['alias'], org_name= org_name)
                provider.save()
                return provider


            def branch_save(branch, provider,org_name):
                b = Ramos(ramo_name=branch['branch_name'], ramo_code=branch['branch_code'], provider=provider, org_name= org_name)
                b.save()
                return b


            def sub_branch_save(sub_branch, branch,org_name):
                sub = SubRamos(subramo_name=sub_branch['subranch_name'], subramo_code=sub_branch['subbranch_code'], ramo=branch, org_name= org_name)
                sub.save()
                return sub


            def package_save(pack, provider, branch, sub,org_name):
                pack = Package(provider=provider, package_name=pack['package_name'],ramo=branch, subramo=sub,org_name= org_name)
                pack.save()
                return pack


            def coverage_save(cov, provider, package,org_name):
                cov = Coverage(coverage_name=cov['coverage_name'], provider=provider,package=package, default=cov['default'], org_name= org_name)
                cov.save()
                return cov


            def sum_insured_save(cov, sum_in,org_name):
                sums = SumInsured(sum_insured=sum_in, coverage_sum=cov, org_name= org_name).save()


            def deductible_save(cov, deductible,org_name):
                ded = Deductible(deductible=deductible, coverage_deductible=cov, org_name= org_name).save()

            # print('1')
            doc = readYaml('scripts/master.yaml')
            # print('2')
            arr = doc['org']
            # print('3')
            list = []
            for company in arr:
                # print('4')
                # Get all providers
                for provider_data in company['company']:
                    provider = provider_save(provider_data,request.data['org_urlname'])
                    # Get all branchs
                    for branch_data in provider_data['branch']:
                        # print('6')
                        branch = branch_save(branch_data, provider,request.data['org_urlname'])
                        for sub_branch in branch_data['subbranch']:
                            # print('7')
                            sub = sub_branch_save(sub_branch, branch,request.data['org_urlname'])
                            for pack in sub_branch['packages']:
                                # print('8')
                                package = package_save(pack, provider, branch, sub,request.data['org_urlname'])
                                for coverage in pack['coverages']:
                                    # print('9')
                                    cov = coverage_save(coverage, provider, package,request.data['org_urlname'])
                                    for sum_insured in coverage['sum_insured']:
                                        # print('11')
                                        sum_insured_save(cov, str(sum_insured),request.data['org_urlname'])
                                    for deductible in coverage['deductible']:
                                        # print('12')
                                        deductible_save(cov, str(deductible),request.data['org_urlname'])
        

        print('Aseguradoras insertadas correctamente')
        return Response(status = 200)
    except Exception as e:
        print('::::::::::::::',e)
        return Response({'error':str(e)})

@api_view(('POST',))
# @permission_classes((IsAuthenticated, IsOrgMemberV2))
def data_validate_area(request, format=None):
    # print(request.data)
    created = False
    org_created = False
    area_created = False
    arear = False
    status = 'OK'
    try:
        created = False
        s =request.data['org']
        us =User.objects.get(username = (request.data['owner']))
        
        if request.data['user']:
            use =User.objects.get(username = (request.data['user']))
        else:
            use = ''
        try:
            area = Areas.objects.get(
                area_name=request.data['area_name'],
                org=s
            )

            if ((request.data['area_name']!= area.area_name)):
                area.area_name = request.data['area_name']
                area.owner = us
                area.org_name= s,
                owner = us
                # area.save()

        except Areas.DoesNotExist:

            area = Areas(
                area_name=request.data['area_name'],
                owner=us,
                org=s ,
            )
            area_created = True
            # area.save()
            created = True

        if area_created:
            print('area created')
            serializeraa= AreasSerializer(area, context={'request':request}, many = True)
        else:
            print('area already exist')
            serializeraa= AreasSerializer(area, context={'request':request}, many = True)
    
        if use:
            try:
                areaexist = AreasResponsability.objects.get(area=area,user=use,org_name=s)
                serializeraR= AreasResponsabilitySerializer(areaexist, context={'request':request}, many = True)
                arear = True
            except Exception as e:
                print('____no_area responsability assigned___',e)
            if arear == False:
                try:           
                    arear_creada= AreasResponsability.objects.get_or_create(area=area,is_active=request.data['is_active'],org_name=s,user=use,owner=us)      
                    serializeraR= AreasSerializer(area, context={'request':request}, many = True)
                    print('________reponsability 1created_')  
                except Exception as e:
                    print('_____ area_responsability_error',e)

        return Response({'Áreas creadas':str(status)})

        # print(token[0])

    except Exception as e:
        return Response({'______error__areas__':str(e)})
@api_view(('POST',))
def update_area(request, format=None):
    # print(request.data)
    created = False
    org_created = False
    area_created = False
    arear = False
    try:
        created = False
        s =request.data['org']
        us =User.objects.get(username = (request.data['owner']))
        use =User.objects.get(username = (request.data['user']))
        try:
            area = Areas.objects.get(
                area_name=request.data['area_name'],
                org=s
            )
            if ((request.data['area_name']!= area.area_name)):
                area.area_name = request.data['area_name']
                area.owner = us
                area.org_name = s,
                owner = us
                area.save()

        except Areas.DoesNotExist:
            area = Areas(
                area_name=request.data['area_name'],
                owner=us,
                org_name=s ,
            )
            area_created = True
            area.save()
            created = True

        try:
            if request.data['is_active'] == 'True':
                request.data['is_active'] = True
            elif request.data['is_active'] == 'False':
                request.data['is_active'] = False
            elif request.data['is_active'] == True:
                request.data['is_active'] = True
            elif request.data['is_active'] == False:
                request.data['is_active'] = False
            areaexist = AreasResponsability.objects.get(area=area,user=use,org_name=s)
            serializeraR= AreasResponsabilityInfoSerializer(areaexist, context={'request':request}, many = True)
            areaexist.is_active = request.data['is_active']
            areaexist.save()
            arear = True
        except Exception as e:
            print('____no er__',e)
        if arear == False:
            try:           
                arear_creada= AreasResponsability.objects.get_or_create(area=area,is_active=request.data['is_active'],org_name=s,user=use,owner=us)      
                serializerarea= AreasInfoSerializer(area, context={'request':request}, many = True)
            except Exception as e:
                print('_____ responsability error',e)

        return Response({'areas_responsabilidad': arear})

        # print(token[0])

    except Exception as e:
        return Response({'___error__updarea__':str(e)})


def only_numerics(seq):
    seq_type= type(seq)
    return seq_type().join(filter(seq_type.isdigit, seq))

'''
Get all data in API view
'''
def local_env(meta):
    return True if not 'org' in meta['QUERY_STRING'] else False


def get_default_org():
    return settings.APIVIEW_ORG_ID


def get_org_by_env(request):
    return request.META['QUERY_STRING'].split('=')[1]


from rest_framework.exceptions import PermissionDenied

class OrgInfoViewSet(viewsets.ModelViewSet):
    serializer_class = OrgInfoSerializer
    permission_classes = (IsAuthenticatedV2,IsOrgMemberV2)
    def perform_create(self, serializer):
        user =  self.request.META['user']
        org_name = user['org']['name']
        OrgInfo.objects.filter(org_name=org_name).delete()
        obj = serializer.save(org_name=org_name)
        return obj

    def partial_update(self, request, pk=None):
        if show_mails(request):
            queryset = OrgInfo.objects.all()
            cf = get_object_or_404(queryset, pk=pk)
            changes = {}
            if 'editconfiguracion' in request.data and request.data['editconfiguracion']:
                atributesthatcanbechanged = request.data
                atributesthatcanbechanged.pop('id', None)  
                atributesthatcanbechanged.pop('updated_at', None)
                atributesthatcanbechanged.pop('url', None)
                for key, value in atributesthatcanbechanged.items():
                    if hasattr(cf, key) and getattr(cf, key) != value:
                        changes[key] = ' de ' + str('Activo' if getattr(cf, key) else 'Inactivo') + str(' a Activo' if value else ' a Inactivo/')

                cambio_nombre_atributos = [
                    ('apply_nota', 'Al aplicar nota de crédito'),
                    ('cancelacion_siniestro', 'Cancelación siniestro'),
                    ('cerrar_recibos', 'Cerrar recibos al cerrar Edo. cuenta'),
                    ('cobranza_pago', 'Al pagar un recibo'),
                    ('create_nota', 'Creación de nota de crédito'),
                    ('solicitud_pol', 'Solicitud OT'),
                    ('registro_pol', 'Regsitro/Emisión OT'),
                    ('renovacion', 'Renovación Póliza'),
                    ('solicitud_siniestro', 'Solicitud siniestro'),
                    ('tramite_siniestro', 'Trámite siniestro'),
                    ('cancelacion_siniestro', 'Cancelación siniestro'),
                    ('rechazo_siniestro', 'Rechazo siniestro'),
                    ('espera_siniestro', 'Espera siniestro'),
                    ('fin_siniestro', 'Fin siniestro'),
                    ('recordatorio_cob', 'Recordatorio Cobranza'),
                    ('recordatorio_ren', 'Recordatorio Renovación'),
                    ('recordatorio_cum', 'Recordatorio Cumpleaños'),
                    ('filtros_agrupacion', 'Filtro Nivel de Agrupación'),
                    ('filtros_celula', 'Filtro Célula'),
                    ('filtros_lineanegocio', 'Filtro Línea Negocio'),
                ]
                changes_str=''
                if changes:
                    updated_changes = {}
                    for key, value in cambio_nombre_atributos:
                        if key in changes:
                            updated_changes[value] = changes.pop(key)
                    updated_changes.update(changes)
                    changes_str = ', '.join(["{}: {}".format(key, value) for key, value in updated_changes.items()])
                dataIdent = ' actualizo la configuración ' +str(cf.id if cf and cf.id else '')                 
                try:
                    send_log(request.user, request.GET.get('org'), 'PATCH', 34, changes_str if changes_str else dataIdent, cf.id)
                except Exception as eee:
                    pass
            serializer = OrgInfoSerializer(cf, context={'request': request}, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            raise PermissionDenied('No tienes acceso a esta función') 

    def get_queryset(self):
        user =  self.request.META['user']
        org_name = user['org']['name']
        orginfo = OrgInfo.objects.filter(org_name= org_name)
        return orginfo

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


@api_view(('POST',))
@permission_classes((IsCasOrigin,))
def add_orginfo(request, format=None):
    try:
        org = request.data['org']
        if org:            
            def provider_save(prov,org):
                provider = Provider(compania=prov['company_name'], rfc=prov['rfc'], description=prov['description'],alias=prov['alias'], org_name=org)
                provider.save()
                return provider


            def branch_save(branch, provider,org):
                b = Ramos(ramo_name=branch['branch_name'], ramo_code=branch['branch_code'], provider=provider, org_name=org)
                b.save()
                return b


            def sub_branch_save(sub_branch, branch,org):
                sub = SubRamos(subramo_name=sub_branch['subranch_name'], subramo_code=sub_branch['subbranch_code'], ramo=branch, org_name=org)
                sub.save()
                return sub


            def package_save(pack, provider, branch, sub,org):
                pack = Package(provider=provider, package_name=pack['package_name'], description=pack['description'],ramo=branch, subramo=sub, org_name=org)
                pack.save()
                return pack


            def coverage_save(cov, provider, package,org):
                cov = Coverage(coverage_name=cov['coverage_name'], provider=provider,package=package, default=cov['default'], org_name=org)
                cov.save()
                return cov


            def sum_insured_save(cov, sum_in,org):
                sums = SumInsured(sum_insured=sum_in, coverage_sum=cov, org_name=org).save()


            def deductible_save(cov, deductible,org):
                ded = Deductible(deductible=deductible, coverage_deductible=cov, org_name=org).save()

            # print('1')
            doc = readYaml('scripts/master.yaml')
            # print('2')
            arr = doc['org']
            # print('3')
            list = []
            for company in arr:
                # print('4')
                # Get all providers
                for provider_data in company['company']:
                    provider = provider_save(provider_data,org)
                    # Get all branchs
                    for branch_data in provider_data['branch']:
                        # print('6')
                        branch = branch_save(branch_data, provider,org)
                        for sub_branch in branch_data['subbranch']:
                            # print('7')
                            sub = sub_branch_save(sub_branch, branch,org)
                            for pack in sub_branch['packages']:
                                # print('8')
                                package = package_save(pack, provider, branch, sub,org)
                                for coverage in pack['coverages']:
                                    # print('9')
                                    cov = coverage_save(coverage, provider, package,org)
                                    for sum_insured in coverage['sum_insured']:
                                        # print('11')
                                        sum_insured_save(cov, str(sum_insured),org)
                                    for deductible in coverage['deductible']:
                                        # print('12')
                                        deductible_save(cov, str(deductible),org)
        

        return Response({'message': 'info added to org' }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error':str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(('POST',))
@permission_classes((IsCasOrigin, ))
def add_userinfo(request, format=None):
    user_created = False
    try:
        created = False
        org =  request.data['org']
        try:
            try:
                saamexist = request.data['saam_exists']
                saampair = request.data['saam_pair']
            except Exception as eroroexists:
                saamexist = False
                saampair = []
                print('error saam exists from cas**',eroroexists)
            first=request.data['first_name']
            last=request.data['last_name']
            usersaam=UserInfo.objects.filter(
                user__first_name__iexact=first,
                user__last_name__iexact=last,
                org_name=org
            ).values_list('id','user__id')
            saampair = UserInfo.objects.filter(
                user__first_name__iexact=first,
                user__last_name__iexact=last,
                org_name=org
            ).values_list('id', 'user__id').first()   # 👈 first()

            saamexist = bool(saampair)
            if usersaam:
                saamexist=True
                saampair=usersaam[0]
            if saamexist and saampair:
                user = User.objects.get(
                    id=saampair[1],
                )
                if user:
                    user.username=request.data['username']
                    user.save()
                    print('actualizo el username*******',user,request.data['username'])
                print('userid****+',user,user.first_name,user.last_name,user.username)
            else:
                user = User.objects.get(
                    username=request.data['username'],
                )
                print('ux*****+',user,user.first_name,user.last_name,user.username)

            new_email = request.data.get('user_email') or request.data.get('email')
            if new_email and new_email != user.email:
                user.email = new_email

            new_first = request.data.get('user_first_name') or request.data.get('first_name')
            if new_first and new_first != user.first_name:
                user.first_name = new_first

            new_last = request.data.get('user_last_name') or request.data.get('last_name')
            if new_last and new_last != user.last_name:
                user.last_name = new_last

            user.save()

        except User.DoesNotExist:
            try:
                saamexist = request.data['saam_exists']
                saampair = request.data['saam_pair']
            except Exception as eroroexists:
                saamexist = False
                saampair = []
                print('error saam exists from cas**',eroroexists)
            if saamexist and saampair:
                user = User.objects.get(
                    id=saampair[1],
                )
            else:
                user = User(
                    username=request.data['username'],
                    email=request.data['email'],
                    first_name = request.data['first_name'],
                    last_name = request.data['last_name']
                )
                user_created = True
                user.save()

            created = True
            pendients = Pendients.objects.filter(email=request.data['email'])
            if pendients:
                for pendiente in pendients:
                    to_assign = Assign(
                        user = user,
                        poliza= pendiente.poliza,
                        is_owner = pendiente.is_owner,
                        active = pendiente.active
                        )
                    to_assign.save()
                    pendiente.delete()


        uinfo, uinfo_created = UserInfo.objects.get_or_create(user=user, org_name=org) 
        if 'perfilRestringido' in request.data and request.data['perfilRestringido'] != '' and ((request.data['perfilRestringido']) != 0 or (request.data['perfilRestringido']) != "0") and request.data['perfilRestringido'] != None:
            try:
                if int(request.data['perfilRestringido']) != 0:
                    uinfo.perfil_restringido = PerfilUsuarioRestringido.objects.get(id = request.data['perfilRestringido'])
                    uinfo.save()
            except Exception as error:
                uinfo.perfil_restringido = None
        
        if (request.data['perfilRestringido']) == 0 or (request.data['perfilRestringido']) == "0" or (request.data['perfilRestringido']) == None:
            try:
                if int(request.data['perfilRestringido']) == 0:
                    uinfo.perfil_restringido = None
            except Exception as ers:
                uinfo.perfil_restringido = None
            uinfo.perfil_restringido = None
            uinfo.save()

        areas = ['Clientes', 'Fianzas', 'Cobranzas', 'Siniestros', 'Endosos', 'Emisiones', 'Renovaciones']
        for area in areas:
            area = Areas.objects.get_or_create(area_name = area, org_name = org, owner = user)

        if user_created:
            print('user created')
        else:
            print('user already exist')
        if uinfo_created:
            print('user info created')
        else:
            print('user info already exist')


        return Response({'message': 'info added to org' }, status=status.HTTP_200_OK)
    except Exception as e:
        print('::::::::::::::',e)
        return Response({'error':str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
# ====================================
@api_view(['POST','GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def saveConfigTableFieldsReports(request):
    org_name = request.GET.get('org')
    user = request.user
    ui = UserInfo.objects.filter(user = user)
    if ui.exists():
        ui = ui.first()
    else:
        ui = None
    if request.method == 'POST':
        tipo_lista = request.data['tipo']
        if tipo_lista:
            tipo_lista=int(tipo_lista)
        if ui:
            if tipo_lista==1:
                ui.configDataCobranza = request.data['configDataCobranza']
                ui.save()
            elif tipo_lista ==2:
                ui.configDataPolizas = request.data['configDataPolizas']
                ui.save()
            elif tipo_lista ==3:
                ui.configDataRenovaciones = request.data['configDataRenovaciones']
                ui.save()
            else:
                return JsonResponse({'error': 'Invalid tipo_lista'}, status=400)
            data = UserInfoHyperSerializer(ui,context = {'request': request}, many = False)
            return JsonResponse({'status':data.data}, status = 200)
        else:
            return JsonResponse({'error':'not found'}, status = 404)
    if request.method == 'GET':
        tipo_lista = request.GET.get('tipo')
        if tipo_lista:
            tipo_lista=int(tipo_lista)
        if ui:
            if tipo_lista ==1:
                return JsonResponse({'data':ui.configDataCobranza if ui.configDataCobranza else ''}, status = 200)
            elif tipo_lista==2:
                return JsonResponse({'data':ui.configDataPolizas if ui.configDataPolizas else ''}, status = 200)
            elif tipo_lista==3:
                return JsonResponse({'data':ui.configDataRenovaciones if ui.configDataRenovaciones else ''}, status = 200)
        else:
            return JsonResponse({'error':'not found'}, status = 404)
         
    

# ====================================