from rest_framework import serializers
from core.models import *
from organizations.models import *
from vendedores.models import *
from contratantes.models import Contractor, Group
from recibos.models import Recibos,Bancos
from polizas.models import Polizas
from core.models import Areas,AreasResponsability
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from datetime import date
import arrow
from datetime import datetime


class SharedHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Shared
        fields = ('url', 'id', 'grupo', 'usuario', 'poliza', 'fianza', 'aseguradora', 
            'grupo_de_contratantes', 'contratante_fisico', 'contratante_moral', 
            'descripcion')
