import json
from coberturas.serializers import *
from polizas.models import Polizas, OldPolicies, Assign, Pendients, Cotizacion, AseguradorasInvolved
from core.serializers import AddressSerializer,SucursalFullSerializer, RefInvolvedHyperSerializer, ReferenciadoresInvolvedHyperSerializer,RefInvolvedInfoSerializer,FullInfoTicketHyperSerializer,RefInvolvedFianzaSerializer
from core.models import Address, ReferenciadoresInvolved, PromotoriaTablero, Ticket
from rest_framework import serializers
from forms.serializers import *
from forms.models import *
from claves.serializers import ClavesByProviderHyperSerializer
from archivos.serializers import PolizasFileSerializer, CreatePolizasFileSerializer
from archivos.models import PolizasFile
from recibos.models import Recibos
from aseguradoras.models import Provider
from paquetes.serializers import *
# from recibos.serializers import ReciboHyperSerializer
from organizations.views import get_org
from coberturas.models import CoverageInPolicy
from endosos.models import Endorsement, EndorsementCert
from contratantes.serializers import *
from ramos.serializers import *
from decimal import Decimal
from datetime import datetime, date, timedelta
import arrow
from siniestros.models import Siniestros
from .models import AseguradorasCotizacionPrimas, Pendients, CondicionGeneral, PolizaCondicionGeneral
from organizations.serializers import SystemUserHyperSerializer
import os
from django.conf import settings
from django.db.models import Q
from operator import __or__ as OR
from functools import reduce
from django.core.exceptions import ObjectDoesNotExist
from fianzas.models import *
from django.db import transaction
from rest_framework import status
# CAS 2.0
from control.cas_functions import  get_user_info
from recordatorios.models import RegistroDeRecordatorio
from recordatorios.serializers import RegistroDeRecordatorioSerializer

class PolizasCasSerializer(serializers.HyperlinkedModelSerializer):
    item_id = serializers.SerializerMethodField()
    item_text = serializers.SerializerMethodField()

    def get_item_text(self, obj):
        return obj.poliza_number
    
    def get_item_id(self, obj):
        return obj.id
    
    class Meta:
        model = Polizas
        fields = ('item_id', 'item_text') 

class ContractHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Contract
        fields = ('id', 'url', 'owner', 'start', 'end', 'number', 'contract_object', 'amount', 'amount_iva', 'guarantee_percentage', 'guarantee_amount', 'rate' , 'sign_date', 'activity', 'business_activity', 'employee_name','no_employees','description','number_inclusion','poliza')
class BeneficiarieHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = BeneficiariesContract
        fields = ('id', 'url', 'first_name', 'j_name', 'last_name', 'second_last_name', 
            'full_name', 'rfc', 'email', 'phone_number', 'owner','type_person','workstation','poliza','poliza_many')

class MinProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ('id','alias','website','url')

class PolizaMoreEditSerializer(serializers.HyperlinkedModelSerializer):
    contractor = serializers.SlugRelatedField(slug_field = 'full_name', many=False,read_only=True)
    owner = serializers.SerializerMethodField()
    subramo = serializers.SlugRelatedField(slug_field = 'subramo_name', many = False, read_only = True)
    aseguradora = serializers.SlugRelatedField(slug_field = 'alias', many = False, read_only = True)
    #renewed_status = serializers.SerializerMethodField()
    
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

#    def get_renewed_status(self, obj):
#        return obj.get_renewed_status()

    class Meta:
        model = Polizas
        fields = ('url', 'id','administration_type', 'internal_number', 'folio', 'owner','sucursal', 'org_name', 'status', 'created_at', 'subramo', 'aseguradora',
                  'poliza_number', 'start_of_validity', 'end_of_validity','certificate_number','document_type','renewed_status','exchange_rate',
                  'rec_antiguedad','collection_executive','receipts_by','certificado_inciso_activo', 'scheme', 'accident_rate', 'steps','emision_date','business_line',
                  'caratula','tabulator','contractor','fecha_pago_comision','maquila','date_emision_factura','month_factura','folio_factura','date_maquila',
                  'year_factura','date_bono','comision_derecho_percent','comision_rpf_percent')

class HistoricoPolicySerializer(serializers.HyperlinkedModelSerializer):
    base_policy = PolizaMoreEditSerializer(many=False, read_only=True)
    new_policy = PolizaMoreEditSerializer(many=False, read_only=True)
    owner = serializers.SerializerMethodField()
    policy = serializers.SerializerMethodField()
    
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    def get_policy(self,obj):
        return obj.__str__()

    class Meta:
        model = OldPolicies
        fields = ('url', 'id', 'base_policy', 'policy', 'new_policy', 'created_at', 'owner')
        
class OldPolicyHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OldPolicies
        exclude = ()

class ReporteRenovacionesSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    antiguedad = serializers.SerializerMethodField()
    existe_ot_renovacion = serializers.SerializerMethodField()
    def get_existe_ot_renovacion(self, obj):
        val = False
        if OldPolicies.objects.filter(base_policy__id = obj.id, new_policy__status = 1).exists() and obj.is_renewable ==1:
            val = True
        return val

    def get_antiguedad(self, instance):
        if not instance.end_of_validity:
            return 0
        else:
            a = instance.end_of_validity
            end_date = a.strftime('%d-%m-%Y %H:%M:%S')
            end_date = datetime.strptime(end_date, '%d-%m-%Y %H:%M:%S')
            today = datetime.now()

            try:
                if end_date > today:
                    response = int((end_date - today).days)
                    response = -abs(response)
                    return response
                elif today > end_date:
                    response = int((end_date - today).days)
                    response = abs(response)
                    return response
                else:
                    return 0 
            except Exception as e:
                print('exception 142',e)
                return 0

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner',  'org_name',
                  'poliza_number','aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'old_policies',
                  'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 'recibos_poliza',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'document_type', 'address', 'coverageInPolicy_policy',
                  'created_at', 'updated_at', 'clave','f_currency', 'identifier',
                  'p_total','derecho','rpf','p_neta', 'iva', 'comision', 'existe_ot_renovacion',
                  'comision_percent', 'parent', 'sucursal','collection_executive','hospital_level',
                  'emision_date','contratante_subgroup','contractor', 'antiguedad','renewed_status','is_renewable','comision_derecho_percent','comision_rpf_percent')

class RepRenovacionesSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    old_policies = OldPolicyHyperSerializer(many=True, read_only=True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    responsable = VendorSerializer(read_only = True)
    conducto_de_pago = serializers.SerializerMethodField()
    def get_conducto_de_pago(self, obj):
        return obj.get_conducto_de_pago_display()

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner',  'org_name',
                  'poliza_number', 'renewed_status',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'old_policies',
                  'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 'recibos_poliza',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'document_type', 'address', 'coverageInPolicy_policy','sucursal',
                  'created_at', 'updated_at', 'clave','f_currency', 'identifier',
                  'p_total','derecho','rpf','p_neta', 'iva', 'comision',
                  'comision_percent', 'parent', 'collection_executive',
                  'ref_policy','responsable','emision_date','contratante_subgroup','contractor','fecha_pago_comision','maquila',
                  'date_emision_factura','month_factura','folio_factura','exchange_rate','date_maquila',
                  'year_factura','date_bono','conducto_de_pago','comision_derecho_percent','comision_rpf_percent')

class ReporteEnProcesoRenovacionesSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    old_policies = OldPolicyHyperSerializer(many=True, read_only=True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    responsable = VendorSerializer(read_only = True)
    conducto_de_pago = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    document_type = serializers.SerializerMethodField()
    def get_conducto_de_pago(self, obj):
        return obj.get_conducto_de_pago_display()
    def get_status(self, obj):
        return obj.get_status_display()
    def get_document_type(self, obj):
        return obj.get_document_type_display()

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner',  'org_name',
                  'poliza_number', 'renewed_status',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'old_policies',
                  'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 'recibos_poliza',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'document_type', 'address', 'coverageInPolicy_policy','sucursal',
                  'created_at', 'updated_at', 'clave','f_currency', 'identifier',
                  'p_total','derecho','rpf','p_neta', 'iva', 'comision',
                  'comision_percent', 'parent', 'collection_executive',
                  'ref_policy','responsable','emision_date','contratante_subgroup','contractor','fecha_pago_comision','maquila',
                  'date_emision_factura','month_factura','folio_factura','exchange_rate','date_maquila',
                  'year_factura','date_bono','conducto_de_pago','comision_derecho_percent','comision_rpf_percent')
class ExcelReporteRenovacionesSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    paquete = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner',  'org_name',
                  'poliza_number',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'old_policies',
                  'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 'recibos_poliza', 'life_policy',
                  'document_type', 'address', 'coverageInPolicy_policy','f_currency','p_neta',
                  'p_total','derecho','rpf', 'iva', 'comision', 'created_at','updated_at','clave','sucursal',
                  'contratante_subgroup','contractor','comision_derecho_percent','comision_rpf_percent'
                  )

    def to_representation(self, instance):
        DICT_REN = [ (0,''),(1,'NO.PÓLIZA'), (2, 'TIPO'), (3, 'CONTRATANTE'), (4,'ASEGURADORA'),
                     (5, 'RAMO'), (6,'SUBRAMO'), (7, 'PAQUETE'), (8,'FRECUENCIA PAGO'),(9,'ESTATUS PÓLIZA'),
                     (10,'INICIO VIGENCIA'),(11,'FECHA CRECIÓN'),(12,'FOLIO'),(13,'MONEDA'),(14,'PRIMA NETA'),(15,'RPF'),
                     (16,'DERECHO'),(17,'IVA'),(18,'PRIMA TOTAL'),(19,'COMISIÓN'),(20,'OBSERVACIONES'),(21,'CLAVE AGENTE'), (22,'FIN VIGENCIA') ]
        data = super(ExcelReporteRenovacionesSerializer, self).to_representation(instance)
        array = self.context['request'].data['orden']
        instance.p_total= '{:,.2f}'.format(instance.p_total);
        instance.p_neta= '{:,.2f}'.format(instance.p_neta);
        instance.derecho= '{:,.2f}'.format(instance.derecho);
        instance.iva= '{:,.2f}'.format(instance.iva);
        instance.rpf= '{:,.2f}'.format(instance.rpf);
        instance.comision= '{:,.2f}'.format(instance.comision);
        if instance.contractor:       
           contratante = str(instance.contractor)
        else:
            contratante = ""

        if instance.status == 1:
            instance.status = "OT Pendiente"
        elif instance.status == 2:
            instance.status = "OT Cancelada"
        elif instance.status == 4:
            instance.status = "Precancelada"
        elif instance.status == 10:
            instance.status = "Por iniciar"
        elif instance.status == 11:
            instance.status = "Cancelada"
        elif instance.status == 12:
            instance.status = "Cerrada"
        elif instance.status == 13:
            if instance.renewed_status == 2:
                instance.status = "Vencida - En proceso de renovación"
            else:
                instance.status = "Vencida"
        elif instance.status == 14:
            instance.status = "Vigente"

        if instance.forma_de_pago == 12:
            instance.forma_de_pago = "Anual"
        elif instance.forma_de_pago == 1:
            instance.forma_de_pago = "Mensual"
        elif instance.forma_de_pago == 2:
            instance.forma_de_pago = "Bimestral"
        elif instance.forma_de_pago == 3:
            instance.forma_de_pago = "Trimestral"
        elif instance.forma_de_pago == 4:
            instance.forma_de_pago = "Cuatrimestral"
        elif instance.forma_de_pago == 5:
            instance.forma_de_pago = "Contado"
        elif instance.forma_de_pago == 6:
            instance.forma_de_pago = "Semestral"

        if instance.f_currency == 1:
            instance.f_currency = "PESOS"
        elif instance.f_currency == 2:
            instance.f_currency = "DOLARES"

        if instance.document_type == 1:       
           instance.document_type = "Póliza"
        elif instance.document_type == 2:
            instance.document_type= "Endoso"
        elif instance.document_type == 3:
            instance.document_type= "Caratula"  

        a = instance.poliza_number
        b = instance.document_type
        c = contratante
        d = str(instance.aseguradora.alias)
        e = str(instance.ramo)
        f = str(instance.subramo)
        g = str(instance.paquete)
        h = instance.forma_de_pago
        i = instance.status
        j = (instance.start_of_validity.strftime("%d/%m/%y"))
        k = instance.created_at.strftime("%d/%m/%y")
        l = instance.folio
        m = instance.f_currency
        n = instance.p_neta
        o = instance.rpf
        p = instance.derecho
        q = instance.iva
        r = instance.p_total
        s = instance.comision 
        t = instance.observations 
        u = str(instance.clave.clave) + '-' + str(instance.clave.name)
        v = (instance.end_of_validity.strftime("%d/%m/%y"))

        DICT_REN_data = [ (0,a),(1, a), (2, b), (3, c),(4,d),
                     (5, e), (6,f), (7,g), (8,h),(9,i),
                     (10,j ),(11,k),(12,l),(13,m),(14,n),(15,o),
                     (16,p),(17,q),(18,r),(19,s),(20,t),(21,u), (22,v) ]

        columnArray = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21];
        try:
            for i in columnArray:
                ren_data = str(DICT_REN_data[array[i]]).split(',')
                if len (ren_data) == 3:
                    ox = ren_data[1]+','+ren_data[2]
                    ul = ox.replace("'","") 
                    ren_d = ul.replace(")","")
                else:
                    oh = ren_data[1].replace(",","")
                    ul = oh.replace("'","") 
                    ren_d = ul.replace(")","")

                ren_title = str(DICT_REN[array[i]]).split(',')
                ds = ren_title[1].replace(",","")
                ff = ds.replace("'","") 
                ren_t = ff.replace(")","")
                # ren_d = ren_d.replace(" ", "")
                data[str(ren_t)] = str(ren_d)
                
        except Exception as e:
            pass

        del data['id']
        del data ['folio']
        del data ['aseguradora']
        del data['coverageInPolicy_policy']
        del data['url']
        del data['owner']
        del data['org_name']
        del data['poliza_number']
        del data['observations']
        del data['old_policies']
        del data['f_currency']
        del data ['life_policy']
        del data['recibos_poliza']
        del data ['document_type']
        del data ['address']
        del data ['internal_number']
        del data ['contractor']
        del data ['clave']
        del data['p_neta']
        del data ['udi']
        del data['rpf']
        del data['derecho']
        del data['iva']
        del data['p_total']
        del data['status']
        del data['comision']
        del data['start_of_validity']
        del data['end_of_validity']
        del data['created_at']
        del data['updated_at']
        del data['subramo']
        del data['ramo']
        del data['forma_de_pago']
        del data['paquete']
        return data


class ReporteRenovacionesSerializerMod(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    paquete = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner',  'org_name',
                  'poliza_number', 'contractor',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'old_policies',
                  'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 'recibos_poliza', 'life_policy',
                  'document_type', 'address', 'coverageInPolicy_policy','f_currency','p_neta',
                  'p_total','derecho','rpf', 'iva', 'comision', 'created_at','updated_at','sucursal',
                  'contratante_subgroup','comision_derecho_percent','comision_rpf_percent')

    def to_representation(self, instance):
        data = super(ReporteRenovacionesSerializerMod, self).to_representation(instance)
        data ['FOLIO'] = instance.folio
        data['No.POLIZA'] = instance.poliza_number
        data['ASEGURADORA'] = str(instance.aseguradora)
        if instance.contractor:       
           data['CONTRATANTE'] =str(instance.contractor) 
        data['PRIMA NETA'] = instance.p_neta
        data['RPF'] = instance.rpf
        data['DERECHO'] = instance.derecho
        data['IVA'] = instance.iva
        data['PRIMA TOTAL'] = instance.p_total
        data['COMISION'] = instance.comision
        data['FECHA I'] = instance.start_of_validity
        data['FECHA F'] = instance.end_of_validity     
        data['CREADO POR'] =  instance.owner.first_name + " "+instance.owner.last_name 

        del data['id']
        del data ['folio']
        del data ['aseguradora']
        del data['coverageInPolicy_policy']
        del data['url']
        del data['owner']
        del data['org_name']
        del data['poliza_number']
        del data['observations']
        del data['old_policies']
        del data['f_currency']
        del data ['life_policy']
        del data['recibos_poliza']
        del data ['document_type']
        del data ['address']
        del data ['internal_number']
        del data ['contractor']
        del data['p_neta']
        del data ['udi']
        del data['rpf']
        del data['derecho']
        del data['iva']
        del data['p_total']
        del data['status']
        del data['comision']
        del data['start_of_validity']
        del data['end_of_validity']
        del data['created_at']
        del data['updated_at']
        del data['subramo']
        del data['ramo']
        del data['forma_de_pago']
        del data['paquete']
        return data

# renovaciones a excel modulo
class ReporteRenovacionFiltersSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    paquete = serializers.StringRelatedField(read_only=True)
    # old_policies = OldPolicyHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner',  'org_name',
                  'poliza_number', 'contractor',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'old_policies',
                  'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 'recibos_poliza', 'life_policy',
                  'document_type', 'address', 'coverageInPolicy_policy','f_currency','p_neta',
                  'p_total','derecho','rpf', 'iva', 'comision', 'created_at','updated_at','sucursal'
                  'contratante_subgroup','comision_derecho_percent','comision_rpf_percent')


    def to_representation(self, instance):
        if instance.forma_de_pago == 12:
            instance.forma_de_pago = "Anual"
        elif instance.forma_de_pago == 1:
            instance.forma_de_pago = "Mensual"
        elif instance.forma_de_pago == 2:
            instance.forma_de_pago = "Bimestral"
        elif instance.forma_de_pago == 3:
            instance.forma_de_pago = "Trimestral"
        elif instance.forma_de_pago == 4:
            instance.forma_de_pago = "Cuatrimestral"
        elif instance.forma_de_pago == 5:
            instance.forma_de_pago = "Contado"
        elif instance.forma_de_pago == 6:
            instance.forma_de_pago = "Semestral"

        if instance.status == 1:
            instance.status = "OT Pendiente"
        elif instance.status == 2:
            instance.status = "OT Cancelada"
        elif instance.status == 4:
            instance.status = "Precancelada"
        elif instance.status == 10:
            instance.status = "Por iniciar"
        elif instance.status == 11:
            instance.status = "Cancelada"
        elif instance.status == 12:
            instance.status = "Cerrada"
        elif instance.status == 13:
            instance.status = "Vencida"
        elif instance.status == 14:
            instance.status = "Vigente"

        data = super(ReporteRenovacionFiltersSerializer, self).to_representation(instance)
        # for p in polizas:
        parent = instance.id
        renew_filters = [Q(base_policy = parent), 
                        Q(new_policy = parent)]
        coincidences = OldPolicies.objects.filter(reduce(OR, renew_filters), org_name=instance.org_name)
        instance.old_policies = coincidences
        old_pol = ''
        if(coincidences):
            for c in coincidences:
                old_pol = Polizas.objects.filter(poliza_number = c)

        # -------------------
        data['No.POLIZA'] = instance.poliza_number
        try:
            if (old_pol):
                data['PÓLIZA A RENOVAR'] = old_pol['poliza_number']
        except Exception as e:
            pass

        if instance.contractor:       
           data['CONTRATANTE'] =str(instance.contractor) 
        data['TIPO'] = "Física"
        data['ASEGURADORA'] = str(instance.aseguradora)
        data['PAQUETE'] = str(instance.paquete)
        data['SUBRAMO'] = str(instance.subramo)
        data['FECHA INICIO'] = instance.start_of_validity.strftime("%d/%m/%y")
        data['FECHA FIN'] = instance.end_of_validity.strftime("%d/%m/%y")
        data ['FORMA PAGO'] = instance.forma_de_pago
        data ['ESTATUS']= instance.status
        data['CREADO POR'] =  instance.owner.first_name + " "+instance.owner.last_name 

        del data['id']
        del data ['folio']
        del data ['aseguradora']
        del data['coverageInPolicy_policy']
        del data['url']
        del data['owner']
        del data['org_name']
        del data['poliza_number']
        del data['observations']
        del data['old_policies']
        del data['f_currency']
        del data ['life_policy']
        del data['recibos_poliza']
        del data ['document_type']
        del data ['address']
        del data ['internal_number']
        del data ['contractor']
        del data['p_neta']
        del data ['udi']
        del data['rpf']
        del data['derecho']
        del data['iva']
        del data['p_total']
        del data['status']
        del data['comision']
        del data['start_of_validity']
        del data['end_of_validity']
        del data['created_at']
        del data['updated_at']
        del data['subramo']
        del data['ramo']
        del data['forma_de_pago']
        del data['paquete']
        return data

class PolizaParentSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    celula = CelulacontractorHyperSerializer(many=False, read_only=True)
    # recibos_poliza = CreateReciboSerializer(many = True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'identifier','aseguradora', 'recibos_poliza','comision_derecho_percent','comision_rpf_percent',
         'certificate_number','sucursal','collection_executive','document_type','emision_date','ramo','subramo','contratante_subgroup','contractor','celula')

class CreateReciboSerializer(serializers.HyperlinkedModelSerializer):
    poliza = serializers.SlugRelatedField(many=False,read_only=True,slug_field='poliza_number')
    endorsement = serializers.SlugRelatedField(many=False,read_only=True,slug_field='number_endorsement')
    serie_manual = serializers.IntegerField(required = False)
    class Meta:
        model = Recibos
        fields = ('id', 'url', 'recibo_numero', 'prima_neta', 'rpf', 'derecho', 'iva',
                'sub_total', 'prima_total', 'fecha_inicio', 'fecha_fin', 'delivered',
                'receipt_type', 'status', 'comision', 'vencimiento', 'poliza', 'track_bitacora',
                'track_email','track_phone', 'endorsement','gastos_investigacion', 'conducto_de_pago','comision_conciliada',
                'serie_manual')
        extra_kwargs = {'id': {'read_only': True, 'required': False}}


class PolizaMinSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    recibos_poliza = CreateReciboSerializer(many = True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'identifier','aseguradora', 'recibos_poliza',
         'certificate_number','sucursal','collection_executive','document_type','emision_date','business_line',
         'contratante_subgroup','contractor','fecha_pago_comision','maquila','exchange_rate',
         'date_emision_factura','month_factura','folio_factura','date_maquila','year_factura','date_bono','comision_derecho_percent','comision_rpf_percent')

class PolizaReportSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    forma_de_pago = serializers.SerializerMethodField()
    # 
    life_policy = LifeGetHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperInfoSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    parent = PolizaMinSerializer(many = False, read_only = True)

    def get_forma_de_pago(self,obj):
        return obj.get_forma_de_pago_display()

    class Meta:
        model = Polizas
        fields = ('id', 'poliza_number','end_of_validity',
            'aseguradora','subramo','ramo','start_of_validity', 'document_type',
            'forma_de_pago', 'status', 'clave','life_policy','automobiles_policy','comision_derecho_percent','comision_rpf_percent',
            'damages_policy','accidents_policy','f_currency','sucursal','collection_executive','emision_date','parent','contratante_subgroup','contractor'
            )

class PolizaReportCompleteSerializer(serializers.HyperlinkedModelSerializer):
    # aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    celula = CelulacontractorHyperSerializer(many=False, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    forma_de_pago = serializers.SerializerMethodField()
    aseguradora = serializers.SerializerMethodField()

    life_policy = LifeGetHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperInfoSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    ref_policy = RefInvolvedInfoSerializer(many=True, read_only=True)
    sucursal = SucursalFullSerializer(read_only = True)   
    responsable = VendorSerializer(read_only = True)
    collection_executive = VendorSerializer(read_only = True)
    parent = PolizaParentSerializer(many = False, read_only = True)

    def get_forma_de_pago(self,obj):
        return obj.get_forma_de_pago_display()

    def get_aseguradora(self, obj):
        if obj.parent and obj.parent.parent and obj.parent.parent.parent:
            if obj.parent.parent.parent.aseguradora:
                return obj.parent.parent.parent.aseguradora.alias
            elif obj.parent.parent.aseguradora:
                return obj.parent.parent.aseguradora.alias
            elif obj.parent.aseguradora:
                return obj.parent.aseguradora.alias
            elif obj.aseguradora:
                return obj.aseguradora.alias
            else:
                return 'Sin aseguradora'
        elif obj.parent and obj.parent.parent:
            if obj.parent.parent.aseguradora:
                return obj.parent.parent.aseguradora.alias
            elif obj.parent.aseguradora:
                return obj.parent.aseguradora.alias
            elif obj.aseguradora:
                return obj.aseguradora.alias
            else:
                return 'Sin aseguradora'
        elif obj.parent:
            if obj.parent.aseguradora:
                return obj.parent.aseguradora.alias
            elif obj.aseguradora:
                return obj.aseguradora.alias
            else:
                return 'Sin aseguradora'
        elif obj.aseguradora:
            return obj.aseguradora.alias
        else:
            return 'Sin aseguradora'
    class Meta:
        model = Polizas
        fields = ('id', 'poliza_number','end_of_validity', 'sucursal','comision_derecho_percent','comision_rpf_percent',
            'aseguradora','subramo','ramo','start_of_validity', 'document_type',
            'forma_de_pago', 'status', 'clave', 'life_policy','automobiles_policy','ref_policy',
            'damages_policy','accidents_policy','identifier','url','responsable','f_currency','sucursal','collection_executive','emision_date','parent',
            'contratante_subgroup','business_line','celula','contractor','fecha_pago_comision','maquila','exchange_rate',
            'date_emision_factura','month_factura','folio_factura','date_maquila','year_factura','date_bono')

class PolizaVendorSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    clave = serializers.SlugRelatedField(many=False,read_only=True,slug_field='clave')
    forma_de_pago = serializers.SerializerMethodField()
    document_type = serializers.SerializerMethodField()

    def get_document_type(self,obj):
        return obj.get_document_type_display()

    def get_forma_de_pago(self,obj):
        return obj.get_forma_de_pago_display()

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'poliza_number','end_of_validity',
            'aseguradora','subramo','ramo','start_of_validity', 'document_type',
            'forma_de_pago', 'status', 'clave', 'sucursal','collection_executive','emision_date','contratante_subgroup',
            'contractor','fecha_pago_comision','maquila','exchange_rate','comision_derecho_percent','comision_rpf_percent',
            'date_emision_factura','month_factura','folio_factura','date_maquila','year_factura','date_bono')
