from core.models import PerfilUsuarioRestringido
from django.db import models
from django.http import Http404
from django.contrib.auth.models import User
from django.contrib.auth.models import Group as DjangoGroups 
from django.http import Http404
from django.contrib.postgres.fields import ArrayField
from jsonfield import JSONField 

OTSTYPE_CHOICES = ((1,'OT Póliza'), (2, 'OT Endoso'),(0,'OT Póliza/Endoso'))

class UserInfo(models.Model):
    user = models.OneToOneField(User, related_name = 'user_info')
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    is_vendedor = models.BooleanField(default=False)
    is_personal = models.BooleanField(default=False)
    is_delivery = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=500, null = True)
    perfil_restringido = models.ForeignKey(PerfilUsuarioRestringido, null = True, blank= True, related_name= 'perfile_restringido')
    subramos_dashboard = ArrayField(models.IntegerField(), null=True)
    tipopoliza_dashboard = ArrayField(models.IntegerField(), null=True)
    subramos_tablero = ArrayField(models.IntegerField(), null=True)
    aseguradoras_tablero = ArrayField(models.IntegerField(), null=True)
    subramos_cotizaciones = ArrayField(models.IntegerField(), null=True)
    type_ots = models.IntegerField(blank=True, null=True, default=0, choices = OTSTYPE_CHOICES)
    configDataCobranza = JSONField(null = True, blank =True, default = dict)
    configDataPolizas = JSONField(null = True, blank =True, default = dict)
    configDataRenovaciones = JSONField(null = True, blank =True, default = dict)

def _get_info(user):
    try:
        UserInfo.objects.get(user=user)
    except UserInfo.DoesNotExist:
        raise Http404


User.info = property(lambda u: _get_info(u))

class DjangoGroupInfo(models.Model):
    group = models.OneToOneField(DjangoGroups, related_name = 'group_info')
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(User, null=True, blank=True)


def _get_info_DjangoGroups(group):
    try:
        DjangoGroupInfo.objects.get(group=group)
    except DjangoGroupInfo.DoesNotExist:
        raise Http404


DjangoGroups.info = property(lambda u: _get_info_DjangoGroups(u))