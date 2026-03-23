from ramos.models import Ramos, SubRamos
from rest_framework import serializers
from core.models import *
from organizations.models import *
from vendedores.models import *
from contratantes.models import Contractor, Group
from recibos.models import Recibos,Bancos
from endosos.models import Endorsement
from polizas.models import Polizas
from core.models import Areas,AreasResponsability
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from datetime import date
import arrow
from datetime import datetime
from django.contrib.auth.models import Group as DjangoGroups 
from jsonfield import JSONField 
from archivos.serializers import LecturaFileGeneralileSerializer, LecturaFileSerializer, NotificationsFileSerializer
from archivos.models import NotificationFile,TicketFile
from recordatorios.models import RegistroDeRecordatorio
from recordatorios.serializers import RegistroDeRecordatorioSerializer,RecordatoriosSerializer
from ramos.serializers import RamosHyperSerializer,SubramoHyperSerializer
# from django.contrib.auth.models import UsersGroups as DjangoUserGroups 
import requests
from archivos.presigned_url import get_presigned_url
from django.conf import settings
import base64
from django.core.files.base import ContentFile

folder = settings.MEDIAFILES_LOCATION

# -----------------
class VendorPhoneHyperSerializer(serializers.HyperlinkedModelSerializer):
    vendedor = serializers.PrimaryKeyRelatedField(read_only = True)
    class Meta:
        model = Phone
        fields = ('url','phone','vendedor')

    def create(self, validated_data):
        phone, phone_created = Phone.objects.get_or_create(**validated_data)
        return phone


class GroupManagerHyperSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.id
    class Meta:
        model = GroupManager
        fields = ('user', )


class SucursalCasSerializer(serializers.HyperlinkedModelSerializer):
    item_text = serializers.SerializerMethodField()
    item_id = serializers.SerializerMethodField()

    def get_item_text(self, obj):
        return obj.sucursal_name

    def get_item_id(self, obj):
        return obj.id

    class Meta:
        model = Sucursales
        fields = ('item_id', 'item_text') 


class PerfilUsuarioRestringidoTableSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PerfilUsuarioRestringido
        fields = ("id", "is_active", "nombre", 'url', 'contratante_contratante',
                "contratante_grupo",
                "contratante_celula",
                "contratante_referenciador",
                "contratante_sucursal",
                "poliza_poliza",
                "poliza_grupo",
                "poliza_celula",
                "poliza_referenciador",
                "poliza_sucursal",
                "poliza_agrupacion",
                "poliza_clave_agente",
                "poliza_subramo",
                "poliza_aseguradora",
                "poliza_estatus",
        )



class PerfilUsuarioRestringidoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PerfilUsuarioRestringido
        fields = ("id", "contratante_contratante", "contratante_grupo", 
        "contratante_celula", "contratante_referenciador", "contratante_sucursal", 
        "poliza_poliza", "poliza_grupo", "poliza_celula", "poliza_referenciador", 
        "poliza_sucursal", "poliza_agrupacion", "poliza_clave_agente", 
        "poliza_subramo", "poliza_aseguradora", "poliza_estatus", 'url', 'nombre', 
        'is_active', 'solo_polizas_visibles')


class SubramosVendedorHyperSerializer(serializers.HyperlinkedModelSerializer):
    vendedor = serializers.PrimaryKeyRelatedField(read_only = True)
    class Meta:
        model = SubramosVendedor
        fields = ('provider', 'ramo', 'subramo', 'comision', 'url', 'id', 'vendedor')

    def create(self, validated_data):
        subramo, subramo_created = SubramosVendedor.objects.get_or_create(**validated_data)
        return subramo


class VendedorHyperSerializer(serializers.HyperlinkedModelSerializer):
    vendedor_subramos = SubramosVendedorHyperSerializer(many=True)
    bank = serializers.PrimaryKeyRelatedField(queryset = Bancos.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only = True)
    vendedor_phone = VendorPhoneHyperSerializer(many = True)
    class Meta:
        model = Vendedor
        # fields = ('hired_date', 'vendedor_phone', 'email', 'bank', 'address', 
        #     'gastos_operacion', 'tipo_pago', 'reference_number', 
        #     'vendedor_subramos', 'frequencia_de_cobro', 'url', 'id', 'user')
        fields = ('hired_date', 'vendedor_phone', 'email', 'bank', 'address', 
            'gastos_operacion', 'tipo_pago', 'reference_number', 
            'vendedor_subramos', 'url', 'id', 'user','concepts')

    def create(self, validated_data):
        vendedor_subramos = validated_data.pop('vendedor_subramos')
        vendedor_phone = validated_data.pop('vendedor_phone')
        obj = Vendedor.objects.create(**validated_data)

        for subramo in vendedor_subramos:
            SubramosVendedor.objects.get_or_create(vendedor = obj, **subramo)

        for telefono in vendedor_phone:
            Phone.objects.get_or_create(vendedor = obj, **telefono)

        return obj

class UserInfoVendedorHyperSerializer(serializers.HyperlinkedModelSerializer):
    info_vendedor = VendedorHyperSerializer(many = True,read_only = True)
    class Meta:
        model = UserInfo
        fields = ('is_vendedor','url', 'info_vendedor','user', 'is_active')

class UserInfoVendedoresSerializer(serializers.HyperlinkedModelSerializer):
    user_info = UserInfoVendedorHyperSerializer(many = False, read_only = True)
    class Meta:
        model = User
        fields = ('username' , "first_name", "last_name", "id",'url','user_info')
# --------------------
class LogSerializer(serializers.ModelSerializer):
    model = serializers.IntegerField(required = True)
    event = serializers.CharField(required = True)
    identifier = serializers.CharField(required = True)
    class Meta:
        model = Log
        fields = ('model','event','identifier', 'associated_id','change','original')

class LogEmailSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()
    created_at =  serializers.SerializerMethodField()
    def get_files(self, obj):
        files = obj.files
        return files

    def get_created_at(self, obj):
        date =  obj.created_at.strftime('%d/%m/%Y %I:%M %p')
        return date

    class Meta:
        model = LogEmail
        fields = ('model','associated_id','log','comment','to','cc','cco', 'subject','body','files', 'created_at')
    def to_representation(self, instance):
        serializer = LogEmailSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data