# reporte cobranzas
class PolizaReportSerializerMod(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    forma_de_pago = serializers.SerializerMethodField()

    def get_forma_de_pago(self,obj):
        return obj.get_forma_de_pago_display()

    class Meta:
        model = Polizas
        fields = ('id', 'poliza_number','end_of_validity', 'contractor',
            'aseguradora','subramo','ramo','start_of_validity','comision_derecho_percent','comision_rpf_percent',
            'forma_de_pago', 'status', 'clave','sucursal','collection_executive','emision_date',
            'contratante_subgroup','fecha_pago_comision','maquila','exchange_rate',
            'date_emision_factura','month_factura','folio_factura','date_maquila','year_factura','date_bono'
            )
# reporte cobranzas

class CreateReciboSerializer(serializers.HyperlinkedModelSerializer):
    poliza = serializers.SlugRelatedField(many=False,read_only=True,slug_field='poliza_number')
    endorsement = serializers.SlugRelatedField(many=False,read_only=True,slug_field='number_endorsement')
    serie_manual = serializers.IntegerField(required = False)
    endosotramite = serializers.SerializerMethodField()
    def get_endosotramite(self,obj):
        try:
            poliza_aux = False
            if obj.poliza:
                poliza_aux = Endorsement.objects.filter(policy = obj.poliza, status__in = [1,5], org_name = obj.poliza.org_name).exists()                
            return poliza_aux
        except Exception as e:
            print('.ee',e)
            poliza_aux = ""
            return poliza_aux 
    class Meta:
        model = Recibos
        fields = ('id', 'url', 'recibo_numero', 'prima_neta', 'rpf', 'derecho', 'iva',
                'sub_total', 'prima_total', 'fecha_inicio', 'fecha_fin', 'delivered','endosotramite',
                'receipt_type', 'status', 'comision', 'vencimiento', 'poliza', 'track_bitacora','track_email','track_phone', 
                'endorsement','created_at','pay_form', 'conducto_de_pago', 'serie_manual','comision_conciliada')
        extra_kwargs = {'id': {'read_only': True, 'required': False}}

class EndosoReciboSerializer(serializers.HyperlinkedModelSerializer):
    poliza = serializers.SlugRelatedField(many=False,read_only=True,slug_field='poliza_number')
    endorsement = serializers.SlugRelatedField(many=False,read_only=True,slug_field='number_endorsement')
    class Meta:
        model = Recibos
        fields = ('id', 'url', 'recibo_numero', 'prima_neta', 'rpf', 'derecho', 'iva', 'delivered', 'excedente',
                'sub_total', 'prima_total', 'fecha_inicio', 'fecha_fin', 'endorsement','folio',
                'receipt_type', 'status', 'comision', 'vencimiento', 'poliza', 'track_bitacora','track_phone','track_email','comision_conciliada')
        extra_kwargs = {'id': {'read_only': True, 'required': False}}

class CertificateSerializer(serializers.HyperlinkedModelSerializer):
    life_policy = LifeGetHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperInfoSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    contract_poliza = ContractHyperSerializer(many = False, read_only=True)
    beneficiaries_poliza = BeneficiarieHyperSerializer(many = True, read_only=True)
    recibos_poliza = CreateReciboSerializer(many = True)
    recordatorios = serializers.SerializerMethodField()
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    def get_recordatorios(self, obj):        
        if obj:
            recs = RegistroDeRecordatorio.objects.filter(recordatorio__tipo=3,record_model__in=[1,25],record_id= obj.id, org_name=obj.org_name)
            serializer = RegistroDeRecordatorioSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        else:
            return []
    class Meta: 
        model = Polizas
        fields = ('certificate_number', 'life_policy', 'id', 'automobiles_policy', 'start_of_validity', 'end_of_validity','p_neta','derecho',
            'damages_policy', 'accidents_policy', 'coverageInPolicy_policy', 'caratula', 'certificado_inciso_activo', 'fecha_baja_inciso',
            'contacto', 'url', 'p_total', 'rec_antiguedad','rpf','iva','sucursal','collection_executive','hospital_level','parent','comision',
            'contractor','document_type','status','receipts_by','updated_at','paquete','emision_date','contract_poliza','beneficiaries_poliza',
            'recibos_poliza','poliza_number','folio','contratante_subgroup','tabulator', 'observations','p_neta_earned', 'derecho_earned','org_name',
            'rpf_earned', 'descuento_earned', 'sub_total_earned', 'iva_earned', 'p_total_earned', 'comision_earned', 'comision_percent_earned',
            'recordatorios','contributory','rfc_cve','rfc_homocve','dom_callenum','dom_colonia','dom_cp','dom_poblacion','dom_estado','subramo',
            'comision_derecho_percent','comision_rpf_percent')


class CertificateExcelSerializer(serializers.HyperlinkedModelSerializer):
    life_policy = LifeGetHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperInfoSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    
    class Meta:
        model = Polizas
        fields = ('certificate_number', 'life_policy', 'id', 'automobiles_policy', 'start_of_validity', 'end_of_validity','emision_date',
            'damages_policy', 'accidents_policy', 'coverageInPolicy_policy', 'caratula', 'certificado_inciso_activo','rec_antiguedad','p_total',
            'sucursal','comision_derecho_percent','comision_rpf_percent')


    def to_representation(self, instance):
        data = super(CertificateExcelSerializer, self).to_representation(instance)

        if instance.document_type == 1:       
           data['TIPO'] = "Póliza"
        elif instance.document_type == 2:
            data['TIPO']= "Endoso"
        elif instance.document_type == 3:
            data['TIPO']= "Caratula" 
        elif instance.document_type ==6:
            data ['TIPO'] = 'Certificado'
        elif instance.document_type == 5:
            data['TIPO'] = 'Categoría'
        elif instance.document_type == 4:
            data['TIPO'] = 'SUBGRUPO'
        else:
            data['TIPO'] = 'OT'
        data['No.PÓLIZA'] = instance.poliza_number
        data['No.CERTIFICADO'] = instance.certificate_number
        if instance.certificado_inciso_activo:
            data['ESTATUS'] = 'ACTIVO'
        else:
            data['ESTATUS'] = 'INACTIVO'

        try:
            if instance.accidents_policy:
                for i in instance.accidents_policy.all():
                    data['ASEGURADO'] = i.personal.first_name + ' ' + i.personal.last_name
            elif instance.life_policy:
                for i in instance.life_policy.all():
                    data['ASEGURADO'] = i.personal.first_name + ' ' + i.personal.last_name
            elif instance.automobiles_policy:
                for i in instance.automobiles_policy.all():
                    data['ASEGURADO'] = i.serial
            elif instance.damages_policy:
                for i in instance.damages_policy.all():
                    data['ASEGURADO'] = i.insured_item
            else:
                data['ASEGURADO'] = 'No aplica'
        except Exception as e:
            pass
        if instance.start_of_validity:
            start = instance.start_of_validity.strftime("%d/%m/%Y")
        else:
            start = 'Sin fecha incio'

        if instance.rec_antiguedad:
            antiguedad_a = instance.rec_antiguedad.strftime("%d/%m/%Y")
        else:
            antiguedad_a = 'Sin fecha de reconocimiento de antigüedad'

        if instance.end_of_validity:
            end = instance.end_of_validity.strftime("%d/%m/%Y")
        else:
            end = 'Sin fecha fin'
        try:
            data['COSTO'] ='$ '+ str('{:,.2f}'.format(instance.p_total))
        except Exception as e:
            data['COSTO'] ='$ '+ str(instance.p_total)
        data['VIGENCIA'] = str(start) + ' - ' + str(end)
        data['ANTIGÜEDAD'] = str(antiguedad_a)



        caratula = Polizas.objects.get(pk = instance.caratula)
 
        data['ASEGURADORA'] = str(caratula.aseguradora)
      
        if instance.ramo:
            data['RAMO'] = str(caratula.ramo)
        else:
            data['RAMO'] = ""

        if instance.subramo:
            data['SUBRAMO'] = str(caratula.subramo)
        else:
            data['SUBRAMO'] = ""        
 
        if instance.observations:
            data ['OBSERVACIONES'] = str(instance.observations )  
        else:
            data ['OBSERVACIONES'] = ''         

        del data['certificate_number']
        del data['id']
        del data['p_total']
        del data['caratula']
        del data['certificado_inciso_activo']
        del data ['coverageInPolicy_policy']
        del data ['automobiles_policy']
        del data ['accidents_policy']
        del data ['life_policy']
        del data ['damages_policy']
        del data ['end_of_validity']
        del data['start_of_validity']
        del data['rec_antiguedad']

        return data

class CertificateEndorsementSerializer(serializers.HyperlinkedModelSerializer):
    life_policy = LifeGetHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperInfoSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    class Meta:
        model = Polizas
        fields = ('certificate_number', 'life_policy', 'id', 'automobiles_policy','comision_derecho_percent','comision_rpf_percent', 
            'damages_policy', 'accidents_policy', 'coverageInPolicy_policy','rec_antiguedad','sucursal','receipts_by','contratante_subgroup')


class PolizaReducedSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'identifier','aseguradora', 'recibos_poliza','comision_derecho_percent','comision_rpf_percent',
         'certificate_number','sucursal','collection_executive','document_type', 'scheme', 'accident_rate', 'steps','business_line',
         'contratante_subgroup','contractor')

class PolizaBasicSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora = serializers.ReadOnlyField(source='aseguradora.id')
    clave = serializers.ReadOnlyField(source='clave.id')
    celula = serializers.ReadOnlyField(source='celula.id')
    ramo = serializers.ReadOnlyField(source='ramo.id')
    subramo = serializers.ReadOnlyField(source='subramo.id')
    collection_executive = serializers.ReadOnlyField(source='collection_executive.id')
    responsable = serializers.ReadOnlyField(source='responsable.id')

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'identifier','aseguradora', 'document_type','contractor','created_at','internal_number','celula','clave',
                'collection_executive','ramo','subramo','business_line','responsable','start_of_validity','end_of_validity')
        
class PolizaMinSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    recibos_poliza = CreateReciboSerializer(many = True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'identifier','aseguradora', 'recibos_poliza','comision_derecho_percent','comision_rpf_percent',
         'certificate_number','sucursal','collection_executive','document_type', 'scheme', 'accident_rate', 'steps','business_line',
         'contratante_subgroup','contractor','cancelnotas')

class PolizaRenoSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = LifeHyperSerializer(many=True, read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    old_policies = OldPolicyHyperSerializer(many=True, read_only=True)    
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    recibos_poliza = CreateReciboSerializer(many = True)
    grouping_level = serializers.SerializerMethodField()
    subgrouping_level = serializers.SerializerMethodField()
    subsubgrouping_level = serializers.SerializerMethodField()
    #renewed_status = serializers.SerializerMethodField()
    
    def get_grouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 1:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.parent.level_grouping,
                'description' : obj.groupinglevel.parent.parent.description,
                'type_grouping' : obj.groupinglevel.parent.parent.type_grouping,
                'id' : obj.groupinglevel.parent.parent.id
            }
        else :
            return None
    def get_subgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        else :
            return None

    def get_subsubgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        else :
            return None

#    def get_renewed_status(self, obj):
#        return obj.get_renewed_status()
    
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner',  'org_name', 'renewed_status', 'responsable',
                  'poliza_number', 'is_renewable', 'reason_ren', 'reason_cancel',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'old_policies', 'give_comision',
                  'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 'recibos_poliza',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy', 'administration_type',
                  'document_type', 'address', 'coverageInPolicy_policy',
                  'created_at', 'updated_at', 'clave','f_currency', 'identifier','receipts_by',
                  'p_total','derecho','rpf','p_neta','sub_total', 'iva', 'comision', 'descuento',
                  'comision_percent', 'parent','comision_derecho_percent','comision_rpf_percent', 
                  'certificado_inciso_activo', 'caratula','name',
                  'certificate_number','rec_antiguedad','sucursal','collection_executive','hospital_level',
                  'personal_life_policy','fecha_baja_inciso','emision_date','business_line','contratante_subgroup',
                  'celula', 'groupinglevel', 'grouping_level', 'subgrouping_level', 'subsubgrouping_level', 'contractor',
                  'conducto_de_pago','date_cancel','state_circulation','cancelnotas')


    def create(self, validated_data):
        recibos = validated_data.pop('recibos_poliza')
        if not len(recibos) and validated_data['status'] != '2':
            raise serializers.ValidationError("No se incluyeron recibos favor de verificar")
        poliza = Polizas.objects.create(**validated_data)

        for recibo in recibos:
            recibo = Recibos.objects.create(poliza = poliza, owner = poliza.owner, org_name = poliza.org_name, **recibo)
            recibo.save()
        return poliza
        
class PolizaHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = LifeHyperSerializer(many=True, read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    old_policies = OldPolicyHyperSerializer(many=True, read_only=True)    
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    ref_policy = RefInvolvedFianzaSerializer(many=True, required = False)
    beneficiaries_poliza = BeneficiarieHyperSerializer(many = True, required=False)
    beneficiaries_poliza_many = BeneficiarieHyperSerializer(many = True, required = False)
    grouping_level = serializers.SerializerMethodField()
    subgrouping_level = serializers.SerializerMethodField()
    subsubgrouping_level = serializers.SerializerMethodField()      
    contract_poliza = ContractHyperSerializer(read_only = True,required = False,many = False)
    #renewed_status = serializers.SerializerMethodField()    
    fianza_type = FianzaTypeHyperSerializer(read_only = True, many = False)
    existe_ot_renovacion = serializers.SerializerMethodField()
    def get_existe_ot_renovacion(self, obj):
        val = False
        if OldPolicies.objects.filter(base_policy__id = obj.id, new_policy__status = 1).exists() and obj.is_renewable ==1:
            val = True
        return val
    def get_grouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 1:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.parent.level_grouping,
                'description' : obj.groupinglevel.parent.parent.description,
                'type_grouping' : obj.groupinglevel.parent.parent.type_grouping,
                'id' : obj.groupinglevel.parent.parent.id
            }
        else :
            return None
    def get_subgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        else :
            return None

    def get_subsubgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        else :
            return None

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner',  'org_name', 'renewed_status', 'responsable',
                  'poliza_number', 'is_renewable', 'reason_ren', 'reason_cancel','cotizacion_asociada',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'old_policies', 'give_comision',
                  'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 'recibos_poliza',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy', 'administration_type',
                  'document_type', 'address', 'coverageInPolicy_policy','comision_derecho_percent','comision_rpf_percent',
                  'created_at', 'updated_at', 'clave','f_currency', 'identifier','receipts_by',
                  'p_total','derecho','rpf','p_neta','sub_total', 'iva', 'comision', 'descuento',
                  'comision_percent', 'parent', 'existe_ot_renovacion','tabulator',
                  'certificado_inciso_activo', 'caratula','name', 'deductible',
                  'certificate_number','rec_antiguedad','sucursal','collection_executive','hospital_level','personal_life_policy','fecha_baja_inciso',
                  'emision_date','fianza_type','beneficiaries_poliza','beneficiaries_poliza_many','reason_rehabilitate','concept_annulment',
                  'total_receipts','ref_policy', 'scheme', 'accident_rate', 'steps','business_line','contratante_subgroup','type_policy',
                  'celula', 'groupinglevel', 'grouping_level', 'subgrouping_level', 'subsubgrouping_level','contractor',
                  'conducto_de_pago','bono_variable', 'has_programa_de_proveedores', 
                  'programa_de_proveedores_contractor','date_cancel', 'fecha_cancelacion' ,'monto_cancelacion','state_circulation',
                  'contract_poliza','fecha_pago_comision','maquila','date_emision_factura','month_factura','folio_factura',
                  'exchange_rate','date_maquila','year_factura','date_bono', 'fecha_entrega','cancelnotas','owner_cancel',
                  'contributory','rfc_cve','rfc_homocve','dom_callenum','dom_colonia','dom_cp','dom_poblacion','dom_estado','from_pdf')

    def create(self, validated_data):
        beneficiaries_poliza_many = []
        beneficiaries_poliza = []
        recibos = validated_data.pop('recibos_poliza')
        
        if not len(recibos) and (validated_data['status'] != '2'):
            if int(validated_data['status']) != 1 and int(validated_data['status']) != 2 and int(validated_data['document_type']) != 6:
                raise serializers.ValidationError("No se incluyeron recibos favor de verificar")
        poliza = Polizas.objects.create(**validated_data)
        for recibo in recibos:
            recibo = Recibos.objects.create(poliza = poliza, owner = poliza.owner, org_name = poliza.org_name, **recibo)
            recibo.save()
        return poliza

    def update(self, instance, validated_data):
        if 'beneficiaries_poliza' in validated_data and validated_data['beneficiaries_poliza'] == [] and 'beneficiaries_poliza_many' in validated_data and validated_data['beneficiaries_poliza_many'] == [] and 'ref_policy' in validated_data and validated_data['ref_policy'] == []:
            validated_data.pop('beneficiaries_poliza_many')
            validated_data.pop('beneficiaries_poliza') 
            referenciadores =validated_data.pop('ref_policy')
             
            p = Polizas.objects.filter(id=instance.id)
            p.update(**validated_data)
            return p[0]
        
        if (instance.document_type == 7 or instance.document_type == 8) and (instance.status ==11 or ('status' in validated_data and validated_data['status'] ==11)):
            instance.fecha_cancelacion = validated_data['fecha_cancelacion'] if 'fecha_cancelacion' in validated_data else datetime.now()
            instance.monto_cancelacion = validated_data['monto_cancelacion'] if 'monto_cancelacion' in validated_data else 0
            instance.save()
        # Update certificados  6
        try:
            if instance.document_type == 6:
                p = Polizas.objects.filter(id=instance.id)
                p.update(**validated_data)
                return p[0]
        except Exception as ed:
            raise Exception(str(ed))
        try:
            beneficiaries_many = []
            recibos = []    
            try:        
                referenciadores = validated_data.pop('ref_policy')
            except Exception as ers:
                referenciadores = []

            if 'beneficiaries_poliza_many' in validated_data:
                beneficiaries_many = self.context.get('request').data['beneficiaries_poliza_many']
                validated_data.pop('beneficiaries_poliza_many')
            if 'beneficiaries_poliza' in validated_data:
                beneficiaries = self.context.get('request').data['beneficiaries_poliza']
                validated_data.pop('beneficiaries_poliza')                
            if not len(beneficiaries_many) and instance.document_type == 8 and (validated_data['status'] != 12 and validated_data['status'] != 17 and validated_data['status'] != 24 and validated_data['status'] != 0):
                raise Exception('Es necesario agregar al menos un beneficiario')
            else:
                beneficiaries_poliza_many = []
                beneficiaries_poliza = []
            with transaction.atomic():
                try:
                    if len(validated_data['recibos_poliza'])  == 0:
                        validated_data.pop('recibos_poliza')
                except Exception as eee:
                    pass
                try:
                    if validated_data['old_policies']:
                        validated_data.pop('old_policies')
                except Exception as eee:
                    pass
                polizaupd = Polizas.objects.filter(id=instance.id).update(**validated_data)
                polizaupd = Polizas.objects.get(id=instance.id)
                # Updtae certificados
                try:
                    if instance.document_type == 8 and validated_data['status'] == 12:
                        cats = Polizas.objects.filter(document_type = 9, parent__id = instance.id)
                        certificates = Polizas.objects.filter(document_type = 10, parent__in = cats)
                        for p in certificates:
                            p.status = 23
                            p.certificado_inciso_activo = False
                            p.save()   

                except Exception as ed:
                    raise Exception(str(ed))
                # Update certificados  6
                try:
                    if instance.document_type == 6:
                        p = Polizas.objects.filter(id=instance.id)
                        p.update(**validated_data)
                        return p[0]
                except Exception as ed:
                    raise Exception(str(ed))
                try:
                    if instance.document_type == 3:
                        p = Polizas.objects.filter(document_type = 6, caratula = str(instance.id)).exclude(status=0)
                        try:
                            p.update(contributory = validated_data['contributory'])
                        except:
                            p=p
                        try:#acutalizar certificados numero poliza***********
                            pcertificates = Polizas.objects.filter(document_type = 6, caratula = str(instance.id)).exclude(status=0)
                            for cert in pcertificates:
                                polizanumber_certificado=str(instance.poliza_number if instance.poliza_number else '')+" - INC. "+str(cert.certificate_number if cert.certificate_number else '')
                                cert.poliza_number = polizanumber_certificado
                                cert.save()
                                print('cert update()',cert.id,cert.poliza_number)
                            
                        except Exception as ex:
                            print('ex********+++',ex)
                except Exception as ed:
                    print('erorr------',ed)


                if instance.document_type == 11 :
                    Polizas.objects.filter(caratula = instance.id, parent = instance).update(collection_executive = instance.collection_executive,
                        responsable = instance.responsable, business_line = instance.business_line, aseguradora = instance.aseguradora,
                        clave = instance.clave, ramo = instance.ramo, subramo = instance.subramo)         
                try:
                    if instance.document_type == 11 and validated_data['status'] == 15:
                        pls = Polizas.objects.filter(parent = instance.id, org_name = instance.org_name, document_type =12, status__in = [13,14]).update(status = 15)
                except Exception as er:
                    pass

                try:
                    if instance.document_type == 3 and validated_data['status'] == 11:
                        subgrupos = Polizas.objects.filter(document_type = 4, parent__id = str(instance.id))  
                        # recs2 = Recibos.objects.filter(poliza__in = subgrupos, receipt_type__in = [1,2,3], status = 4)
                        recs2 = Recibos.objects.filter(poliza__in = subgrupos, receipt_type__in = [1,2], status = 4)
                        for p in recs2:
                            p.status = 2
                            p.save() 
                        if polizaupd.cancelnotas:
                            recs2 = Recibos.objects.filter(poliza__in = subgrupos, receipt_type__in = [3], status = 4)
                            for p in recs2:
                                p.status = 2
                                p.save() 
                        subc = Polizas.objects.filter(document_type = 6, caratula = str(instance.id))
                        for p in subc:
                            p.status = 11
                            p.certificado_inciso_activo = False
                            p.save()   
                        # recs = Recibos.objects.filter(poliza = instance, receipt_type__in = [1,2,3], status = 4)
                        recs = Recibos.objects.filter(poliza = instance, receipt_type__in = [1,2], status = 4)
                        for p in recs:
                            p.status = 2
                            p.save() 
                        if polizaupd.cancelnotas:                         
                            recs = Recibos.objects.filter(poliza = instance, receipt_type__in = [3], status = 4)
                            for p in recs:
                                p.status = 2
                                p.save() 
                        endos = Endorsement.objects.filter(policy = instance,org_name = instance.org_name).exclude(status = 2)
                        for p in endos:
                            p.status = 4
                            p.save()  
                except Exception as ed:
                    pass
                    # raise Exception(str(ed))

                try:
                    ids_benef = []
                    for beneficiarie in beneficiaries_many:
                        id = None
                        if 'url' in beneficiarie:
                            beneficiarie.pop('url')
                        if 'owner' in beneficiarie:
                            beneficiarie.pop('owner')
                        if 'id' in beneficiarie:
                            id = beneficiarie.pop('id')
                        if id:
                            benef = BeneficiariesContract.objects.get(id=id)
                            ids_benef.append(benef.id)
                        else:
                            if beneficiarie['type_person'] ==1 and ( not beneficiarie['first_name'] or not beneficiarie['last_name']): # or not beneficiarie['second_last_name'] or not beneficiarie['rfc'] or not beneficiarie['email'] or not beneficiarie['phone_number'])
                                raise Exception('Los siguientes campos son requeridos para el beneficiario: Nombre, apellido Paterno')
                            elif beneficiarie['type_person'] ==2 and ( not beneficiarie['j_name']):
                                raise Exception('Los siguientes campos son requeridos para el beneficiario:Razon Social')
                            benef = BeneficiariesContract.objects.create(owner = instance.owner, org_name = instance.org_name, **beneficiarie)
                            ids_benef.append(benef.id)
                        if not benef.poliza_many.filter(id=instance.id).exists():
                            benef.poliza_many.add(instance)
                        r_ben = BeneficiariesContract.objects.filter(poliza_many=instance).exclude(id__in=ids_benef)
                        for ri in r_ben:
                            ri.poliza_many.remove(instance)
                except Exception as e:
                    raise Exception(str(e))

                # fianza anulada = 17, certificados status = 1 pasar a 20 e inactivos, recibos status = 4,
                #  pasar a 10...
                try:
                    concpAnula = [3,4,5]
                    concpAnula1 = [2,3,4,5]
                    if validated_data['status'] == 17:#Anulación
                        certificados = Polizas.objects.filter(caratula = instance.id, document_type = 10)
                        for c in certificados:
                            if c.status == 1 or c.status == 14:
                                c.status = 20
                                c.certificado_inciso_activo = False
                                c.save()
                        recibosF = Recibos.objects.filter(poliza = instance.id, status__in = [4,11], receipt_type = 1)
                        for r in recibosF:
                            r.status = 10
                            r.save()
                        endososF = Endorsement.objects.filter(policy = instance.id)                    
                        for en in endososF:
                            if en.status == 2:                           
                                if validated_data['concept_annulment'] in concpAnula1:
                                    en.status = 6
                                en.save()
                                certificadosEnd = EndorsementCert.objects.filter(endorsement = en, certificate__document_type__in = [6,10])
                                for c in certificadosEnd:
                                    if (c.certificate.status == 1 or c.certificate.status == 18) and validated_data['concept_annulment'] == 2:
                                        c.certificate.status = 20
                                    if c.certificate.status == 18 and (validated_data['concept_annulment'] in concpAnula):
                                        c.certificate.status = 21
                                    c.certificate.certificado_inciso_activo = False
                                    c.certificate.save()
                                if validated_data['concept_annulment'] == 2:
                                    recibosE = Recibos.objects.filter(endorsement = en)
                                    for rend in recibosE:
                                        rend.status = 10
                                        rend.save()
                                if validated_data['concept_annulment'] in concpAnula:
                                    recibosE = Recibos.objects.filter(endorsement = en, status__in = [4,11], receipt_type=2)
                                    for rend in recibosE:
                                        rend.status = 10
                                        rend.save()
                                    notas = Recibos.objects.filter(endorsement = en, status__in = [4,8], receipt_type=3)
                                    for rend in notas:
                                        rend.status = 2
                                        rend.save()
                    if validated_data['status'] == 24:#Preanulación
                        certificados = Polizas.objects.filter(caratula = instance.id, document_type = 10)
                        for c in certificados:
                            if c.status == 1 or c.status == 14:
                                c.status = 20
                                c.certificado_inciso_activo = False
                                # c.save()
                        recibosF = Recibos.objects.filter(poliza = instance.id, status__in = [4], receipt_type = 1)
                        for r in recibosF:
                            r.status = 11
                            r.save()
                        endososF = Endorsement.objects.filter(policy = instance.id)
                        for en in endososF:
                            if en.status == 2:                                
                                recibosE = Recibos.objects.filter(endorsement = endososF, status= 4, receipt_type = 2)
                                for rend in recibosE:
                                    if validated_data['concept_annulment'] == 1:
                                        rend.status = 11
                                        rend.save()
                    if validated_data['status'] == 14 and (instance.status == 17 or instance == 24):# Rehabilitar
                        recibosF = Recibos.objects.filter(status__in = [10,11], poliza = instance, receipt_type = 1)
                        for rf in recibosF:
                            rf.status = 4
                            rf.save()
                        certificadosF = Polizas.objects.filter(caratula = instance.id, status = 20, document_type = 10)
                        for cf in certificadosF:
                            cf.status = 1
                            # c.certificado_inciso_activo = True
                            cf.save()
                        endosoF = Endorsement.objects.filter(policy = instance, status = 6)
                        for end in endosoF:
                            end.status = 2
                            end.save()
                            recE = Recibos.objects.filter(endorsement = end,status__in=[10,11], receipt_type = 2)
                            for rE in recE:
                                rE.status = 4
                                rE.save()
                            nota = Recibos.objects.filter(endorsement = end,status__in=[10], receipt_type = 3)
                            for rEn in nota:
                                rEn.status = 4
                                rEn.save()
                            certificadosE = EndorsementCert.objects.filter(endorsement = end, certificate__status = 21)
                            for ce in certificadosE:
                                ce.certificate.status = 18
                                ce.certificate.save()
                    try:
                        if validated_data['document_type'] == 11:
                            Polizas.objects.filter(id=instance.id).update(**validated_data)
                            polizas_col = Polizas.objects.filter(org_name = instance.org_name, caratula = instance.id, parent = instance)
                            try:
                                ids_ref = []
                                # dels = ReferenciadoresInvolved.objects.filter(policy = instance,org_name = instance.org_name).delete()
                                for referenciador in referenciadores:
                                    ref = None
                                    if 'referenciador' in referenciador and referenciador['referenciador']:
                                        ref = ReferenciadoresInvolved.objects.filter(policy = instance, owner = instance.owner, org_name= instance.org_name, referenciador=referenciador['referenciador'])
                                        if ref.exists():
                                            ref = ref[0]  
                                            ref.comision_vendedor = referenciador['comision_vendedor']
                                            ref.save()
                                        else:
                                            ref = ReferenciadoresInvolved.objects.create(policy = instance, owner = instance.owner, org_name = instance.org_name, **referenciador)
     
                                    if ref:
                                        ids_ref.append(ref.id)
                                    for pc in polizas_col:
                                        ids_refcol = []
                                        for referenciador in referenciadores:
                                            ref = None
                                            if 'referenciador' in referenciador and referenciador['referenciador']:
                                                ref = ReferenciadoresInvolved.objects.filter(policy = pc, org_name= instance.org_name, referenciador=referenciador['referenciador'])
                                                if ref.exists():
                                                    ref = ref[0]  
                                                    ref.comision_vendedor = referenciador['comision_vendedor']
                                                    ref.save()
                                                else:
                                                    ref = ReferenciadoresInvolved.objects.create(policy = pc, owner = instance.owner, org_name = instance.org_name, **referenciador)
             
                                            if ref:
                                                ids_refcol.append(ref.id)
                                        if ids_refcol:
                                            ReferenciadoresInvolved.objects.filter(policy = pc,org_name = instance.org_name).exclude(id__in=ids_refcol).delete()
                                if ids_ref:
                                    ReferenciadoresInvolved.objects.filter(policy = instance,org_name = instance.org_name).exclude(id__in=ids_ref).delete()

                            except Exception as e:
                                raise Exception(str(e))
                                pass
                    except Exception as erss:
                        pass
                    try:
                        if validated_data['status'] == 0:#Eliminación
                            certificados = Polizas.objects.filter(caratula = instance.id, document_type = 10)
                            for c in certificados:
                                    c.status = 0
                                    c.certificado_inciso_activo = False
                                    c.save()
                            recibosF = Recibos.objects.filter(poliza = instance.id, receipt_type = 1)
                            for r in recibosF:
                                r.status = 0
                                r.save()
                            endososF = Endorsement.objects.filter(policy = instance.id)              
                            for en in endososF:
                                en.status = 0
                                en.save()
                                certificadosEnd = EndorsementCert.objects.filter(endorsement = en, certificate__document_type__in = [6,10])
                                for c in certificadosEnd:
                                    c.certificate.status = 0
                                    c.certificate.certificado_inciso_activo = False
                                    c.certificate.save()
                                recibosE = Recibos.objects.filter(endorsement = en)
                                for rend in recibosE:
                                    rend.status = 0
                                    rend.save()                            
                    except Exception as df:                      
                        pass
                except Exception as esr:
                    print('--error--',esr)
            return instance
        except Exception as e:
            pass
            raise serializers.ValidationError(str(e))
