from rest_framework import permissions
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from organizations.models import UserInfo
from .models import ModelsPermissions, UserPermissions
from .utils import decode_token
from rest_framework.parsers import JSONParser,ParseError
import requests
from django.conf import settings
from control.permissions import IsOrgMemberV2

# Permisos nuevos
class IsOrgMember(permissions.BasePermission):
    def has_permission(self, request, view):
        org_request = request.GET.get('org')
        org_usuario = UserInfo.objects.get(user = request.user).org.urlname
        if org_usuario != org_request:
            return False
        else:
            return True        


@api_view(['GET','POST','PUT','PATCH','DELETE','OPTIONS'])
@permission_classes((IsAuthenticated, IsOrgMemberV2))
def is_org_member(request):
    org_request = request.GET.get('org')
    org_usuario = UserInfo.objects.get(user = request.user).org.urlname
    if org_usuario != org_request:
        return Response(False)
    else:
        return Response(True)



class AgendaPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'PATCH' or request.method == 'PUT' or request.method == 'POST' or request.method == 'DELETE' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            agenda_permiso = permiso.get(permission_name = 'Agenda')
            if agenda_permiso.checked:
                return True    
            return False
        return False


class CampaniasPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'PATCH' or request.method == 'PUT' or request.method == 'POST' or request.method == 'DELETE' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            agenda_permiso = permiso.get(permission_name = 'Campañas')
            if agenda_permiso.checked:
                return True    
            return False
        return False


class EmailInfoPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'PATCH' or request.method == 'PUT' or request.method == 'POST' or request.method == 'DELETE' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            agenda_permiso = permiso.get(permission_name = 'Correos')
            if agenda_permiso.checked:
                return True    
            return False
        return False



class MensajeriaPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'PATCH' or request.method == 'PUT' or request.method == 'POST' or request.method == 'DELETE' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            agenda_permiso = permiso.get(permission_name = 'Mensajeria')
            if agenda_permiso.checked:
                return True    
            return False
        return False



class FormatosPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'PATCH' or request.method == 'PUT' or request.method == 'POST' or request.method == 'DELETE' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            agenda_permiso = permiso.get(permission_name = 'Formatos')
            if agenda_permiso.checked:
                return True    
            return False
        return False


class VerContratantesGruposPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'PATCH' or request.method == 'PUT' or request.method == 'POST' or request.method == 'DELETE' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_groups = permiso.get(permission_name = 'Ver contratantes y grupos')
            admin_groups = permiso.get(permission_name = 'Administrar contratantes y grupos')
            if view_groups.checked or admin_groups.checked:
                return True    
            return False
        return False


class PolizasChartPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Gráfica OTs')
            if view_chart.checked:
                return True    
            return False
        return False     


class CobranzaChartPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Gráfica cobranza')
            if view_chart.checked:
                return True    
            return False
        return False 


class RenovacionesChartPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Gráfica renovaciones')
            if view_chart.checked:
                return True    
            return False
        return False 


class SiniestrosChartPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Gráfica siniestros')
            if view_chart.checked:
                return True    
            return False
        return False 


class FianzasReportesPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Reporte fianzas')
            if view_chart.checked:
                return True    
            return False
        return False  


class EndososReportesPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Reporte Endosos')
            if view_chart.checked:
                return True    
            return False
        return False    



class SiniestrosReportesPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Reporte Siniestros')
            if view_chart.checked:
                return True    
            return False
        return False  



class CobranzaReportesPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Reporte cobranza')
            if view_chart.checked:
                return True    
            return False
        return False   


class PolizasReportesPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Reporte pólizas')
            if view_chart.checked:
                return True    
            return False
        return False        


class RenovacionesReportesPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Reporte renovaciones')
            if view_chart.checked:
                return True    
            return False
        return False  



class FianzasPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Ver fianzas')
            if view_chart.checked:
                return True    
            return False
        return False


class FianzasDeletePermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'DELETE':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Eliminar fianzas')
            if view_chart.checked:
                return True    
            return False
        if request.method == 'PATCH' or request.method == 'POST' or request.method == 'PUT':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Administrar fianzas')
            if view_chart.checked:
                return True    
            return False
        return False


class FianzasAnularPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Cancelar fianzas')
            if view_chart.checked:
                return True    
            return False
        return False



class AdminReferenciadoresPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'PATCH' or request.method == 'POST' or request.method == 'PUT':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Administrar referenciadores')
            if view_chart.checked:
                return True    
            return False
        return False



class AccountStatePermission(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'OPTIONS' or request.method == 'PATCH' or request.method == 'POST' or request.method == 'PUT' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Pagar a referenciadores')
            if view_chart.checked:
                return True    
            return False
        return False



class PolizasPermission(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Ver pólizas')
            if view_chart.checked:
                return True    
            return False
        return True



class OTSPermission(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Ver OTs')
            if view_chart.checked:
                return True    
            return False
        return True



class CobranzaPermission(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST' or request.method == 'GET' or request.method == 'OPTIONS':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Ver cobranza')
            if view_chart.checked:
                return True    
            return False
        return True



class KBIPermission(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = "KBI's")
            if view_chart.checked:
                return True    
            return False
        return True



class ComisionesPermission(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'POST' or request.method == 'GET' or request.method == 'DELETE' or request.method == 'PATCH' or request.method == 'PUT':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            view_chart = permiso.get(permission_name = 'Comisiones')
            if view_chart.checked:
                return True    
            return False
        return True

class ArchivosPermissions(permissions.BasePermission):
    message = 'No tienes acceso a esta función'
    def has_permission(self, request, view):
        if request.method == 'PATCH' or request.method == 'PUT' or request.method == 'POST' or request.method == 'DELETE' or request.method == 'GET':
            model = ModelsPermissions.objects.filter(user = request.user).values_list('pk', flat = True)
            permiso = UserPermissions.objects.filter(model__in = list(model))
            # view_files_sensibles = permiso.get(permission_name = 'Ver archivos sensibles')
            admin_files_sensibles = permiso.get(permission_name = 'Administrar archivos sensibles')
            if admin_files_sensibles.checked:
                return True    
            return False
        return False






