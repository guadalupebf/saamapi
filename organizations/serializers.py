from django.contrib.auth.models import User
from rest_framework import serializers
from organizations.models import UserInfo
from aseguradoras.models import Provider
from ramos.models import Ramos,SubRamos
from vendedores.models import Phone, SubramosVendedor, Vendedor
from recibos.models import Bancos
from vendedores.serializers import VendedorHyperSerializer
from core.models import OrgInfo
import requests
from django.conf import settings
import json

class UserInfoHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserInfo
        exclude = ()


class ReferenciadoresCasSerializer(serializers.HyperlinkedModelSerializer):
    item_text = serializers.SerializerMethodField()
    item_id = serializers.SerializerMethodField()

    def get_item_text(self, obj):
        return "%s %s"%(obj.user.first_name, obj.user.last_name)

    def get_item_id(self, obj):
        return obj.user.id

    class Meta:
        model = UserInfo
        fields = ('item_id', 'item_text')

class SystemUserHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        exclude = ()


class UserInfoVendedorHyperSerializer(serializers.HyperlinkedModelSerializer):
    info_vendedor = VendedorHyperSerializer(many = True,read_only = True)
    class Meta:
        model = UserInfo
        fields = ('is_vendedor','url', 'info_vendedor','user', 'is_active','org_name')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    user_info = UserInfoVendedorHyperSerializer(many = False, read_only = True)
    class Meta:
        model = User
        fields = ('username' , "first_name", "last_name", "email",'url', 'user_info', 'id','is_active')



class UserInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name",'id')



class UserInfoVendedoresSerializer(serializers.HyperlinkedModelSerializer):
    user_info = UserInfoVendedorHyperSerializer(many = False, read_only = True)
    class Meta:
        model = User
        fields = ('username' , "first_name", "last_name", "id",'url','user_info')

class OrgInfoSerializer(serializers.HyperlinkedModelSerializer):
    correoorg = serializers.SerializerMethodField(read_only=True)
    def get_correoorg(self, obj):
        request = self.context.get('request')
        if request:
            return getOrg(request)
        return None

    class Meta:
        model = OrgInfo
        fields = ('solicitud_pol', 'solicitud_endoso', 'registro_pol', 'registro_endoso', 'solicitud_siniestro', 
                'fin_siniestro', 'recordatorio_cob', 'recordatorio_cum', 'cobranza_pago', 'create_nota', 'apply_nota', 'id', 'url',
                'updated_at', 'recordatorio_ren', 'renovacion','tramite_siniestro','rechazo_siniestro',
                'cancelacion_siniestro','espera_siniestro','cerrar_recibos','recordatorio_sms','contacto_dudas','fecha_limite_email',
                'filtros_agrupacion','filtros_celula','filtros_lineanegocio','fecha_limite_email_cobranza','correoorg','boton_segumovil','moduleName',
                'dato_contratante','dato_numero_poliza','dato_concepto','dato_aseguradora','dato_subramo','dato_serie','dato_total',                
                'dato_pvigencia','dato_paseguradora','dato_psubramo','dato_pmoneda','dato_pfrecuenciapago','dato_pasegurado','dato_ptotal','dato_ptotalrecibo'
                ,'activar_contacto_dudas','copia_user_envio','dato_cnumcertificado','dato_cvigencia','dato_caseguradora','dato_csubramo','dato_cmoneda','dato_cfrecuenciapago','dato_casegurado',
                'dato_cptotal','dato_cpneta','dato_cderecho','dato_crpf','dato_civ','dato_ccontratante')
        
def getOrg(request):
    org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
    response_org = org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    if org_info:
        return org_info['email']
    return ''