# ___________________________________________________________________Caratulas


class GetCaratulaSerializer(serializers.ModelSerializer):
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    ramo = RamosResumeSerializer(many=False, read_only=True)
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Polizas
        fields = ('id', 'identifier', 'url', 'certificate_number', 'created_at', 'aseguradora', 'subramo', 'ramo','cancelnotas','comision_derecho_percent','comision_rpf_percent',
         'contractor','sucursal','collection_executive','receipts_by','document_type','status','poliza_number','business_line','contratante_subgroup')

class PolizaSissSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    recibos_poliza = CreateReciboSerializer(many = True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    caratula = GetCaratulaSerializer(many=False, read_only=True)
    ramo = serializers.ReadOnlyField(source='ramo.ramo_code')
    subramo =  serializers.ReadOnlyField(source='subramo.subramo_code')
    #org = OrganizationsHyperSerializer(many = False, read_only=True)

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'identifier', 'ramo', 'start_of_validity', 'end_of_validity',
                  'aseguradora', 'recibos_poliza', 'certificate_number', 'caratula', 'subramo','sucursal',
                  'collection_executive','org_name','emision_date','contratante_subgroup','contractor','comision_derecho_percent','comision_rpf_percent')

class ProviderMiniSerializer(serializers.ModelSerializer):
    class Meta:
       model = Provider
       fields = ('id', 'alias', 'url','compania','website')
            

class GetCaratulaFullSerializer(serializers.ModelSerializer):
    # files = CreatePolizasFileSerializer(many = True)
    # forma_de_pago = serializers.CharField(source='get_forma_de_pago_display')
    administration_type = serializers.CharField(source='get_administration_type_display')
    f_currency = serializers.CharField(source='get_f_currency_display')
    status = serializers.CharField(source='get_status_display')
    document_type = serializers.CharField(source='get_document_type_display')
    # recibos_poliza = CreateReciboSerializer(many = True)
    recibos_poliza = serializers.SerializerMethodField('get_receipts')
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    aseguradora = ProviderMiniSerializer(many = False, read_only=True)
    ramo = RamosResumeSerializer(many=False, read_only=True)
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    responsable = VendorSerializer(read_only = True)
    collection_executive = VendorSerializer(read_only = True)
    owner = serializers.SerializerMethodField()
    parent = PolizaMinSerializer(many = False, read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    # ref_policy = RefInvolvedInfoSerializer(many=True, read_only=True)
    life_policy = LifeGetHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    group= serializers.SerializerMethodField()
    subgrupo = serializers.SerializerMethodField()
    subsubgrupo = serializers.SerializerMethodField()
    grouping_level = serializers.SerializerMethodField()
    subgrouping_level = serializers.SerializerMethodField()
    subsubgrouping_level = serializers.SerializerMethodField()
    # renewed_status = serializers.SerializerMethodField()
    recordatorios = serializers.SerializerMethodField()
    contributory = serializers.SerializerMethodField()
    seguimiento = serializers.SerializerMethodField()
    task_associated_info = serializers.SerializerMethodField()
    ref_policy = serializers.SerializerMethodField()
    def get_ref_policy(self, obj):
        val = []
        try:
            if ReferenciadoresInvolved.objects.filter(policy = obj, is_changed= False,org_name=obj.org_name).exists():
                rp = ReferenciadoresInvolved.objects.filter(policy = obj, is_changed= False,org_name=obj.org_name)
                serializer = RefInvolvedInfoSerializer(rp, context={'request':self.context.get("request")}, many=True)
                data = serializer.data 
                return data
        except Exception as e:
            print('**************************************',e)
            val =[]
        return val
    def get_task_associated_info(self, obj):
        val = None
        try:
            if Ticket.objects.filter(id = obj.task_associated, ot_model = 1).exists():
                ticket = Ticket.objects.select_related('owner', 'closedBy', 'assigned', 'reassignBy').prefetch_related(
                    'involved_task',
                ).get(pk=obj.task_associated)  

                serializer = FullInfoTicketHyperSerializer(ticket, context={'request':self.context.get("request")})
                data = serializer.data 
                return data
        except Exception as e:
            val =None
        return val
    def get_seguimiento(self,obj):
        tab = ''
        if obj.status ==1:
            tablero =PromotoriaTablero.objects.filter(org_name=obj.org_name,is_active=True)#polizas_ots
            if tablero:
                confTab = tablero[0].polizas_ots
                try:
                    confTab = json.loads(confTab)
                except Exception as eee:
                    confTab = confTab
                    try:
                        confTab = eval(confTab)
                    except Exception as e:
                        pass
                # for y in confTab['contenedores']:
                for ind,y in enumerate(confTab):
                    for u in y['polizas']:
                        if obj.id in y['polizas']:
                            if u ==obj.id:
                                return y['tablero']
                            else:
                                tab= ''
                        else:
                            tab= ''
            else:
                tab= ''
        else:
            tab= ''
        return tab
    def get_recordatorios(self, obj):        
        if obj:
            recs = RegistroDeRecordatorio.objects.filter(recordatorio__tipo =3,record_model=1,record_id= obj.id, org_name=obj.org_name)
            serializer = RegistroDeRecordatorioSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        else:
            return []
    def get_grouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 1:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.parent.level_grouping,
                'description' : obj.groupinglevel.parent.parent.description,
                'type_grouping' : obj.groupinglevel.parent.parent.type_grouping,
                'id' : obj.groupinglevel.parent.parent.id
            }
        else :
            return None
    def get_subgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        else :
            return None

    def get_subsubgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        else :
            return None


    def get_group(self,obj):
        if obj.contratante_subgroup:
            grupo1 = Group.objects.get(pk = obj.contratante_subgroup,org_name = obj.org_name)
            if grupo1.type_group == 1:
                grupo = grupo1.group_name
            if grupo1.type_group ==2:
                grupo = grupo1.parent.group_name
            if grupo1.type_group ==3:
                grupo = grupo1.parent.parent.group_name
        else:
            grupo = ''
        return grupo
    def get_subgrupo(self,obj):
        if obj.contratante_subgroup:
            grupo1 = Group.objects.get(pk = obj.contratante_subgroup,org_name = obj.org_name)
            if grupo1.type_group == 1:
                subgrupo = ''
            if grupo1.type_group ==2:
                subgrupo = grupo1.group_name
            if grupo1.type_group ==3:
                subgrupo = grupo1.parent.group_name
        else:
            subgrupo = ''
        return subgrupo
    def get_subsubgrupo(self,obj):
        if obj.contratante_subgroup:
            grupo1 = Group.objects.get(pk = obj.contratante_subgroup,org_name = obj.org_name)
            if grupo1.type_group == 1:
                subsubgrupo = ''
            if grupo1.type_group ==2:
                subsubgrupo = grupo1.group_name
            if grupo1.type_group ==3:
                subsubgrupo = grupo1.parent.group_name
        else:
            subsubgrupo = ''
        return subsubgrupo
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

#    def get_renewed_status(self, obj):
#        return obj.get_renewed_status()
    def get_contributory(self, obj):
        val =False
        try:
            certs = Polizas.objects.filter(parent__parent__parent__id = obj.id,document_type = 6, contributory = True).exclude(status = 0)
            if certs:
                val = True
        except:
            val = False
        return val

    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id,receipt_type=1).exclude(status = 0)
        serializer = CreateReciboSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        return serializer.data
    class Meta:
        model = Polizas
        fields = ('id', 'observations', 'start_of_validity', 'derecho','responsable','ref_policy',
            'end_of_validity', 'recibos_poliza', 'forma_de_pago', 'status', 'p_neta', 'p_total','emision_date',
            'administration_type', 'f_currency', 'parent', 'document_type', 'owner', 'iva', 'descuento',
            'identifier', 'url', 'folio', 'internal_number', 'aseguradora', 'ramo', 'rpf', 'comision','org_name',
            'subramo', 'clave', 'comision_percent', 'poliza_number','renewed_status','receipts_by','is_renewable','rec_antiguedad',
            'address','sucursal','collection_executive','total_receipts','sub_total', 'scheme', 'accident_rate', 'steps','business_line','certificate_number',
            'life_policy','automobiles_policy','damages_policy','accidents_policy','contratante_subgroup','group',
            'subgrupo','subsubgrupo','reason_cancel','reason_ren','type_policy', 'celula', 'groupinglevel', 
            'grouping_level', 'subgrouping_level', 'subsubgrouping_level','contractor', 'conducto_de_pago', 
            'paquete','date_cancel','state_circulation', 'reason_rehabilitate','cancelnotas','recordatorios',
            'contributory','rfc_cve','rfc_homocve','dom_callenum','dom_colonia','dom_cp','dom_poblacion','updated_at',
            'dom_estado','seguimiento','from_task','task_associated','task_associated_info','comision_derecho_percent','comision_rpf_percent')


class GetCaratulaMinSerializer(serializers.ModelSerializer):
    contractor = serializers.StringRelatedField(read_only=True)
    aseguradora = ProviderMiniSerializer(many = False, read_only=True)
    ramo = RamosResumeSerializer(many=False, read_only=True)
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    sucursal = SucursalFullSerializer(read_only = True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Polizas
        fields = ('id', 'start_of_validity', 'identifier', 'url', 'aseguradora', 
            'ramo', 'subramo','sucursal','collection_executive','ref_policy', 'scheme', 'accident_rate', 'steps',
            'business_line','contratante_subgroup','contractor','comision_derecho_percent','comision_rpf_percent')

class CreateCaratulaSerializer(serializers.ModelSerializer):
    document_type = serializers.IntegerField()
    recibos_poliza = CreateReciboSerializer(many = True)
    responsable = VendorSerializer(read_only = True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    #renewed_status = serializers.SerializerMethodField()
    
#    def get_renewed_status(self, obj):
#        return obj.get_renewed_status()
    
    class Meta:
        model = Polizas
        fields = ('id', 'observations', 'start_of_validity', 'is_renewable','ref_policy',
            'end_of_validity', 'url', 'recibos_poliza', 'forma_de_pago', 'status', 'p_neta', 'p_total',
            'administration_type', 'f_currency', 'parent', 'document_type', 'identifier', 'responsable',
            'aseguradora', 'ramo', 'subramo', 'clave', 'folio', 'internal_number', 'iva', 'rpf', 'derecho', 'comision', 
            'poliza_number', 'comision', 'comision_percent','renewed_status','receipts_by','address',
            'sucursal','collection_executive','emision_date','scheme', 'accident_rate', 'steps',
            'business_line','contratante_subgroup','contractor','fecha_pago_comision','maquila','exchange_rate',
            'date_emision_factura','month_factura','folio_factura','date_maquila','year_factura','date_bono','comision_derecho_percent','comision_rpf_percent')


    def create(self, validated_data): 
        recibos = validated_data.pop('recibos_poliza')
        poliza = Polizas.objects.create(**validated_data)

        for recibo in recibos:
            Recibos.objects.create(poliza = poliza, owner = poliza.owner, org_name = poliza.org_name, **recibo)     

        return poliza
# Carátula pólizas-------
class CreateCaratulaPolizasSerializer(serializers.ModelSerializer):
    document_type = serializers.IntegerField()
    # responsable = VendorSerializer(many = False)
    owner = serializers.ReadOnlyField(source='owner.username')
    ref_policy = RefInvolvedFianzaSerializer(many=True)   
    grouping_level = serializers.SerializerMethodField()
    
    def get_grouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 1:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.parent.level_grouping,
                'description' : obj.groupinglevel.parent.parent.description,
                'type_grouping' : obj.groupinglevel.parent.parent.type_grouping,
                'id' : obj.groupinglevel.parent.parent.id
            }
        else :
            return None
    class Meta:
        model = Polizas
        fields = ('id', 'url', 'address', 'aseguradora', 'clave','created_at', 'document_type', 'end_of_validity', 'start_of_validity', 'poliza_number',
                  'identifier', 'internal_number', 'observations', 'ramo', 'status', 'subramo', 'owner','comision_derecho_percent','comision_rpf_percent', 
                   'emision_date','is_renewable', 'ref_policy', 'f_currency','responsable','type_policy','sucursal', 'celula', 
                   'groupinglevel','contractor','grouping_level','collection_executive','business_line','state_circulation','fecha_pago_comision',
                   'date_emision_factura','month_factura','folio_factura','maquila','exchange_rate','date_maquila','year_factura','date_bono','from_task','task_associated')

    def create(self, validated_data):
        try:        
            referenciadores =  validated_data.pop('ref_policy')
            # if not len(referenciadores):
            #     raise Exception('Es necesario incluir al menos un referenciador')

            if not 'document_type' in validated_data:
                validated_data['document_type'] = 11#Carátula Ancora

            with transaction.atomic():    
                poliza = Polizas.objects.create(**validated_data)
                for referenciador in referenciadores:
                    ReferenciadoresInvolved.objects.create(policy = poliza, owner = poliza.owner, org_name = poliza.org_name, **referenciador)                
                return poliza
        except Exception as e:
            raise serializers.ValidationError(str(e))


    def update(self, instance, validated_data): 
        try:
            referenciadores = validated_data.pop('ref_policy')
            # if not len(referenciadores):
            #     raise Exception('Es necesario incluir al menos un referenciador')                
            with transaction.atomic():
                Polizas.objects.filter(id=instance.id).update(**validated_data)              
                try:
                    ids_ref = []
                    for referenciador in referenciadores:
                        ref = None
                        if 'referenciador' in referenciador and referenciador['referenciador']:
                            ref = ReferenciadoresInvolved.objects.filter(policy = instance, owner = instance.owner, org_name= instance.org_name, referenciador=referenciador['referenciador'])
                            if ref.exists():
                                ref = ref[0]  
                                ref.comision_vendedor = referenciador['comision_vendedor']
                                ref.save()
                            else:
                                ref = ReferenciadoresInvolved.objects.create(policy = instance, owner = instance.owner, org_name = instance.org_name, **referenciador)
                        ids_ref.append(ref.id)
                    ReferenciadoresInvolved.objects.filter(policy = instance, owner = instance.owner, org_name = instance.org_name).exclude(id__in=ids_ref).delete()

                except Exception as e:
                    raise Exception(str(e))
            return instance
        except Exception as e:
            raise serializers.ValidationError(str(e))
# -----------------------
# ___________________________________________________________________SubGrupos

class ProvisionalPolizaSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    recibos_poliza = CreateReciboSerializer(many = True, read_only = True)
    parent = GetCaratulaFullSerializer(many = False, read_only = True)

    class Meta:
        model = Polizas
        fields = ('id', 'parent', 'poliza_number','aseguradora', 'recibos_poliza','sucursal','comision_derecho_percent','comision_rpf_percent',
            'collection_executive','ref_policy','document_type','contratante_subgroup','contractor')
    
        

class SubGroupSerializer(serializers.ModelSerializer):
    document_type = serializers.IntegerField()
    recibos_poliza = CreateReciboSerializer(many = True)
    coverageInPolicy_policy = CreateCoverageInPolicySerializer(many=True)
    parent = ProvisionalPolizaSerializer(many = False, read_only = True)
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    ramo = RamosResumeSerializer(many=False, read_only=True)
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    aseguradora = ProviderMiniSerializer(many = False, read_only=True)
    ref_policy = RefInvolvedInfoSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)

    class Meta:
        model = Polizas
        fields = ('id', 'observations', 'p_total', 'caratula','aseguradora',
            'derecho','rpf', 'p_neta', 'iva', 'address', 'descuento','ref_policy','clave',
            'name', 'recibos_poliza', 'coverageInPolicy_policy', 'parent', 'document_type', 'poliza_number',
            'subramo','ramo','sucursal','collection_executive','contratante_subgroup','contractor','comision_derecho_percent','comision_rpf_percent')

class SubGroupSaveSerializer(serializers.ModelSerializer):
    document_type = serializers.IntegerField()
    recibos_poliza = CreateReciboSerializer(many = True)
    coverageInPolicy_policy = CreateCoverageInPolicySerializer(many=True)
    
    class Meta:
        model = Polizas
        fields = ('id', 'observations', 'p_total', 'caratula',
            'derecho','rpf', 'p_neta', 'iva', 'descuento', 'url','comision_derecho_percent','comision_rpf_percent',
            'name', 'recibos_poliza', 'document_type', 'coverageInPolicy_policy',
            'sucursal','collection_executive','hospital_level','contratante_subgroup','contractor')

        # 'files'

    def create(self, validated_data):
        recibos = validated_data.pop('recibos_poliza')
        coberturas = validated_data.pop('coverageInPolicy_policy')
        try:
            p = Polizas.objects.get(id = validated_data['caratula'])
        except Polizas.DoesNotExist:
            p= None
        poliza = Polizas.objects.create(parent = p, **validated_data)

        for recibo in recibos:
            Recibos.objects.create(poliza = poliza, owner = poliza.owner, org_name = poliza.org_name, **recibo)

        for cobertura in coberturas:
            CoverageInPolicy.objects.create(policy = poliza, owner = poliza.owner, org_name = poliza.org_name, **cobertura)


        # for file in files:
        #     PolizasFile.objects.create(owner = poliza,**file)        

        return poliza


# ___________________________________________________________________ Category


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    # files = CreatePolizasFileSerializer(many = True)
    document_type = serializers.IntegerField()
    class Meta:
        model = Polizas
        fields = ('id', 'observations', 'name', 'parent', 'hospital_level', 'document_type', 'caratula','sucursal',
                  'collection_executive','deductible','comision_derecho_percent','comision_rpf_percent')

        # 'files'

    def create(self, validated_data): 
        # files = validated_data.pop('files')
        poliza = Polizas.objects.create(**validated_data)

        # for file in files:
        #     PolizasFile.objects.create(owner = poliza,**file)        

        return poliza


# ___________________________________________________________________


class PolizaHyperReadSerializer(serializers.HyperlinkedModelSerializer):
    contractor = serializers.StringRelatedField(read_only=True)
    # aseguradora = serializers.StringRelatedField(many=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    old_policies = OldPolicyHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = LifeHyperSerializer(many=True, read_only=True)
    owner = serializers.SerializerMethodField()
    
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    # recibos_poliza = ReciboHyperSerializer(many=True, read_only=True)


    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner', 'org_name',
                  'poliza_number', 'contractor', 'aseguradora', 'ramo', 'subramo',
                  'paquete', 'old_policies', 'start_of_validity', 'end_of_validity',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'document_type', 'address','comision_derecho_percent','comision_rpf_percent',
                  'coverageInPolicy_policy', 'created_at', 'updated_at',
                  'clave','f_currency', 'identifier', 'comision',
                  'comision_percent', 'sucursal','collection_executive','emision_date',
                  'scheme', 'accident_rate', 'steps','business_line','contratante_subgroup','caratula')

class PolicyCleanHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Polizas
        exclude = ()

class CertificadoSerializer(serializers.ModelSerializer):
    aseguradora=serializers.SerializerMethodField()
    poliza_number=serializers.SerializerMethodField()
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='package_name')
    life_policy = LifeGetHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    contractor = serializers.SerializerMethodField()

    def get_contractor(self, obj):
        if obj.caratula:
            caratula = Polizas.objects.get(id = obj.caratula)
            return caratula.contractor.full_name
        else: 
            return 'Sin Contratante'
                


    def get_poliza_number(self, obj):
        try:
            return Polizas.objects.get(id = obj.caratula).poliza_number
        except:
            return obj.poliza_number

    def get_aseguradora(self, obj):
        if obj.parent and obj.parent.parent and obj.parent.parent.parent:
            if obj.parent.parent.parent.aseguradora:
                return obj.parent.parent.parent.aseguradora.alias
            elif obj.parent.parent.aseguradora:
                return obj.parent.parent.aseguradora.alias
            elif obj.parent.aseguradora:
                return obj.parent.aseguradora.alias
            elif obj.aseguradora:
                return obj.aseguradora.alias
            else:
                return 'Caratula sin aseguradora'
        else:
            return 'Caratula sin aseguradora'

    class Meta:
        model = Polizas
        fields = ('id', 'internal_number', 'folio', 'url','poliza_number', 'contacto', 'fecha_baja_inciso',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'start_of_validity', 'end_of_validity', 'forma_de_pago',
                  'status', 'is_renewable','emision_date',
                  'address', 'caratula', 'parent', 'certificate_number',
                  'clave','f_currency', 'identifier', 'responsable','certificado_inciso_activo',
                  'derecho','rpf','p_neta', 'iva', 'comision', 'descuento', 'give_comision', 'sub_total',
                  'comision_percent','rec_antiguedad','sucursal','collection_executive','hospital_level',
                  'certificado_inciso_activo', 'scheme', 'accident_rate', 'steps','business_line','contratante_subgroup', 'celula', 
                  'groupinglevel', 'contractor', 'conducto_de_pago' , 'tabulator', "life_policy", "automobiles_policy", "damages_policy", 
                  'accidents_policy','charge_date','document_type','comision_derecho_percent','comision_rpf_percent')




class PolizaSerializer(serializers.ModelSerializer): 
    automobiles_policy = CreateAutomobileSerializer(many = True)
    damages_policy = CreateDamageSerializer(many = True)
    accidents_policy = CreateAccidentsSerializer(many = True)
    life_policy = CreateLifeSerializer(many = True)
    recibos_poliza = CreateReciboSerializer(many = True)
    coverageInPolicy_policy = CreateCoverageInPolicySerializer(many=True)
    document_type = serializers.IntegerField()
    p_total = serializers.DecimalField(decimal_places=2, max_digits=20)
    # paquete = serializers.StringRelatedField(read_only=True)
    grouping_level = serializers.SerializerMethodField()
    subgrouping_level = serializers.SerializerMethodField()
    subsubgrouping_level = serializers.SerializerMethodField()
    existe_ot_renovacion = serializers.SerializerMethodField()
    def get_existe_ot_renovacion(self, obj):
        val = False
        if OldPolicies.objects.filter(base_policy__id = obj.id, new_policy__status = 1).exists() and obj.is_renewable ==1:
            val = True
        return val

    def get_grouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 1:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.parent.level_grouping,
                'description' : obj.groupinglevel.parent.parent.description,
                'type_grouping' : obj.groupinglevel.parent.parent.type_grouping,
                'id' : obj.groupinglevel.parent.parent.id
            }
        else :
            return None
    def get_subgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        else :
            return None

    def get_subsubgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        else :
            return None
    
    class Meta:
        model = Polizas
        fields = ('id', 'internal_number', 'folio', 'url','poliza_number', 'contacto', 'fecha_baja_inciso',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 
                  'recibos_poliza', 'automobiles_policy', 'damages_policy', 'accidents_policy', 'is_renewable','emision_date',
                  'life_policy', 'document_type', 'address', 'caratula', 'parent', 'certificate_number',
                  'coverageInPolicy_policy', 'clave','f_currency', 'identifier', 'responsable','certificado_inciso_activo',
                  'p_total','derecho','rpf','p_neta', 'iva', 'comision', 'descuento', 'give_comision', 'sub_total','from_pdf',
                  'comision_percent','rec_antiguedad','sucursal','collection_executive','hospital_level','renewed_status','existe_ot_renovacion',
                  'certificado_inciso_activo', 'scheme', 'accident_rate', 'steps','business_line','contratante_subgroup', 'celula', 
                  'groupinglevel', 'grouping_level', 'subgrouping_level', 'subsubgrouping_level', 'contractor', 'conducto_de_pago' , 'tabulator',
                  'date_cancel','state_circulation','from_task','task_associated','comision_derecho_percent','comision_rpf_percent','cotizacion_asociada')

    def create(self, validated_data):
        recibos = validated_data.pop('recibos_poliza')
        coberturas = validated_data.pop('coverageInPolicy_policy')
        accident_form = validated_data.pop('accidents_policy')
        car_form = validated_data.pop('automobiles_policy')
        life_form = validated_data.pop('life_policy')
        damages_form = validated_data.pop('damages_policy')

        poliza = Polizas.objects.create(**validated_data)
        
        if car_form:
            for car in car_form:
                car_email = car.pop('email')
                AutomobilesDamages.objects.create( email = car_email, policy = poliza, owner = poliza.owner, org_name = poliza.org_name,**car)
        
        elif damages_form:
            for damage in damages_form:
                Damages.objects.create(policy = poliza, owner = poliza.owner, org_name = poliza.org_name,**damage)
        
        elif accident_form:
            for accident in accident_form:
                personal = accident.pop('personal')
                relationships = accident.pop('relationship_accident')
                personal_information = Personal_Information.objects.create(owner = poliza.owner, org_name = poliza.org_name, **personal)
                personal_information.full_name = str(personal_information.first_name) + ' ' + str(personal_information.last_name) + ' ' + str(personal_information.second_last_name)
                personal_information.save()
                
                accident_instance = AccidentsDiseases.objects.create(personal = personal_information, policy = poliza, owner = poliza.owner, org_name = poliza.org_name,**accident)
                for relationship in relationships:
                    relationship_instance = Relationship.objects.create(accident = accident_instance, owner = poliza.owner, org_name = poliza.org_name, **relationship)
                    relationship_instance.full_name = str(relationship_instance.first_name) + ' ' + str(relationship_instance.last_name) + ' ' + str(relationship_instance.second_last_name)
                    relationship_instance.save()

        elif life_form:
            for life in life_form:
                personal = life.pop('personal')
                beneficiaries = life.pop('beneficiaries_life')
                personal_information = Personal_Information.objects.create(owner = poliza.owner, org_name = poliza.org_name,policy=poliza, **personal)
                personal_information.full_name = (personal_information.first_name + ' ' + personal_information.last_name + ' ' + (personal_information.second_last_name  if personal_information.second_last_name else '')).strip()   
                personal_information.save()
                life_instance = Life.objects.create(personal = personal_information, policy = poliza, owner = poliza.owner, org_name = poliza.org_name,**life)
                for beneficiarie in beneficiaries:
                    beneficiarie_instance = Beneficiaries.objects.create(life = life_instance, owner = poliza.owner, org_name = poliza.org_name, **beneficiarie)
                    beneficiarie_instance.full_name = str(beneficiarie_instance.first_name) + ' ' + str(beneficiarie_instance.last_name) + ' ' + str(beneficiarie_instance.second_last_name)
                    beneficiarie_instance.save()

        for cobertura in coberturas:
            CoverageInPolicy.objects.create(policy = poliza, owner = poliza.owner, org_name = poliza.org_name, **cobertura)

        for recibo in recibos:
            recibo = Recibos.objects.create(poliza = poliza, owner = poliza.owner, org_name = poliza.org_name, **recibo)
            recibo.save()

        
      
        return poliza

    def validate(self, attrs):
        ramo = attrs.get('ramo') or getattr(self.instance, 'ramo', None)
        subramo = attrs.get('subramo') or getattr(self.instance, 'subramo', None)
        if not ramo:
            raise serializers.ValidationError({'ramo': 'El ramo es obligatorio.'})
        if not subramo:
            raise serializers.ValidationError({'subramo': 'El subramo es obligatorio.'})
        return attrs

class PolizaHyperReadResumeSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    # old_policies = OldPolicyHyperSerializer(many=True, read_only=True)
    # old_policies = HistoricoPolicySerializer(many = True,read_only = True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    antiguedad = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.created_at
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number',
        'aseguradora', 'ramo', 'subramo','paquete','observations', 'antiguedad',
        'forma_de_pago', 'status', 'created_at','owner','org_name','document_type','comision_derecho_percent','comision_rpf_percent',
        'coverageInPolicy_policy','start_of_validity','end_of_validity','f_currency', 'clave',
        'p_total','derecho','rpf','p_neta', 'iva', 'descuento','sucursal','collection_executive','emision_date',
        'scheme', 'accident_rate', 'steps','business_line','contratante_subgroup','contractor','from_task','task_associated')

class PolizaResumeGraphicSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorsResumeSerializer(many=False, read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    owner = serializers.SerializerMethodField()
    antiguedad = serializers.SerializerMethodField()
    # old_policies = HistoricoPolicySerializer(many = True,read_only = True)
    
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.created_at
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number','comision_derecho_percent','comision_rpf_percent',
            'aseguradora', 'ramo', 'subramo', 'status', 'created_at','owner','org_name','document_type','owner',
            'antiguedad','sucursal','collection_executive','emision_date','business_line','contratante_subgroup','contractor','from_task','task_associated')


class ExcelPolizaResumeGraphicSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    contractor = ContractorsResumeSerializer(many=False, read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    old_policies = OldPolicyHyperSerializer(many=True, read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)

    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number','contractor', 'aseguradora', 'ramo', 'subramo','paquete','observations',
        'forma_de_pago', 'status', 'created_at','owner','org_name','document_type','old_policies',
        'coverageInPolicy_policy','start_of_validity','end_of_validity','f_currency', 'descuento',
        'clave','p_total','derecho','rpf','p_neta', 'iva','accidents_policy','comision_derecho_percent','comision_rpf_percent',
        'automobiles_policy','life_policy','damages_policy','sucursal','collection_executive','from_task','task_associated')
    def to_representation(self, instance):
        data = super(ExcelPolizaResumeGraphicSerializer, self).to_representation(instance)

        if instance.forma_de_pago == 12:
            instance.forma_de_pago = "Anual"
        elif instance.forma_de_pago == 1:
            instance.forma_de_pago = "Mensual"
        elif instance.forma_de_pago == 2:
            instance.forma_de_pago = "Bimestral"
        elif instance.forma_de_pago == 3:
            instance.forma_de_pago = "Trimestral"
        elif instance.forma_de_pago == 4:
            instance.forma_de_pago = "Cuatrimestral"
        elif instance.forma_de_pago == 5:
            instance.forma_de_pago = "Contado"
        elif instance.forma_de_pago == 6:
            instance.forma_de_pago = "Semestral"

        if instance.status == 1:
            status = "OT Pendiente"
        elif instance.status == 2:
            status = "OT Cancelada"
        elif instance.status == 4:
            status = "Precancelada"
        elif instance.status == 10:
            status = "Por iniciar"
        elif instance.status == 11:
            status = "Cancelada"
        elif instance.status == 12:
            status = "Cerrada"
        elif instance.status == 13:
            status = "Vencida"
        elif instance.status == 14:
            status = "Vigente"

        if instance.f_currency == 1:
            instance.f_currency = "PESOS"
        elif instance.f_currency == 2:
            instance.f_currency = "DOLARES"

        if instance.contractor:       
           data['CONTRATANTE'] =str(instance.contractor)
           if instance.contractor.email:
                data['CORREO ELECTRÓNICO'] =str(instance.contractor.email) 

        data['No.PÓLIZA'] = instance.poliza_number
 
        data['ASEGURADORA'] =str(instance.aseguradora)
      
        if instance.ramo:
            data['RAMO'] = str(instance.ramo)
        else:
            data['RAMO'] = ""

        if instance.subramo:
            data['SUBRAMO'] = str(instance.subramo)
        else:
            data['SUBRAMO'] = ""

        if instance.paquete:
            data['PAQUETE'] = str(instance.paquete)
        else:
            data['PAQUETE'] = ""

        try:
            if instance.accidents_policy:
                data['ASEGURADO'] = instance.accidents_policy.personal.full_name
            elif instance.life_policy:
                data['ASEGURADO'] = instance.life_policy.personal.full_name
            elif instance.automobiles_policy:
                data['ASEGURADO'] = instance.automobiles_policy.serial
            else:
                data['ASEGURADO'] = 'No aplica'
        except :
            pass

        if instance.status != 1 or instance.status != 2 or instance.document_type != 3:
            if instance.p_neta:
                data['PRIMA NETA'] = str('${:,.2f}'.format(float(instance.p_neta)))
            else:
                data['PRIMA NETA'] = str('${:,.2f}'.format(float(0)))

            if instance.rpf:
                data['RPF'] = str('${:,.2f}'.format(float(instance.rpf)))
            else:
                data['RPF'] = str('${:,.2f}'.format(float(0)))

            if instance.derecho:
                data['DERECHO'] = str('${:,.2f}'.format(float(instance.derecho)))
            else:
                data['DERECHO'] = str('${:,.2f}'.format(float(0)))

            if instance.iva and instance.p_neta:
                data['IVA'] = str('${:,.2f}'.format(float(instance.iva)))
            else:
                data['IVA'] = str('${:,.2f}'.format(float(0)))

            if instance.p_total:
                data['PRIMA TOTAL'] = str('${:,.2f}'.format(float(instance.p_total)))
            else:
                data['PRIMA TOTAL'] = str('${:,.2f}'.format(float(0)))

            if instance.comision:
                data['COMISIÓN'] = str('${:,.2f}'.format(float(instance.comision)))
            else:
                data['COMISIÓN'] = str('${:,.2f}'.format(float(0)))

        data ['FRECUENCIA DE PAGO'] = instance.forma_de_pago
        
        if instance.document_type == 1:       
           data['TIPO'] = "Póliza"
        elif instance.document_type == 2:
            data['TIPO']= "Endoso"
        elif instance.document_type == 3:
            data['TIPO']= "Caratula" 
        elif instance.document_type ==6:
            data ['TIPO'] = 'Certificado'
        elif instance.document_type == 5:
            data['TIPO'] = 'Categoría'
        elif instance.document_type == 4:
            data['TIPO'] = 'SUBGRUPO'
        else:
            data['TIPO'] = 'OT'
        data['ESTATUS'] = status
        data['VIGENCIA'] = instance.start_of_validity.strftime("%d/%m/%Y") + ' - ' + instance.end_of_validity.strftime("%d/%m/%Y")

        if instance.folio:
            data ['FOLIO'] = instance.folio 
        else:
            data ['FOLIO'] = "" 
        data ['FOLIO INTERNO'] = instance.internal_number 
        data ['MONEDA'] = instance.f_currency 
        if instance.observations:
            data ['OBSERVACIONES'] = str(instance.observations )  
        else:
            data ['OBSERVACIONES'] = 'N / O'         
        data['CLAVE DE AGENTE'] = str(instance.clave.clave) + str(instance.clave.name)
        data['CREADO POR'] =  instance.owner.first_name + " "+instance.owner.last_name 

        del data['url']
        del data['id']
        del data['owner']
        del data['poliza_number']
        del data['contractor']
        del data['document_type']
        del data ['coverageInPolicy_policy']
        del data ['automobiles_policy']
        del data ['accidents_policy']
        del data ['life_policy']
        del data ['damages_policy']
        del data['observations']
        del data['org_name']
        del data ['end_of_validity']
        del data ['old_policies']
        del data ['clave']
        del data['aseguradora']
        del data['ramo']
        del data['subramo']
        del data['f_currency']
        del data['p_total']
        del data['derecho']
        del data['rpf']
        del data['p_neta']
        del data['iva']
        del data['status']
        del data['descuento']
        del data['created_at']
        del data['internal_number']
        del data['folio']
        del data['paquete']
        del data['start_of_validity']
        del data['forma_de_pago']

        return data

# +++++++++++++++++++++++++++++++++++++++
class PolizaResumeInfoSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()
    collection_executive = VendorSerializer(many=False, read_only=True)
    responsable = VendorSerializer(many=False, read_only=True)
    ramo = serializers.StringRelatedField(read_only=True)
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo = serializers.StringRelatedField(read_only=True)
    recibos_poliza = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    antiguedad = serializers.SerializerMethodField()
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    address = AddressSerializer(read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    ref_policy = RefInvolvedInfoSerializer(many = True, read_only = True)  
    # old_policies = HistoricoPolicySerializer(many = True,read_only = True)

    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.start_of_validity
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    class Meta:
        model = Polizas
        fields = ('url', 'id','owner' , 'caratula', 'poliza_number', 'document_type', 'end_of_validity', 'clave', 'automobiles_policy',
        'aseguradora', 'ramo', 'subramo','recibos_poliza','poliza_number', 'comision', 'life_policy','receipts_by',
        'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento', 'damages_policy','sucursal',
        'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago', 'antiguedad', 'accidents_policy','address',
        'identifier', 'parent','collection_executive','responsable','ref_policy','is_renewable','emision_date','comision_derecho_percent','comision_rpf_percent',
        'scheme', 'accident_rate', 'steps','business_line','contratante_subgroup','contractor','comision_percent','state_circulation',
        'contributory','rfc_cve','rfc_homocve','dom_callenum','dom_colonia','dom_cp','dom_poblacion','dom_estado','from_task','task_associated')

class PolizaCaratulaResumeInfoSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()
    collection_executive = VendorSerializer(many=False, read_only=True)
    responsable = VendorSerializer(many=False, read_only=True)
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    aseguradora = ProviderMiniSerializer(many = False, read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    ramo = RamosResumeCleanHyperSerializer(many=False,read_only=True)
    paquete = PackageResumeSerializer(many=False,read_only=True)
    antiguedad = serializers.SerializerMethodField()
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    address = AddressSerializer(read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    ref_policy = RefInvolvedInfoSerializer(many = True, read_only = True)  
    old_policies = HistoricoPolicySerializer(many = True,read_only = True)    
    recibos_poliza =  serializers.SerializerMethodField('get_receipts')
    grouping_level = serializers.SerializerMethodField()
    subgrouping_level = serializers.SerializerMethodField()
    subsubgrouping_level = serializers.SerializerMethodField()
    recordatorios = serializers.SerializerMethodField()
    statuslabel = serializers.SerializerMethodField()
    def get_recordatorios(self, obj):        
        if obj:
            recs = RegistroDeRecordatorio.objects.filter(recordatorio__tipo=3,record_model=1,record_id= obj.id, org_name=obj.org_name)
            serializer = RegistroDeRecordatorioSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        else:
            return []
    def get_grouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 1:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping if obj.groupinglevel.parent else 2,
                'description' : obj.groupinglevel.parent.description if obj.groupinglevel.parent else 2,
                'type_grouping' : obj.groupinglevel.parent.type_grouping if obj.groupinglevel.parent else 2,
                'id' : obj.groupinglevel.parent.id if obj.groupinglevel.parent else 3
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.parent.level_grouping if obj.groupinglevel.parent and obj.groupinglevel.parent.parent else 3,
                'description' : obj.groupinglevel.parent.parent.description if obj.groupinglevel.parent and obj.groupinglevel.parent.parent else 3,
                'type_grouping' : obj.groupinglevel.parent.parent.type_grouping if obj.groupinglevel.parent and obj.groupinglevel.parent.parent else 3,
                'id' : obj.groupinglevel.parent.parent.id if obj.groupinglevel.parent else 3
            }
        else :
            return None
    def get_subgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping if obj.groupinglevel.parent else 3,
                'description' : obj.groupinglevel.parent.description if obj.groupinglevel.parent else 3,
                'type_grouping' : obj.groupinglevel.parent.type_grouping if obj.groupinglevel.parent else 3,
                'id' : obj.groupinglevel.parent.id if obj.groupinglevel.parent else 3
            }
        else :
            return None

    def get_subsubgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping if obj.groupinglevel else 3,
                'description' : obj.groupinglevel.description if obj.groupinglevel else 3,
                'type_grouping' : obj.groupinglevel.type_grouping if obj.groupinglevel else 3,
                'id' : obj.groupinglevel.id
            }
        else :
            return None
    

    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id).exclude(status =0)
        serializer = ReciboFlotillaSerializer(instance = queryset,context={'request':self.context.get("request")}, many = True)
        return serializer.data
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.start_of_validity
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_owner(self,obj):
        owner=''
        if obj.owner:
            owner = obj.owner.first_name + ' ' + obj.owner.last_name
        return owner

    def get_statuslabel(self,obj):
        owner = obj.get_status_display()
        return owner
    class Meta:
        model = Polizas
        fields = ('url', 'id','owner' , 'caratula', 'poliza_number', 'document_type', 'end_of_validity', 'clave', 'automobiles_policy',
        'aseguradora', 'ramo', 'subramo','recibos_poliza','poliza_number', 'comision', 'life_policy','receipts_by','from_pdf',
        'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento', 'damages_policy','sucursal','comision_derecho_percent','comision_rpf_percent',
        'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago', 'antiguedad', 'accidents_policy','address',
        'identifier', 'parent','collection_executive','responsable','ref_policy','old_policies','is_renewable','emision_date',
        'scheme', 'accident_rate', 'steps','business_line','contratante_subgroup','observations','sub_total','type_policy', 'celula', 'groupinglevel', 
        'grouping_level', 'subgrouping_level', 'subsubgrouping_level','contractor', 'reason_ren', 'conducto_de_pago','date_cancel','reason_cancel','migrated',
        'comision_percent','state_circulation', 'reason_rehabilitate','org_name','recordatorios','renewed_status','updated_at','from_task','task_associated','statuslabel')



# BigBot Endpoint Methods

class DateSerializer(serializers.Serializer):
    fecha_inicio = serializers.DateField(input_formats=['%d/%m/%Y'])
    fecha_fin = serializers.DateField(input_formats=['%d/%m/%Y'])
    
    
class BigBotRecibosSerializer(serializers.HyperlinkedModelSerializer):
    status_display = serializers.SerializerMethodField(read_only = True)
    
    poliza = serializers.SerializerMethodField(read_only = True)
    endoso = serializers.SerializerMethodField(read_only = True)
    
    def get_status_display(self,obj):
        return obj.get_status_display()

    def get_poliza(self,obj):
        return obj.poliza.poliza_number if obj.poliza else ""

    def get_endoso(self,obj):
        return obj.endorsement.number_endorsement if obj.endorsement else ""

    class Meta:
        model = Recibos
        fields = ('id', 'recibo_numero', 'fecha_inicio','fecha_fin', 'prima_neta',
                  'status_display', 'status', 'created_at', 'prima_neta', 'endoso', 'poliza')


class PolizasBigBotSerializer(serializers.HyperlinkedModelSerializer):
    recibos_poliza = BigBotRecibosSerializer(read_only = True, many = True)
    
    class Meta:
        model = Polizas
        fields = ('id', 'poliza_number','p_total', 'comision', 'recibos_poliza',
                  'created_at')
    
    
class PolizaResumeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()
    ramo = serializers.StringRelatedField(read_only=True)
    contractor = ContractorInfoSerializer(read_only = True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo = serializers.StringRelatedField(read_only=True)
    recibos_poliza = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)    
    # old_policies = HistoricoPolicySerializer(many = True,read_only = True)
    antiguedad = serializers.SerializerMethodField()
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    sucursal = SucursalFullSerializer(read_only = True)
    fianza_type = FianzaTypeHyperSerializer(read_only = True, many = False)
    conducto_de_pago = serializers.SerializerMethodField()
    existe_ot_renovacion = serializers.SerializerMethodField()
    def get_existe_ot_renovacion(self, obj):
        val = False
        if OldPolicies.objects.filter(base_policy__id = obj.id, new_policy__status = 1).exists() and obj.is_renewable ==1:
            val = True
        return val
    def get_conducto_de_pago(self, obj):
        return obj.get_conducto_de_pago_display()
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        try:
            aux_date = obj.start_of_validity
            b = arrow.get(aux_date)
            antiguedad = (a-b).days
            antiguedad = int(antiguedad)+1
            return antiguedad
        except:
            return 0

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    class Meta:
        model = Polizas
        fields = ('url', 'id','owner' , 'caratula', 'poliza_number', 'document_type', 'end_of_validity', 'clave', 'automobiles_policy',
        'aseguradora', 'ramo', 'subramo','recibos_poliza','poliza_number', 'comision', 'life_policy','receipts_by',
        'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento', 'damages_policy','sucursal',
        'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago', 'antiguedad', 'accidents_policy',
        'identifier', 'parent','collection_executive','ref_policy','certificado_inciso_activo','sucursal','renewed_status','existe_ot_renovacion','org_name','is_renewable',
        'scheme', 'accident_rate', 'steps','emision_date','fianza_type','business_line','contratante_subgroup','contractor',
        'date_cancel','reason_cancel','conducto_de_pago','from_task','task_associated','comision_derecho_percent','comision_rpf_percent')

class PolizaColectivaResumeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()
    ramo = serializers.PrimaryKeyRelatedField( read_only=True)
    contractor = ContractorInfoSerializer(read_only = True)
    aseguradora = serializers.PrimaryKeyRelatedField( read_only=True)
    subramo = serializers.PrimaryKeyRelatedField( read_only=True)
    recibos_poliza = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)    
    old_policies = HistoricoPolicySerializer(many = True,read_only = True)
    antiguedad = serializers.SerializerMethodField()
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    sucursal = SucursalFullSerializer(read_only = True)
    fianza_type = FianzaTypeHyperSerializer(read_only = True, many = False)

    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.start_of_validity
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_owner(self,obj):
        owner = obj.owner.first_name + ' ' + obj.owner.last_name
        return owner

    class Meta:
        model = Polizas
        fields = ('url', 'id','owner' , 'caratula', 'poliza_number', 'document_type', 'end_of_validity', 'clave', 'automobiles_policy',
         'aseguradora', 'ramo', 'subramo','recibos_poliza','poliza_number', 'comision', 'life_policy','receipts_by',
        'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento', 'damages_policy','sucursal',
        'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago', 'antiguedad', 'accidents_policy','old_policies',
        'identifier', 'parent','collection_executive','ref_policy','certificado_inciso_activo','sucursal','comision_derecho_percent','comision_rpf_percent',
        'scheme', 'accident_rate', 'steps','emision_date','fianza_type','business_line','contractor','from_task','task_associated')

class PolizaMinimalizeSerializerExcel(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()
    ramo = serializers.StringRelatedField(read_only=True)
    contractor = serializers.StringRelatedField(read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo = serializers.StringRelatedField(read_only=True)

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    class Meta:
        model = Polizas
        fields = ('url', 'id','owner' ,'poliza_number', 'contractor', 'document_type', 'end_of_validity', 'clave', 'automobiles_policy',
        'aseguradora', 'ramo', 'subramo','recibos_poliza','poliza_number', 'comision', 'life_policy','sucursal',
        'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento', 'damages_policy','comision_derecho_percent','comision_rpf_percent',
        'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago', 'accidents_policy',
        'collection_executive','emision_date','business_line','contratante_subgroup','from_task','task_associated')
# ----REPORTE
class PolizaResumeSerializerExcel(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()
    ramo = serializers.StringRelatedField(read_only=True)
    contractor = serializers.StringRelatedField(read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo = serializers.StringRelatedField(read_only=True)
    recibos_poliza = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    # antiguedad = serializers.SerializerMethodField()
    clave = serializers.ReadOnlyField(source='clave.clave')
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)

    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.created_at
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    class Meta:
        model = Polizas
        fields = ('url', 'id','owner' ,'poliza_number', 'contractor', 'document_type', 'end_of_validity', 'clave', 'automobiles_policy',
        'aseguradora', 'ramo', 'subramo','recibos_poliza','poliza_number', 'comision', 'life_policy','sucursal',
        'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento', 'damages_policy','comision_derecho_percent','comision_rpf_percent',
        'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago', 'accidents_policy',
        'collection_executive','emision_date','business_line','contratante_subgroup','from_task','task_associated')

    def to_representation(self, instance):

        if instance.forma_de_pago == 12:
            instance.forma_de_pago = "Anual"
        elif instance.forma_de_pago == 1:
            instance.forma_de_pago = "Mensual"
        elif instance.forma_de_pago == 2:
            instance.forma_de_pago = "Bimestral"
        elif instance.forma_de_pago == 3:
            instance.forma_de_pago = "Trimestral"
        elif instance.forma_de_pago == 4:
            instance.forma_de_pago = "Cuatrimestral"
        elif instance.forma_de_pago == 5:
            instance.forma_de_pago = "Contado"
        elif instance.forma_de_pago == 6:
            instance.forma_de_pago = "Semestral"

        if instance.status == 1:
            instance.status = "OT Pendiente"
        elif instance.status == 2:
            instance.status = "OT Cancelada"
        elif instance.status == 4:
            instance.status = "Precancelada"
        elif instance.status == 10:
            instance.status = "Por iniciar"
        elif instance.status == 11:
            instance.status = "Cancelada"
        elif instance.status == 12:
            instance.status = "Cerrada"
        elif instance.status == 13:
            instance.status = "Vencida"
        elif instance.status == 14:
            instance.status = "Vigente"

        if instance.f_currency == 1:
            instance.f_currency = "PESOS"
        elif instance.f_currency == 2:
            instance.f_currency = "DOLARES"

        data = super(PolizaResumeSerializerExcel, self).to_representation(instance)

        DICT_POL = [ (0,''),(1,'NO.PÓLIZA'), (2, 'TIPO'), (3, 'CONTRATANTE'), (4,'ASEGURADORA'),
                     (5, 'RAMO'), (6,'SUBRAMO'), (7, 'PAQUETE'), (8,'FRECUENCIA PAGO'),(9,'ESTATUS PÓLIZA'),
                     (10,'VIGENCIA'),(11,'FOLIO'),(12,'MONEDA'),(13,'PRIMA NETA'),(14,'RPF'),(15,'DERECHO'),
                     (16,'IVA'),(17,'PRIMA TOTAL'),(18,'COMISIÓN'),(19,'OBSERVACIONES'),(20,'CREADO POR'),(21,'CLAVE AGENTE'),(22,'ASEGURADO/SERIE'),(23,'FECHA CREACIÓN') ]
        
        array = self.context['request'].data['orden']

        try:
            instance.p_total= '{:,.2f}'.format(instance.p_total)
            instance.p_neta= '{:,.2f}'.format(instance.p_neta)
            instance.derecho= '{:,.2f}'.format(instance.derecho)
            instance.iva= '{:,.2f}'.format(instance.iva)
            instance.rpf= '{:,.2f}'.format(instance.rpf)
            instance.comision= '{:,.2f}'.format(instance.comision)
        except Exception as e:
            with open(os.path.join(settings.MEDIA_ROOT, 'reporte_pol.txt'), 'w') as f:
                f.write(str(e))

       
        if instance.contractor:       
           contratante =str(instance.contractor)  

        if instance.document_type == 1:       
           instance.document_type= "Poliza"
        elif instance.document_type == 2:
            instance.document_type= "Endoso"
        elif instance.document_type == 3:
            instance.document_type= "Caratula"

        asegurado = ''
        try:
            if data['accidents_policy']:
                asegurado = data['accidents_policy'][0]['personal']['full_name']
            elif data['life_policy']:
                asegurado = data['life_policy'][0]['personal']['full_name']
            elif data['automobiles_policy']:
                asegurado = data['automobiles_policy'][0]['serial'] + ' - ' + data['automobiles_policy'][0]['brand'] + ' - ' + data['automobiles_policy'][0]['model']
            else:
                asegurado = 'No aplica'
        except Exception as e:
            asegurado = ''


        a = instance.poliza_number 
        b = instance.document_type
        c = contratante
        d =str(instance.aseguradora)
        e =str(instance.ramo)
        f = str(instance.subramo)
        g = str(instance.paquete)
        h = instance.forma_de_pago
        i = instance.status
        j = (instance.start_of_validity.strftime("%d/%m/%y"))+' - '+(instance.end_of_validity.strftime("%d/%m/%y"))
        k = instance.folio
        l = instance.f_currency
        m = instance.p_neta
        n = instance.rpf
        o = instance.derecho
        p = instance.iva
        q = instance.p_total
        r = instance.comision
        s = instance.observations   
        t =  str(instance.owner.first_name + ' ' + instance.owner.last_name)
        u = str(instance.clave.clave) + '-' + str(instance.clave.name)
        v = str(asegurado)
        w = (instance.created_at.strftime("%d/%m/%y"))

        DICT_POL_data = [ (0,a),(1, a), (2, b), (3, c),(4,d),
                     (5, e), (6,f), (7,g), (8,h),(9,i),
                     (10,j ),(11,k),(12,l),(13,m),(14,n),(15,o),
                     (16,p),(17,q),(18,r),(19,s),(20,t),(21,u),(22,v),(23,w) ]

        columnArray = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23];
        try:
            for i in columnArray:
                pol_data = str(DICT_POL_data[array[i]]).split(',')
                if len (pol_data) == 3:
                    ox = pol_data[1]+','+pol_data[2]
                    ul = ox.replace("'","") 
                    pol_d = ul.replace(")","")
                else:
                    oh = pol_data[1].replace(",","")
                    ul = oh.replace("'","") 
                    pol_d = ul.replace(")","")

                pol_title = str(DICT_POL[array[i]]).split(',')
                ds = pol_title[1].replace(",","")
                ff = ds.replace("'","") 
                pol_t = ff.replace(")","")
                # pol_d = pol_d.replace(" ", "")
                data[str(pol_t)] = str(pol_d)
                
        except Exception as e:
            pass        

        del data['url']
        del data['id']
        del data['owner']
        del data['poliza_number']
        del data['contractor']
        del data['document_type']
        del data['automobiles_policy']
        del data['comision']
        del data ['life_policy']
        del data['damages_policy']
        # del data['antiguedad']
        del data ['end_of_validity']
        del data ['clave']
        del data ['accidents_policy']
        del data['aseguradora']
        del data['ramo']
        del data['subramo']
        del data['recibos_poliza']
        del data['f_currency']
        del data['p_total']
        del data['derecho']
        del data['rpf']
        del data['p_neta']
        del data['iva']
        del data['status']
        del data['descuento']
        del data['created_at']
        del data['internal_number']
        del data['folio']
        del data['paquete']
        del data['start_of_validity']
        del data['forma_de_pago']

        return data

# policy filter report
class PolizaFilterReportSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    ramo = serializers.StringRelatedField(read_only=True)
    contractor = serializers.StringRelatedField(read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo = serializers.StringRelatedField(read_only=True)
    recibos_poliza = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    forma_de_pago = serializers.SerializerMethodField()
        

    def get_forma_de_pago(self,obj):
        return obj.get_forma_de_pago_display()
    
    class Meta:
            model = Polizas
            fields = ('url', 'id','owner' ,'poliza_number', 'contractor', 'document_type',
            'aseguradora', 'ramo', 'subramo','recibos_poliza','sucursal','comision_derecho_percent','comision_rpf_percent',
            'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento','from_task','task_associated',
            'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago','collection_executive','emision_date','contratante_subgroup')

    def to_representation(self, instance):

        if instance.forma_de_pago == 12:
            instance.forma_de_pago = "Anual"
        elif instance.forma_de_pago == 1:
            instance.forma_de_pago = "Mensual"
        elif instance.forma_de_pago == 2:
            instance.forma_de_pago = "Bimestral"
        elif instance.forma_de_pago == 3:
            instance.forma_de_pago = "Trimestral"
        elif instance.forma_de_pago == 4:
            instance.forma_de_pago = "Cuatrimestral"
        elif instance.forma_de_pago == 5:
            instance.forma_de_pago = "Contado"
        elif instance.forma_de_pago == 6:
            instance.forma_de_pago = "Semestral"

        if instance.status == 1:
            instance.status = "OT Pendiente"
        elif instance.status == 2:
            instance.status = "OT Cancelada"
        elif instance.status == 4:
            instance.status = "Precancelada"
        elif instance.status == 10:
            instance.status = "Por iniciar"
        elif instance.status == 11:
            instance.status = "Cancelada"
        elif instance.status == 12:
            instance.status = "Cerrada"
        elif instance.status == 13:
            instance.status = "Vencida"
        elif instance.status == 14:
            instance.status = "Vigente"


        data = super(PolizaFilterReportSerializer, self).to_representation(instance)
        if instance.document_type == 1:       
           data['TIPO'] = "Poliza"
        elif instance.document_type == 2:
            data['TIPO']= "Endoso"
        elif instance.document_type == 3:
            data['TIPO']= "Caratula"

        data['No_POLIZA'] = instance.poliza_number
        if instance.contractor:       
           data['CONTRATANTE'] =str(instance.contractor) 
           data['GRUPO'] =str(instance.contractor.group.group_name)   
        data['ASEGURADORA'] =str(instance.aseguradora)
        data['RAMO'] =str(instance.ramo)
        data['SUBRAMO'] = str(instance.subramo)
        data['FORMA PAGO'] = instance.forma_de_pago
        data['ESTATUS'] = instance.status
        try:
            data['VIGENCIA'] = (instance.start_of_validity.strftime("%d/%m/%y")) + ' - ' + (instance.end_of_validity.strftime("%d/%m/%y"))
        except:
            data['VIGENCIA'] = str(instance.start_of_validity )+ ' - ' + str(instance.end_of_validity)
        # data['ANTIGÜEDAD'] = instance.antiguedad
        data['CREACION'] = instance.created_at.strftime("%d/%m/%y")
        data['CREADO POR'] =  str(instance.owner.first_name) + ' ' + str(instance.owner.last_name)

        del data['url']
        del data['id']
        del data['owner']
        del data['poliza_number']
        del data['contractor']
        del data['document_type']
        del data['aseguradora']
        del data['ramo']
        del data['subramo']
        del data['recibos_poliza']
        del data['f_currency']
        del data['p_total']
        del data['derecho']
        del data['rpf']
        del data['p_neta']
        del data['iva']
        del data['status']
        del data['descuento']
        del data['created_at']
        del data['internal_number']
        del data['folio']
        del data['paquete']
        del data['start_of_validity']
        del data['forma_de_pago']

        return data

class EndorsementInfoExcelHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
            model = Endorsement
            fields = ('id', 'url', 'org_name' ,'endorsement_type', 'number_endorsement', 'other_desc', 'migrated',
                'policy', 'status', 'owner','original', 'change' ,'created_at' ,'updated_at' ,
                'end_date','init_date', 'observations', 'internal_number', 'concept',
                'p_neta', 'derecho', 'rpf', 'p_total', 'iva', 'comision', 'endorsement_receipt',
                'comision_percent', 'anuency','insurancefolio','maquila',
                'date_maquila','year_factura','date_bono','bono_variable','date_emision_factura','month_factura','folio_factura') 

# ot filter report
class PolizaFilterOTReportSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    ramo = serializers.StringRelatedField(read_only=True)
    contractor = serializers.StringRelatedField(read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo = serializers.StringRelatedField(read_only=True)
    recibos_poliza = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    forma_de_pago = serializers.SerializerMethodField()
        

    def get_forma_de_pago(self,obj):
        return obj.get_forma_de_pago_display()
    
    class Meta:
            model = Polizas
            fields = ('url', 'id','owner' ,'poliza_number', 'contractor', 'document_type',
            'aseguradora', 'ramo', 'subramo','recibos_poliza','sucursal','comision_derecho_percent','comision_rpf_percent',
            'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento',
            'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago',
            'collection_executive','business_line','from_task','task_associated')

    def to_representation(self, instance):

        if instance.forma_de_pago == 12:
            instance.forma_de_pago = "Anual"
        elif instance.forma_de_pago == 1:
            instance.forma_de_pago = "Mensual"
        elif instance.forma_de_pago == 2:
            instance.forma_de_pago = "Bimestral"
        elif instance.forma_de_pago == 3:
            instance.forma_de_pago = "Trimestral"
        elif instance.forma_de_pago == 4:
            instance.forma_de_pago = "Cuatrimestral"
        elif instance.forma_de_pago == 5:
            instance.forma_de_pago = "Contado"
        elif instance.forma_de_pago == 6:
            instance.forma_de_pago = "Semestral"

        if instance.status == 1:
            instance.status = "OT Pendiente"
        elif instance.status == 2:
            instance.status = "OT Cancelada"
        elif instance.status == 4:
            instance.status = "Precancelada"
        elif instance.status == 10:
            instance.status = "Por iniciar"
        elif instance.status == 11:
            instance.status = "Cancelada"
        elif instance.status == 12:
            instance.status = "Cerrada"
        elif instance.status == 13:
            instance.status = "Vencida"
        elif instance.status == 14:
            instance.status = "Vigente"


        data = super(PolizaFilterOTReportSerializer, self).to_representation(instance)

        data['ORDEN DE TRABAJO'] = instance.internal_number
        if instance.contractor:       
           data['CONTRATANTE'] =str(instance.contractor) 
           data['GRUPO'] =str(instance.contractor.group.group_name) 
        data['ASEGURADORA'] =str(instance.aseguradora)
        if str(instance.paquete) == "None":
            data['PAQUETE'] = 'Sin paquete'
        else:
            data['PAQUETE'] =str(instance.paquete)
        data['SUBRAMO'] = str(instance.subramo)
        data['FORMA PAGO'] = instance.forma_de_pago
        data['ESTATUS'] = instance.status
        data['VIGENCIA'] = (instance.start_of_validity.strftime("%d/%m/%y")) + ' - ' + (instance.end_of_validity.strftime("%d/%m/%y"))
        data['CREADO POR'] =  str(instance.owner.first_name + ' ' + instance.owner.last_name)
        # data['ANTIGÜEDAD'] = instance.antiguedad
        # data['CREACION'] = instance.created_at

        del data['url']
        del data['id']
        del data['owner']
        del data['poliza_number']
        del data['contractor']
        del data['document_type']
        del data['aseguradora']
        del data['ramo']
        del data['subramo']
        del data['recibos_poliza']
        del data['f_currency']
        del data['p_total']
        del data['derecho']
        del data['rpf']
        del data['p_neta']
        del data['iva']
        del data['status']
        del data['descuento']
        del data['created_at']
        del data['internal_number']
        del data['folio']
        del data['paquete']
        del data['start_of_validity']
        del data['forma_de_pago']

        return data


class CollectForEndorsementsSerializer(serializers.HyperlinkedModelSerializer):
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    automobiles_policy = EndosoAutomobileSerializer(many = True)
    damages_policy = CreateDamageSerializer(many = True)
    accidents_policy = EndosoAccidentsSerializer(many = True)
    life_policy = EndosoLifeSerializer(many = True)

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'status','sucursal','status','certificate_number','caratula','contacto',
                    'document_type','receipts_by','p_neta','p_total','comision','comision_percent','comision_derecho_percent','comision_rpf_percent',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy','start_of_validity','end_of_validity','collection_executive',
                  'scheme', 'accident_rate', 'steps','business_line','contractor','org_name','from_task','task_associated')

class CertForEndorsementsSerializer(serializers.HyperlinkedModelSerializer):
    contractor = serializers.StringRelatedField(read_only=True)
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'status','sucursal','status','certificate_number','caratula','contacto',
                    'document_type','identifier','parent','contractor','certificado_inciso_activo','charge_date',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy','start_of_validity','comision_derecho_percent','comision_rpf_percent',
                  'end_of_validity','collection_executive','rec_antiguedad','folio','paquete','contributory','from_task','task_associated')



class SiniestrosSerializer(serializers.HyperlinkedModelSerializer):
   
    class Meta:
        model = Siniestros
        fields =('id', 'url', 'status', 'numero_siniestro','fecha_siniestro',
                'reason', 'fecha_ingreso','aux_affected')

class PolizaForEndorsementsSerializer(serializers.HyperlinkedModelSerializer):
    contractor = serializers.StringRelatedField(read_only=True)    
    recibos_poliza =  serializers.SerializerMethodField('get_receipts')
    endosos_poliza =  serializers.SerializerMethodField()
    siniestros_poliza =  serializers.SerializerMethodField()

    def get_endosos_poliza(self, instance):
        endosos = Endorsement.objects.filter(policy = instance)
        serializer = EndorsementInfoExcelHyperSerializer(instance = endosos, context = {'request':self.context.get("request")}, many=True)
        return serializer.data

    def get_siniestros_poliza(self, instance):
        siniestros = Siniestros.objects.filter(poliza = instance)
        serializer = SiniestrosSerializer(instance = siniestros, context = {'request':self.context.get("request")}, many=True)
        return serializer.data

    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id)
        serializer = ReciboAppSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        return serializer.data

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'status','document_type',
        'sucursal','contractor','start_of_validity','end_of_validity','comision_derecho_percent','comision_rpf_percent',
        'recibos_poliza', 'endosos_poliza', 'siniestros_poliza','from_task','task_associated')

