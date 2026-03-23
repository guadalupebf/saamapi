 # -*- coding: utf-8 -*-
from dateutil.relativedelta import TU
from django.db import models
from contratantes.models import Group as ContractorGroup, Contractor
from .push_messages import send_push
from aseguradoras.models import Provider
from django.contrib.auth.models import User, Group as DjangoGroups
from django.core.mail import EmailMessage,EmailMultiAlternatives
from django.template.loader import render_to_string
from jsonfield import JSONField 
import re
from django.conf import settings
import requests
import json
from django.contrib.postgres.fields import ArrayField
import random
import datetime
import base64

EVENT_CHOICES = ((1, u'creó'), (2, u'eliminó'), (3, u'actualizó'), (4, u'canceló'),(5,u'consulto'))
PERIODICIDAD_CHOICES =((1,u'Por día'),(2,u'Cada 2 días'),(3,u'Cada 3 días'),(4,u'Cada 5 días'),(5,u'Cada 10 días'),(6,u'Cada 15 días'),
    (7,u'Cada mes'))
MODEL_CHOICES = ((1, u'Pólizas'), 
    (2, u'Contratantes'), 
    (4, u'Recibos'), 
    (5, u'Siniestros'), 
    (6, u'Renovaciones'),    
    (7, u'Recibos-Comisiones'), 
    (8, u'Grupos'), 
    (9, u'Paquetes'), 
    (10, u'Endosos'), 
    (11, u'Aseguradoras'), 
    (12, u'Estados de Cuenta'), 
    (13, u'Fianzas'), 
    (14, u'Afianzadoras'), 
    (15, u'Comentarios'), 
    (16, u'Logs') , 
    (17, u'Cartas'), 
    (18, u'Colectividades'), 
    (19, u'Graphs'),
    (20, u'Notes'),
    (21, u'Fianzas Reclamaciones'), 
    (22, u'Tareas'),
    (23, u'Tareas Completados'),
    (24, u'Events'),
    (25, u'Certificado'),
    (26, u'Reportes'),
    (27, u'NotificaciónApp'),
    (28, u'Flotillas'),
    (29, u'Plantilla Correo'), 
    (30, u'Cotizacion'), 
    (31, u'Recordatorios'), 
    (32, u'LogSystem'), 
    (33, u'Plantilla SMS'), 
    (34, u'Conceptos Generales Referenciador'), 
    (35, u'Configuración Correos Automáticos'), 
    (36, u'Tablero'), 
    )

LETTER_MODEL_CHOICES = ((4, u'Recibos'), (1, u'Pólizas'), (5, u'Siniestros'), (3, u'Renovaciones'), (2, u'Endosos'), (6, u'OT'))
TYPE_CHOICES = ((1, u'Casa'), (2, u'Oficina'), (3, u'Móvil'),(4,u'CFDI'), (5, u'Otros'),(6,u'WhatsApp/SMS'))
TIPO_COBRO_CHOICES = ((0, u'Domiciliado'), (1, u'No Domiciliado'), (2, u'Todos'), (3, u'Domiciliado'), (4, u'No Domiciliado y Agente'))
TIPO_FECHA_CHOICES = ((1, u'Inicio de vigencia'), (2, u'Vencimiento'))
TIPO_RECIBO_CHOICES =((0, u'Todos'), (1, u'Recibos de Póliza/Endoso'), (2, u'Recibos de Póliza'), (3, u'Notas de Crédito'))
TIPO_MESSAGE_CHOICES = ((1, u'Whatsapp'), (2, u'SMS'),(0,u'Whatsapp/SMS'))

EMAIL_MODEL_CHOICES = ((1, 'OT Solicitud'), (2, 'OT Registro'), (3, 'Siniestro Solicitud'), (4, 'Siniestro Fin'), 
                       (5, 'Recordatorio'), (6, 'Pago'), (7, 'Nota Creada'), (8, 'Nota Aplicada'), (9, 'Renovar póliza'), (10, 'Recordatorio de renovación póliza'),
                       (11,'Siniestro En Trámite'),(12,'Siniestro Cancelado'),(13,'Siniestro Rechazado'),(14,'Siniestro En Espera'),(15,'Recordatorio Pago WhatsApp/SMS'))

EMAIL_FREQ_CHOICES = ((1, 'Mensual'), (2, 'Quincenal'), (3, 'Semanal'), (4, 'Vencido'), (5, 'SemanalPosterior'), 
    (6, 'QuincenalPosterior'), (7, 'MensualPosterior'),(8,'Pólizas a renovar vencidas/-10 DIAS ANTES DEL'),(9,'-20 DIAS ANTES DEL'),(10,'+20 DIAS ANTES DEL'))
EMAIL_TYPE_CHOICES = ((1, 'Póliza'), (2, 'Póliza Ind de Colectividad'),((3, 'Póliza Grupo')),(0,'Todos'))

EMAIL_RAMO_CHOICES = ((1, 'Vida'), (2, 'Accidentes y enfermedades'),(3,'Daños'),(0,'Todos'))