class LogEmailSerializer2(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()
    created_at =  serializers.SerializerMethodField()
    def get_files(self, obj):
        files = []
        try:
            for f in obj.files:
                uno = f['url'].split('?')[0]
                dos=uno.split('.com/')[1]
                d = { 
                    'name':f['name'],
                    'original':f['url'], 
                    'url':get_presigned_url("{url}".format(url=dos), 28800)              
                }
                files.append(d)
        except Exception as e:
            print('errorr',e)
        return files

    def get_created_at(self, obj):
        date =  obj.created_at.strftime('%d/%m/%Y %I:%M %p')
        return date 
    class Meta:
        model = LogEmail
        fields = ('model','associated_id','log','comment','to','cc','cco', 'subject','body','files', 'created_at')
class LogReportSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()
    event = serializers.SerializerMethodField()

    def get_user(self,obj):
        user = obj.user.first_name + ' ' + obj.user.last_name
        return user

    def get_model(self,obj):
        return obj.get_model_display()

    def get_event(self,obj):
        return obj.get_event_display()

    class Meta:
        model = Log
        fields = ('model','event','identifier', 'associated_id','user','created_at')

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ('id','app_label', 'model')

class PermissionSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer()
    class Meta:
        model = Permission
        fields = ('id','name', 'codename','content_type')
#    core
class UserPermissionSerializer(serializers.ModelSerializer):
    checked = serializers.SerializerMethodField()

    def get_checked(self,obj):
        if obj.checked:
            return "true"
        else:
            return "false"
    class Meta:
        model = UserPermissions
        fields = ('id', 'checked', 'permission_name')

class ModelsPermissionSerializer(serializers.ModelSerializer):
    permissions = UserPermissionSerializer(read_only = True, many=True)
    class Meta:
        model = ModelsPermissions
        fields = ('id','user', 'model_name', 'permissions')

#    /core
class AreasSerializer(serializers.ModelSerializer):
    org = serializers.SerializerMethodField()
    owner = serializers.SlugRelatedField('username', read_only = True)

    def get_org(self, obj):
        return obj.org_name

    class Meta:
        model = Areas
        fields = ('id','org_name','owner','area_name','url')
        
class AreasResponsabilityMinSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return "%s %s" % (obj.user.first_name, obj.user.last_name)
    class Meta:
        model = AreasResponsability
        fields = ('id','user', 'ramo', 'url')
class AreasFullSerializer(serializers.ModelSerializer):
    org = serializers.SerializerMethodField()
    owner = serializers.SlugRelatedField('username', read_only = True)
    responsable_area = AreasResponsabilityMinSerializer(read_only = True, many = True)

    def get_org(self, obj):
        return obj.org_name

    class Meta:
        model = Areas
        fields = ('id','org_name','owner','area_name','url', 'responsable_area')

class AreasInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Areas
        fields = ('id','org_name','owner','area_name','url')
class AreasResponsabilitySerializer(serializers.ModelSerializer):
    org = serializers.SerializerMethodField()
    def get_org(self, obj):
        return obj.org_name

    class Meta:
        model = AreasResponsability
        fields = ('id','org_name','owner','area','url','user', 'ramo')


class AreasResponsabilityInfoSerializer(serializers.HyperlinkedModelSerializer):
    # user = UserInfoHyperSerializer(many = False, read_only = True)
    # owner = UserInfoHyperSerializer(many = False, read_only = True)
    # area = AreasInfoSerializer(many=False, read_only=True)
    # org = OrganizationsHyperSerializer(many = False, read_only=True)    
    user=serializers.SlugRelatedField(many=False,read_only=True,slug_field='username')
    area=serializers.SlugRelatedField(many=False,read_only=True,slug_field='area_name')
    org=serializers.SerializerMethodField()
    owner=serializers.SlugRelatedField(many=False,read_only=True,slug_field='username')

    def get_org(self, obj):
        return obj.org_name

    class Meta:
        model = AreasResponsability
        fields = ('id','org_name','owner','area','url','user', 'ramo')


class PhonesSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Phones
        fields = ("contractor","phone", "phone_type", "url")

class EmailsSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Emails
        fields = ( 'correo', 'contractor', 'email_type','url','id')

class InvolvedResponsablesSerializer(serializers.HyperlinkedModelSerializer):

    responsable_name = serializers.SerializerMethodField()

    def get_responsable_name(self, obj):
        return obj.responsable.first_name + ' ' + obj.responsable.last_name
    
    class Meta:
        model = ResponsablesInvolved
        exclude = ('org_name', )

class CommentSerializer(serializers.ModelSerializer):
    user  = serializers.StringRelatedField()
    parent = serializers.StringRelatedField()
    user_info = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_image(self,obj):
        try:
            atchivo_imagen =requests.get(settings.CAS_URL + 'get-image-user/' + obj.user.username)
            infoa = json.loads(atchivo_imagen.text)
            return infoa['logo']
        except:
            return ''
    def get_user_info(self,obj):
        return obj.user.first_name + ' ' + obj.user.last_name

    class Meta:
        model = Comments
        fields = ('id','model', 'content', 'parent', 'created_at', 
            'user', 'is_child', 'user_info', 'has_reminder', 'reminder_date','image','mentioned_users')


class CommentInfoSerializer(serializers.ModelSerializer):
    user  = serializers.StringRelatedField()
    user_info = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()
    id_model = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    parent_data = serializers.SerializerMethodField()

    def get_parent_data(self,obj):
        try:
            parent_data = Comments.objects.get(id=obj.parent.id)
            data={
                'id':parent_data.id,
                'model':parent_data.model,
                'id_model':parent_data.id_model
            }
            return data
        except:
            return {}
    def get_model(self,obj):
        try:
            return obj.parent.model
        except:
            return obj.model
    def get_id_model(self,obj):
        try:
            return obj.parent.id_model
        except:
            return obj.id_model
    def get_image(self,obj):
        try:
            atchivo_imagen =requests.get(settings.CAS_URL + 'get-image-user/' + obj.user.username)
            infoa = json.loads(atchivo_imagen.text)
            return infoa['logo']
        except:
            return ''
    def get_user_info(self,obj):
        return obj.user.first_name + ' ' + obj.user.last_name

    class Meta:
        model = Comments
        fields = ('id','model', 'content', 'parent', 'created_at', 'parent_data','id_model',
            'user', 'is_child', 'user_info', 'has_reminder', 'reminder_date','image','mentioned_users')

class CityHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Cities
        fields = ('url', 'id', 'state', 'city',)
   
class StateHyperSerializer(serializers.HyperlinkedModelSerializer):
    cities = CityHyperSerializer(many=True, read_only=True)

    class Meta:
        model = States
        fields = ('url', 'id', 'state', 'cities',)

class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = ('url', 'id', 'org_name', 'administrative_area_level_1', 'administrative_area_level_2',
                  'country', 'sublocality', 'route','street_number','street_number_int',
                  'postal_code','details', 'aseg', 'tipo','sucursal','contractor')

class AddressStringSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = ('administrative_area_level_1','administrative_area_level_2',)

class CartaFullSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Cartas
        fields = ('name','title','text','model','org_name','owner', 'id', 'created_at', 'url')

class InternalHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Internal
        fields = ('id','org_name')

class EmailInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EmailInfo
        fields = ('id', 'text', 'url', 'model')

class EmailInfoReminderSerializer(serializers.HyperlinkedModelSerializer):
    useremail = serializers.SerializerMethodField(read_only=True)
    def get_useremail(self, obj):
        request = self.context.get('request')
        if request:
            return getOrg(request)
        return None
    class Meta:
        model = EmailInfoReminder
        fields = ('id', 'text','text_end', 'url', 'model','frequency','type_policy','ramo_code', 'tipo_cobro', 'remitente','useremail',
            'tipo_fecha', 'aseguradora','aseguradoras','subramos','receipt_type','type_message','days', 'relative_date', 'relative_time','dato_asegurado')
def getOrg(request):
    org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
    response_org = org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    if org_info:
        return org_info['email']
    return ''
class GraphHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Graphics
        fields = ('type_graphic' , "red", "orange", "yellow",'green', 'owner', 'option_filter')

class UserSerialzier(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'url')

class ScheduleParticipantsSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerialzier(read_only = True, required = False)

    class Meta:
        model= ScheduleParticipants
        fields = ('user','schedule')


class ScheduleSerializer(serializers.HyperlinkedModelSerializer):
    participants = ScheduleParticipantsSerializer(read_only = True , many=True)


    def get_org(self,obj):
            return obj.org_name

    class Meta:
        model = Schedule
        fields = ('title', 'color', 'startsAt', 'endsAt', 'id', 'url', 'draggable', 'resizable', 'org_name',
         'participants', 'observations')


class InvolvedTaskSerializer(serializers.HyperlinkedModelSerializer):
    person = UserInfoVendedoresSerializer(many = False, read_only = True)
    class Meta:
        model = Involved
        fields = ('id', 'person')



class InvolvedMinTaskSerializer(serializers.HyperlinkedModelSerializer):
    person_info = UserInfoVendedoresSerializer(many = False, read_only = True)
    class Meta:
        model = Involved
        fields = ('id', 'person', 'person_info' )

from datetime import date
class TicketHyperSerializer(serializers.HyperlinkedModelSerializer):
    involved_task = InvolvedMinTaskSerializer(many = True)
    antiguedad = serializers.SerializerMethodField()
    assigned = UserInfoVendedoresSerializer(many = False, read_only = True)
    owner = UserInfoVendedoresSerializer(many = False, read_only = True)

    contador_dias_cierre = serializers.SerializerMethodField()
    reassignBy = serializers.SerializerMethodField()
    recordatorios = serializers.SerializerMethodField()
    def get_recordatorios(self, obj):        
        if obj:
            recs = RegistroDeRecordatorio.objects.filter(record_model=22,record_id= obj.id, org_name=obj.org_name)
            serializer = RegistroDeRecordatorioSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        else:
            return []
    def get_reassignBy(self, obj):
        response = ''
        if obj.reassignBy:
            response = "%s %s"%(obj.reassignBy.first_name, obj.reassignBy.last_name)
        return response


    def get_contador_dias_cierre(self, obj):
        if not obj.closed:
            return "La tarea no ha sido cerrada"
        created = obj.created_at
        close_date = obj.close_day
        delta = close_date - created
        return "%s días"%delta.days


    def get_antiguedad(self,obj):
            today = date.today()
            a = arrow.get(today)
            aux_date = obj.created_at
            b = arrow.get(aux_date)
            antiguedad = (a-b).days
            antiguedad = int(antiguedad)+1
            return antiguedad

    def update(self, instance, validated_data):
        request = self.context.get('request')
        try:
            involved = validated_data.pop('involved_task')
        except Exception as error_inv:
            involved = []
        involved_list = []
        if len(involved) !=0:
            for inv in involved:
                involv, created = Involved.objects.get_or_create(involved = instance, owner = instance.owner, org_name = instance.org_name, **inv)
                involved_list.append(involv.id)
                if created:
                    notification = Notifications.objects.create(
                        model = 22, 
                        involucrado = True,
                        id_reference = instance.id, 
                        title = instance.title , 
                        description = instance.descrip , 
                        assigned = involv.person, 
                        owner = instance.owner,
                        org_name = instance.org_name 
                    )
                    notification.send_push(request)
                    notification.send_email(request, instance)
            try:
                Involved.objects.filter(involved=instance).exclude(id__in=involved_list).delete()
            except Exception as e:
                pass
        else:
            print('se quedará sin involucrados')
            try:
                Involved.objects.filter(involved=instance).exclude(id__in=involved_list).delete()
            except Exception as e:
                pass
            pass
        try:
            instance.title = validated_data.pop('title')
        except Exception as err:
            pass
        try:
            instance.descrip = validated_data.pop('descrip')
        except Exception as err:
            pass
        try:
            instance.date = validated_data.pop('date')
        except Exception as err:
            pass
        # instance.org = validated_data.pop('org_name')
        try:
            instance.close_day = validated_data.pop('close_day')
        except Exception as err:
            pass
        try:
            instance.closed = validated_data.pop('closed')
        except Exception as err:
            pass
        try:
            instance.route = validated_data.pop('route')
        except Exception as err:
            pass
        try:
            instance.associated = validated_data.pop('associated')
        except Exception as err:
            pass
        try:
            instance.model = validated_data.pop('model')
        except Exception as err:
            pass
        try:
            instance.closedBy = validated_data.pop('closedBy')
        except Exception as err:
            pass
        try:
            instance.archived = validated_data.pop('archived')
        except Exception as err:
            pass
        try:
            instance.priority = validated_data.pop('priority')
        except Exception as err:
            pass
        try:
            if instance.assigned.id != request.data['assigned']:
                instance.reassignBy = request.user
                instance.reassign_date = datetime.now()
                try:
                    new_assigned = User.objects.get(id =request.data['assigned'])
                    notification = Notifications.objects.create(
                        model = 22, 
                        involucrado = False,
                        id_reference = instance.id, 
                        title = instance.title , 
                        description = instance.descrip , 
                        assigned = new_assigned, 
                        owner = request.user,
                        org_name = instance.org_name 
                    )
                    notification.send_push(request)
                    notification.send_email(request, instance)
                except:
                    pass
            instance.assigned = User.objects.get(id = request.data['assigned'])
        except Exception as err:
            pass
        try:
            instance.ot_model = validated_data.pop('ot_model')
        except Exception as err:
            pass
        try:
            instance.concept = validated_data.pop('concept')
        except Exception as err:
            pass
        try:
            instance.ot_id_reference = validated_data.pop('ot_id_reference')
        except Exception as err:
            pass
        instance.save()
        return instance

    class Meta:
        model = Ticket
        fields = ('url', 'id' ,'title', 'descrip', 'date', 'assigned', 'owner', 'concept','involved_task',
            'org_name', 'priority', 'close_day','closed', 'archived', 'route', 'associated', 'model','closedBy',
            'antiguedad', 'identifier', 'reassignBy', 'reassign_date', 'contador_dias_cierre','created_at','recordatorios',
            'ot_model','ot_id_reference'
        )

from archivos.serializers import TicketFileHyperSerializer
class TicketSerializer(serializers.HyperlinkedModelSerializer):
    archivos_ticket = TicketFileHyperSerializer(read_only = True, many = True)
    involved_task = InvolvedTaskSerializer(read_only = True, many = True)
    assigned = serializers.SerializerMethodField(read_only = True)

    def get_assigned(self, obj):
        if obj.assigned:
            return {
                "id" : obj.assigned.id,
                "first_name": obj.assigned.first_name,
                "last_name": obj.assigned.last_name,
            }
        else:
            return {"name" : "Sin asignación" }

    class Meta:
        model = Ticket
        fields = ('url', 'id' ,'title', 'descrip', 'date', 'assigned', 'owner', 'concept',
                 'org_name', 'priority', 'close_day','closed', 'archived', 'route', 'associated', 'model',
                 'archivos_ticket','closedBy', 'involved_task','ot_model','ot_id_reference')  


class FullInfoTicketHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = UserInfoVendedoresSerializer(many=False, read_only=True)
    closedBy = UserInfoVendedoresSerializer(many=False, read_only=True)
    involved_task = InvolvedTaskSerializer(many=True, read_only=True)
    assigned = UserInfoVendedoresSerializer(many=False, read_only=True)
    antiguedad = serializers.SerializerMethodField()
    ruta = serializers.SerializerMethodField(read_only=True)
    up_date = serializers.SerializerMethodField()
    contador_dias_cierre = serializers.SerializerMethodField()
    reassignBy = serializers.SerializerMethodField()
    recordatorios = serializers.SerializerMethodField()
    def get_recordatorios(self, obj):
        try:
            recs = RegistroDeRecordatorio.objects.filter(
                record_model=22,
                record_id=obj.id,
                org_name=obj.org_name
            ).select_related('recordatorio')
            return RegistroDeRecordatorioSerializer(instance=recs, context={'request': self.context.get("request")}, many=True).data
        except:
            return {}

    def get_reassignBy(self, obj):
        return str(obj.reassignBy.first_name) +''+ str(obj.reassignBy.last_name) if obj.reassignBy else ''

    def get_contador_dias_cierre(self, obj):
        if not obj.closed:
            return "La tarea no ha sido cerrada"
        delta = obj.close_day - obj.created_at
        return str(delta.days) +" días"

    def get_ruta(self, obj):
        try:
            return str(obj.comment.get_model_display())+" numero  "+str(obj.comment.id_model)
        except AttributeError: 
            return ""

    def get_antiguedad(self, obj):
        return (arrow.get(date.today()) - arrow.get(obj.created_at)).days + 1

    def get_up_date(self, obj):
        return (arrow.get(date.today()) - arrow.get(obj.updated_at)).days + 1

    class Meta:
        model = Ticket
        fields = (
            'url', 'id', 'title', 'descrip', 'date', 'assigned', 'owner', 'identifier', 'antiguedad',
            'concept', 'org_name', 'priority', 'close_day', 'closed', 'involved_task', 'archived', 'route', 
            'associated', 'model', 'ruta', 'closedBy', 'up_date', 'contador_dias_cierre', 'reassign_date', 
            'reassignBy', 'recordatorios', 'ot_model', 'ot_id_reference'
        )
class CommentHyperSerializer(serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField()
    user  = serializers.StringRelatedField()
    comment_child = serializers.SerializerMethodField()   
    user_info = serializers.SerializerMethodField()
    created_at_filtered = serializers.SerializerMethodField()
    has_email = serializers.SerializerMethodField()
    comment_tasks =  TicketSerializer(many =True, read_only = True)
    image = serializers.SerializerMethodField()
    def get_comment_child(self, obj):
        childs = Comments.objects.filter(is_child=True,parent=obj).order_by('created_at')
        return CommentSerializer(childs, many=True).data
    def get_image(self,obj):
        try:
            atchivo_imagen =requests.get(settings.CAS_URL + 'get-image-user/' + obj.user.username)
            infoa = json.loads(atchivo_imagen.text)
            return infoa['logo']
        except:
            return ''
    def get_created_at_filtered(self,obj):
        return obj.created_at.strftime('%d/%m/%Y')
    def get_user_info(self,obj):
        return obj.user.first_name + ' ' + obj.user.last_name
    def get_has_email(self, obj):
        return  LogEmail.objects.filter(comment=obj).exists()

    class Meta:
        model = Comments
        fields = ('is_child','url', 'id', 'model', 'content', 'parent',
            'user', 'org_name', 'id_model', 'comment_child', 'created_at', 
            'user_info', 'has_reminder', 'reminder_date', 'modelo_tareas',
            'created_at_filtered', 'has_email', 'comment_tasks','image','mentioned_users')



    

class CedulaHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Cedula
        exclude = ('org_name', 'owner')

class SucursalHyperSerializer(serializers.HyperlinkedModelSerializer):    
    address_sucursal = AddressSerializer(many=True, read_only=True)
    class Meta:
        model = Sucursales
        exclude = ('org_name', 'owner')

class SucursalFullSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SerializerMethodField()   
    address_sucursal = AddressSerializer(many=True, read_only=True) 
    def get_owner(self,obj):
            owner = obj.owner.first_name + ' ' + obj.owner.last_name
            return owner
    class Meta:
        model = Sucursales
        fields = ('url','id','sucursal_name','details','org_name', 'owner','address_sucursal')


from datetime import date
class FullTicketHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = UserInfoVendedoresSerializer(many = False, read_only = True)
    closedBy = UserInfoVendedoresSerializer(many = False, read_only = True)
    involved_task = InvolvedTaskSerializer(many = True, read_only = True)
    assigned = UserInfoVendedoresSerializer(many = False, read_only = True)
    antiguedad = serializers.SerializerMethodField()
    ruta = serializers.SerializerMethodField(read_only = True)
    up_date = serializers.SerializerMethodField()
    contador_dias_cierre = serializers.SerializerMethodField()
    reassignBy = serializers.SerializerMethodField()
    recordatorios = serializers.SerializerMethodField()
    def get_recordatorios(self, obj):        
        if obj:
            recs = RegistroDeRecordatorio.objects.filter(record_model=22,record_id= obj.id, org_name=obj.org_name)
            serializer = RegistroDeRecordatorioSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        else:
            return []
    def get_reassignBy(self, obj):
        response = ''
        if obj.reassignBy:
            response = "%s %s"%(obj.reassignBy.first_name, obj.reassignBy.last_name)
        return response


    def get_contador_dias_cierre(self, obj):
        if not obj.closed:
            return "La tarea no ha sido cerrada"
        created = obj.created_at
        close_date = obj.close_day
        delta = close_date - created
        return "%s días"%delta.days



    def get_ruta(self, obj):
        try:
            return "%s numero %s "%(obj.comment.get_model_display(),obj.comment.id_model)
        except: 
            return ""
     

    
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.created_at
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_up_date(self,obj):
        up_date = int((arrow.get(date.today()) - arrow.get(obj.updated_at)).days) + 1
        return up_date

    class Meta:
        model = Ticket
        fields = ('url', 'id' ,'title', 'descrip', 'date', 'assigned', 'owner', 'identifier', 'antiguedad', 'concept',
                 'org_name', 'priority', 'close_day','closed', 'involved_task', 'archived', 'route', 'associated', 'model', 
                 'ruta','closedBy','up_date', 'contador_dias_cierre', 'reassign_date', 'reassignBy','recordatorios','ot_model','ot_id_reference')


class RespInvolvedHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ResponsablesInvolved
        fields = ('url', 'id', 'responsable', 'resp_type', 'contractor' )

class RefInvolvedHyperSerializer(serializers.HyperlinkedModelSerializer):
    # referenciador = UserInfoVendedoresSerializer(many = False, read_only = True)
    ref_name = serializers.SerializerMethodField()
    def get_ref_name(self, obj):
        return "%s %s"%(obj.referenciador.first_name, obj.referenciador.last_name)
    def to_representation(self, instance):
        serializer = RefInvolvedDetailsHyperSerializer(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data
    class Meta:
        model = ReferenciadoresInvolved
        fields = ('url', 'id', 'referenciador','policy','comision_vendedor', 'ref_name','created_at','updated_at','is_changed','anterior')
class RefInvolvedDetailsHyperSerializer(serializers.HyperlinkedModelSerializer):
    # referenciador = UserInfoVendedoresSerializer(many = False, read_only = True)
    ref_name = serializers.SerializerMethodField()
    comision_vendedor =  serializers.SerializerMethodField()
    
    def get_comision_vendedor(self, obj):
        cv = obj.comision_vendedor
        if obj.comision_vendedor and float(obj.comision_vendedor) >0:
            cv = obj.comision_vendedor
        else:
            ref = obj.referenciador
            cv =get_vendedorcomission_poliza(self,obj.policy,ref)
            if cv == 'No existe subramo':
                cv = obj.comision_vendedor
        return cv
    def get_ref_name(self, obj):
        return "%s %s"%(obj.referenciador.first_name, obj.referenciador.last_name)
    class Meta:
        model = ReferenciadoresInvolved
        fields = ('url', 'id', 'referenciador','policy','comision_vendedor', 'ref_name','created_at','updated_at','is_changed','anterior')
class RefInvolvedInfoSerializer(serializers.HyperlinkedModelSerializer):
    referenciador = UserInfoVendedoresSerializer(many = False, read_only = True, required = False)
    ref_name = serializers.SerializerMethodField()
    comision_vendedor =  serializers.SerializerMethodField()
    def get_ref_name(self, obj):
        return "%s %s"%(obj.referenciador.first_name, obj.referenciador.last_name)
    
    def get_comision_vendedor(self, obj):
        cv = obj.comision_vendedor
        if obj.comision_vendedor and float(obj.comision_vendedor) >0:
            cv = obj.comision_vendedor
        else:
            ref = obj.referenciador
            cv =get_vendedorcomission_poliza(self,obj.policy,ref)
            if cv == 'No existe subramo':
                cv = obj.comision_vendedor
        return cv
    class Meta:
        model = ReferenciadoresInvolved
        fields = ('url', 'id', 'referenciador','policy','comision_vendedor','is_changed','anterior','ref_name')

class RefInvolvedFianzaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ReferenciadoresInvolved
        fields = ('url', 'id', 'referenciador','comision_vendedor','is_changed','anterior')

class ReferenciadoresInvolvedHyperSerializer(serializers.HyperlinkedModelSerializer):
    # referenciador = serializers.SerializerMethodField()  
    # referenciador = serializers.SlugRelatedField(many=False,read_only=True,slug_field='id')    
    referenciador = UserInfoVendedoresSerializer(many = False, read_only = True)
    class Meta:
        model = ReferenciadoresInvolved
        fields = ('url', 'id', 'referenciador','policy','comision_vendedor','is_changed','anterior')

class NotificationstHyperSerializer(serializers.HyperlinkedModelSerializer):
    involucrado_por_area = serializers.BooleanField(read_only = True, required = False)
    class Meta:
        model = Notifications
        fields = ('url', 'title', 'description', 'seen', 'involucrado', 'created_at','id_reference', 
            'involucrado_por_area', 'model', 'org_name','type_notification', 'site','poliza_groupinglevel',
            'poliza_contractor','poliza_provider','poliza_ramo','startsAt','id','owner')

class NotificationsAppHyperSerializer(serializers.HyperlinkedModelSerializer):
    involucrado_por_area = serializers.BooleanField(read_only = True, required = False)
    image = serializers.SerializerMethodField()
    recRegistro = RegistroDeRecordatorioSerializer(many = False, read_only = True)
    recordatorio =RecordatoriosSerializer(many = False, read_only = True)
    def get_image(self,obj):
            queryset = NotificationFile.objects.filter(owner = obj.id)
            serializer = NotificationsFileSerializer(instance = queryset, context={'request':self.context.get("request")}, many = True)
            return serializer.data
    class Meta:
        model = Notifications
        fields = ('url', 'title', 'description', 'seen', 'involucrado', 'created_at','id_reference', 
            'involucrado_por_area', 'model', 'org_name','type_notification', 'site','image','poliza_groupinglevel',
            'poliza_contractor','poliza_provider','poliza_ramo','created_at','id','startsAt','owner','recRegistro','recordatorio')

class SaveTicketHyperSerializer(serializers.HyperlinkedModelSerializer):
    involved_task = InvolvedMinTaskSerializer(many = True)
    class Meta:
        model = Ticket
        fields = ('url', 'id' ,'title', 'descrip', 'date', 'assigned', 'priority', 'concept', 'close_day','closed', 
            'involved_task', 'identifier', 'archived', 'route', 'associated', 'model','closedBy')

    def create(self, validated_data):
        request = self.context.get('request')
        involved = validated_data.pop('involved_task')

        ticket = Ticket.objects.create(**validated_data)

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
        notification.send_push(request)
        
        involved_mails = []
        for inv in involved:
            involv = Involved.objects.create(involved = ticket, owner = ticket.owner, org_name = ticket.org_name, **inv)
            involved_mails.append(involv.person.email)

            notification_involved = Notifications.objects.create(
                model = 22, 
                involucrado = True,
                id_reference = ticket.id, 
                title = ticket.title , 
                description = ticket.descrip , 
                assigned = involv.person, 
                owner = ticket.owner, 
                org_name = ticket.org_name 
            )
            notification_involved.send_push(request)
            try:
                if request.user.email != involv.person.email:
                    notification_involved.send_email(request, ticket)
            except Exception as et:
                print('error **',et)
        
        notification.send_email(request, ticket)
        

        return ticket

class SaveTicketHyperSerializerMc(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Ticket
        fields = (
            'url', 'id', 'title', 'descrip', 'date', 'assigned', 'priority',
            'concept', 'close_day', 'closed', 'involved_task', 'identifier',
            'archived', 'route', 'associated', 'model', 'closedBy'
        )

    def create(self, validated_data):
        
        request = self.context.get('request')
        involved = validated_data.pop('involved_task')
        file_data = request.data.get('link')
        print("request:",request)

        try:
            if ';base64,' in file_data:
                file_str = file_data.split(';base64,')[-1]
            else:
                file_str = file_data

            decoded_file = base64.b64decode(file_str)

            content_file = ContentFile(decoded_file, name="uploaded_file.pdf")
        except Exception as e:
            print('---Error **',e)

        ticket = Ticket.objects.create(**validated_data)
        file = TicketFile.objects.create(
                owner=ticket,
                arch=content_file,
                nombre=content_file.name,
                org_name=ticket.org_name,
                sensible=False
            )

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
        notification.send_push(request)
        
        involved_mails = []
        for inv in involved:
            involv = Involved.objects.create(involved = ticket, owner = ticket.owner, org_name = ticket.org_name, **inv)
            involved_mails.append(involv.person.email)

            notification_involved = Notifications.objects.create(
                model = 22, 
                involucrado = True,
                id_reference = ticket.id, 
                title = ticket.title , 
                description = ticket.descrip , 
                assigned = involv.person, 
                owner = ticket.owner, 
                org_name = ticket.org_name 
            )
            notification_involved.send_push(request)
            try:
                if request.user.email != involv.person.email:
                    notification_involved.send_email(request, ticket)
            except Exception as et:
                print('error **',et)
        
        notification.send_email(request, ticket)
        

        return ticket

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goals
        fields = ('goal',)

class ExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        exclude = ('org_name',)
class ExpensesInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = ('cantidad', 'concept', 'month', 'org_name', 'id', 'url')

# shared Filtro por usuario
class SharedApiHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Shared
        fields = ('id','url', 'owner', 'org_name', 'grupo', 'usuario','poliza', 'aseguradora','grupo_de_contratantes','contractor', 'descripcion')


class DjangoGroupInfoHyperSerializer(serializers.HyperlinkedModelSerializer):
    # group = DjangoGroupsHyperSerializer(many = False, read_only = True)
    class Meta:
        model = DjangoGroupInfo
        fields = ('id','org_name', 'is_active','group','owner')


class DjangoGroupsHyperSerializer(serializers.HyperlinkedModelSerializer):
    group_info = DjangoGroupInfoHyperSerializer(many = False, read_only = True)
    class Meta:
        model = DjangoGroups
        fields = ('name', 'id','url','group_info')


class SignatureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Signature
        fields = ('signature', 'enabled','in_amazon','image_amazon','id','url')

class BirthdateTemplateSerializer(serializers.HyperlinkedModelSerializer):
    useremail = serializers.SerializerMethodField(read_only=True)
    def get_useremail(self, obj):
        request = self.context.get('request')
        if request:
            return getOrg(request)
        return None
    class Meta:
        model = BirthdateTemplate
        fields = ('text','subject','enabled','remitente','useremail')

class EmailTemplateFullSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ('name','title','text','org_name','owner', 'id', 'created_at', 'url','bottom_text','template_model','subject_default','ramo_code',
                'dato_cnumcertificado','dato_cvigencia','dato_caseguradora','dato_csubramo','dato_cmoneda','dato_cfrecuenciapago','dato_casegurado',
                'dato_cptotal','dato_cpneta','dato_cderecho','dato_crpf','dato_civ','dato_ccontratante')


class ConfigKbiFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigKbi
        fields = ('tipocambio','id',)


class ReadFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LecturaArchivos
        fields = ('nombre', 'tipo_poliza', 
        'aseguradora', 'ramo', 'subramo', 'url', 'id')


class TagsLecturaArchivosGeneralSerializer(serializers.HyperlinkedModelSerializer):
    label = serializers.SerializerMethodField()
    xmin = serializers.SerializerMethodField()
    ymin = serializers.SerializerMethodField()
    xmax = serializers.SerializerMethodField()
    ymax = serializers.SerializerMethodField()
    
    def get_label(self,instance):
        obj = {
            "Nombre": "name",
            "Fecha de nacimiento": "dob",
            "Sexo": "sex",
            "RFC": "rfc",
            "Número de teléfono": "phone",
            "Correo electrónico": "email",
            "Dirección": "address",
            "Dirección complementaria": "address_2",
            "Código postal": "zip_code",
            "Marca del vehículo": "brand",
            "Descripción del vehículo": "vehicle",
            "Versión del vehículo": "version",
            "Año del vehículo": "year_model",
            "Número de serie": "serial",
            "Código del motor": "motor",
            "Código de placas": "plates",
            "Tipo de carga": "charge_type",
            "Aseguradora": "insurance",
            "Ramo del seguro": "insurance_branch",
            "Número de poliza": "policy_number",
            "Tipo de moneda": "currency",
            "Forma de pago": "payment_method",
            "Paquete del contrato": "policy_package",
            "Procedencia": "origin" ,
            "Tipo de vehículo": "vehicle_type",
            "Fumador" :"smoker_condition",
            "Tipo de suma asegurada" :"type_sa",
            "Tipo de póliza" :"policy_type",
            "Beneficiario" :"beneficiarie_name",
            "Fecha nacimiento beneficiario" :"beneficiarie_birthdate",
            "Tipo régimen" :"j_name",
            "Tipo de relación" :"relationship",
            "Porcentaje designado" :"designation_percentage",
            "RFC beneficiario" :"beneficiarie_rfc",
            "Sexo beneficiario" :"beneficiarie_sex",
            "Número de póliza" :"policy_number",
            "Estado de circulación" : "circulation_state",
            "Color del vehículo" : "vehicle_color",
            "Uso del vehículo" : "vehicle_use",
            "Servicio del vehículo" : "vehicle_service",
            "Antigüedad"  : "antiquity" ,
            "Sexo beneficiario"  : "beneficiarie_sex" ,
            "Antigüedad(Beneficiario)" : "beneficiarie_antiquity" ,

            "Prima Neta" : "p_neta" ,
            "Monto de Derecho" : "derecho" ,
            "Monto de RPF" : "rpf" ,
            "Conducto de pago" : "payment_conduit" ,
            "Nivel hospitalario" : "hospital_level", 
            "Nombre Dependiente" : "relationship_name", 
            "Fecha de nacimiento Dependiente" : "relationship_birthdate", 
            "Sexo Dependiente" : "relationship_sex", 
            "Antigüedad Dependiente" : "relationship_antiquity",

            "Tipo de daño" : "damage_type",
            "Dirección de la pertenencia" : "item_address",
            "Pertenencia asegurada" : "insured_item",
            "Detalles de la pertenencia" : "item_details"
        }
        try:
            return obj[instance.name]
        except:
            return instance.name

    def get_xmin(self,instance):
        response = instance.x
        try:
            return float(response)
        except:
            return response

    def get_ymin(self,instance):
        response = instance.y
        try:
            return float(response)
        except:
            return response

    def get_xmax(self,instance):
        response = float(instance.x) + float(instance.width)
        return response

    def get_ymax(self,instance):
        response = float(instance.y) + float(instance.height)
        return response

    class Meta:
        model = TagsLecturaArchivos
        fields = ('label', 'xmin', 'ymin', 'xmax', 'ymax')



class TagsLecturaArchivosSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TagsLecturaArchivos
        fields = ('id', 'url', 'areaid', 'cssClass', 'height', 
        'name', 'pageNumber', 'tag', 'width', 'x', 'y', 'z', 'owner')



class RepositorioPagoSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField('username', read_only = True)
    
    class Meta:
        model = RepositorioPago
        fields = ('id', 'url', "nombre_archivo", "registros_del_archivo", 
        "movimientos_cargados", "movimientos_no_cargados", "owner", "arch",
        "org_name", "fuente", "created_at")

class ConfigProviderScrapperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField('username', read_only = True)
    
    class Meta:
        model = ConfigProviderScrapper
        fields = ('id', 'url', 'created_at','updated_at','org_name','owner','username','password','title',
            'descrip','periodicidad','startDate','provider','ramos','subramos','active','startDate_scraper','endDate_scraper')

class ProviderMiniSerializer(serializers.ModelSerializer):
    class Meta:
       model = Provider
       fields = ('id', 'alias', 'url','compania','website')

class ConfigProviderScrapperInfoSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField('username', read_only = True)
    provider = ProviderMiniSerializer(many = False, read_only=True)
    ramos_sel = serializers.SerializerMethodField()
    subramos_sel = serializers.SerializerMethodField()
    def get_ramos_sel(self, instance):
        ramos_sel=[]
        try:
            ram = Ramos.objects.filter(ramo_code__in = instance.ramos,provider = instance.provider, org_name = instance.org_name)            
            serializer = RamosHyperSerializer(instance = ram, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        except Exception as o:
            print('err',o)
            return 'Todos'
    def get_subramos_sel(self, instance):
        subramos_sel=[]
        try:
            ram = SubRamos.objects.filter(subramo_code__in = instance.subramos,ramo__provider = instance.provider, org_name = instance.org_name)       
            serializer = SubramoHyperSerializer(instance = ram, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        except Exception as o:
            print('err',o)
            return 'Todos'
    class Meta:
        model = ConfigProviderScrapper
        fields = ('id', 'url', 'created_at','updated_at','org_name','owner','username','password','title',
            'descrip','periodicidad','startDate','provider','ramos','subramos','active','ramos_sel','subramos_sel','startDate_scraper','endDate_scraper')


class LecturaArchivosSerializer(serializers.HyperlinkedModelSerializer):
    archivos_lectura = LecturaFileSerializer(many=True, read_only=True)
    tags_lectura_archivos = TagsLecturaArchivosSerializer(many=True, read_only=True)
    aseguradora = serializers.SerializerMethodField()
    ramo = serializers.SerializerMethodField()
    subramo = serializers.SerializerMethodField()

    def get_aseguradora(self, instance):
        try:
            aseguradora = Provider.objects.get(id = instance.aseguradora)
            return aseguradora.alias
        except:
            return ''
    
    def get_ramo(self, instance):
        try:
            ramo = Ramos.objects.get(id = instance.ramo)
            return ramo.ramo_name
        except:
            return ''
    
    def get_subramo(self, instance):
        try:
            subramo = SubRamos.objects.get(id = instance.subramo)
            return subramo.subramo_name
        except:
            return ''
        
    class Meta:
        model = LecturaArchivos
        fields = ('nombre', 'tipo_poliza', 
        'aseguradora', 'ramo', 'subramo', 'archivos_lectura', 'url', 
        'id', 'created_at', 'tags_lectura_archivos')

class LecturaArchivosGeneralSerializer(serializers.HyperlinkedModelSerializer):
    archivos_lectura = LecturaFileGeneralileSerializer(many=True, read_only=True)
    tags_lectura_archivos = TagsLecturaArchivosGeneralSerializer(many=True, read_only=True)
    aseguradora = serializers.SerializerMethodField()
    ramo = serializers.SerializerMethodField()
    subramo = serializers.SerializerMethodField()
    tipo_poliza = serializers.SerializerMethodField()
    metodo = serializers.SerializerMethodField()

    def get_metodo(self, instance):
        if instance.nombre in ['AUTOS_MANUAL_MAPFRE', 'AUTOS_MANUAL_PS', 
        'AUTOS_MANUAL_SURA', 'GNP_VIDA_MANUAL', 'ALLIANZ_GMM_MANUAL','DAÑOS_MANUAL_ZURICH','DAÑOS_MANUAL_CHUBB']:
            return 'REGEX'
        else:
            return 'OCR'

    def get_tipo_poliza(self, instance):
        try:
            tipos_poliza = {
                '1' : 'Individual',
                '12': 'Colectiva',
                '3': 'Grupo'
            }
            return tipos_poliza[instance.tipo_poliza]
        except:
            return instance.tipo_poliza

    def get_aseguradora(self, instance):
        try:
            aseguradora = Provider.objects.get(id = instance.aseguradora)
            return aseguradora.alias
        except:
            return ''
    
    def get_ramo(self, instance):
        if instance.nombre in ['AUTOS_MANUAL_SURA']:
            return 'Daños'
        if instance.nombre in ['GNP_VIDA_MANUAL']:
            return 'Vida'
        if instance.nombre in ['ALLIANZ_GMM_MANUAL']:
            return 'Accidentes y Enfermedades'
        
        
        try:
            ramo = Ramos.objects.get(id = instance.ramo)
            return ramo.ramo_name
        except:
            return ''
    
    def get_subramo(self, instance):
        if instance.nombre in ['AUTOS_MANUAL_SURA']:
            return 'Automóviles'
        if instance.nombre in ['GNP_VIDA_MANUAL']:
            return 'Vida'
        if instance.nombre in ['ALLIANZ_GMM_MANUAL']:
            return 'Gastos Médicos'
        
        try:
            subramo = SubRamos.objects.get(id = instance.subramo)
            return subramo.subramo_name
        except:
            return ''
        
    class Meta:
        model = LecturaArchivos
        fields = ('nombre', 'tipo_poliza', 
        'aseguradora', 'ramo', 'subramo', 'archivos_lectura', 'url', 
        'id', 'created_at', 'tags_lectura_archivos','org_name', 'metodo')


class LecturaArchivosEditSerializer(serializers.HyperlinkedModelSerializer):
    archivos_lectura = LecturaFileSerializer(many=True, read_only=True)
    tags_lectura_archivos = TagsLecturaArchivosSerializer(many=True, read_only=True)
    tags_existentes_general = serializers.SerializerMethodField()

    def get_tags_existentes_general(self, obj):
        tla = []
        la = LecturaArchivos.objects.filter(
            aseguradora = obj.aseguradora,
            org_name = obj.org_name,
            ramo = obj.ramo,
            subramo = obj.subramo
        )
        tla = TagsLecturaArchivos.objects.filter(
            owner__in = list(la)
        ).values_list('name', flat=True)
        return tla
        
        
 
    class Meta:
        model = LecturaArchivos
        fields = ('nombre', 'tipo_poliza', 
        'aseguradora', 'ramo', 'subramo', 'archivos_lectura', 'url', 
        'id', 'created_at', 'tags_lectura_archivos', 'tags_existentes_general')

class PromotoriaTableroSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField('username', read_only = True)
    
    class Meta:
        model = PromotoriaTablero
        fields = ('id', 'url', 'created_at','updated_at','org_name','owner','polizas_ots','config',
            'is_active','color','name','org_name')


class PolizaHyperPromotoriaSerializer(serializers.HyperlinkedModelSerializer):
    aseguradora=serializers.SlugRelatedField(many=False,read_only=True,slug_field='alias')
    subramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='subramo_name')
    ramo=serializers.SlugRelatedField(many=False,read_only=True,slug_field='ramo_name')
    contractor=serializers.SlugRelatedField(many=False,read_only=True,slug_field='full_name')
    # clave = ClavesByProviderHyperSerializer(many=False, read_only=True)
    forma_de_pago = serializers.SerializerMethodField()
    antiguedad = serializers.SerializerMethodField()
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.created_at
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad
    def get_forma_de_pago(self,obj):
        return obj.get_forma_de_pago_display()

    class Meta:
        model = Polizas
        fields = ('id', 'poliza_number','end_of_validity', 'contractor',
            'aseguradora','subramo','ramo','start_of_validity',
            'forma_de_pago', 'status', 'clave','sucursal','collection_executive','emision_date',
            'contratante_subgroup','fecha_pago_comision','maquila','exchange_rate','created_at','document_type',
            'internal_number','month_factura','folio_factura','date_maquila','year_factura','date_bono','antiguedad'
            )

class EndorsementHyperPromotoriaSerializer(serializers.HyperlinkedModelSerializer):
    policy = PolizaHyperPromotoriaSerializer(read_only=True)
    antiguedad = serializers.SerializerMethodField()
    antiguedad = serializers.SerializerMethodField()
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.created_at
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad
    
    def get_antiguedad(self,obj):
        today = date.today()
        a = arrow.get(today)
        aux_date = obj.created_at
        b = arrow.get(aux_date)
        antiguedad = (a-b).days
        antiguedad = int(antiguedad)+1
        return antiguedad

    def get_owner(self,obj):
        owner = obj.owner.first_name + ' ' + obj.owner.last_name
        return owner

    class Meta:
        model = Endorsement
        fields = ('id', 'url', 'endorsement_type', 'policy', 'status','created_at' ,'updated_at','antiguedad',
                'end_date','init_date', 'internal_number','antiguedad','insurancefolio','number_endorsement','observations') 

class PromotoriaTableroDetailSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField('username', read_only = True)
    data_details = serializers.SerializerMethodField()
    def get_data_details(self, obj):
        request = self.context.get('request')
        user = request.user
        ui = UserInfo.objects.filter(user = user)
        if ui.exists():
            ui = ui.first()
        else:
            ui = None
        if obj.polizas_ots:
            try:
                obj.polizas_ots = json.loads(obj.polizas_ots)
            except Exception as eee:
                obj.polizas_ots = obj.polizas_ots
                try:
                    obj.polizas_ots = eval(obj.polizas_ots)
                except Exception as e:
                    pass
            for y in obj.polizas_ots:
                if ui and ui.type_ots and int(ui.type_ots)==1:
                    y['details_endoso']=[]
                    if 'polizas' in y and y['polizas']:
                        listap = Polizas.objects.filter(pk__in = y['polizas'],status=1, org_name=obj.org_name)
                        y['details_polizas'] = PolizaHyperPromotoriaSerializer(instance = listap, context={'request':self.context.get("request")}, many = True).data
                elif ui and ui.type_ots and int(ui.type_ots)==2:
                    y['details_polizas']=[]
                    if 'endoso' in y and y['endoso']:
                        listae = Endorsement.objects.filter(pk__in = y['endoso'], org_name=obj.org_name,status__in=[5,1])
                        y['details_endoso'] = EndorsementHyperPromotoriaSerializer(instance = listae, context={'request':self.context.get("request")}, many = True).data
                elif ui and ui.type_ots and int(ui.type_ots)==0:
                    if 'polizas' in y and y['polizas']:
                        listap = Polizas.objects.filter(pk__in = y['polizas'],status=1, org_name=obj.org_name)
                        y['details_polizas'] = PolizaHyperPromotoriaSerializer(instance = listap, context={'request':self.context.get("request")}, many = True).data
                    if 'endoso' in y and y['endoso']:
                        listae = Endorsement.objects.filter(pk__in = y['endoso'], org_name=obj.org_name,status__in=[5,1])
                        y['details_endoso'] = EndorsementHyperPromotoriaSerializer(instance = listae, context={'request':self.context.get("request")}, many = True).data
                else:
                    if 'polizas' in y and y['polizas']:
                        listap = Polizas.objects.filter(pk__in = y['polizas'],status=1, org_name=obj.org_name)
                        y['details_polizas'] = PolizaHyperPromotoriaSerializer(instance = listap, context={'request':self.context.get("request")}, many = True).data
                    if 'endoso' in y and y['endoso']:
                        listae = Endorsement.objects.filter(pk__in = y['endoso'], org_name=obj.org_name,status__in=[5,1])
                        y['details_endoso'] = EndorsementHyperPromotoriaSerializer(instance = listae, context={'request':self.context.get("request")}, many = True).data
                
                
                
        return obj.polizas_ots

    class Meta:
        model = PromotoriaTablero
        fields = ('id', 'url', 'created_at','updated_at','org_name','owner','polizas_ots','config',
            'is_active','color','name','org_name','data_details')

class LogInfoSerializer(serializers.ModelSerializer):
    model = serializers.IntegerField(required = True)
    event = serializers.CharField(required = True)
    identifier = serializers.CharField(required = True)
    class Meta:
        model = Log
        fields = ('id','model','event','identifier', 'associated_id','change','original')

class SmsTemplateFullSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SmsTemplate
        fields = ('title','text','org_name','owner', 'id', 'created_at', 'url','type_message')

def get_vendedorcomission_poliza(self,poliza,parVendor):
    vendedor = ''
    if not parVendor:
        if poliza.contractor:
            vendedor = poliza.contractor.vendor
        else:
            print('faltan datos')
    else:
        vendedor = parVendor
    
    if vendedor:
        try:
            uiUser = User.objects.get(pk = vendedor)
        except Exception as error:
            uiUser = None
            try:
                uiUser = User.objects.get(username = vendedor)
            except Exception as error2:
                uiUser = None
                print('eeeror',uiUser,error2)
        ui = UserInfo.objects.get(user = vendedor)
        vendedor = Vendedor.objects.filter(user=ui).order_by('-id').first()
        sub_ramos = SubramosVendedor.objects.filter(vendedor =  vendedor)
        try:#get referenciadores policy
            refs = ReferenciadoresInvolved.objects.filter(referenciador = uiUser, policy = poliza).exclude(is_changed=True)
            for rf in refs:
                if float(rf.comision_vendedor) != 0.00:
                    return rf.comision_vendedor
        except Exception as e:
            print('--error refs--',e)
        esAseguradora=''
        esAfianzadora=''
        if poliza and poliza.aseguradora and poliza.aseguradora.provider_type and poliza.aseguradora.provider_type==1:
            esAseguradora=True
        if poliza and poliza.aseguradora and poliza.aseguradora.provider_type and poliza.aseguradora.provider_type==2:
            esAfianzadora=True
        try:
            if poliza.ramo:
                specific_subramo = sub_ramos.get(provider = 0, ramo = (poliza.ramo.ramo_code)*-1, subramo = 0)
                # print('--com vendeo',specific_subramo.comision)
                return specific_subramo.comision
        except SubramosVendedor.DoesNotExist:
            try:
                if poliza.ramo:
                    specific_subramo = sub_ramos.get(provider = 0, ramo = (poliza.ramo.ramo_code)*-1, subramo = (poliza.subramo.subramo_code)*-1)
                    # print('-2-com vendeo',specific_subramo.comision)
                    return specific_subramo.comision
            except SubramosVendedor.DoesNotExist:
                try:
                    specific_subramo = sub_ramos.get(provider = poliza.aseguradora.id, ramo = poliza.ramo.id, subramo = poliza.subramo.id)
                    # print('-3-com vendeo',specific_subramo.comision)
                    return specific_subramo.comision
                except SubramosVendedor.DoesNotExist:
                    try:
                        specific_subramo = sub_ramos.get(provider = poliza.aseguradora.id, ramo = poliza.ramo.id, subramo = 0)
                        # print('-4-com vendeo',specific_subramo.comision)
                        return specific_subramo.comision
                    except SubramosVendedor.DoesNotExist:
                        try:
                            specific_subramo = sub_ramos.get(provider = poliza.aseguradora.id, ramo = 0, subramo = 0)
                            # print('-5-com vendeo',specific_subramo.comision)
                            return specific_subramo.comision
                        except SubramosVendedor.DoesNotExist:
                            try:
                                specific_subramo = sub_ramos.get(provider = -2, ramo = 0, subramo = 0)
                                if esAfianzadora:
                                    specific_subramo = sub_ramos.get(provider = -1, ramo = 0, subramo = 0)
                                    if not specific_subramo:
                                        specific_subramo = sub_ramos.get(provider = -2, ramo = 0, subramo = 0)
                                # print('-6-com vendeo',specific_subramo.comision)
                                return specific_subramo.comision
                            except SubramosVendedor.MultipleObjectsReturned:
                                specific_subramo = sub_ramos.filter(provider = -2, ramo = 0, subramo = 0)[0]
                                # print('-7-com vendeo',specific_subramo.comision)
                                return specific_subramo.comision
                            except SubramosVendedor.DoesNotExist:
                                try:
                                    specific_subramo = sub_ramos.get(provider = 0, ramo = 0, subramo = 0)
                                    # print('-8-com vendeo',specific_subramo.comision,poliza)
                                    return specific_subramo.comision
                                except SubramosVendedor.MultipleObjectsReturned:
                                    specific_subramo = sub_ramos.filter(provider = 0, ramo = 0, subramo = 0)[0]
                                    # print('-9-com vendeo',specific_subramo.comision)
                                    return specific_subramo.comision
                                except SubramosVendedor.DoesNotExist:
                                    # print('-10-com vendeo',specific_subramo.comision)
                                    return 'No existe subramo'