class CollectivityForEndorsementsSerializer(serializers.HyperlinkedModelSerializer):
    contractor = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number', 'status','contractor','from_task','task_associated')


class PolizaResumeRenewSerializer(serializers.HyperlinkedModelSerializer):
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    class Meta:
        model = Polizas
        fields = ('url','id','coverageInPolicy_policy','from_task','task_associated')


class PolizaAppSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='package_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    recibos_poliza = serializers.SlugRelatedField(many=True,read_only=True,slug_field='prima_total')

    class Meta:
        model = Polizas
        fields = ('id', 'poliza_number','end_of_validity','paquete',
            'aseguradora','subramo','ramo','start_of_validity','comision_derecho_percent','comision_rpf_percent',
            'coverageInPolicy_policy','sucursal','collection_executive', 'scheme', 
            'accident_rate', 'steps','emision_date','business_line','contratante_subgroup','contractor','from_task','task_associated')

class PolizaDashSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='package_name')
    contractor =ContractorNameInfoSerializer(many=False, read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    recibos_poliza = serializers.SlugRelatedField(many=True,read_only=True,slug_field='prima_total')
    owner = serializers.SerializerMethodField()
    antiguedad = serializers.SerializerMethodField()

    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.end_of_validity
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad) +1
        return antiguedad

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number','end_of_validity','paquete','status', 'antiguedad',
            'aseguradora','subramo','contractor','ramo','start_of_validity','sucursal','comision_derecho_percent','comision_rpf_percent',
            'forma_de_pago','f_currency', 'status', 'clave', 'coverageInPolicy_policy','recibos_poliza'
            , 'p_neta', 'p_total', 'comision', 'descuento', 'iva', 'derecho', 'rpf','owner','collection_executive',
            'scheme', 'accident_rate', 'steps','business_line','contratante_subgroup','internal_number','document_type','from_task','task_associated')

class PolizaDashGraphicSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='package_name')
    contractor = ContractorsResumeSerializer(many=False, read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    recibos_poliza =  serializers.SerializerMethodField('get_receipts')
    antiguedad = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    renewed_status = serializers.SerializerMethodField()
    existe_ot_renovacion = serializers.SerializerMethodField()
    def get_existe_ot_renovacion(self, obj):
        val = False
        if OldPolicies.objects.filter(base_policy__id = obj.id, new_policy__status = 1).exists() and obj.is_renewable ==1:
            val = True
        return val

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.end_of_validity
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad) +1
        return antiguedad

    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id)
        serializer = ReciboAppSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        return serializer.data

    def get_renewed_status(self, obj):
        try:
            renew_filters = [Q(base_policy = obj), 
                        Q(new_policy = obj)]
            coincidences = OldPolicies.objects.filter(reduce(OR, renew_filters), org_name = obj.org_name,new_policy__status=2)
            coincidences = coincidences.exclude(base_policy__status = 0).exclude(new_policy__status = 0)
            if coincidences:
                return 0
            else:
                return obj.renewed_status
        except:
            return obj.renewed_status
    class Meta:
        model = Polizas
        fields = ('url','id', 'poliza_number','end_of_validity','paquete','status', 'renewed_status', 'track_bitacora',
            'aseguradora','subramo','contractor','ramo','start_of_validity', 'antiguedad','sucursal',
            'forma_de_pago','f_currency', 'status', 'clave', 'coverageInPolicy_policy','recibos_poliza','comision_derecho_percent','comision_rpf_percent',
            'document_type', 'p_neta', 'p_total', 'comision', 'descuento', 'iva', 'derecho', 'rpf','owner',
            'collection_executive','business_line','existe_ot_renovacion','is_renewable','org_name','from_task','task_associated')
        
class PolizaFormsMinSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    contractor = serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    subramo = serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    owner = serializers.SerializerMethodField()
    antiguedad = serializers.SerializerMethodField()
    contratante_sub = serializers.SerializerMethodField()
    def get_contratante_sub(self,obj):
            try:
                if obj.parent:
                    if obj.parent.parent:
                        if obj.parent.parent.contractor:
                            if obj.parent.parent.contractor.full_name:
                                contratante_sub = obj.parent.parent.contractor.full_name
                        elif obj.parent.parent.parent:
                            if obj.parent.parent.parent.contractor:
                                if obj.parent.parent.parent.contractor.full_name:
                                    contratante_sub = obj.parent.parent.parent.contractor.full_name
                            elif obj.parent.parent.parent.parent:
                                if obj.parent.parent.parent.parent.contractor:
                                    if obj.parent.parent.parent.parent.contractor.full_name:
                                        contratante_sub = obj.parent.parent.parent.parent.contractor.full_name
                                else:
                                    contratante_sub = ""
                            else:
                                contratante_sub = ""
                        else:
                            contratante_sub = ""
                    else:
                        contratante_sub = ""

                    return contratante_sub
            except Exception as e:
                contratante_sub = ""
                return contratante_sub 
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.created_at
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    class Meta:
        model = Polizas
        fields = ('url','id','poliza_number', 'subramo', 'aseguradora','contratante_sub',
                    'document_type', 'owner', 'start_of_validity', 'end_of_validity','antiguedad','f_currency','sucursal','collection_executive',
                    'business_line','contractor','from_task','task_associated')
class ReciboHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    endo_aux = serializers.SerializerMethodField()
    serie_manual = serializers.IntegerField(required = False)
    # endorsement = MinEndo(many = False,read_only = True)
    endosotramite = serializers.SerializerMethodField()
    def get_endosotramite(self,obj):
        try:
            poliza_aux = False
            if obj.poliza:
                poliza_aux = Endorsement.objects.filter(policy = obj.poliza, status__in = [1,5], org_name = obj.poliza.org_name).exists()                
            return poliza_aux
        except Exception as e:
            print('.ee',e)
            poliza_aux = ""
            return poliza_aux 
    def get_endo_aux(self, obj):
        if obj.endorsement:
            return obj.endorsement.number_endorsement
        else:
            return ""

    class Meta:
        model = Recibos
        fields = ('id','url', 'owner', 'org_name', 'pay_date', 'endorsement', 'liquidacion_folio', 'excedente', 'track_email',
                 'poliza', 'recibo_numero', 'prima_neta', 'rpf', 'delivered', 'track_bitacora',
                 'derecho', 'iva', 'sub_total', 'prima_total', 'status', 'comision','folio_pago', 'endo_aux', 'track_phone',
                 'fecha_inicio', 'fecha_fin', 'description', 'created_at', 'updated_at','receipt_type', 'rate_exchange',
                 'pay_form','pay_doc','bank', 'isCopy', 'isActive', 'vencimiento', 'comision_conciliada', 'conciliacion_date', 'liquidacion_folio',
                 'conciliacion_observation', 'conciliation_account', 'conciliacion_folio', 'liquidacion_date','endosotramite',
                 'liquidacion_form', 'liquidacion_doc', 'liquidacion_bank', 'liquidacion_curr_rate', 'folio', 'cambiar_comision_al_vendedor',
                 'comision_al_vendedor', 'bono', 'vendedor_cerrado_new','user_pay','user_liq', 'gastos_investigacion', 'conducto_de_pago', 'serie_manual','comision_conciliada_p_estimada')

class PolizaInfoSerializer(serializers.HyperlinkedModelSerializer):
    address = AddressSerializer(read_only = True)
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    contractor = serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')
    aseguradora = MinProviderSerializer(many = False, read_only = True)
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    owner = serializers.SerializerMethodField()
    responsable = VendorSerializer(read_only = True)
    collection_executive = VendorSerializer(read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    # ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    ref_policy = serializers.SerializerMethodField()
    grouping_level = serializers.SerializerMethodField()
    subgrouping_level = serializers.SerializerMethodField()
    subsubgrouping_level = serializers.SerializerMethodField()
    celula_id = serializers.SerializerMethodField()
    conducto_de_pago = serializers.SerializerMethodField()
    recordatorios = serializers.SerializerMethodField()
    paquete_info = serializers.SerializerMethodField()
    receipts_poliza = serializers.SerializerMethodField()
    seguimiento = serializers.SerializerMethodField()  
    renewed_status = serializers.SerializerMethodField()
    existe_ot_renovacion = serializers.SerializerMethodField()
    task_associated_info = serializers.SerializerMethodField()
    nueva = serializers.SerializerMethodField()
    def get_ref_policy(self, obj):
        val = []
        try:
            if ReferenciadoresInvolved.objects.filter(policy = obj, is_changed= False,org_name=obj.org_name).exists():
                rp = ReferenciadoresInvolved.objects.filter(policy = obj, is_changed= False,org_name=obj.org_name)
                serializer = RefInvolvedHyperSerializer(rp, context={'request':self.context.get("request")}, many=True)
                data = serializer.data 
                return data
        except Exception as e:
            val =[]
        return val
    def get_task_associated_info(self, obj):
        val = None
        try:
            if Ticket.objects.filter(id = obj.task_associated, ot_model = 1).exists():
                ticket = Ticket.objects.select_related('owner', 'closedBy', 'assigned', 'reassignBy').prefetch_related(
                    'involved_task',
                ).get(pk=obj.task_associated)  

                serializer = FullInfoTicketHyperSerializer(ticket, context={'request':self.context.get("request")})
                data = serializer.data 
                return data
        except Exception as e:
            val =None
        return val
    def get_existe_ot_renovacion(self, obj):
        val = False
        if OldPolicies.objects.filter(base_policy__id = obj.id, new_policy__status = 1).exists() and obj.is_renewable ==1:
            val = True
        return val
    def get_seguimiento(self,obj):
        tab = ''
        if obj.status ==1:
            tablero =PromotoriaTablero.objects.filter(org_name=obj.org_name,is_active=True)#config
            if tablero:
                confTab = tablero[0].polizas_ots
                try:
                    confTab = json.loads(confTab)
                except Exception as eee:
                    confTab = confTab
                    try:
                        confTab = eval(confTab)
                    except Exception as e:
                        pass
                # for y in confTab['contenedores']:
                for ind,y in enumerate(confTab):
                    for u in y['polizas']:
                        if obj.id in y['polizas']:
                            if u ==obj.id:
                                return y['tablero']
                            else:
                                tab= ''
                        else:
                            tab= ''
            else:
                tab= ''
        else:
            tab= ''
        return tab

    def get_renewed_status(self, obj):
        try:
            renew_filters = [Q(base_policy = obj), 
                        Q(new_policy = obj)]
            coincidences = OldPolicies.objects.filter(reduce(OR, renew_filters), org_name = obj.org_name,new_policy__status=2)
            coincidences = coincidences.exclude(base_policy__status = 0).exclude(new_policy__status = 0)
            if coincidences:
                return 0
            else:
                return obj.renewed_status
        except:
            return obj.renewed_status
    def get_receipts_poliza(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id).exclude(status=0).order_by('fecha_inicio')
        serializer = ReciboHyperSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        return serializer.data
    def get_paquete_info(self,obj): 
        if obj.paquete:      
            pq = Package.objects.get(id= obj.paquete.id, org_name=obj.org_name)
            serializer = PackageResumeSerializer(instance = pq, context={'request':self.context.get("request")}, many = False)
            return serializer.data
        else:
            return []

    def get_recordatorios(self, obj):        
        if obj:
            recs = RegistroDeRecordatorio.objects.filter(recordatorio__tipo =3,record_model=1,record_id= obj.id, org_name=obj.org_name)
            serializer = RegistroDeRecordatorioSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        else:
            return []
    def get_conducto_de_pago(self, obj):
        if obj.conducto_de_pago:
            return obj.get_conducto_de_pago_display()
        else:
            return obj.conducto_de_pago

    def get_celula_id(self, obj):
        if obj.celula:
            return obj.celula.id
        else:
            return None

    def get_grouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 1:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.parent.level_grouping if obj.groupinglevel and obj.groupinglevel.parent else '',
                'description' : obj.groupinglevel.parent.parent.description if obj.groupinglevel and obj.groupinglevel.parent else '',
                'type_grouping' : obj.groupinglevel.parent.parent.type_grouping if obj.groupinglevel and obj.groupinglevel.parent else '',
                'id' : obj.groupinglevel.parent.parent.id if obj.groupinglevel and obj.groupinglevel.parent else ''
            }
        else :
            return None
    def get_subgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping if obj.groupinglevel and obj.groupinglevel.parent else '',
                'description' : obj.groupinglevel.parent.description if obj.groupinglevel and obj.groupinglevel.parent else '',
                'type_grouping' : obj.groupinglevel.parent.type_grouping if obj.groupinglevel and obj.groupinglevel.parent else '',
                'id' : obj.groupinglevel.parent.id if obj.groupinglevel and obj.groupinglevel.parent else ''
            }
        else :
            return None

    def get_subsubgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        else :
            return None

    def get_nueva(self, obj):
        posterior = OldPolicies.objects.filter(base_policy = obj).exclude(new_policy__status=0)
        if posterior.exists():
            posterior = posterior.last()
            try:
                serializer = PolizaBasicSerializer(instance = posterior.new_policy, many = False,context={'request':self.context.get("request")})
                return serializer.data
                # poliza_siguiente = posterior.new_policy
            except Exception as xc:
                poliza_siguiente = ''
        else:
            poliza_siguiente = ''
        return poliza_siguiente
    
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

#    def get_renewed_status(self, obj):
#        return obj.get_renewed_status()


    class Meta:
        model = Polizas
        fields = ('caratula', 'url', 'id', 'internal_number', 'folio', 'poliza_number', 'aseguradora',
            'ramo', 'subramo', 'parent', 'paquete', 'start_of_validity', 'end_of_validity', 'reason_ren', 'reason_cancel',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name', 'is_renewable',
                  'document_type','coverageInPolicy_policy', 'descuento', 'renewed_status','certificate_number',
                  'created_at', 'updated_at', 'f_currency','clave', 'identifier', 'p_total', 'p_neta', 'sub_total',
                  'derecho', 'rpf', 'iva', 'comision', 'responsable', 'give_comision','comision_derecho_percent','comision_rpf_percent',
                  'comision_percent', 'automobiles_policy','damages_policy','ref_policy','existe_ot_renovacion',
                  'accidents_policy','life_policy', 'owner', 'caratula','address','sucursal','collection_executive',
                  'hospital_level','personal_life_policy', 'scheme', 'accident_rate', 'steps','emision_date','business_line',
                    'contratante_subgroup','type_policy', 'celula', 'groupinglevel', 'grouping_level', 'subgrouping_level', 
                    'subsubgrouping_level','celula_id','contractor', 'conducto_de_pago', 'tabulator','date_cancel',
                    'state_circulation', 'reason_rehabilitate','cancelnotas','recordatorios','scraper','from_pdf','nueva',
                    'paquete_info','receipts_poliza','seguimiento','fecha_cancelacion','org_name','created_at','from_task','task_associated','task_associated_info','cotizacion_asociada')

class PolizaIbisSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorNameInfoSerializer(read_only=True)
    address = AddressSerializer(read_only = True)
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    aseguradora = MinProviderSerializer(many = False, read_only = True)
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    owner = serializers.SerializerMethodField()
    responsable = VendorSerializer(read_only = True)
    collection_executive = VendorSerializer(read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)    

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    def get_renewed_status(self, obj):
            return obj.get_renewed_status()

    class Meta:
        model = Polizas
        fields = ('caratula', 'url', 'id', 'internal_number', 'folio', 'poliza_number', 'contractor', 'aseguradora',
            'ramo', 'subramo', 'parent', 'paquete', 'start_of_validity', 'end_of_validity', 'reason_ren', 'reason_cancel',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name', 'is_renewable','org_name',
                  'document_type','coverageInPolicy_policy', 'descuento', 'renewed_status',
                  'created_at', 'updated_at', 'f_currency','clave', 'identifier', 'p_total', 'p_neta',
                  'derecho', 'rpf', 'iva', 'comision', 'responsable', 'give_comision',
                  'comision_percent', 'automobiles_policy','damages_policy','ref_policy','comision_derecho_percent','comision_rpf_percent',
                  'accidents_policy','life_policy', 'owner', 'caratula','address','sucursal',
                  'collection_executive','hospital_level','personal_life_policy','business_line','date_cancel','from_task','task_associated')


class PolizaInfoReferenciadoresSerializer(serializers.HyperlinkedModelSerializer):
    address = AddressSerializer(read_only = True)
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    contractor = serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')
    aseguradora = MinProviderSerializer(many = False, read_only = True)
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    owner = serializers.SerializerMethodField()
    responsable = VendorSerializer(read_only = True)
    collection_executive = VendorSerializer(read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    ref_policy = ReferenciadoresInvolvedHyperSerializer(many=True, read_only=True)
    #renewed_status = serializers.SerializerMethodField()
    
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    
#    def get_renewed_status(self, obj):
#        return obj.get_renewed_status()

    class Meta:
        model = Polizas
        fields = ('caratula', 'url', 'id', 'internal_number', 'folio', 'poliza_number', 'contractor', 'aseguradora',
            'ramo', 'subramo', 'parent', 'paquete', 'start_of_validity', 'end_of_validity', 'reason_ren', 'reason_cancel',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name', 'is_renewable',
                  'document_type','coverageInPolicy_policy', 'descuento', 'renewed_status',
                  'created_at', 'updated_at', 'f_currency','clave', 'identifier', 'p_total', 'p_neta',
                  'derecho', 'rpf', 'iva', 'comision', 'responsable', 'give_comision','comision_derecho_percent','comision_rpf_percent',
                  'comision_percent', 'automobiles_policy','damages_policy','ref_policy',
                  'accidents_policy','life_policy', 'owner', 'caratula','address','sucursal','collection_executive',
                  'hospital_level','personal_life_policy', 'scheme', 'accident_rate', 'steps','business_line','tabulator','date_cancel','from_task','task_associated')

class PolizaFullInfoForPDFSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    recibos_poliza = serializers.SerializerMethodField('get_receipts')
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    address = AddressSerializer(many=False, read_only=True)
    aseguradora = serializers.SerializerMethodField('get_aseguradora_poliza')
    clave = serializers.SerializerMethodField('get_clave_poliza')

    def get_clave_poliza(self,obj):
        if obj.clave:
            serializer = ClavesByProviderHyperSerializer(instance = obj.clave, many = False,context={'request':self.context.get("request")})
            return serializer.data
        else:
            if obj.caratula:
                pol = Polizas.objects.get(pk = obj.caratula)
                serializer = ClavesByProviderHyperSerializer(instance = pol.clave, many = False,context={'request':self.context.get("request")})
                return serializer.data
    def get_aseguradora_poliza(self,obj):
        if obj.aseguradora:
            serializer = ProviderMiniSerializer(instance = obj.aseguradora, many = False,context={'request':self.context.get("request")})
            return serializer.data
        else:
            if obj.caratula:
                pol = Polizas.objects.get(pk = obj.caratula)
                serializer = ProviderMiniSerializer(instance = pol.aseguradora, many = False,context={'request':self.context.get("request")})
                return serializer.data
    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id).exclude(status=0)
        serializer = ReciboAppSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        return serializer.data


    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number', 'aseguradora',
            'ramo', 'subramo', 'parent', 'paquete', 'start_of_validity', 'end_of_validity',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name',
                  'document_type','coverageInPolicy_policy', 'descuento',
                  'created_at', 'updated_at','f_currency','clave', 'identifier', 'p_total', 'p_neta',
                  'derecho', 'rpf', 'iva', 'comision', 'sucursal','comision_derecho_percent','comision_rpf_percent', 
                  'comision_percent', 'automobiles_policy','damages_policy',
                  'accidents_policy','life_policy','address', 'administration_type', 'certificate_number',
                  'collection_executive','business_line','contractor','from_task','task_associated')

class PolizaSubCatCertForPDFSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)


    class Meta:
        model = Polizas
        fields = ('url', 'id', 'parent', 'paquete', 'start_of_validity', 'end_of_validity',
                'forma_de_pago', 'status', 'observations', 'name','sucursal',
                'document_type', 'p_total', 'automobiles_policy','damages_policy',
                'accidents_policy', 'life_policy', 'certificate_number','collection_executive','from_task','task_associated')


class PolizaFullInfoSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.compania')
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number', 'aseguradora',
            'ramo', 'subramo', 'parent', 'paquete', 'start_of_validity', 'end_of_validity',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name',
                  'document_type','coverageInPolicy_policy', 'descuento',
                  'created_at', 'updated_at', 'f_currency','clave', 'identifier', 'p_total', 'p_neta',
                  'derecho', 'rpf', 'iva', 'comision', 'sucursal','comision_derecho_percent','comision_rpf_percent', 
                  'comision_percent', 'automobiles_policy','damages_policy',
                  'accidents_policy','life_policy','collection_executive', 'scheme', 'accident_rate', 'steps',
                  'emision_date','business_line','contractor','from_task','task_associated')