GRAPHIC_TYPES = ((1, 'OTs'), (2, 'Cobranza'), (3, 'Renovaciones'), (4, 'Siniestros'), (5, 'Tareas'), (6, 'Cotizaciones'))
GRAPHIC_OPTION_FILTER = ((1, 'Inicio de vigencia'), (2, 'Vencimiento'), (3, 'Ambos'))
PRIORITY = ((3, 'Baja'), (2, 'Media'), (1, 'Alta'))
RAMO_CHOICES  = ((1, u'Sin ramo'), (2, u'Daños'), (3, u'Personas'), (4, u'Automóviles'))
CONCEPT = ((3, 'Endoso'), (2, 'Emision'), (1, 'Cotizacion'), (4, 'Corrección'), (5, 'Cancelación'), (6, 'Renovación'), (7, 'Otro'), (8, 'Reembolso'),
    (9, 'Programación de cirugía'), (10, 'Endoso B'),(11, 'Endoso D'),(12,'Reconocimiento de antigüedad'),(13,'Carta de antigüedad'))
AREAS = ((1, 'Cobranza'), (2, 'Emisión'), (3, 'Siniestros'),(0, 'General'))
MONTHS = ((1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),(4, 'Abril'), (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'),(12, 'Diciembre'))

TYPENOT_CHOICES = ((1, u'Notificación'), (2, u'Promoción'))

EMAIL_RELATIVE_TIME = ((1, 'ANTES DE'), (2, 'DESPUES DE'), (3, 'VENCIDO')) 
EMAIL_RELATIVE_DATE = ((1, 'Inicio de vigencia'), (2, 'Vencimiento'), (3, 'VENCIDO'))
OT_MODEL_CHOICES = ((1,u'Póliza'),(2, u'Endoso'),(3,u'Cotización'),(4,u'Siniestros'),(5,u'Certificados'),(6,u'Endoso (plantilla adicional)'))
TEMPLATE_MODEL_CHOICES = ((1,u'Cobranza'),(2, u'Póliza'))
TYPETEMPLATE_CHOICES = ((1, u'SMS'), (2, u'WHATSAPPWEB'),(3, u'WHATSAPPWEBSINIESTRO'))
    
class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-
    . fields.
    updating ``created`` and ``updated_at``
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Sucursales(TimeStampedModel):
    sucursal_name = models.CharField(max_length=500, blank=True, null=True)
    owner = models.ForeignKey('auth.User', related_name='sucursal_owner', null = True, on_delete=models.CASCADE)
    details = models.CharField(max_length=500, blank=True, null=True)
    org_name =  models.CharField(max_length=50, null=True)


class Areas(TimeStampedModel):
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    area_name = models.CharField(max_length=500)

    def __str__(self):
        return self.area_name


class AreasResponsability(TimeStampedModel):
    user = models.ForeignKey(User, related_name = 'user_area', on_delete=models.CASCADE)
    org_name = models.CharField(max_length=500, null = True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    area = models.ForeignKey(Areas, related_name = 'responsable_area', on_delete=models.CASCADE)
    ramo = models.IntegerField(default = 1, choices = RAMO_CHOICES)


class States(models.Model):
    state = models.CharField(max_length=500)

    def __str__(self):
        return self.state

    class Meta:
        ordering = ('state',)


class Cities(models.Model):
    city = models.CharField(max_length=500)
    state = models.ForeignKey(States, related_name='cities', on_delete=models.CASCADE)

    def __str__(self):
        return self.city

    class Meta:
        ordering = ('city', )

class Address(models.Model):
    administrative_area_level_1 = models.CharField(max_length=500, blank=True) # Estado
    administrative_area_level_2 = models.CharField(max_length=500, blank=True) # Municipio
    country = models.CharField(max_length=500, blank=True) # País
    sublocality = models.CharField(max_length=500, blank=True) # Colonia
    route = models.CharField(max_length=500, blank=True) # Calle/Avenida
    street_number = models.CharField(max_length=500, blank=True) # Número Ext
    street_number_int = models.CharField(max_length=500, blank=True) # Número Int
    postal_code = models.CharField(max_length=500, blank=True) # Código Postal
    details = models.TextField(blank=True, null=True) # Detalles del domicilio
    tipo = models.TextField(blank=True, null=True) # Tipo de direccion
    contractor = models.ForeignKey(Contractor, related_name="address_contractor", null=True, blank=True, on_delete=models.CASCADE)#Nueva FK Contractor
    aseg = models.ForeignKey('aseguradoras.Provider', related_name="address_provider", null=True, blank=True, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursales, related_name="address_sucursal", null=True, blank=True, on_delete=models.CASCADE)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', related_name='address', null=True, on_delete=models.CASCADE)
    migrated = models.BooleanField(default = False)

    def concatenate(self):
        c = ' '.join([self.route, self.street_number, self.street_number_int,  self.sublocality, self.administrative_area_level_2, self.administrative_area_level_1, self.country])
        c = c.replace(',', '')
        c = re.sub(' +', ' ', c)
        return c
        
    def __str__(self):
        return self.concatenate()


class Log(TimeStampedModel):
    model = models.IntegerField(default = 0, choices = MODEL_CHOICES)
    event = models.IntegerField(default = 0, choices = EVENT_CHOICES)
    associated_id = models.IntegerField(default = 0, null = True)
    identifier = models.TextField(blank =True, null = True)
    user = models.ForeignKey('auth.User', related_name='log_user', on_delete=models.CASCADE)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    # Mofdified to save specific changes    
    original = JSONField(null = True, blank =True, default = "", max_length=6000)
    change = JSONField(null = True, blank =True, default = "", max_length=6000)

    def __str__(self):
        return "%s: El usuario %s %s el modelo %s con identificador: %s" % (self.created_at.strftime("%d/%m/%Y-%H:%M:%S"), self.user.username, self.get_event_display(), self.get_model_display(), self.identifier)


class LogEmail(TimeStampedModel):
    model = models.IntegerField(default = 0, choices = MODEL_CHOICES)
    associated_id = models.CharField(null=False, max_length=500)
    log = models.ForeignKey(Log, null=True, on_delete=models.CASCADE)
    comment = models.ForeignKey('Comments', null=True, on_delete=models.CASCADE)
    to = models.CharField(max_length=255, null=True)
    cc = models.CharField(max_length=255, null=True)
    cco = models.CharField(max_length=255, null=True)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    files = JSONField()

class Comments(TimeStampedModel):
    model = models.IntegerField(default = 0, choices = MODEL_CHOICES)
    id_model =  models.IntegerField(default = 0, null = True)
    content = models.TextField(null = True)
    parent = models.ForeignKey('self', null = True, related_name = "comment_child", on_delete=models.CASCADE) 
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    user = models.ForeignKey('auth.User', related_name='comment_user', on_delete=models.CASCADE)
    is_child = models.BooleanField(default=False)
    has_reminder = models.BooleanField(default = False)
    reminder_date = models.DateTimeField(null = True, blank = True)
    modelo_tareas = models.IntegerField(null = True)
    mentioned_users = models.ManyToManyField(User, related_name='mentioned_in_comments',blank = True)

    # def __str__(self):
    #     return self.content


class Reports(models.Model):
    dummy = models.CharField(max_length=1)

    def __str__(self):
        return self.dummy


class Phones(models.Model):
    phone = models.CharField(max_length = 500)
    contractor = models.ForeignKey(Contractor, related_name="phone_contractor", null=True, blank=True, on_delete=models.CASCADE)#Nueva FK Contractor
    org_name =  models.CharField(max_length=50, null=True)
    phone_type = models.IntegerField(default = 1, choices = TYPE_CHOICES)


class Emails(models.Model):
    correo = models.CharField(max_length = 500)
    contractor = models.ForeignKey(Contractor, related_name="email_contractor", null=True, blank=True, on_delete=models.CASCADE)#Nueva FK Contractor
    org_name  = models.CharField(max_length=50, null=True)
    email_type = models.IntegerField(default = 1, choices = TYPE_CHOICES)

class Cartas(TimeStampedModel):
    name = models.CharField(max_length = 500)
    title = models.CharField(max_length=500, blank=True)
    text = models.TextField(blank=True, null=True)
    model = models.IntegerField(default = 0, choices = LETTER_MODEL_CHOICES)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', related_name='carta_owner', null=True, on_delete=models.CASCADE)


class Internal(TimeStampedModel):
    org_name = models.CharField(max_length=50, null=True, db_index=True)


class OrgInfo(TimeStampedModel):
    solicitud_pol = models.BooleanField(default=False)
    solicitud_endoso = models.BooleanField(default=False)
    renovacion = models.BooleanField(default=False)
    registro_pol = models.BooleanField(default=False)
    registro_endoso = models.BooleanField(default=False)
    solicitud_siniestro = models.BooleanField(default=False)
    fin_siniestro = models.BooleanField(default=False)
    tramite_siniestro = models.BooleanField(default=False)
    rechazo_siniestro = models.BooleanField(default=False)
    cancelacion_siniestro = models.BooleanField(default=False)
    espera_siniestro = models.BooleanField(default=False)
    recordatorio_cob = models.BooleanField(default=False)
    recordatorio_sms = models.BooleanField(default=False)
    recordatorio_ren = models.BooleanField(default=False)
    recordatorio_cum = models.BooleanField(default=False)
    cobranza_pago = models.BooleanField(default=False)
    create_nota = models.BooleanField(default=False)
    apply_nota = models.BooleanField(default=False)
    cerrar_recibos = models.BooleanField(default=False)
    contacto_dudas = models.TextField(blank=True, null=True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    fecha_limite_email= models.BooleanField(default=False)
    filtros_agrupacion= models.BooleanField(default=False)
    filtros_lineanegocio= models.BooleanField(default=False)
    filtros_celula= models.BooleanField(default=False)
    fecha_limite_email_cobranza = models.BooleanField(default=True)
    boton_segumovil = models.BooleanField(default=True)
    moduleName = models.CharField(max_length=50, null=True, db_index=True)
    dato_contratante = models.BooleanField(default=True)
    dato_numero_poliza = models.BooleanField(default=True)
    dato_concepto = models.BooleanField(default=True)
    dato_aseguradora = models.BooleanField(default=True)
    dato_subramo = models.BooleanField(default=True)
    dato_serie = models.BooleanField(default=True)
    dato_total = models.BooleanField(default=True)
    dato_pvigencia = models.BooleanField(default=True)
    dato_paseguradora = models.BooleanField(default=True)
    dato_psubramo = models.BooleanField(default=True)
    dato_pmoneda = models.BooleanField(default=True)
    dato_pfrecuenciapago = models.BooleanField(default=True)
    dato_pasegurado = models.BooleanField(default=True)
    dato_ptotal = models.BooleanField(default=True)
    dato_ptotalrecibo = models.BooleanField(default=True)
    activar_contacto_dudas = models.BooleanField(default=True)
    copia_user_envio = models.BooleanField(default=False)
    dato_cvigencia = models.BooleanField(default=True)
    dato_caseguradora = models.BooleanField(default=True)
    dato_csubramo = models.BooleanField(default=True)
    dato_cmoneda = models.BooleanField(default=True)
    dato_cfrecuenciapago = models.BooleanField(default=True)
    dato_casegurado = models.BooleanField(default=True)
    dato_cptotal = models.BooleanField(default=True)
    dato_cpneta = models.BooleanField(default=True)
    dato_cderecho = models.BooleanField(default=True)
    dato_crpf = models.BooleanField(default=True)
    dato_civ = models.BooleanField(default=True)
    dato_cnumcertificado = models.BooleanField(default=True)
    dato_ccontratante = models.BooleanField(default=True)


class EmailInfo(TimeStampedModel):
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    model = models.IntegerField(default = 0, choices = EMAIL_MODEL_CHOICES)
    owner = models.ForeignKey('auth.User', related_name='email_owner', null=True, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)


class EmailInfoReminder(TimeStampedModel):
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    model = models.IntegerField(default = 0, choices = EMAIL_MODEL_CHOICES)
    owner = models.ForeignKey('auth.User', related_name='email_owner_rem', null=True, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    text_end = models.TextField(blank=True, null=True)
    frequency = models.IntegerField(default = 0, choices = EMAIL_FREQ_CHOICES,null=True)
    type_policy = models.IntegerField(default = 0, choices = EMAIL_TYPE_CHOICES)
    ramo_code = models.IntegerField(default = 0, choices = EMAIL_RAMO_CHOICES)
    tipo_cobro = models.IntegerField(default = 0, choices = TIPO_COBRO_CHOICES)
    tipo_fecha = models.IntegerField(default = 1, choices = TIPO_FECHA_CHOICES)
    aseguradora = models.ForeignKey(Provider, null=True, default=None, on_delete=models.CASCADE)
    aseguradoras = ArrayField(models.IntegerField(), default = [], null = True, blank = True)
    subramos = ArrayField(models.IntegerField(), default = [], null = True, blank = True)
    receipt_type = models.IntegerField(default = 0, choices = TIPO_RECIBO_CHOICES)
    type_message = models.IntegerField(default = 0, choices = TIPO_MESSAGE_CHOICES)
    days = models.IntegerField(null = True, blank = True)
    relative_time = models.IntegerField(default = 0, choices = EMAIL_RELATIVE_TIME)
    relative_date = models.IntegerField(default = 0, choices = EMAIL_RELATIVE_DATE)
    remitente = models.CharField(max_length=100, null=True, db_index=True)
    dato_asegurado = models.BooleanField(default=True)

    

class Graphics(TimeStampedModel):
    type_graphic = models.IntegerField(null = True, choices = GRAPHIC_TYPES)
    red = models.IntegerField(null = True, blank = True)
    orange = models.IntegerField(null = True, blank = True)
    yellow = models.IntegerField(null = True, blank = True)
    green = models.IntegerField(null = True, blank = True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    option_filter =  models.IntegerField(choices=GRAPHIC_OPTION_FILTER, default=1)


class Schedule(TimeStampedModel):
    title = models.CharField(max_length = 500)
    color = models.CharField(max_length = 500)
    startsAt = models.DateTimeField()
    endsAt = models.DateTimeField()
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    resizable = models.BooleanField(default=True)
    draggable = models.BooleanField(default=True)
    observations = models.TextField(blank=True, null=True)


class ScheduleParticipants(TimeStampedModel):
    user= models.ForeignKey(User, blank=True, default=None, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, related_name='participants', on_delete=models.CASCADE,default=None)


class Notifications(TimeStampedModel):
    def __str__(self):
        return self.title

    def send_push_reminder(self):
        if not self.id:
            return
        if self.assigned.user_info.fcm_token:
            send_push(self.title, self.description, self.assigned.user_info.fcm_token)

    def send_push_generic(self, request=None):
        if not self.id:
            return
        try:
            if self.assigned and self.assigned.user_info and  self.assigned.user_info.fcm_token:
                send_push(self.title, self.description, self.assigned.user_info.fcm_token)
        except:
            pass

    def send_push_involucrado(self, request):
        if not self.id:
            return
        if self.assigned.user_info.fcm_token:
            send_push(self.title, self.description, self.assigned.user_info.fcm_token)

    def send_push_comment(self, request,user_mentionated,notificat,user_created):
        if not self.id:
            return
        if user_mentionated.user_info:
            send_push(self.title, self.description, self.assigned.user_info.fcm_token)
        else:
            print('no se envío la notificación',self.title,user_mentionated,user_mentionated.user_info)
        try:
            today = datetime.datetime.now().date()
            tomorrow = today + datetime.timedelta(1)
            today_start = datetime.datetime.combine(today, datetime.time())
            today_end = datetime.datetime.combine(tomorrow, datetime.time())
            nots = Notifications.objects.filter(
                org_name = request.GET.get('org'),
                seen = False, 
                assigned = user_mentionated, 
                created_at__gte = today_start, 
                created_at__lte = today_end
            ).order_by('-id')
            payload = {
                'channel' : 'notificaciones_'+str(user_mentionated.username),
                'title': notificat.title,
                'description': notificat.description,
                'id_user':user_mentionated.id,
                'count':len(nots)
            }
            # notificaciones-count
            # send_push(notificat.title, notificat.description, user_mentionated.user_info.fcm_token)
            #bitacoras enviar al canal del usuario mencionado y actualizar sus notificaciones
            # r = requests.post(settings.SERVICEEXCEL_2_URL + 'notificaciones-count/', data = payload, stream=True)
        except Exception as esendn:
            print('error *n',esendn)
        # if notificat.owner and notificat.owner.user_info and notificat.owner.user_info.fcm_token and notificat.owner.id != user_created.id:
        #     self.title = "%s menciono en un comentario a \'%s\'" % (notificat.owner.first_name + ' ' + notificat.owner.last_name ,  user_mentionated.first_name + ' ' + user_mentionated.last_name)
        #     self.save()
        #     send_push(self.title, self.description, notificat.owner.user_info.fcm_token)

    def send_push(self, request):
        if not self.id:
            return
        if self.involucrado :
            try:
                self.title = "%s te ha involucrado en la tarea \'%s\'" % (request.user.first_name if request.user and request.user.first_name else '' + ' ' + request.user.last_name if request and request.user.last_name else '' ,  self.title)
            except:
                self.title = "Se ha involucrado en la tarea "+ str(self.title)
        elif self.involucrado == False:
            try:
                self.title = "%s te ha asignado la tarea \'%s\'" % (request.user.first_name if request.user and request.user.first_name else '' + ' ' + request.user.last_name if request and request.user.last_name else '',  self.title)
            except:
                self.title = "Se ha asignado en la tarea "+ str(self.title)

        self.save()
        if self.assigned.user_info.fcm_token:
            send_push(self.title, self.description, self.assigned.user_info.fcm_token)
    
    def send_email_calendar(self, request, destinatario, schedule):
        try:
            subject = "Creacion de evento en la agenda"
            if request.user.email:
                remitente = "{} <{}>".format(self.org_name, request.user.email)
            elif self.org.email:
                remitente = "{} <{}>".format(self.org_name, self.org_name)
            else:
                remitente = "{} <no-reply@miurabox.com>".format(self.org_name)
                
            email_multiples = [destinatario]

            f = "%d/%m/%Y"

            try:
                color_json = json.loads(schedule.color.replace('\'','"'))
            except: 
                color_json = {'name': 'Sin color asignado'}

            event_obj = {
                "title": schedule.title,
                "date": schedule.created_at.strftime(f) ,
                "startsAt": schedule.startsAt.strftime(f) ,
                "endsAt": schedule.endsAt.strftime(f) ,
                "descrip": schedule.observations,
                "color": color_json['name']
            }

            data = {'event':event_obj, 'title':subject}

            data['subject'] = subject
            data['org'] = schedule.org_name
            data['remitente'] = remitente
            data['receiver'] = email_multiples
            data['cco'] = [request.user.email]
      
            url = settings.MAILSERVICE + "mails/send-event-email/"
            
            req = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'} )

        except Exception as e:
            pass
 
    def send_email(self, request, ticket):
        try:
            subject = self.title
            if request.user.email:
                remitente = "{} <{}>".format(ticket.org_name, request.user.email)
            elif self.org.email:
                remitente = "{} <{}>".format(ticket.org_name, self.org_name)
            else:
                remitente = "{} <no-reply@miurabox.com>".format(ticket.org_name)
                
            email_multiples = [self.assigned.email]

            f = "%d/%m/%Y"

            ticket_obj = {
                "title": ticket.title,
                "date": ticket.date.strftime(f) ,
                "get_priority_display": ticket.get_priority_display(),
                "get_concept_display": ticket.get_concept_display(),
                "descrip": ticket.descrip,
                "assigned": "%s %s"%(ticket.assigned.first_name if ticket and ticket.assigned else '', ticket.assigned.last_name if ticket and ticket.assigned else '')
            } 

            if 'link' in request.data and request.data['link']:   
                if is_base64(request.data['link']):
                    ticket_obj = {
                        "link": '',
                        "base64": request.data['link'],
                        "title": ticket.title,
                        "date": ticket.date.strftime(f) ,
                        "get_priority_display": ticket.get_priority_display(),
                        "get_concept_display": ticket.get_concept_display(),
                        "descrip": ticket.descrip,
                        "assigned": "%s %s"%(ticket.assigned.first_name if ticket and ticket.assigned else '', ticket.assigned.last_name if ticket and ticket.assigned else '')
                    }
                else:
                    ticket_obj = {
                        "link": request.data['link'],
                        "base64": '',
                        "title": ticket.title,
                        "date": ticket.date.strftime(f) ,
                        "get_priority_display": ticket.get_priority_display(),
                        "get_concept_display": ticket.get_concept_display(),
                        "descrip": ticket.descrip,
                        "assigned": "%s %s"%(ticket.assigned.first_name if ticket and ticket.assigned else '', ticket.assigned.last_name if ticket and ticket.assigned else '')
                    }
            data = {'tarea':ticket_obj, 'title':self.title}
            data['subject'] = subject
            data['remitente'] = remitente
            data['receiver'] = email_multiples
            try:
                data['cc'] = [request.user.email]
            except:
                data['cc'] = ['guadalupe.becerril@miurabox.com']

            data['cco'] = []
            data['org'] = []
      
            url = settings.MAILSERVICE + "mails/send-ticket-email/"
            
            if not self.involucrado:
                req = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'} )
            else:
                req = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'} )

        except Exception as e:
            print('error****',e)
            try:
                subject = self.title
                remitente = "{} <no-reply@miurabox.com>".format(ticket.org_name)                
                email_multiples = [self.assigned.email]
                f = "%d/%m/%Y"

                ticket_obj = {
                    "title": ticket.title,
                    "date": ticket.date.strftime(f) ,
                    "get_priority_display": ticket.get_priority_display(),
                    "get_concept_display": ticket.get_concept_display(),
                    "descrip": ticket.descrip,
                    "assigned": "%s %s"%(ticket.assigned.first_name if ticket and ticket.assigned else '', ticket.assigned.last_name if ticket and ticket.assigned else '')
                }
                
                if 'link' in request.data and request.data['link']:   
                    if is_base64(request.data['link']):
                        ticket_obj = {
                            "link": '',
                            "base64": request.data['link'],
                            "title": ticket.title,
                            "date": ticket.date.strftime(f) ,
                            "get_priority_display": ticket.get_priority_display(),
                            "get_concept_display": ticket.get_concept_display(),
                            "descrip": ticket.descrip,
                            "assigned": "%s %s"%(ticket.assigned.first_name if ticket and ticket.assigned else '', ticket.assigned.last_name if ticket and ticket.assigned else '')
                        }
                    else:
                        ticket_obj = {
                            "link": request.data['link'],
                            "base64": '',
                            "title": ticket.title,
                            "date": ticket.date.strftime(f) ,
                            "get_priority_display": ticket.get_priority_display(),
                            "get_concept_display": ticket.get_concept_display(),
                            "descrip": ticket.descrip,
                            "assigned": "%s %s"%(ticket.assigned.first_name if ticket and ticket.assigned else '', ticket.assigned.last_name if ticket and ticket.assigned else '')
                        }
                data = {'tarea':ticket_obj, 'title':self.title}

                data['subject'] = subject
                data['remitente'] = remitente
                data['receiver'] = email_multiples
                try:
                    data['cc'] = [request.user.email]
                except:
                    data['cc'] = ['guadalupe.becerril@miurabox.com']

                data['cco'] = []
                data['org'] = []
        
                url = settings.MAILSERVICE + "mails/send-ticket-email/"
                if not self.involucrado:
                    req = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'} )
                else:
                    req = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'} )
            except Exception as i:
                print('eeeee',i)
                pass

    model = models.IntegerField(blank=True, null=True, choices = MODEL_CHOICES)
    id_reference = models.IntegerField()

    title = models.CharField(max_length=500)
    description = models.CharField(max_length = 500)
    seen = models.BooleanField(default = False)

    involucrado = models.BooleanField(default = False)
    
    assigned = models.ForeignKey('auth.User', related_name='notification_assigned', null = True, on_delete=models.CASCADE)
    owner = models.ForeignKey('auth.User', related_name='notification_owner', null=True, on_delete=models.CASCADE)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    involucrado_por_area = models.BooleanField(default = False)

    type_notification = models.IntegerField(blank=True, null=True, choices = TYPENOT_CHOICES,default = 1)
    site = models.CharField(max_length=50, null=True, db_index=True, blank = True)
    poliza_groupinglevel = models.IntegerField(null = True, blank = True)
    poliza_contractor = ArrayField(models.IntegerField(null = True, blank = True), blank=True, default=[])
    poliza_provider = ArrayField(models.IntegerField(null = True, blank = True), blank=True, default=[])
    poliza_ramo = ArrayField(models.IntegerField(null = True, blank = True), blank=True, default=[])
    startsAt = models.DateTimeField(null = True, blank = True)
    recRegistro = models.ForeignKey('recordatorios.RegistroDeRecordatorio', related_name="registro_recordatorio", null=True, blank=True, on_delete=models.CASCADE)
    recordatorio = models.ForeignKey('recordatorios.Recordatorios', related_name="notificacion_recordatorios", null=True, blank=True, on_delete=models.CASCADE)

class Ticket(TimeStampedModel):
    title = models.CharField(max_length=500)
    descrip = models.CharField(max_length=500)
    date = models.DateTimeField()
    assigned = models.ForeignKey('auth.User', related_name='assigned_man', on_delete=models.CASCADE)
    owner = models.ForeignKey('auth.User', related_name='owner_ticket', null = True, on_delete=models.CASCADE)
    closedBy = models.ForeignKey('auth.User', related_name='closed_by__ticket', null = True,blank = True, on_delete=models.CASCADE)
    
    reassignBy = models.ForeignKey('auth.User', related_name='reassign_by__ticket', null = True,blank = True, on_delete=models.CASCADE)
    reassign_date = models.DateTimeField(null = True)
    
    org_name =  models.CharField(max_length=50, null=True)
    priority = models.IntegerField(blank=True, null=True, default=1, choices = PRIORITY)
    concept = models.IntegerField(blank=True, null=True, default=1, choices = CONCEPT)
    close_day = models.DateTimeField(null = True)
    closed = models.BooleanField(default=False)
    identifier = models.CharField(max_length=500, null=True, blank=True)
    route = models.CharField(max_length=500, null = True)
    associated = models.CharField(max_length=500, null = True)
    archived = models.BooleanField(default=False)
    model = models.IntegerField(blank=True, null=True)
    comment = models.ForeignKey(Comments, null = True, blank = True, related_name = 'comment_tasks', on_delete=models.CASCADE)
    ot_model = models.IntegerField(blank=True, null=True, choices = OT_MODEL_CHOICES)
    ot_id_reference = models.IntegerField(null = True)

    def __str__(self):
        return self.title
    # def __str__(self):
    #     return "%s" % (self.action)


class GroupManager(TimeStampedModel):
    manager = models.ForeignKey('auth.User', related_name='group_manager_user', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', related_name='group_task_user', null = True, blank= True, on_delete=models.CASCADE)

class Involved(TimeStampedModel):
    person = models.ForeignKey('auth.User', related_name='involved_man', on_delete=models.CASCADE)
    involved = models.ForeignKey(Ticket, related_name='involved_task', null = True, on_delete=models.CASCADE)
    org_name  = models.CharField(max_length=50, null=True)
    owner = models.ForeignKey('auth.User', related_name='involved_ticket', null = True, on_delete=models.CASCADE)

    # def __str__(self):
    #     return "%s" % (self.action)

class Remitente(TimeStampedModel):
    email = models.CharField(max_length=500)
    pass_app = models.CharField(max_length=500)
    org_name  = models.CharField(max_length=50, null=True)
    area = models.IntegerField(blank=True, null=True, default=1, choices = AREAS)
    is_active = models.BooleanField(default=True)

from polizas.models import Polizas


class ReferenciadoresInvolved(TimeStampedModel):
    referenciador = models.ForeignKey('auth.User', related_name='ref_policy', on_delete=models.CASCADE)
    policy = models.ForeignKey(Polizas, related_name="ref_policy", null=True, blank=True, on_delete=models.CASCADE)
    comision_vendedor = models.DecimalField(max_digits=20, decimal_places=2, default=0, blank=True, null=True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    is_changed = models.BooleanField(default=False)
    anterior = models.CharField(max_length=50, null=True,blank=True)
    owner = models.ForeignKey('auth.User', related_name='involved_ref', null = True, on_delete=models.CASCADE)

   
class ModelsPermissions(TimeStampedModel):
    user = models.ForeignKey('auth.User', related_name = 'usuario_permisos', on_delete=models.CASCADE)
    model_name = models.CharField(max_length = 500)


class UserPermissions(TimeStampedModel):
    model = models.ForeignKey(ModelsPermissions, related_name = 'permissions', on_delete=models.CASCADE)
    permission_name = models.CharField(max_length = 300)
    checked = models.BooleanField(default = True)
    is_active = models.BooleanField(default=True)


class ResponsablesInvolved(TimeStampedModel):
    responsable = models.ForeignKey('auth.User', related_name='resp_man', on_delete=models.CASCADE)
    contractor = models.ForeignKey(Contractor, related_name="resp_contractor", null=True, blank=True, on_delete=models.CASCADE)#Nueva FK Contractor
    responsable_name = models.CharField(max_length=50, null=True)
    resp_type = models.IntegerField(blank=True, null=True, default=1)
    org_name  = models.CharField(max_length=50, null=True)
    owner = models.ForeignKey('auth.User', related_name='involved_resp', null = True, on_delete=models.CASCADE)

class Goals(TimeStampedModel):
    goal = models.DecimalField(max_digits=20, decimal_places=2, null = True, blank = True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)

class Expenses(TimeStampedModel):
    cantidad = models.DecimalField(max_digits=20, decimal_places=2, null = True, blank = True)
    concept = models.CharField(max_length=500)
    month = models.IntegerField(blank=True, null=True, default=1, choices = MONTHS)
    org_name = models.CharField(max_length=50, null=True, db_index=True)

class Cedula(TimeStampedModel):
    cedula = models.CharField(max_length=500)
    expiracion = models.DateTimeField(null = True)
    observaciones = models.TextField(null = True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', related_name='cedula_owner', null = True, on_delete=models.CASCADE)

from polizas.models import Polizas


class Shared(TimeStampedModel):
    grupo = models.ForeignKey(DjangoGroups, null = True, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, null = True, on_delete=models.CASCADE)
    poliza = models.ForeignKey(Polizas, null = True, on_delete=models.CASCADE )
    aseguradora = models.ForeignKey(Provider, null = True, on_delete=models.CASCADE)
    grupo_de_contratantes = models.ForeignKey(ContractorGroup, null = True, on_delete=models.CASCADE)
    contractor = models.ForeignKey(Contractor, null=True, blank=True, on_delete=models.CASCADE)#Nueva FK Contractor
    descripcion = models.TextField(null = True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', related_name='shared_owner', on_delete=models.CASCADE )

class PerfilUsuarioRestringido(TimeStampedModel):
    contratante_contratante = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    contratante_grupo = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    contratante_celula = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    contratante_referenciador = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    contratante_sucursal = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    
    poliza_poliza = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_grupo = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_celula = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_referenciador = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_sucursal = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_agrupacion = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_clave_agente = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_subramo = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_aseguradora = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])
    poliza_estatus = ArrayField(JSONField(null=True, blank=True, default=dict), blank=True, default=[])

    solo_polizas_visibles = models.BooleanField(default= False)

    is_active = models.BooleanField(default= True)
    nombre = models.CharField(max_length=500)
    
    org_name = models.CharField(max_length=50, null=True, db_index=True)



class Signature(TimeStampedModel):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    signature = models.TextField()
    enabled = models.BooleanField(default=True)
    in_amazon = models.BooleanField(default = False, blank=True)
    image_amazon =models.CharField(max_length=500,null=True)


class BirthdateTemplate(TimeStampedModel):
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    subject = models.CharField(max_length=500)
    remitente = models.CharField(max_length=100,null=True,blank=True)
    text = models.TextField()
    enabled = models.BooleanField(default=True)


class ZipCodeSepomex(models.Model):
    cp = models.CharField(max_length = 10)
    colonia = models.CharField(max_length = 100)
    municipio = models.CharField(max_length = 100)
    estado = models.CharField(max_length = 50)
    codigo = models.CharField(max_length = 50)
    munid = models.CharField(max_length = 10)

class EmailTemplate(TimeStampedModel):
    name = models.CharField(max_length = 500)
    title = models.CharField(max_length=500, blank=True)
    text = models.TextField(blank=True, null=True)
    bottom_text = models.TextField(blank=True, null=True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    subject_default= models.BooleanField(default = False)
    template_model = models.IntegerField(blank=True, null=True,default=1,choices = OT_MODEL_CHOICES)
    ramo_code = ArrayField(models.IntegerField(), default = [], null = True, blank = True)
    owner = models.ForeignKey('auth.User', related_name='emailtemplate_owner', null=True, on_delete=models.CASCADE)
    dato_cvigencia = models.BooleanField(default=True)
    dato_caseguradora = models.BooleanField(default=True)
    dato_csubramo = models.BooleanField(default=True)
    dato_cmoneda = models.BooleanField(default=True)
    dato_cfrecuenciapago = models.BooleanField(default=True)
    dato_casegurado = models.BooleanField(default=True)
    dato_cptotal = models.BooleanField(default=True)
    dato_cpneta = models.BooleanField(default=True)
    dato_cderecho = models.BooleanField(default=True)
    dato_crpf = models.BooleanField(default=True)
    dato_civ = models.BooleanField(default=True)
    dato_cnumcertificado = models.BooleanField(default=True)
    dato_ccontratante = models.BooleanField(default=True)

class ConfigKbi(TimeStampedModel):
    tipocambio = models.DecimalField(max_digits=20, decimal_places=2, default=20, blank=True, null=True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    
    

class LecturaArchivos(TimeStampedModel):
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=500, blank=True)
    tipo_poliza = models.CharField(max_length=500, blank=True)
    aseguradora = models.CharField(max_length=500, blank=True)
    ramo = models.CharField(max_length=500, blank=True)
    subramo = models.CharField(max_length=500, blank=True)
    

class TagsLecturaArchivos(TimeStampedModel):
    areaid = models.CharField(max_length=100, null=True, blank=True)
    cssClass = models.CharField(max_length=100, null=True, blank=True)
    height = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    pageNumber = models.CharField(max_length=100, null=True, blank=True)
    tag = models.CharField(max_length=100, null=True, blank=True)
    width = models.CharField(max_length=100, null=True, blank=True)
    x = models.CharField(max_length=100, null=True, blank=True)
    y = models.CharField(max_length=100, null=True, blank=True)
    z = models.CharField(max_length=100, null=True, blank=True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey(LecturaArchivos, related_name='tags_lectura_archivos', on_delete=models.CASCADE)
    
import time
from unidecode import unidecode
base = '{org}/{type}/' + time.strftime("%Y/%m/%d") + '/{file_id}_{img}'

def file_type(filetype, instance, filename):
    return base.format(org=instance.org_name, type=filetype, img=unidecode(filename.replace(' ', '')), id=instance.id, file_id = random.randint(1,10001)) 


def get_repositorio_pago(instance, filename):
    return file_type('repositoriopago', instance, filename)

class RepositorioPago(TimeStampedModel):
    nombre_archivo = models.CharField(max_length=500)
    registros_del_archivo = models.IntegerField(default = 0)
    movimientos_cargados = models.IntegerField(default = 0)
    movimientos_no_cargados = models.IntegerField(default = 0)
    owner = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    arch = models.FileField(upload_to = get_repositorio_pago, max_length=500)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    fuente = models.CharField(max_length=100, null=True)

class ConfigProviderScrapper(TimeStampedModel):
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', related_name='configprovider_owner', null=True, on_delete=models.CASCADE)
    username = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    descrip = models.TextField(blank=True, null=True)
    periodicidad = models.IntegerField(default = 7, choices = PERIODICIDAD_CHOICES)
    startDate = models.DateTimeField(null = True, blank = True)
    startDate_scraper = models.DateTimeField(null = True, blank = True)
    endDate_scraper = models.DateTimeField(null = True, blank = True)
    provider = models.ForeignKey(Provider, null=True, default=None, on_delete=models.CASCADE)
    ramos = ArrayField(models.IntegerField(), default = [], null = True, blank = True)
    subramos = ArrayField(models.IntegerField(), default = [], null = True, blank = True)
    active = models.BooleanField(default = True)
    running = models.BooleanField(default = False)

class LogScrapper(TimeStampedModel):
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    configscrapper = models.ForeignKey(ConfigProviderScrapper, null = True, blank = True, related_name = 'configprovider_scrapper', on_delete=models.CASCADE )  
    rundate = models.DateTimeField(null = True, blank = True)
    listpolicies = ArrayField(models.IntegerField(), default = [], null = True, blank = True)
    active = models.BooleanField(default = True)

class PromotoriaTablero(TimeStampedModel):
    polizas_ots = JSONField(null=True, blank=True, default=list)
    config = JSONField(null=True, blank=True, default={})
    orden = models.IntegerField(default= 0)
    is_active = models.BooleanField(default= True)
    color = models.CharField(max_length=500, null=True)    
    name = models.CharField(max_length=500, null=True)    
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', related_name='promotoriatablero_owner', null=True, on_delete=models.CASCADE)

class SmsTemplate(TimeStampedModel):
    title = models.CharField(max_length=500, blank=True)
    text = models.TextField(blank=True, null=True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)
    owner = models.ForeignKey('auth.User', related_name='smstemplate_owner', null=True, on_delete=models.CASCADE)
    type_message = models.IntegerField(default = 1, choices = TYPETEMPLATE_CHOICES)

    
def is_base64(string):
    try:
        # Intentar decodificar la cadena
        base64.b64decode(string, validate=True)
        return True
    except (ValueError, TypeError):
        return False