class ColectividadSerializer(serializers.HyperlinkedModelSerializer):
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)    
    # recibos_poliza = serializers.SerializerMethodField('get_receipts')
    recibos_poliza = CreateReciboSerializer(many = True) 
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    paquete = config_data(read_only=True)
    coverageInPolicy_policy = serializers.SerializerMethodField('get_coverages')
    certificados_activos = serializers.SerializerMethodField()
    certificados_inactivos = serializers.SerializerMethodField()
    poliza_aux = serializers.SerializerMethodField()
    responsable = VendorSerializer(read_only = True)

    def get_poliza_aux(self,obj):
        try:
            if obj.parent:
                if obj.parent.poliza_number:
                    poliza_aux = obj.parent.poliza_number
                elif obj.parent.parent:
                    if obj.parent.parent.poliza_number:
                        poliza_aux = obj.poliza.parent.parent.poliza_number
                    elif obj.parent.parent.parent:
                        if obj.parent.parent.parent.poliza_number:
                            poliza_aux = obj.parent.parent.parent.poliza_number
                        else:
                            poliza_aux = ""
                    else:
                        poliza_aux = ""
                else:
                    poliza_aux = ""
            else:
                poliza_aux = ""

            return poliza_aux
        except Exception as e:
            poliza_aux = ""
            return poliza_aux

    def get_certificados_activos(self, obj):
        queryset = Polizas.objects.filter(parent = obj.id, certificado_inciso_activo = True, org_name=obj.org_name)
        return len(queryset)

    def get_certificados_inactivos(self, obj):
        queryset = Polizas.objects.filter(parent = obj.id, certificado_inciso_activo = False, org_name=obj.org_name)
        return len(queryset)

    def get_coverages(self,obj):
        queryset = CoverageInPolicy.objects.filter(policy = obj.id)
        serializer = CoverageInPolicyModelSerializer(instance = queryset, many = True)
        return serializer.data

    # def get_receipts(self,obj):
    #     queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id)
    #     serializer = ReciboAppSerializer(instance = queryset, many = True)
    #     return serializer.data
            
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number', 'contractor','sucursal', 
                  'parent', 'paquete', 'start_of_validity', 'end_of_validity', 'coverageInPolicy_policy','caratula',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name', 'poliza_aux','comision_derecho_percent','comision_rpf_percent',
                  'document_type', 'certificate_number', 'accidents_policy', 'life_policy', 'automobiles_policy','damages_policy',
                  'created_at', 'updated_at','identifier', 'coverageInPolicy_policy', 'certificados_activos', 'certificados_inactivos',
                  'collection_executive', 'scheme', 'accident_rate', 'steps','emision_date','business_line','comision','comision_percent',
                  'responsable','type_policy', 'conducto_de_pago', 'has_programa_de_proveedores', 'programa_de_proveedores_contractor',
                  'contributory','rfc_cve','rfc_homocve','dom_callenum','dom_colonia','dom_cp','dom_poblacion','dom_estado','from_task','task_associated')

class CategoriaColectividadSerializer(serializers.HyperlinkedModelSerializer):
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    # recibos_poliza = serializers.SerializerMethodField('get_receipts')
    recibos_poliza = CreateReciboSerializer(many = True) 
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    paquete = config_data(read_only=True)
    coverageInPolicy_policy = serializers.SerializerMethodField('get_coverages')
    certificados_activos = serializers.SerializerMethodField()
    certificados_inactivos = serializers.SerializerMethodField()
    poliza_aux = serializers.SerializerMethodField()
    
    def get_poliza_aux(self,obj):
        try:
            if obj.parent:
                if obj.parent.poliza_number:
                    poliza_aux = obj.parent.poliza_number
                elif obj.parent.parent:
                    if obj.parent.parent.poliza_number:
                        poliza_aux = obj.poliza.parent.parent.poliza_number
                    elif obj.parent.parent.parent:
                        if obj.parent.parent.parent.poliza_number:
                            poliza_aux = obj.parent.parent.parent.poliza_number
                        else:
                            poliza_aux = ""
                    else:
                        poliza_aux = ""
                else:
                    poliza_aux = ""
            else:
                poliza_aux = ""

            return poliza_aux
        except Exception as e:
            poliza_aux = ""
            return poliza_aux

    def get_certificados_activos(self, obj):
        queryset = Polizas.objects.filter(parent = obj, certificado_inciso_activo = True, org_name=obj.org_name).exclude(status = 0)
        return len(queryset)

    def get_certificados_inactivos(self, obj):
        queryset = Polizas.objects.filter(parent = obj, certificado_inciso_activo = False, org_name=obj.org_name).exclude(status = 0)
        return len(queryset)

    def get_coverages(self,obj):
        queryset = CoverageInPolicy.objects.filter(policy = obj.id)
        serializer = CoverageInPolicyModelSerializer(instance = queryset, many = True)
        return serializer.data
          
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number', 'contractor','sucursal', 
                  'parent', 'paquete', 'start_of_validity', 'end_of_validity', 'coverageInPolicy_policy','caratula',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name', 'poliza_aux',
                  'document_type', 'certificate_number', 'accidents_policy', 'life_policy', 'automobiles_policy',
                  'created_at', 'updated_at','identifier', 'coverageInPolicy_policy', 'certificados_activos',
                  'certificados_inactivos','collection_executive','hospital_level','from_task','task_associated')


class SubgrupoCategoríaSerializer(serializers.HyperlinkedModelSerializer):
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    # recibos_poliza = serializers.SerializerMethodField('get_receipts')
    recibos_poliza = CreateReciboSerializer(many = True) 
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    paquete = config_data(read_only=True)
    coverageInPolicy_policy = serializers.SerializerMethodField('get_coverages')
    certificados_activos = serializers.SerializerMethodField()
    certificados_inactivos = serializers.SerializerMethodField()
    poliza_aux = serializers.SerializerMethodField()
    categorias = serializers.SerializerMethodField()
    address = AddressSerializer(many=False, read_only=True)

    def get_poliza_aux(self,obj):
        try:
            if obj.parent:
                if obj.parent.poliza_number:
                    poliza_aux = obj.parent.poliza_number
                elif obj.parent.parent:
                    if obj.parent.parent.poliza_number:
                        poliza_aux = obj.poliza.parent.parent.poliza_number
                    elif obj.parent.parent.parent:
                        if obj.parent.parent.parent.poliza_number:
                            poliza_aux = obj.parent.parent.parent.poliza_number
                        else:
                            poliza_aux = ""
                    else:
                        poliza_aux = ""
                else:
                    poliza_aux = ""
            else:
                poliza_aux = ""

            return poliza_aux
        except Exception as e:
            poliza_aux = ""
            return poliza_aux

    def get_certificados_activos(self, obj):
        queryset = Polizas.objects.filter(parent = obj.id, certificado_inciso_activo = True, org_name=obj.org_name).exclude(status = 0)
        return len(queryset)

    def get_certificados_inactivos(self, obj):
        queryset = Polizas.objects.filter(parent = obj.id, certificado_inciso_activo = False, org_name=obj.org_name).exclude(status = 0)
        return len(queryset)

    def get_coverages(self,obj):
        queryset = CoverageInPolicy.objects.filter(policy = obj.id)
        serializer = CoverageInPolicyModelSerializer(instance = queryset, many = True)
        return serializer.data

    def get_categorias(self,obj):
        queryset = Polizas.objects.filter(parent = obj.id, caratula = obj.caratula, document_type = 5)
        serializer = CategoriaColectividadSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        return serializer
            
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number','sucursal', 
                  'parent', 'paquete', 'start_of_validity', 'end_of_validity', 'coverageInPolicy_policy','caratula',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name', 'poliza_aux','comision_derecho_percent','comision_rpf_percent',
                  'document_type', 'certificate_number', 'accidents_policy', 'life_policy', 'automobiles_policy',
                  'created_at', 'updated_at','identifier', 'coverageInPolicy_policy', 'certificados_activos',
                  'certificados_inactivos','collection_executive','categorias','address','hospital_level','p_total',
                  'derecho','rpf','p_neta', 'iva', 'descuento','sub_total','business_line','contractor','f_currency','from_task','task_associated')

class ReciboAppSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.SerializerMethodField()
    poliza = serializers.SlugRelatedField(slug_field = 'id', many=False,read_only=True)
    endorsement = serializers.SlugRelatedField(slug_field = 'id', many=False,read_only=True)
    owner = serializers.SerializerMethodField()
    endosotramite = serializers.SerializerMethodField()
    def get_endosotramite(self,obj):
        try:
            poliza_aux = False
            if obj.poliza:
                poliza_aux = Endorsement.objects.filter(policy = obj.poliza, status__in = [1,5], org_name = obj.poliza.org_name).exists()                
            return poliza_aux
        except Exception as e:
            print('.ee',e)
            poliza_aux = ""
            return poliza_aux 
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    def get_status(self,obj):
        if obj.status and obj.status in [1,5,6,7]:
            return 'Pagado'
        else:
            return obj.get_status_display()

    class Meta:
        model = Recibos
        fields =('recibo_numero', 'status', 'fecha_inicio', 'fecha_fin',
            'receipt_type', 'prima_total', 'id','vencimiento','prima_neta','endosotramite',
            'derecho','rpf','iva','comision','sub_total','isActive','isCopy','poliza',
            'url', 'conducto_de_pago','endorsement','owner','comision_conciliada')
class ReciboFlotillaSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.SerializerMethodField()
    poliza = serializers.SlugRelatedField(slug_field = 'id', many=False,read_only=True)
    endorsement = serializers.SlugRelatedField(slug_field = 'id', many=False,read_only=True)
    owner = serializers.SerializerMethodField()
    endosotramite = serializers.SerializerMethodField()
    def get_endosotramite(self,obj):
        try:
            poliza_aux = False
            if obj.poliza:
                poliza_aux = Endorsement.objects.filter(policy = obj.poliza, status__in = [1,5], org_name = obj.poliza.org_name).exists()                
            return poliza_aux
        except Exception as e:
            print('.ee',e)
            poliza_aux = ""
            return poliza_aux 
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    def get_status(self,obj):
        return obj.get_status_display()

    class Meta:
        model = Recibos
        fields =('recibo_numero', 'status', 'fecha_inicio', 'fecha_fin',
            'receipt_type', 'prima_total', 'id','vencimiento','prima_neta','endosotramite',
            'derecho','rpf','iva','comision','sub_total','isActive','isCopy','poliza',
            'url', 'conducto_de_pago','endorsement','owner','comision_conciliada')
class AseguradoraAppSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Provider
        fields = ('alias' , 'phone')

class PolizaEditAppSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    contractor = serializers.SlugRelatedField(slug_field = 'full_name', many=False,read_only=True)
    coverageInPolicy_policy = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    aseguradora = serializers.SerializerMethodField()
    ramo=serializers.SerializerMethodField()
    subramo=serializers.SerializerMethodField()
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='package_name')
    recibos_poliza = serializers.SerializerMethodField('get_receipts')
    f_currency = serializers.SerializerMethodField('get_currency')
    natural = serializers.SerializerMethodField()
    juridical = serializers.SerializerMethodField()
    emails_to_send = serializers.SerializerMethodField()
    medico_telefono = serializers.SerializerMethodField()
    def get_ramo(self, obj):
        if obj.caratula:
            pol = Polizas.objects.get(pk = obj.caratula)
            return pol.ramo.ramo_name
        else:
            if obj.ramo:
                return obj.ramo.ramo_name
            else:
                return ''
    def get_subramo(self, obj):
        if obj.caratula:
            pol = Polizas.objects.get(pk = obj.caratula)
            return pol.subramo.subramo_name
        else:
            if obj.subramo:
                return obj.subramo.subramo_name
            else:
                return ''
    def get_medico_telefono(self, obj):
        val = {}
        if obj.celula:
            medico_celula = MedicosCelulas.objects.filter(org_name = obj.org_name,celulas__id__in = [obj.celula.id], clientes__id__in = [obj.contractor.id], default=False)
            if medico_celula:
                val['medico'] = medico_celula[0].medico
                val['medico_telefono'] = medico_celula[0].medico_telefono
                return val
            else:
                medico_celula = MedicosCelulas.objects.filter(org_name = obj.org_name,default=True)
                if medico_celula:
                    val['medico'] = medico_celula[0].medico
                    val['medico_telefono'] = medico_celula[0].medico_telefono
                return val
        else:
            medico_celula = MedicosCelulas.objects.filter(org_name = obj.org_name,default=True)
            if medico_celula:
                val['medico'] = medico_celula[0].medico
                val['medico_telefono'] = medico_celula[0].medico_telefono
            return val
    def get_natural(self, obj):
        if obj.contractor:
            if int(obj.contractor.type_person)==1:
                return obj.contractor.full_name                
            else:
                return ''
        else:
            return ''
    def get_juridical(self, obj):
        if obj.contractor:
            if int(obj.contractor.type_person) ==2:
                return obj.contractor.full_name                
            else:
                return ''
        else:
            return ''
    def get_emails_to_send(self, obj):
        email_to = []
        if obj.celula:
            if obj.celula.id == 37 or obj.celula.celula_name == 'Célula uno':
                email_to = ['fundador@ancora.com.mx','sgmm@teleton.org.mx','bal@ancora.com.mx','profuturo@ancora.com.mx']
                return email_to
            elif obj.celula.id == 39 or obj.celula.celula_name == 'Célula dos':
                email_to = ['ancora@up.edu.mx','ancora.ags@up.edu.mx','ancoragdl@up.edu.mx']
                return email_to
            elif obj.celula.id == 40 or obj.celula.celula_name == 'Célula tres':
                email_to = ['segurosmls@ancora.com.mx','ipade@ancora.com.mx','elililly@ancora.com.mx']
                return email_to
            elif obj.celula.id == 36 or obj.celula.celula_name == 'Célula cuatro':
                email_to = ['cen4a@ancora.com.mx', 'cen4b@ancora.com.mx']
                return email_to
            elif obj.celula.id == 41 or obj.celula.celula_name == 'Célula cinco':
                email_to = ['mhernandez@ancora.com.mx']
                return email_to          
            else:
                email_to = []
        else:
            return []
    def get_files(self,obj):
        # obtener condiciones
        rels = PolizaCondicionGeneral.objects.filter(
            policy=obj.id,
            policy__org_name=obj.org_name,
            shared=True
        ).select_related('condicion')
        cg = []
        for r in rels:
            c = r.condicion
            if not c or not c.activo or c.deleted_at:
                continue
            cg.append({
                "id": c.id,
                "nombre": c.nombre,
                "shared": r.shared,
                "tipo": c.tipo,
                "arch": get_presigned_url(folder + "/{url}".format(url=c.arch), 28800),
                "shared": True,
                "source": "CONDICION_GENERAL",
            })
        # condiciones generales
        queryset = PolizasFile.objects.filter(shared = True, owner = obj.id)
        serializer = PolizasFileSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        if cg:
            return serializer.data + cg
        else:
            return serializer.data

    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id).exclude(status=0)
        serializer = ReciboAppSerializer(instance = queryset,context={'request':self.context.get("request")}, many = True)
        return serializer.data

    def get_currency(self,obj):
        return obj.get_f_currency_display()

    def get_aseguradora(self, obj):
        if obj.aseguradora:
            serializer = AseguradoraAppSerializer(instance = obj.aseguradora, many = False)
            return serializer.data
        else:
            if obj.caratula:
                pol = Polizas.objects.get(pk = obj.caratula)
                serializer = AseguradoraAppSerializer(instance = pol.aseguradora, many = False)
                return serializer.data
    def get_coverageInPolicy_policy(self,obj):
        if obj.caratula:
            try:
                pcert = PolizaEditSerializer(obj, context={'request':self.context.get("request")}, many = False)
                paquete = pcert.data['paquete']['id']
                packGet = Package.objects.get(pk = paquete)
                cobx = Coverage.objects.filter(package = paquete)
                coverageInPolicy_policy = []
                dataCovs = {}
                for x in cobx:
                    suma = SumInsured.objects.get(coverage_sum = x)
                    deducible = Deductible.objects.get(coverage_deductible = x)
                    try:
                        coi = Coinsurance.objects.get(coverage_coinsurance = x)
                        coi = coi.coinsurance
                    except Exception as ers:
                        coi = 0
                    try:
                        tope = TopeCoinsurance.objects.get(coverage_topecoinsurance = x)
                        tope = tope.topecoinsurance
                    except Exception as eer:
                        tope = 0
                    dataCovs = {
                        'package': x.package.id,
                        'coverage_name': x.coverage_name,
                        'sum_insured': suma.sum_insured,
                        'deductible': deducible.deductible,
                        'coinsurance': coi if coi else 0,
                        'topecoinsurance': tope if tope else 0,
                    }
                    coverageInPolicy_policy.append(dataCovs)
                return coverageInPolicy_policy
            except Exception as ere:
                return []
        else:
            if obj.document_type ==1:
                covPol = CoverageInPolicy.objects.filter(policy = obj.id)
                serializer = CoverageInPolicyHyperAppSerializer(covPol,context={'request':self.context.get("request")}, many = True, read_only = True)
                return serializer.data
            else:
                covPol = CoverageInPolicy.objects.filter(policy = obj.id)
                serializer = CoverageInPolicyHyperAppSerializer(covPol,context={'request':self.context.get("request")}, many = True, read_only = True)
                return serializer.data

    class Meta:
        model = Polizas
        fields = ('id', 'poliza_number', 'start_of_validity', 'end_of_validity',
                  'coverageInPolicy_policy', 'files','automobiles_policy','sucursal',
                  'damages_policy', 'accidents_policy','life_policy','aseguradora',
                  'ramo', 'subramo','paquete', 'f_currency','recibos_poliza','p_total','comision_derecho_percent','comision_rpf_percent',
                  'derecho','rpf','p_neta', 'iva', 'descuento', 'org_name', 'contractor', 
                  'collection_executive', 'scheme', 'accident_rate', 'steps','caratula','emision_date',
                  'business_line','natural','juridical','emails_to_send','medico_telefono','from_task','task_associated')


class PolizaListAppLiteSerializer(serializers.ModelSerializer):
    aseguradora = serializers.CharField(source='aseguradora.alias', read_only=True)
    ramo = serializers.CharField(source='ramo.ramo_name', read_only=True)
    subramo = serializers.CharField(source='subramo.subramo_name', read_only=True)
    paquete = serializers.CharField(source='paquete.package_name', read_only=True)
    contractor = serializers.CharField(source='contractor.full_name', read_only=True)

    automobiles_policy = app_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Polizas
        fields = [
            'id',
            'poliza_number',
            'start_of_validity',
            'end_of_validity',
            'aseguradora',
            'ramo',
            'subramo',
            'paquete',
            'contractor',
            'automobiles_policy',
            'damages_policy',
            'accidents_policy',
            'life_policy',
            'status',
            'document_type',
        ]

class PolizaListAppSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora = serializers.SerializerMethodField()
    # ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    # subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo = serializers.SerializerMethodField()
    subramo = serializers.SerializerMethodField()
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='package_name')
    automobiles_policy = app_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)
    contractor = serializers.SlugRelatedField(slug_field = 'full_name', many=False,read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    celula = CelulacontractorHyperSerializer(many = False, read_only = True)
    natural = serializers.SerializerMethodField()
    juridical = serializers.SerializerMethodField()
    medico_telefono = serializers.SerializerMethodField()
    coverageInPolicy_policy = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    recibos_poliza = serializers.SerializerMethodField('get_receipts')
    def get_ramo(self, obj):
        if obj.caratula:
            pol = Polizas.objects.get(pk = obj.caratula)
            return pol.ramo.ramo_name
        else:
            if obj.ramo:
                return obj.ramo.ramo_name
            else:
                return ''
    def get_subramo(self, obj):
        if obj.caratula:
            pol = Polizas.objects.get(pk = obj.caratula)
            return pol.subramo.subramo_name
        else:
            if obj.subramo:
                return obj.subramo.subramo_name
            else:
                return ''
    # def get_files(self,obj):
    #     queryset = PolizasFile.objects.filter(shared = True, owner = obj.id)
    #     serializer = PolizasFileSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
    #     # condiciones generales
    #     # 2) Condiciones generales asociadas (compartibles)
    #     rels = PolizaCondicionGeneral.objects.filter(policy=obj.id, org_name=obj.org_name).select_related('condicion')
    #     cg = []
    #     for r in rels:
    #         c = r.condicion
    #         if not c.activo or c.deleted_at:
    #             continue
    #         if not getattr(r, 'shared', True):
    #             continue

    #         cg.append({
    #             "id": c.id,
    #             "nombre": c.nombre,
    #             "tipo": c.tipo,
    #             "url": getattr(c.arch, 'url', None),  # o presigned
    #             "source": "CONDICION_GENERAL",
    #             "shared": True,
    #             "sensible": getattr(c, 'sensible', False)
    #         })
    #     # condiciones generales *
    #     return serializer.data
    def get_files(self, obj):
        queryset = PolizasFile.objects.filter(shared=True, owner=obj.id)
        files_ser = PolizasFileSerializer(instance=queryset, context={'request': self.context.get("request")}, many=True)
        manual = list(files_ser.data)

        rels = PolizaCondicionGeneral.objects.filter(
            policy_id=obj.id,
            org_name=obj.org_name,
            shared=True
        ).select_related('condicion')

        cg = []
        for r in rels:
            c = r.condicion
            if not c or not c.activo or c.deleted_at:
                continue

            cg.append({
                "id": c.id,
                "nombre": c.nombre,
                "shared": r.shared,
                "tipo": c.tipo,
                "arch": get_presigned_url(folder + "/{url}".format(url=c.arch), 28800),
                "shared": True,
                "source": "CONDICION_GENERAL",
            })
        return manual + cg

    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id).exclude(status=0)
        serializer = ReciboAppSerializer(instance = queryset,context={'request':self.context.get("request")}, many = True)
        return serializer.data

    def get_coverageInPolicy_policy(self,obj):
        if obj.caratula:
            try:
                pcert = PolizaEditSerializer(obj, context={'request':self.context.get("request")}, many = False)
                paquete = pcert.data['paquete']['id']
                packGet = Package.objects.get(pk = paquete)
                cobx = Coverage.objects.filter(package = paquete)
                coverageInPolicy_policy = []
                dataCovs = {}
                for x in cobx:
                    suma = SumInsured.objects.get(coverage_sum = x)
                    deducible = Deductible.objects.get(coverage_deductible = x)
                    try:
                        coi = Coinsurance.objects.get(coverage_coinsurance = x)
                        coi = coi.coinsurance
                    except Exception as ers:
                        coi = 0
                    try:
                        tope = TopeCoinsurance.objects.get(coverage_topecoinsurance = x)
                        tope = tope.topecoinsurance
                    except Exception as eer:
                        tope = 0
                    dataCovs = {
                        'package': x.package.id,
                        'coverage_name': x.coverage_name,
                        'sum_insured': suma.sum_insured,
                        'deductible': deducible.deductible,
                        'coinsurance': coi if coi else 0,
                        'topecoinsurance': tope if tope else 0,
                    }
                    coverageInPolicy_policy.append(dataCovs)
                return coverageInPolicy_policy
            except Exception as ere:
                return []
        else:
            if obj.document_type ==1:
                covPol = CoverageInPolicy.objects.filter(policy = obj.id)
                serializer = CoverageInPolicyHyperAppSerializer(covPol,context={'request':self.context.get("request")}, many = True, read_only = True)
                return serializer.data
            else:
                covPol = CoverageInPolicy.objects.filter(policy = obj.id)
                serializer = CoverageInPolicyHyperAppSerializer(covPol,context={'request':self.context.get("request")}, many = True, read_only = True)
                return serializer.data

    def get_medico_telefono(self, obj):
        val = {}
        if obj.celula:
            medico_celula = MedicosCelulas.objects.filter(org_name = obj.org_name,celulas__id__in = [obj.celula.id], clientes__id__in = [obj.contractor.id], default=False)
            if medico_celula:
                val['medico'] = medico_celula[0].medico
                val['medico_telefono'] = medico_celula[0].medico_telefono
                return val
            else:
                medico_celula = MedicosCelulas.objects.filter(org_name = obj.org_name,default=True)
                if medico_celula:
                    val['medico'] = medico_celula[0].medico
                    val['medico_telefono'] = medico_celula[0].medico_telefono
                return val
        else:
            medico_celula = MedicosCelulas.objects.filter(org_name = obj.org_name,default=True)
            if medico_celula:
                val['medico'] = medico_celula[0].medico
                val['medico_telefono'] = medico_celula[0].medico_telefono
            return val
    def get_natural(self, obj):
        if obj.contractor:
            if int(obj.contractor.type_person) ==1:
                return obj.contractor.full_name                
            else:
                return ''
        else:
            return ''
    def get_juridical(self, obj):
        if obj.contractor:
            if int(obj.contractor.type_person) ==2:
                return obj.contractor.full_name                
            else:
                return ''
        else:
            return ''
    def get_aseguradora(self, obj):
        if obj.aseguradora:
            return obj.aseguradora.alias
        else:
            if obj.caratula:
                pol = Polizas.objects.get(pk = obj.caratula)
                return pol.aseguradora.alias

    class Meta:
        model = Polizas
        fields = ('id','poliza_number', 'start_of_validity', 'end_of_validity', 'automobiles_policy','comision_derecho_percent','comision_rpf_percent',
                  'damages_policy','accidents_policy','life_policy','aseguradora','ramo','sucursal','medico_telefono','celula','document_type',
                  'subramo','paquete', 'contractor', 'parent','collection_executive','emision_date','natural','juridical','files','recibos_poliza',
                  'coverageInPolicy_policy','from_task','task_associated','status')


class PolizaEditSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = LifeHyperSerializer(many=True, read_only=True)
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')
    # aseguradora = ProviderMiniSerializer(many=False, read_only=True)
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    ramo = RamosResumeCleanHyperSerializer(many=False,read_only=True)
    paquete = PackageResumeSerializer(many=False,read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    # recibos_poliza = CreateReciboSerializer(many = True)    
    # ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    ref_policy = serializers.SerializerMethodField()
    responsable = VendorSerializer(read_only = True)
    collection_executive = VendorSerializer(read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    grouping_level = serializers.SerializerMethodField()
    subgrouping_level = serializers.SerializerMethodField()
    subsubgrouping_level = serializers.SerializerMethodField()
    parentContractor = serializers.SerializerMethodField()
    parentAseguradora = serializers.SerializerMethodField()
    
    def get_ref_policy(self, obj):
        val = []
        try:
            if ReferenciadoresInvolved.objects.filter(policy = obj, is_changed= False,org_name=obj.org_name).exists():
                rp = ReferenciadoresInvolved.objects.filter(policy = obj, is_changed= False,org_name=obj.org_name)
                serializer = RefInvolvedHyperSerializer(rp, context={'request':self.context.get("request")}, many=True)
                data = serializer.data 
                return data
        except Exception as e:
            val =[]
        return val
    def get_grouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 1:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.parent.level_grouping,
                'description' : obj.groupinglevel.parent.parent.description,
                'type_grouping' : obj.groupinglevel.parent.parent.type_grouping,
                'id' : obj.groupinglevel.parent.parent.id
            }
        else :
            return None
    def get_subgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 2:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        elif obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.parent.level_grouping,
                'description' : obj.groupinglevel.parent.description,
                'type_grouping' : obj.groupinglevel.parent.type_grouping,
                'id' : obj.groupinglevel.parent.id
            }
        else :
            return None

    def get_subsubgrouping_level(self, obj):
        if obj.groupinglevel and obj.groupinglevel.type_grouping == 3:
            return {
                'level_grouping' : obj.groupinglevel.level_grouping,
                'description' : obj.groupinglevel.description,
                'type_grouping' : obj.groupinglevel.type_grouping,
                'id' : obj.groupinglevel.id
            }
        else :
            return None

    def get_parentContractor(self, obj):
        cont = ''
        if obj.document_type == 6:
            if obj.parent:
                if obj.parent.parent:
                    if obj.parent.parent.parent:
                        if obj.parent.parent.parent.contractor:
                            cont = obj.parent.parent.parent.contractor.full_name
                        else:
                            cont = ''
        elif obj.document_type == 5:
            if obj.parent.parent.contractor:
                cont = obj.parent.parent.contractor.full_name
            else:
                cont = ''
        elif obj.document_type == 4:
            if obj.parent.parent:
                cont = obj.parent.parent.contractor.full_name 
            else:
                cont = '' 
        elif obj.document_type == 12:
            cont = obj.parent.contractor.full_name        
        else :
            if obj.contractor:
                cont = obj.contractor.full_name
            else:
                cont = ''
        return cont
    def get_parentAseguradora(self, obj):
        aseg = ''
        if obj.document_type == 6:
            if obj.parent:
                if obj.parent.parent:
                    if obj.parent.parent.parent:
                        if obj.parent.parent.parent.aseguradora:
                            aseg = obj.parent.parent.parent.aseguradora.alias
                        else:
                            aseg = ''
        elif obj.document_type == 5:
            if obj.parent.parent.aseguradora:
                aseg = obj.parent.parent.aseguradora.alias
            else:
                aseg = ''
        elif obj.document_type == 4:
            aseg = obj.parent.parent.aseguradora.alias 
        elif obj.document_type == 12:
            aseg = obj.parent.aseguradora.alias        
        else :
            if obj.aseguradora:
                aseg = obj.aseguradora.alias
            else:
                aseg = ''
        return aseg
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'caratula', 'internal_number', 'folio', 'owner', 'org_name', 'responsable',
                  'poliza_number', 'contractor', 'aseguradora', 'ramo', 'subramo',
                  'paquete', 'old_policies', 'start_of_validity', 'end_of_validity', 'give_comision',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'is_renewable',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'document_type', 'address', 'descuento','sucursal',
                  'coverageInPolicy_policy', 'created_at', 'updated_at', 'clave',
                  'f_currency','p_total','derecho','rpf','p_neta', 'sub_total', 'iva', 'comision',
                  'comision_percent', 'parent', 'identifier','comision_derecho_percent','comision_rpf_percent',
                  'collection_executive','hospital_level','personal_life_policy','ref_policy','administration_type',
                  'scheme', 'accident_rate', 'steps','emision_date','business_line', 'celula', 'groupinglevel',
                  'grouping_level', 'subgrouping_level', 'subsubgrouping_level','contractor', 'conducto_de_pago', 'tabulator',
                  'parentContractor','parentAseguradora','state_circulation','from_task','task_associated')

class PolizaGetEditSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = LifeHyperSerializer(many=True, read_only=True)
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    ramo = RamosResumeCleanHyperSerializer(many=False,read_only=True)
    paquete = PackageResumeSerializer(many=False,read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    recibos_poliza = CreateReciboSerializer(many = True)
    sucursal = SucursalFullSerializer(read_only = True)
    
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner', 'org_name',
                  'poliza_number', 'contractor', 'aseguradora', 'ramo', 'subramo',
                  'paquete', 'old_policies', 'start_of_validity', 'end_of_validity',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'document_type', 'address','sucursal',
                  'coverageInPolicy_policy', 'created_at', 'updated_at', 'clave',
                  'f_currency','p_total','derecho','rpf','p_neta', 'iva', 'comision',
                  'comision_percent', 'parent','comision_derecho_percent','comision_rpf_percent',
                  'collection_executive', 'scheme', 'accident_rate', 'steps','emision_date','business_line','from_task','task_associated')

class PolizaAppSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = LifeHyperSerializer(many=True, read_only=True)
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='compania')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='package_name')
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'owner', 'org_name',
                  'poliza_number', 'contractor', 'aseguradora', 'ramo', 'subramo',
                  'paquete', 'old_policies', 'start_of_validity', 'end_of_validity',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations',
                  'automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'document_type', 'address', 'descuento','sucursal','comision_derecho_percent','comision_rpf_percent',
                  'coverageInPolicy_policy', 'created_at', 'updated_at', 'clave',
                  'f_currency','p_total','derecho','rpf','p_neta', 'iva', 'collection_executive',
                  'emision_date','business_line','from_task','task_associated','from_task','task_associated')


class PolizaSiniesterSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsSiniesterSerializer(many=True, read_only=True)
    life_policy = LifeHyperSerializer(many=True, read_only=True)
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    ramo = RamosResumeCleanHyperSerializer(many=False,read_only=True)

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'poliza_number','automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy','personal_life_policy',
                  'document_type','status','f_currency', 'parent','end_of_validity','start_of_validity','sucursal','ramo',
                  'subramo','collection_executive','contractor','from_task','task_associated','comision_derecho_percent','comision_rpf_percent')



class PolizaviewSiniesterSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')
    parent = SubGroupSerializer(many = False, read_only = True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsSiniesterSerializer(many=True, read_only=True)
    life_policy = LifeHyperSerializer(many=True, read_only=True)
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'poliza_number', 'aseguradora','subramo',
                  'paquete','start_of_validity', 'end_of_validity','comision_derecho_percent','comision_rpf_percent',
                  'forma_de_pago', 'status','automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'address','created_at', 'p_total','derecho','rpf','p_neta', 'iva',
                  'descuento','document_type','sucursal','collection_executive','parent','contractor','from_task','task_associated')

class PolizaviewSiniesterVidaSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    paquete=serializers.SlugRelatedField(many=False,read_only=True,slug_field='package_name')
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'poliza_number', 'contractor', 'aseguradora','subramo',
                  'paquete','start_of_validity', 'end_of_validity','sucursal','comision_derecho_percent','comision_rpf_percent',
                  'forma_de_pago', 'status','automobiles_policy', 'damages_policy', 'accidents_policy', 'life_policy',
                  'address','created_at', 'p_total','derecho','rpf','p_neta', 'iva',
                   'coverageInPolicy_policy','descuento','collection_executive','from_task','task_associated')


class PolizaTableSiniesterVidaSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    life_policy = LifeInfoHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamageInfoHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    parent = SubGroupSerializer(many = False, read_only = True)
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    ref_policy = ReferenciadoresInvolvedHyperSerializer(many=True, read_only=True)
    owner = serializers.SerializerMethodField()
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    class Meta:
        model = Polizas
        fields = ('url', 'subramo', 'id', 'poliza_number', 'aseguradora','comision_derecho_percent','comision_rpf_percent',
                  'life_policy', 'parent', 'document_type', 'damages_policy', 'automobiles_policy', 'personal_life_policy',
                  'accidents_policy','start_of_validity','end_of_validity','ramo','sucursal','collection_executive','caratula','certificate_number',
                  'ref_policy','contractor','owner','from_task','task_associated')

class PolizaTableSiniesterInfoSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    life_policy = LifeInfoHyperSerializer(many=True, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamageInfoHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    parent = SubGroupSerializer(many = False, read_only = True)
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    ref_policy = ReferenciadoresInvolvedHyperSerializer(many=True, read_only=True)
    
    class Meta:
        model = Polizas
        fields = ('url', 'subramo', 'id', 'poliza_number', 'aseguradora','comision_derecho_percent','comision_rpf_percent',
                  'life_policy', 'parent', 'document_type', 'damages_policy', 'automobiles_policy', 'personal_life_policy',
                  'accidents_policy','start_of_validity','end_of_validity','ramo','sucursal','collection_executive','caratula','certificate_number',
                  'ref_policy','contractor','from_task','task_associated')


class PolizaReciboDashSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    ref_policy = ReferenciadoresInvolvedHyperSerializer(many=True, read_only=True)
    sucursal = SucursalFullSerializer(read_only = True)
    conducto_de_pago = serializers.SerializerMethodField()
    phone_mensajeria = serializers.SerializerMethodField()
    def get_phone_mensajeria(self,obj):
        phone_mensajeria = ''
        if obj.contractor:
            phone_mensajeria = obj.contractor.phone_mensajeria
        return phone_mensajeria
    def get_conducto_de_pago(self, obj):
        return obj.get_conducto_de_pago_display()
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'poliza_number', 'contractor', 'aseguradora', 'subramo','iva','comision_derecho_percent','comision_rpf_percent',
                  'p_neta', 'p_total', 'descuento', 'comision', 'derecho', 'rpf','document_type','ramo',
                  'forma_de_pago','status','start_of_validity','end_of_validity','sucursal','ref_policy',
                  'clave','automobiles_policy','parent','f_currency','collection_executive','forma_de_pago','identifier',
                  'comision_percent','conducto_de_pago','phone_mensajeria','from_task','task_associated')
class PolizaReciboDashProvSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora = ProviderMiniSerializer(many = False, read_only=True)
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'poliza_number', 'contractor', 'aseguradora', 'subramo','iva',
                  'p_neta', 'p_total', 'descuento', 'comision', 'derecho', 'rpf','document_type','ramo',
                  'forma_de_pago','status','start_of_validity','end_of_validity','comision_derecho_percent','comision_rpf_percent',
                  'clave','automobiles_policy','f_currency','sucursal','collection_executive','from_task','task_associated')


class pendientsSerializer(serializers.Serializer):
    poliza = serializers.PrimaryKeyRelatedField(read_only = True)
    email = serializers.CharField(read_only = True)
    active = serializers.CharField(read_only = True)
    is_owner = serializers.BooleanField(read_only = True)
    id = serializers.IntegerField(read_only = True)

    class Meta:
        model = Pendients
        fields = ('id','email','poliza','is_owner','active')


class AssignSerializer(serializers.Serializer):
    poliza = serializers.PrimaryKeyRelatedField(read_only = True)
    user = serializers.SlugRelatedField(slug_field = 'email',read_only = True)
    active = serializers.CharField(read_only = True)
    is_owner = serializers.BooleanField(read_only = True)
    id = serializers.IntegerField(read_only = True)

    class Meta:
        model = Assign
        fields = ('id','user','poliza','is_owner','active')



class EndorsementFullSerializer(serializers.ModelSerializer): 
    automobiles_policy = CreateAutomobileSerializer(many = True)
    damages_policy = CreateDamageSerializer(many = True)
    accidents_policy = CreateAccidentsSerializer(many = True)
    life_policy = CreateLifeSerializer(many = True)
    recibos_poliza = CreateReciboSerializer(many = True)
    coverageInPolicy_policy = CreateCoverageInPolicySerializer(many=True)
    document_type = serializers.IntegerField()
    p_total = serializers.DecimalField(decimal_places=2, max_digits=20)
    # paquete = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Polizas
        fields = ('id', 'internal_number', 'folio', 'poliza_number', 'contractor','comision_derecho_percent','comision_rpf_percent',
                  'aseguradora', 'ramo', 'subramo', 'paquete', 'observations', 'start_of_validity', 'end_of_validity', 'forma_de_pago', 'status', 
                  'recibos_poliza', 'automobiles_policy', 'damages_policy', 'accidents_policy','sucursal', 
                  'life_policy', 'document_type', 'address', 'caratula', 'parent', 'certificate_number',
                  'coverageInPolicy_policy', 'clave','f_currency', 'identifier',
                  'p_total','derecho','rpf','p_neta', 'iva', 'comision',
                  'comision_percent', 'descuento','collection_executive','from_task','task_associated')

    def create(self, validated_data):
        recibos = validated_data.pop('recibos_poliza')
        coberturas = validated_data.pop('coverageInPolicy_policy')
        accident_form = validated_data.pop('accidents_policy')
        car_form = validated_data.pop('automobiles_policy')
        life_form = validated_data.pop('life_policy')
        damages_form = validated_data.pop('damages_policy')

        poliza = Polizas.objects.create(**validated_data)        
        if car_form:
            for car in car_form:
                AutomobilesDamages.objects.create(policy = poliza, owner = poliza.owner, org_name = poliza.org_name,**car)
        
        elif damages_form:
            for damage in damages_form:
                Damages.objects.create(policy = poliza, owner = poliza.owner, org_name = poliza.org_name,**damage)
        
        elif accident_form:
            for accident in accident_form:
                personal = accident.pop('personal')
                relationships = accident.pop('relationship_accident')
                personal_information = Personal_Information.objects.create(owner = poliza.owner, org_name = poliza.org_name, **personal)
                accident_instance = AccidentsDiseases.objects.create(personal = personal_information, policy = poliza, owner = poliza.owner, org_name = poliza.org_name,**accident)
                for relationship in relationships:
                    relationship_instance = Relationship.objects.create(accident = accident_instance, owner = poliza.owner, org_name = poliza.org_name, **relationship)

        elif life_form:
            for life in life_form:
                personal = life.pop('personal')
                beneficiaries = life.pop('beneficiaries_life')
                personal_information = Personal_Information.objects.create(owner = poliza.owner, org_name = poliza.org_name, **personal)
                life_instance = Life.objects.create(personal = personal_information, policy = poliza, owner = poliza.owner, org_name = poliza.org_name,**life)
                for beneficiarie in beneficiaries:
                    beneficiarie_instance = Beneficiaries.objects.create(life = life_instance, owner = poliza.owner, org_name = poliza.org_name, **beneficiarie)

        for cobertura in coberturas:
            CoverageInPolicy.objects.create(policy = poliza, owner = poliza.owner, org_name = poliza.org_name, **cobertura)

        for recibo in recibos:
            recibo = Recibos.objects.create(poliza = poliza, owner = poliza.owner, org_name = poliza.org_name, **recibo)
            recibo.save()
      
        return poliza
# *********** PRUEBA PDF CARTA (PÓLIZA)
class CartaFullInfoForPDFSerializer(serializers.HyperlinkedModelSerializer):
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    recibos_poliza = serializers.SerializerMethodField('get_receipts')
    contractor = ContractorInfoSerializer(many=False, read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.compania')
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    f_currency = serializers.SerializerMethodField()
    ref_policy = ReferenciadoresInvolvedHyperSerializer(many=True, read_only=True)

    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id)
        serializer = ReciboAppSerializer(instance = queryset, many = True, context=self.context)
        return serializer.data

    def get_f_currency(self, obj):
        if obj.f_currency == 1:
            f_currency = 'Pesos'
        elif obj.f_currency == 2:
            f_currency = 'Dolares'
        elif obj.f_currency == 3:
            f_currency = 'UDI'
        return f_currency

    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number', 'contractor', 'aseguradora',
            'ramo', 'subramo', 'parent', 'paquete', 'start_of_validity', 'end_of_validity',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name',
                  'document_type','coverageInPolicy_policy', 'descuento',
                  'created_at', 'updated_at', 'f_currency','clave', 'identifier', 'p_total', 'p_neta',
                  'derecho', 'rpf', 'iva', 'comision','comision_derecho_percent','comision_rpf_percent',
                  'comision_percent', 'automobiles_policy','damages_policy',
                  'accidents_policy','life_policy', 'sucursal','collection_executive','ref_policy','from_task','task_associated')

class PolizaReciboReminderSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'poliza_number', 'contractor', 'aseguradora', 'subramo')

class AsegInvolvSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    class Meta:
        model = AseguradorasInvolved
        fields = ('aseguradora',
                'cot_id', 'car_descr' )



class AsegCotPrimaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AseguradorasCotizacionPrimas
        fields = ('cotizacion', 'aseguradora', 'prima', 'url', 'checked')



class CotizacionSerializer(serializers.HyperlinkedModelSerializer):
    # full_name = serializers.SerializerMethodField(read_only=True)
    # cotizacion_primas = AsegCotPrimaSerializer(many = True, required = False)

    def get_full_name(self, obj):
        if int(obj.prospecto == 1):
            return "%s %s %s"%(obj.first_name, obj.last_name if obj.last_name else ' ', obj.second_last_name if obj.second_last_name else '')
        elif int(obj.prospecto) == 2:
            if obj.contractor:
                return obj.contractor.full_name
            else:
                return ""
        else :
            return ""
    class Meta:
        model = Cotizacion
        fields = ('id','url', 'contractor', 
            'org_name', 'status', 'observations', 
            'prospecto', 'life', 'accidents', 'danios', 'auto', 'first_name', 
            'last_name', 'second_last_name', 'email', 'phone', 'ramo', 
            'subramo', 'tipo', 'aseguradora', 'aseguradora_seleccionada','document_type', 'autos_cotizados','personas_cotizadas','inmuebles_cotizados',
            'is_complete','from_task','task_associated','type_person','referenciador')

    def create(self, validated_data): 
        cot = Cotizacion.objects.create(**validated_data)      
        return cot  




class CotizacionShowSerializer(serializers.HyperlinkedModelSerializer):
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    status = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    ramo = serializers.SerializerMethodField()
    subramo = serializers.SerializerMethodField()
    aseguradoras = serializers.SerializerMethodField()
    asegurado = serializers.SerializerMethodField()
    
    def get_asegurado(self, cotizacion):
        if isinstance(cotizacion.ramo,dict):
            ramo_obj = cotizacion.ramo
        else: 
            ramo_obj = json.loads(cotizacion.ramo.replace('\'','"'))

        if isinstance(cotizacion.subramo,dict):
            subramo_obj = cotizacion.subramo
        else: 
            subramo_obj = json.loads(cotizacion.subramo.replace('\'','"'))
        
        if ramo_obj['value'] == 1:
            try:
                life = json.loads(cotizacion.life.replace('\'','"'))
            except:
                life = None            
            if life:
                for asegurado in life['aseguradosList']:
                    nombre_asegurado = "%s %s %s"%(asegurado['first_name'], asegurado['last_name'], asegurado['second_last_name'])
                return nombre_asegurado
        
        if ramo_obj['value'] == 2:
            if cotizacion.accidents:
                accidentes = json.loads(cotizacion.accidents.replace('\'','"'))
            else:
                accidentes = None

            if accidentes:   
                nombre_titular = "%s %s %s"%(accidentes['first_name'], accidentes['last_name'], accidentes['second_last_name'])
            else:
                nombre_titular = ""
            return nombre_titular
        
        if ramo_obj['value'] == 3 and subramo_obj['value'] != 9:
            if cotizacion.danios:
                danios = json.loads(cotizacion.danios.replace('\'','"'))
            else:
                danios = None
            return danios['insured_item'] if danios else ''

        if ramo_obj['value'] == 3 and subramo_obj['value'] == 9:
            if cotizacion.auto:
                try:
                    auto = json.loads(cotizacion.auto.replace('\'','"'))
                except:
                    auto = None
            else:
                auto = None
            print(auto)
            if auto and 'selectedCar' in auto and 'value' in auto['selectedCar'] and 'car_search' in auto['selectedCar']['value']:
                selectedCar = auto['selectedCar']['value']['car_search']
            else:
                selectedCar = ''
            return selectedCar      
    
    def get_full_name(self, obj):
        if int(obj.prospecto == 1):
            return "%s %s %s"%(obj.first_name, obj.last_name, obj.second_last_name)
        elif int(obj.prospecto) == 2:
            if obj.contractor:
                return obj.contractor.full_name
            else:
                return ""
        else :
            return ""

    def get_ramo(self, obj):
        if isinstance(obj.ramo,dict):
            ramo_obj = obj.ramo
        else: 
            ramo_obj = json.loads(obj.ramo.replace('\'','"'))
        try:
            return ramo_obj['name']
        except:
            return obj.ramo
        
        
    def get_subramo(self, obj):
        if isinstance(obj.subramo,dict):
            subramo_obj = obj.subramo
        else: 
            subramo_obj = json.loads(obj.subramo.replace('\'','"'))
        try:
            return subramo_obj['name']
        except:
            return obj.subramo

    def get_aseguradoras(self, obj):
        aux = []
        for aseguradora in obj.aseguradora:
            aseguradora = aseguradora.replace('\\"','').replace('\\\\','')
            aseguradoras_ = json.loads((json.loads(aseguradora)).replace('\'','"'))
            aseguradoras_ = aseguradoras_['alias']
            aux.append(aseguradoras_)
        return", ".join(aux)

    def get_status(self,obj):
            return obj.get_status_display()
    
    class Meta:
        model = Cotizacion
        fields = ('id','url',  'main_parent',
            'org_name', 'status','contractor','prospecto',
            'life', 'accidents', 'danios', 'auto', 'first_name', 
            'last_name', 'second_last_name', 'email', 'phone', 'ramo', 
            'subramo', 'tipo', 'aseguradora', 'full_name', 'aseguradora_seleccionada',
            'is_complete', 'aseguradoras', 'asegurado','type_person','referenciador','document_type', 'autos_cotizados','personas_cotizadas','inmuebles_cotizados',)


class CotizacionFullSerializer(serializers.HyperlinkedModelSerializer):
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    status = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    cotizacion_primas = AsegCotPrimaSerializer(many = True, required = False)
    task_associated_info = serializers.SerializerMethodField()
    poliza_asociada = serializers.SerializerMethodField()
    referenciador_name = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    def get_data(self,obj):
        val = ''
        if obj.contractor:
            val = {'email':obj.contractor.email,'phone':obj.contractor.phone_number}
        return val
    def get_poliza_asociada(self, obj):
        val = []
        try:
            if Polizas.objects.filter(cotizacion_asociada = obj.id,org_name=obj.org_name).exclude(status=0).exists():
                poliza_lista = Polizas.objects.filter(cotizacion_asociada = obj.id,org_name=obj.org_name).exclude(status=0)
                serializer_p = PolizaBasicSerializer(poliza_lista, context={'request':self.context.get("request")},many=True)
                data = serializer_p.data 
                return data
        except Exception as e:
            val =[]
        return val
    def get_task_associated_info(self, obj):
        val = None
        try:
            if Ticket.objects.filter(id = obj.task_associated, ot_model = 3).exists():
                ticket = Ticket.objects.select_related('owner', 'closedBy', 'assigned', 'reassignBy').prefetch_related(
                    'involved_task',
                ).get(pk=obj.task_associated)  

                serializer = FullInfoTicketHyperSerializer(ticket, context={'request':self.context.get("request")})
                data = serializer.data 
                return data
        except Exception as e:
            val =None
        return val
    def get_full_name(self, obj):
        if int(obj.prospecto == 1):
            return "%s %s %s"%(obj.first_name, obj.last_name if obj.last_name else ' ', obj.second_last_name if obj.second_last_name else '')
        elif int(obj.prospecto) == 2:
            if obj.contractor:
                return obj.contractor.full_name
            else:
                return ""
        else :
            return ""
    def get_referenciador_name(self, obj):
        val=''
        if obj.referenciador:
            val=obj.referenciador.first_name +' '+str(obj.referenciador.last_name)
        return val
    
    def get_status(self,obj):
            return obj.get_status_display()
    
    class Meta:
        model = Cotizacion
        fields = ('id','url',  'main_parent','created_at',
            'org_name', 'status', 'observations','contractor','prospecto',
            'life', 'accidents', 'danios', 'auto', 'first_name', 'data',
            'last_name', 'second_last_name', 'email', 'phone', 'ramo', 'document_type', 'autos_cotizados','personas_cotizadas','inmuebles_cotizados',
            'subramo', 'tipo', 'aseguradora', 'full_name', 'aseguradora_seleccionada','poliza_asociada','referenciador_name',
            'is_complete', 'cotizacion_primas','from_task','task_associated','task_associated_info','type_person','referenciador')
# ---------------------------Fianz colectiva Nueva---------------------

class FianzaCollectiveHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    contract_poliza = ContractHyperSerializer(many = False)
    beneficiaries_poliza = BeneficiarieHyperSerializer(many = True)
    recibos_poliza = CreateReciboSerializer(many = True)
    ref_policy = RefInvolvedHyperSerializer(many=True)
    # beneficiaries_poliza_many = BeneficiarieHyperSerializer(many = True)

    class Meta:
        model = Polizas
        fields = ('id', 'url', 'address', 'aseguradora', 'clave', 'comision', 'comision_percent', 'contract_poliza',
                  'created_at', 'document_type', 'end_of_validity', 'start_of_validity', 'poliza_number', 'recibos_poliza',
                  'fianza_type', 'folio', 'identifier', 'internal_number','comision_derecho_percent','comision_rpf_percent',
                  'observations', 'ramo', 'status', 'subramo', 'owner', 'beneficiaries_poliza',
                  'p_total', 'derecho', 'rpf', 'p_neta', 'descuento', 'iva', 'emision_date',
                  'emision_status','is_renewable','fecha_anuencia','emision_date','ref_policy',
                  'certificado_inciso_activo','f_currency','bono_variable', 'has_programa_de_proveedores', 
                  'programa_de_proveedores_contractor','contractor','date_emision_factura','month_factura','folio_factura',
                  'maquila','exchange_rate','date_maquila','year_factura','date_bono','fecha_pago_comision','from_task','task_associated')

    def create(self, validated_data):
        contract = validated_data.pop('contract_poliza')

        # beneficiaries = validated_data.pop('beneficiaries_poliza')
        categorias = []
        beneficiaries_many = []
        if 'beneficiaries_poliza' in validated_data:
            beneficiaries_many = self.context.get('request').data['beneficiaries_poliza']
            validated_data.pop('beneficiaries_poliza')        
        referenciadores = validated_data.pop('ref_policy')
        # categorias = validated_data.pop('categorias')
        recibos = []
        if 'recibos_poliza' in validated_data:
            recibos = validated_data.pop('recibos_poliza')
        if not len(recibos) and validated_data['status'] != 1:
            raise Exception('La fianza no contiene recibos')
        if not len(referenciadores):
            raise Exception('Es necesario incluir al menos un referenciador')

        try:
            colectividadFianza = Polizas.objects.create(**validated_data)
        except Exception as dds:           
            raise serializers.ValidationError("Error al crear Carátula de Fianza, favor de verificar "+str(dds))

        Contract.objects.create(poliza = colectividadFianza, owner = colectividadFianza.owner, org_name = colectividadFianza.org_name, **contract)

        org =colectividadFianza.org_name
        # ---******************************
        for beneficiarie in beneficiaries_many:
            id = None
            try:
                if 'url' in beneficiarie:
                    beneficiarie.pop('url')
                if 'owner' in beneficiarie:
                    beneficiarie.pop('owner')
                if 'id' in beneficiarie:
                    id = beneficiarie.pop('id')
            except Exception as err:
                pass
            if id:
                benef = BeneficiariesContract.objects.get(id=id)
            else:
                if beneficiarie['first_name']:
                    beneficiarie['full_name'] = beneficiarie['first_name']+' '+beneficiarie['last_name'] +' '+beneficiarie['second_last_name']
                else:
                    beneficiarie['full_name'] = ''
                if beneficiarie['type_person'] ==1 and ( not beneficiarie['first_name'] or not beneficiarie['last_name']): # or not beneficiarie['second_last_name'] or not beneficiarie['rfc'] or not beneficiarie['email'] or not beneficiarie['phone_number'])
                    raise Exception('Los siguientes campos son requeridos para el beneficiario: Nombre, apellido Paterno')
                elif beneficiarie['type_person'] ==2 and ( not beneficiarie['j_name']):
                    raise Exception('Los siguientes campos son requeridos para el beneficiario:Razon Social')
                
                benef = BeneficiariesContract.objects.create(owner = colectividadFianza.owner, org_name = colectividadFianza.org_name, **beneficiarie)
            benef.poliza_many.add(colectividadFianza)

        for recibo in recibos:
            recibo = Recibos.objects.create(poliza = colectividadFianza, owner = colectividadFianza.owner, org_name = colectividadFianza.org_name, **recibo)
            recibo.save()
        # Referenciadores
        for refs in referenciadores:    
            nb = ReferenciadoresInvolved.objects.create(policy = colectividadFianza, owner = colectividadFianza.owner, org_name = colectividadFianza.org_name, **refs)
            # nb.poliza_many.add(colectividadFianza)

        return colectividadFianza

    def update(self, instance, validated_data):      
        instance.identifier = validated_data.get('identifier', instance.identifier)
        instance.folio = validated_data.get('folio', instance.folio)
        instance.poliza_number = validated_data.get('poliza_number', instance.poliza_number)
        instance.contractor = validated_data.get('contractor', instance.contractor)
        instance.address = validated_data.get('address', instance.address)
        instance.start_of_validity = validated_data.get('start_of_validity', instance.start_of_validity)
        instance.end_of_validity = validated_data.get('end_of_validity', instance.end_of_validity)
        instance.emision_date = validated_data.get('emision_date', instance.emision_date)
        instance.aseguradora = validated_data.get('aseguradora', instance.aseguradora)
        instance.clave = validated_data.get('clave', instance.clave)
        instance.ramo = validated_data.get('ramo', instance.ramo)
        instance.subramo = validated_data.get('subramo', instance.subramo)
        instance.fianza_type =validated_data.get('fianza_type',  instance.fianza_type)
        instance.f_currency =validated_data.get('f_currency',  instance.f_currency)
        # instance.monto_afianzado = validated_data.get('monto_afianzado', instance.monto_afianzado)
        instance.comision = validated_data.get('comision', instance.comision)
        instance.comision_percent = validated_data.get('comision_percent', instance.comision_percent)
        instance.udi = validated_data.get('udi', instance.udi)
        instance.observations = validated_data.get('observations', instance.observations)
        instance.descuento =validated_data.get('descuento',  instance.descuento)
        instance.derecho = validated_data.get('derecho', instance.derecho)
        instance.rpf = validated_data.get('rpf', instance.rpf)
        instance.iva = validated_data.get('iva', instance.iva)
        instance.p_neta = validated_data.get('p_neta', instance.p_neta)
        instance.p_total = validated_data.get('p_total', instance.p_total)
        # instance.number_inclusion = validated_data.get('number_inclusion', instance.number_inclusion)
        instance.emision_status = validated_data.get('emision_status', instance.emision_status)
        # instance.project_name = validated_data.get('project_name', instance.project_name)
        instance.is_renewable = validated_data.get('is_renewable', instance.is_renewable)
        # instance.tarifa_afianzada = validated_data.get('tarifa_afianzada', instance.tarifa_afianzada)
        try:
            instance.status = validated_data.get('status', instance.status)
        except Exception as e:
            pass

        instance.save()

        try:
            contract_arr = validated_data.pop('contract_poliza')
            contract = contract_arr[0]
        except Exception as e:
            pass
        
        self_contract = self.data['contract_poliza']
        self_beneficiaries = self.data['beneficiaries_poliza']


        instance_contr = Contract.objects.get(id = self_contract[0]['id'], poliza = instance)
        try:
            instance_contr.start = contract['start']
            instance_contr.end = contract['end']
            instance_contr.number = contract['number']
            instance_contr.contract_object = contract['contract_object']
            instance_contr.amount = contract['amount']
            instance_contr.guarantee_percentage = contract['guarantee_percentage']
            instance_contr.activity = contract['activity']
            instance_contr.no_employees = contract['no_employees']
        except Exception as e:
            pass

        instance_contr.save()

        try:
            recibos = validated_data.pop('recibos_poliza')

            for recibo in recibos:
                recibo = Recibos.objects.create(poliza = instance, owner = instance.owner, org_name = instance.org_name, **recibo)
                recibo.save()
        except Exception as e:
            pass

        return instance

class CategoriaCollSuretySerializer(serializers.HyperlinkedModelSerializer):
    recibos_poliza = CreateReciboSerializer(many = True) 
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    certificados_activos = serializers.SerializerMethodField()
    certificados_inactivos = serializers.SerializerMethodField()
    poliza_aux = serializers.SerializerMethodField()
    certificados = serializers.SerializerMethodField()
    address = AddressSerializer(many=False, read_only=True)

    def get_poliza_aux(self,obj):
        try:
            if obj.parent:
                if obj.parent.poliza_number:
                    poliza_aux = obj.parent.poliza_number
                elif obj.parent.parent:
                    if obj.parent.parent.poliza_number:
                        poliza_aux = obj.poliza.parent.parent.poliza_number
                    elif obj.parent.parent.parent:
                        if obj.parent.parent.parent.poliza_number:
                            poliza_aux = obj.parent.parent.parent.poliza_number
                        else:
                            poliza_aux = ""
                    else:
                        poliza_aux = ""
                else:
                    poliza_aux = ""
            else:
                poliza_aux = ""

            return poliza_aux
        except Exception as e:
            poliza_aux = ""
            return poliza_aux

    def get_certificados_activos(self, obj):
        queryset = Polizas.objects.filter(parent = obj.id, certificado_inciso_activo = True, org_name=obj.org_name)
        return len(queryset)

    def get_certificados_inactivos(self, obj):
        queryset = Polizas.objects.filter(parent = obj.id, certificado_inciso_activo = False, org_name=obj.org_name)
        return len(queryset)

    def get_coverages(self,obj):
        queryset = CoverageInPolicy.objects.filter(policy = obj.id)
        serializer = CoverageInPolicyModelSerializer(instance = queryset, many = True)
        return serializer.data

    def get_certificados(self,obj):
        queryset = Polizas.objects.filter(parent = obj.id, caratula = obj.caratula, document_type = 10)
        serializer = FianzaCollectiveHyperSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        return serializer
            
    class Meta:
        model = Polizas
        fields = ('url', 'id', 'internal_number', 'folio', 'poliza_number', 'contractor','sucursal', 
                  'parent', 'paquete', 'start_of_validity', 'end_of_validity','caratula','deductible',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name', 'poliza_aux',
                  'document_type', 'certificate_number', 'created_at', 'updated_at','identifier', 'certificados_activos',
                  'certificados_inactivos','collection_executive','certificados','address','document_type',
                  'fecha_cancelacion', 'monto_cancelacion','from_task','task_associated','comision_derecho_percent','comision_rpf_percent')

class GetCollSuretyFullSerializer(serializers.HyperlinkedModelSerializer):
    contractor = ContractorInfoSerializer(many=False, read_only=True)
    # afianzadora = serializers.ReadOnlyField(source='afianzadora.alias')
    aseguradora = ProviderMiniSerializer(many = False, read_only=True)
    # ramo = serializers.StringRelatedField(read_only=True)
    # subramo = serializers.StringRelatedField(read_only=True)    
    subramo = SubramoResumeSerializer(many=False, read_only=True)
    ramo = RamosResumeCleanHyperSerializer(many=False,read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    owner = serializers.SerializerMethodField()
    contract_poliza = ContractHyperSerializer(many = False, read_only=True)
    beneficiaries_poliza = BeneficiarieHyperSerializer(many = True, read_only=True)
    beneficiaries_poliza_many = BeneficiarieHyperSerializer(many = True, read_only=True)
    recibos_poliza = CreateReciboSerializer(many = True, read_only=True)
    ref_policy = ReferenciadoresInvolvedHyperSerializer(many=True, read_only=True)
    fianza_type = FianzaTypeHyperSerializer(read_only = True, many = False)
    address = AddressSerializer(many=False, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    #renewed_status = serializers.SerializerMethodField()
    recordatorios = serializers.SerializerMethodField()
    task_associated_info = serializers.SerializerMethodField()
    def get_task_associated_info(self, obj):
        val = None
        try:
            if Ticket.objects.filter(id = obj.task_associated, ot_model = 1).exists():
                ticket = Ticket.objects.select_related('owner', 'closedBy', 'assigned', 'reassignBy').prefetch_related(
                    'involved_task',
                ).get(pk=obj.task_associated)  

                serializer = FullInfoTicketHyperSerializer(ticket, context={'request':self.context.get("request")})
                data = serializer.data 
                return data
        except Exception as e:
            val =None
        return val
    def get_recordatorios(self, obj):        
        if obj:
            recs = RegistroDeRecordatorio.objects.filter(recordatorio__tipo=3,record_model=13,record_id= obj.id, org_name=obj.org_name)
            serializer = RegistroDeRecordatorioSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        else:
            return []
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

#    def get_renewed_status(self, obj):
#        return obj.get_renewed_status()

    class Meta:
        model = Polizas
        fields = ('id', 'url', 'address', 'aseguradora', 'clave', 'comision', 'comision_percent', 'contract_poliza',
                  'created_at','f_currency', 'document_type', 'end_of_validity', 'start_of_validity', 'poliza_number', 
                  'recibos_poliza', 'fianza_type', 'folio', 'identifier', 'internal_number',
                  'observations', 'ramo', 'status', 'subramo', 'owner', 'beneficiaries_poliza','sub_total',
                  'p_total', 'derecho', 'rpf', 'p_neta', 'descuento', 'iva', 'emision_date','deductible','ref_policy',
                  'emision_status','is_renewable','updated_at','beneficiaries_poliza_many','certificate_number','certificado_inciso_activo',
                  'renewed_status', 'reason_cancel', 'reason_rehabilitate', 'concept_annulment','caratula','parent','contractor',
                  'bono_variable',  'has_programa_de_proveedores','programa_de_proveedores_contractor','date_cancel',
                  'fecha_cancelacion', 'monto_cancelacion','date_emision_factura','month_factura','folio_factura','maquila','exchange_rate',
                  'date_maquila','year_factura','date_bono','fecha_pago_comision','recordatorios','from_task','task_associated','task_associated_info')


class PolizaAIAResumeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()
    ramo = serializers.StringRelatedField(read_only=True)
    contractor = ContractorInfoSerializer(read_only = True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo = serializers.StringRelatedField(read_only=True)
    recibos_poliza = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)    
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    sucursal = SucursalFullSerializer(read_only = True)
    fianza_type = FianzaTypeHyperSerializer(read_only = True, many = False)
    antiguedad = serializers.SerializerMethodField()
    administration_type = serializers.CharField(source='get_administration_type_display')
    status = serializers.CharField(source='get_status_display')
    f_currency = serializers.CharField(source='get_f_currency_display')
    forma_de_pago = serializers.CharField(source='get_forma_de_pago_display')
    scheme = serializers.CharField(source='get_scheme_display')
    
    nopolizas = serializers.SerializerMethodField()
    noendosos = serializers.SerializerMethodField()
    nonotas = serializers.SerializerMethodField()
    beneficiaries_poliza_many = BeneficiarieHyperSerializer(many = True, read_only=True)    
    categorias = serializers.SerializerMethodField()
    endosos = serializers.SerializerMethodField()
    start_of_validity = serializers.SerializerMethodField()
    end_of_validity = serializers.SerializerMethodField()

    def get_start_of_validity(self,obj):
        start_of_validity = ''
        if obj.start_of_validity:
            start_of_validity = obj.start_of_validity.strftime("%d/%m/%y")
        return start_of_validity
        
    def get_end_of_validity(self,obj):
        end_of_validity = ''
        if obj.end_of_validity:
            end_of_validity = obj.end_of_validity.strftime("%d/%m/%y")
        return end_of_validity

    def get_categorias(self,obj):
        if obj.document_type ==3:
            queryset = Polizas.objects.filter(parent = obj.id, caratula = obj.caratula, document_type = 5)
            serializer = CategoriaColectividadSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        elif obj.document_type ==8:
            queryset = Polizas.objects.filter(parent = obj.id, caratula = obj.caratula, document_type = 9)
            serializer = CategoriaColectividadSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        else:
            serializer = None
        if serializer:
            serializer = serializer.data
        return serializer

    def get_endosos(self,obj):        
        queryset = Endorsement.objects.filter(policy = obj.id).exclude(status = 0)
        serializer = EndorsementInfoExcelHyperSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
        if serializer:
            serializer = serializer.data
        else:
            serializer = None
        return serializer

    def get_nopolizas(self,obj):
        nopolizas = 0
        if obj.document_type ==11:
           nopolizas = Polizas.objects.filter(document_type = 12, org_name = obj.org_name, parent__id = obj.id).exclude(status = 0).count()
        if obj.document_type ==3:
           nopolizas = Polizas.objects.filter(document_type = 6, org_name = obj.org_name, caratula = str(obj.id)).exclude(status = 0).count()
        if obj.document_type ==8:
           nopolizas = Polizas.objects.filter(document_type = 10, org_name = obj.org_name, caratula = str(obj.id)).exclude(status = 0).count()
        return nopolizas
    def get_noendosos(self,obj):
        noendosos = 0
        noendosos = Endorsement.objects.filter(policy__id = obj.id, org_name = obj.org_name).exclude(status = 0).count()
        return noendosos
    def get_nonotas(self,obj):
        nonotas = 0
        nonotas = Recibos.objects.filter(poliza__id = obj.id, org_name = obj.org_name, receipt_type = 3).exclude(status = 0).count()
        return nonotas
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.start_of_validity
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    class Meta:
        model = Polizas
        fields = ('url', 'id','owner' , 'caratula', 'poliza_number', 'document_type', 'end_of_validity', 'clave', 'automobiles_policy',
        'aseguradora', 'ramo', 'subramo','recibos_poliza','poliza_number', 'comision', 'life_policy','receipts_by',
        'f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento', 'damages_policy','sucursal',
        'created_at', 'internal_number','folio','paquete', 'start_of_validity', 'forma_de_pago', 'antiguedad', 'accidents_policy',
        'identifier', 'parent','collection_executive','ref_policy','certificado_inciso_activo','sucursal',
        'scheme', 'accident_rate', 'steps','emision_date','fianza_type','business_line','contratante_subgroup',
        'contractor','date_cancel','reason_cancel','nopolizas','nonotas','noendosos','administration_type','beneficiaries_poliza_many',
        'categorias','endosos','from_task','task_associated')

class PolizaInfoShareSerializer(serializers.HyperlinkedModelSerializer):
    address = AddressSerializer(read_only = True)
    automobiles_policy = app_detail_AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = app_detail_DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = app_detail_AccidentsHyperSerializer(many=True, read_only=True)
    life_policy = app_detail_LifeHyperSerializer(many=True, read_only=True)
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    aseguradora = MinProviderSerializer(many = False, read_only = True)
    ramo = serializers.StringRelatedField(read_only=True)
    subramo = serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    coverageInPolicy_policy = CoverageInPolicyHyperSerializer(many=True, read_only=True)
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    owner = serializers.SerializerMethodField()
    responsable = VendorSerializer(read_only = True)
    collection_executive = VendorSerializer(read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    personal_life_policy = PersonalAppSerializer(many=True, read_only=True)
    ref_policy = RefInvolvedHyperSerializer(many=True, read_only=True)
    
    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner

    class Meta:
        model = Polizas
        fields = ('caratula', 'url', 'id', 'internal_number', 'folio', 'poliza_number', 'aseguradora',
            'ramo', 'subramo', 'parent', 'paquete', 'start_of_validity', 'end_of_validity', 'reason_ren', 'reason_cancel',
                  'forma_de_pago', 'status', 'recibos_poliza', 'observations', 'name', 'is_renewable',
                  'document_type','coverageInPolicy_policy', 'descuento', 'renewed_status',
                  'created_at', 'updated_at', 'f_currency','clave', 'identifier', 'p_total', 'p_neta', 'sub_total',
                  'derecho', 'rpf', 'iva', 'comision', 'responsable', 'give_comision',
                  'comision_percent', 'automobiles_policy','damages_policy','ref_policy',
                  'accidents_policy','life_policy', 'owner', 'caratula','address','sucursal','collection_executive',
                  'hospital_level','personal_life_policy', 'scheme', 'accident_rate', 'steps','emision_date','business_line',
                    'contratante_subgroup','type_policy', 'celula', 'groupinglevel','contractor','cancelnotas',
                    'conducto_de_pago','from_task','task_associated')
# reporte auditoria
class PolizasAuditoriaInfoSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()
    collection_executive = VendorSerializer(many=False, read_only=True)
    responsable = VendorSerializer(many=False, read_only=True)
    ramo = serializers.StringRelatedField(read_only=True)
    contractor = ContractorNameInfoSerializer(many=False, read_only=True)
    aseguradora = serializers.ReadOnlyField(source='aseguradora.alias')
    subramo = serializers.StringRelatedField(read_only=True)
    poliza_number= serializers.StringRelatedField(read_only=True)
    paquete = serializers.StringRelatedField(read_only=True)
    antiguedad = serializers.SerializerMethodField()
    clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    automobiles_policy = AutomobilesDamagesHyperSerializer(many=True, read_only=True)
    damages_policy = DamagesHyperSerializer(many=True, read_only=True)
    accidents_policy = AccidentsGetHyperSerializer(many=True, read_only=True)
    life_policy = app_LifeHyperSerializer(many=True, read_only=True)
    parent = SubGroupSerializer(many = False, read_only = True)
    address = AddressSerializer(read_only = True)
    sucursal = SucursalFullSerializer(read_only = True)
    ref_policy = RefInvolvedInfoSerializer(many = True, read_only = True)    
    recibos_poliza = serializers.SerializerMethodField('get_receipts')
    auditoria = serializers.SerializerMethodField()    
    endosos_poliza =  serializers.SerializerMethodField()
    poliza_anterior = serializers.SerializerMethodField()
    poliza_siguiente = serializers.SerializerMethodField()
    forma_de_pago = serializers.SerializerMethodField()
    conducto_de_pago = serializers.SerializerMethodField()
    def get_conducto_de_pago(self,obj):
        return obj.get_conducto_de_pago_display()
    def get_forma_de_pago(self,obj):
        return obj.get_forma_de_pago_display()

    f_currency = serializers.SerializerMethodField()
    def get_f_currency(self,obj):
        return obj.get_f_currency_display()
    def get_poliza_anterior(self,obj):
        anterior = OldPolicies.objects.filter(new_policy = obj)
        if anterior.exists():
            anterior = anterior.last()
            poliza_anterior = anterior.base_policy.poliza_number
        else:
            poliza_anterior = ''
        return poliza_anterior
    def get_poliza_siguiente(self,obj):
        posterior = OldPolicies.objects.filter(base_policy = obj)
        if posterior.exists():
            posterior = posterior.last()
            try:
                poliza_siguiente = posterior.new_policy.poliza_number
            except:
                poliza_siguiente = ''
        else:
            poliza_siguiente = ''
        return poliza_siguiente
    def get_endosos_poliza(self, obj):
        endosos = Endorsement.objects.filter(policy = obj).exclude(status=0)
        serializer = EndorsementInfoExcelHyperSerializer(instance = endosos, context = {'request':self.context.get("request")}, many=True)
        return serializer.data
    def get_auditoria(self, obj):
        pre = int(self.context.get("request").data['ot'])
        suma = 0
        valores = {}
        try:
            endosos = Endorsement.objects.filter(policy__id = obj.id).exclude(status=0).exclude(concept =1)
            if endosos and (pre ==1 or pre ==3):
                png_sum = endosos.aggregate(Sum('p_neta'))
                valores['pnetasuma']=Decimal(png_sum['p_neta__sum'] if 'p_neta__sum' in png_sum else 0)+Decimal(obj.p_neta if obj.p_neta else 0)
                ptg_sum = endosos.aggregate(Sum('p_total'))
                valores['ptotalsuma']=Decimal(ptg_sum['p_total__sum'] if 'p_total__sum' in ptg_sum else 0)+Decimal(obj.p_total if obj.p_total else 0)
                rpfg_sum = endosos.aggregate(Sum('rpf'))
                valores['rpfsuma']=Decimal(rpfg_sum['rpf__sum'] if 'rpf__sum' in rpfg_sum else 0)+Decimal(obj.rpf if obj.rpf else 0)
                ivag_sum = endosos.aggregate(Sum('iva'))
                valores['ivasuma']=Decimal(ivag_sum['iva__sum'] if 'iva__sum' in ivag_sum else 0)+Decimal(obj.iva if obj.iva else 0)
                derechog_sum = endosos.aggregate(Sum('derecho'))
                valores['derechosuma']=Decimal(derechog_sum['derecho__sum'] if 'derecho__sum' in derechog_sum else 0)+Decimal(obj.derecho if obj.derecho else 0)
                comisiong_sum = endosos.aggregate(Sum('comision'))
                valores['comisionsuma']=Decimal(comisiong_sum['comision__sum'] if 'comision__sum' in comisiong_sum else 0)+Decimal(obj.comision if obj.comision else 0)
            
            else:
                valores['pnetasuma']= obj.p_neta
                valores['ptotalsuma']= obj.p_total
                valores['rpfsuma']= obj.rpf
                valores['ivasuma']= obj.iva
                valores['derechosuma']= obj.derecho
                valores['comisionsuma']= obj.comision
            # recibos = Recibos.objects.filter(poliza__id = obj.id, isActive=True, isCopy=False, receipt_type__in=[1,2,3]).exclude(status=0).exclude(receipt_type=1)
            if pre !=3:
                recibos = Recibos.objects.filter(poliza__id = obj.id, isActive=True, isCopy=False, receipt_type__in=[1,2,3]).exclude(status=0)
                pagRecibos = Recibos.objects.filter(poliza__id = obj.id, isActive=True, isCopy=False, receipt_type__in=[1,2,3],  status__in=[1,5,6,7]).exclude(status=0)
                pendRecibos = Recibos.objects.filter(poliza__id = obj.id, isActive=True, isCopy=False, receipt_type__in=[1,2,3], status__in=[4,3]).exclude(status=0)
                cancRecibos = Recibos.objects.filter(poliza__id = obj.id, isActive=True, isCopy=False, receipt_type__in=[1,2,3], status__in=[2]).exclude(status=0)
                today = datetime.today()
                recibos_vencidos = Recibos.objects.filter(fecha_inicio__lte = today,poliza__id = obj.id, isActive=True, isCopy=False, receipt_type__in=[1,2,3], status__in=[3,4]).exclude(status=0)
                valores['vencidos'] = len(recibos_vencidos)
                balComRecPol = Recibos.objects.filter(poliza__id = obj.id, isActive=True, isCopy=False, receipt_type__in=[1]).exclude(status__in=[0,2])
            else:
                recibos=None
            if recibos:
                rpng_sum = recibos.aggregate(Sum('prima_neta'))
                valores['r_pnetasuma']=Decimal(rpng_sum['prima_neta__sum'] if 'prima_neta__sum' in rpng_sum else 0)
                rptg_sum = recibos.aggregate(Sum('prima_total'))
                valores['r_ptotalsuma']=Decimal(rptg_sum['prima_total__sum'] if 'prima_total__sum' in rptg_sum else 0)
                rpfg_sum = recibos.aggregate(Sum('rpf'))
                valores['r_rpfsuma']=Decimal(rpfg_sum['rpf__sum'] if 'rpf__sum' in rpfg_sum else 0)
                ivag_sum = recibos.aggregate(Sum('iva'))
                valores['r_ivasuma']=Decimal(ivag_sum['iva__sum'] if 'iva__sum' in ivag_sum else 0)
                derechog_sum = recibos.aggregate(Sum('derecho'))
                valores['r_derechosuma']=Decimal(derechog_sum['derecho__sum'] if 'derecho__sum' in derechog_sum else 0)
                comisiong_sum = recibos.aggregate(Sum('comision'))
                valores['r_comisionsuma']=Decimal(comisiong_sum['comision__sum'] if 'comision__sum' in comisiong_sum else 0)
                # total pagado    
                if pagRecibos:            
                    tpagado = pagRecibos.aggregate(Sum('prima_total'))
                    valores['total_pagado']=Decimal(tpagado['prima_total__sum'] if 'prima_total__sum' in tpagado else 0)
                else:
                    valores['total_pagado']=0
                # total pendiente     
                if pendRecibos:           
                    tpendiente = pendRecibos.aggregate(Sum('prima_total'))
                    valores['total_pendiente']=Decimal(tpendiente['prima_total__sum'] if 'prima_total__sum' in tpendiente else 0)
                else:
                    valores['total_pendiente']=0
                # total cancelado    
                if cancRecibos:            
                    tcancelado = cancRecibos.aggregate(Sum('prima_total'))
                    valores['total_cancelado']=Decimal(tcancelado['prima_total__sum'] if 'prima_total__sum' in tcancelado else 0)
                else:
                    valores['total_cancelado']=0
                if balComRecPol:
                    balcom = balComRecPol.aggregate(Sum('comision'))
                    valores['balance_comision']= obj.comision - Decimal(balcom['comision__sum'] if 'comision__sum' in balcom else 0)
                else:
                    valores['balance_comision']=0
            else:
                valores['r_pnetasuma']= obj.p_neta
                valores['r_ptotalsuma']= obj.p_total
                valores['r_rpfsuma']= obj.rpf
                valores['r_ivasuma']= obj.iva
                valores['r_derechosuma']= obj.derecho
                valores['r_comisionsuma']= obj.comision
                valores['total_pagado']=0
                valores['total_pendiente']=0
                valores['total_cancelado']=0
                valores['balance_comision']=0
            return valores
        except Exception as png:
            print('error suma primas neta global',png)
            return 0
    def get_receipts(self,obj):
        queryset = Recibos.objects.filter(isActive = True, isCopy = False, poliza = obj.id).exclude(status=0)
        serializer = ReciboAppSerializer(instance = queryset,context={'request':self.context.get("request")}, many = True)
        return serializer.data
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.start_of_validity
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_owner(self,obj):
        owner =  ''
        if obj.owner:
            owner = obj.owner.first_name + " "+obj.owner.last_name 
        return owner
    class Meta:
        model = Polizas
        fields = ('url', 'id','owner' , 'caratula', 'poliza_number', 'document_type', 'end_of_validity', 'clave', 
        'automobiles_policy','aseguradora', 'ramo', 'subramo','recibos_poliza','poliza_number', 'comision', 
        'life_policy','receipts_by','f_currency', 'p_total','derecho','rpf','p_neta', 'iva', 'status', 'descuento', 
        'damages_policy','sucursal','created_at', 'internal_number','folio','paquete', 'start_of_validity', 
        'forma_de_pago', 'antiguedad', 'accidents_policy','address','identifier', 'parent','collection_executive',
        'responsable','ref_policy','is_renewable','emision_date','scheme', 'accident_rate', 'steps','business_line',
        'contratante_subgroup','contractor','comision_percent','state_circulation','contributory','rfc_cve',
        'rfc_homocve','dom_callenum','dom_colonia','dom_cp','dom_poblacion','dom_estado','endosos_poliza','auditoria',
        'poliza_anterior','poliza_siguiente','conducto_de_pago','from_task','task_associated')

# https://miurabox.atlassian.net/browse/DES-875
from archivos.presigned_url import get_presigned_url
folder = settings.MEDIAFILES_LOCATION
class CondicionGeneralSerializer(serializers.ModelSerializer):
    # url = serializers.SerializerMethodField()

    class Meta:
        model = CondicionGeneral
        fields = ('id','org_name','aseguradora','subramo','nombre','tipo','arch','url','activo','deleted_at','created_at')

    # def get_url(self, obj):
    #     try:
    #         return obj.arch.url
    #     except Exception:
    #         return None
    def to_representation(self, instance):
        serializer = CondicionGeneralSerializer_detalle(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data
class CondicionGeneralSerializer_detalle(serializers.ModelSerializer):
    arch = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    subramo_name = serializers.SerializerMethodField()

    def get_provider(self, obj):
        return obj.aseguradora.alias if obj.aseguradora else ''

    def get_subramo_name(self, obj):
        return obj.subramo.subramo_name if obj.subramo else ''

    def get_arch(self, obj):
        return get_presigned_url(folder + "/{url}".format(url=obj.arch), 28800)

    class Meta:
        model = CondicionGeneral
        fields = ('id','org_name','aseguradora','subramo','nombre','tipo','arch','activo','deleted_at','created_at',
                  'provider','subramo_name')
from rest_framework import serializers
from aseguradoras.models import Provider
from ramos.models import SubRamos  # ajusta imports reales
import re
class CondicionGeneralWriteSerializer(serializers.ModelSerializer):
    aseguradora = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all())
    subramo = serializers.PrimaryKeyRelatedField(queryset=SubRamos.objects.all())
    arch = serializers.FileField()

    class Meta:
        model = CondicionGeneral
        fields = ('id', 'org_name', 'aseguradora', 'subramo', 'nombre', 'tipo', 'arch')
        read_only_fields = ('id', 'org_name')
class PolizaCondicionGeneralSerializer(serializers.ModelSerializer):
    shared = serializers.BooleanField(read_only=False, required=False)  # permite PATCH si quieres
    condicion_detalle = serializers.SerializerMethodField()

    class Meta:
        model = PolizaCondicionGeneral
        fields = ('id', 'policy', 'condicion', 'shared', 'condicion_detalle', 'created_at','org_name')
        read_only_fields = ('policy',)

    def get_condicion_detalle(self, obj):
        # Usa tu serializer detalle (si ya existe) o el simple
        # Si solo tienes CondicionGeneralSerializer, úsalo.
        data = CondicionGeneralSerializer_detalle(
            instance=obj.condicion,
            context=self.context
        ).data

        # Inyecta shared de la relación
        data['shared'] = obj.shared
        return data
class AsignarCondicionesGeneralesPolizaSerializer(serializers.Serializer):
    # Acepta cualquiera de los dos:
    policy_id = serializers.IntegerField(required=False)
    policy = serializers.CharField(required=False) 
    # Lo que usas para filtrar catálogo (provider == aseguradora en tu payload)
    aseguradora = serializers.IntegerField(required=True)
    subramo = serializers.IntegerField(required=True)

    # Opcional: si mandas ids explícitos de condiciones (mejor)
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )

    # Si True: reemplaza selección (borra previas y deja estas)
    replace = serializers.BooleanField(required=False, default=True)

    def validate(self, data):
        # Resolver policy_id si viene como URL
        if not data.get('policy_id'):
            policy_url = data.get('policy')
            if policy_url:
                m = re.search(r'/polizas/(\d+)/?$', policy_url)
                if m:
                    data['policy_id'] = int(m.group(1))
                else:
                    raise serializers.ValidationError({'policy': 'No pude extraer el id de la URL de policy.'})
            else:
                raise serializers.ValidationError({'policy_id': 'policy_id es requerido si no mandas policy URL.'})

        return data
# https://miurabox.atlassian.net/browse/DES-875