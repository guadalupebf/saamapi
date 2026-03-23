from datetime import datetime, timedelta
from polizas.models import Polizas
from fianzas.models import Fianzas
import kronos
import re
import requests
import json
from organizations.views import get_org
from django.conf import settings
from recibos.models import Recibos
from endosos.models import Endorsement
from siniestros.models import Siniestros
from django.core.mail import EmailMessage,EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from organizations.models import UserInfo
import os
from django.db.models import Q,F
from functools import reduce
from operator import __or__ as OR
from operator import __and__ as AND
import operator
import operator
from core.models import Comments, Notifications
from django.utils import timezone
from campaigns.views import send_auto_campaign
import os
from campaigns.models import Campaign
from .utils import send_email_smtp

# Cuando una póliza en estatus “Vigente” termina su vigencia y no existe una póliza que le siga, se pasa a Estatus "Vencida".
# Ejemplo, una póliza es del 20 de Enero de 2015 al 20 de Enero del 2016, el día 21 de Enero de 2016 esa póliza pasa a estatus “Vencida”,
# esto es sólo en caso de que no se haya renovado y exista una póliza pendiente de ser vigente (es decir, en estatus Activa).
# No importan las OT, sólo pólizas.

@kronos.register('*/5 * * * *') #Activar el cron y probar los recordatorios
def RemindersAction():
    delta_minutes_crone = 5
    today = timezone.now()
    today_delta = today + timedelta(minutes = delta_minutes_crone)
    comments = Comments.objects.filter(has_reminder = True, reminder_date__lt = today_delta, reminder_date__gte = today)
    if len(comments) == 0:
        return

    for comment in comments:
        notification = Notifications.objects.create(
            model = comment.model, 
            id_reference = comment.id_model, 
            title = 'Aviso de recordatorio', 
            description = 'Recordatorio: %s...'%(comment.content[0:400]), 
            assigned = comment.user, 
            owner = comment.user, 
            org = comment.org
        )
        
        # Enviamos la notificacion
        notification.send_push_reminder()




def getDate(date=datetime.now()):
    return re.search(re.compile('\d{4}[-/]\d{2}[-/]\d{2}'), str(date)).group(0)

def getTime(date=datetime.now()):
    return re.search(re.compile('\d{2}[:/]\d{2}[:/]\d{2}'), str(date)).group(0)

@kronos.register('0 4 * * *')
def policiesCron():

    policies = Polizas.objects.filter(document_type__in=[1, 3, 7, 8]).exclude(status__in = [0,1,2,4,15,11,12])
    policies = policies.exclude(org_name__in = ['byaseguros','balderas_test'])

    today = getDate()
    changes = [0,0,0,0]
    por_iniciar = 0
    cerrada = 0
    vencida = 0
    vigente = 0
    no_renovada = 0


    for p in policies:
        try:
            if p.start_of_validity:
                if today < getDate(p.start_of_validity):
                    if p.status != 10:
                        por_iniciar += 1
                        p.status = 10
                        p.save()
                elif today > getDate(p.end_of_validity):
                    if p.renewed_status == 1 or p.is_renewable == 0:
                        if p.status != 12:
                            cerrada += 1
                            p.status = 12
                            p.save()
                    else:
                        if p.status not in (12, 13):
                            vencida += 1
                            p.status = 13
                            p.save()
                elif today < getDate(p.end_of_validity):
                    if p.status != 14:
                        vigente += 1
                        p.status = 14
                        p.save()
                elif p.reason_ren:
                    if p.status != 15:
                        no_renovada += 1
                        p.status = 15
                        p.save()
            else:
                pass
        except Exception as e:
            pass

    send_email_smtp('Update status','Polizas con status cambiado:  \nPor iniciar: {}, \nCerrada: {}, \nVencida: {}, \nVigente: {}, \nNo Renovada: {}'.format(por_iniciar,cerrada,vencida,vigente, no_renovada))



# Envio automatico de campañas

@kronos.register('0 8 1 * *')
def send_campaign_mensual():
    for campaign in Campaign.objects.filter(active_season = True, active_season = True , repeatEmail = 3):
        send_auto_campaign(campaign)


@kronos.register('0 8 * * 1')
def send_campaign_semanal():
    for campaign in Campaign.objects.filter(active_season = True, active_season = True , repeatEmail = 2):
        send_auto_campaign(campaign)


@kronos.register('0 8 * * *')
def send_campaign_diario():
    for campaign in Campaign.objects.filter(active_season = True, active_season = True , repeatEmail = 1):
        send_auto_campaign(campaign)


    # Campañas de unica vez
    for campaign in Campaign.objects.filter(active_season = True, active_season = True ,repeatEmail = 0):
        send_auto_campaign(campaign)
        campaign.active_season = False
        campaign.save()



# / Envio automatico de campañas

        
@kronos.register('0 12 * * 1')
def mailAdminCron():

    # policies = Polizas.objects.filter(document_type__in=[1, 3]).exclude(status__in = [0,1,2,4,15,11,12])
    polizas = Polizas.objects.exclude(status__in = [2,11,0]).exclude(document_type__in = [2])
    p = []
    p_dt2 = []
    organization_name = ''
    for poliz in polizas:
        if poliz.document_type == 2:
            p_dt2.append(poliz)
        else:
            p.append(poliz)
            

    for pol in p:
        if pol.document_type == 2:
            p_dt2.append(poliz)       
    polizas = p
    days_o = 15
    days_oe = 20
    today = datetime.today()
    o_days = timedelta(days = days_o)
    oe_days = timedelta(days = days_oe)

    diasO = today + o_days
    diasO_e = today + oe_days

    diasO = today + o_days
    recibos = Recibos.objects.filter(poliza__in = polizas)
    pendingRed = recibos.filter(poliza__in = polizas, isActive = True, status__in = [3,4], vencimiento__lt = today).exclude(status__in = [1,2,5,6,7,0]).exclude(isCopy = True).exclude(isActive = False).exclude(isCopy = True)
    for r in pendingRed:
        organization_name = r.org

    ahora = datetime.now() 
    dia = ahora.strftime("%a")
    # OTs
    # pol = Polizas.objects.filter(document_type__in=list([1,3]))
    # polizasRed = pol.filter(document_type__in=list([1,3]), status = 1,created_at__lte = diasO)
    days_ora = 20
    today_a = datetime.today()
    orange_d = timedelta(days = days_ora)
    diasO_a = today_a - orange_d
    polizas_a = Polizas.objects.filter(document_type__in=list([1,3]))
    polizasRed = polizas_a.filter(document_type__in=list([1,3]), status = 1, created_at__lte = diasO_a)
    for p in polizasRed:
        organization_name = p.org
    # Renovaciones
    ren = Polizas.objects.filter(document_type__in = list([1, 3]),  renewed_status=0, is_renewable = 1)
    renovacionesRed = ren.filter(document_type__in = list([1,3]),renewed_status=0, is_renewable = 1, status__in = [13,14], reason_ren = None, end_of_validity__lte = today)
    for renp in renovacionesRed:
        organization_name = renp.org
    total_p = len(polizasRed) + len(renovacionesRed)
    # Siniestros+
    days_orange_s = 14
    orange_days_s = timedelta(days = days_orange_s)
    diasO_s = today - orange_days_s
    siniestros = Siniestros.objects.exclude(status__in = list([3,4,5])).distinct('id')
    siniestrosRed = siniestros.filter(fecha_ingreso__lte = diasO_s).exclude(status__in = list([3,4,5]))
    for sins in siniestrosRed:
        organization_name = sins.org
    # Endosos
    polizas_e = Endorsement.objects.filter(status__in = [1, 5])
    endosos_red = polizas_e.filter(status__in = [1, 5], created_at__lte = diasO_a)
    for end in endosos_red:
        organization_name = end.org


    org_ = requests.get(settings.CAS_URL + 'get-org-info/'+org.urlname)
    response_org= org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']

    emails_ = requests.get(settings.CAS_URL + 'get-emails/?org_id='+str(organization_name))
    response_emails= emails_.text
    response_m = json.loads(response_emails)
    users = response_m['data']
    receiver = []
    for email in users:
        if email['email']:
            receiver.append(email['email'])

    rem = str(organization_name)
    from_email= rem + '<no-reply@miurabox.com>'
    subject = "Notificación de Indicadores para Atención Urgente"
    if organization_name == 'gpi':
        logo_org = 'https://s3.amazonaws.com/miurabox/testing/template_email/recordatorio_semanal_GPI.png'
    elif organization_name == 'prevex':
        logo_org = 'https://s3.amazonaws.com/miurabox/testing/template_email/recordatorio_semanal_PREVEX.png'
    elif organization_name == 'onecoach':
        logo_org = 'https://s3.amazonaws.com/miurabox/testing/template_email/recordatorio_semanal_ONECOACH.png'
    else:
        logo_org = 'https://s3.amazonaws.com/miurabox/testing/atencion_urgente_general.jpeg'


    message=render_to_string("correo.html",{
        'custom_txt': 'Notificación semanal de operaciones que necesitan atención urgente',
        'logo_org':logo_org,
        'org_name': org_data['data']['org'],
        'recibos_total': len(pendingRed),
        'renovacion_total': len(renovacionesRed),
        'total_p': total_p,
        'ots_total': len(polizasRed),
        'endosos_total': len(endosos_red),
        'siniestros_total': len(siniestrosRed),
        'action': 'RECORDATORIO DE ATENCIÓN URGENTE',
        'fecha': today.strftime("%d/%m/%Y ")
        })

    email = EmailMultiAlternatives(subject, message, from_email=from_email, to=receiver)

    email.content_subtype="html"
    email.mixed_subtype = 'related'


    email.send()
    val={'status':'sent'}
    # return JsonResponse(val, status=200)


@kronos.register('0 8 * * 1')
def weeklyOperationMailCron():
    date = datetime.today()
    start_week = date - timedelta(date.weekday() + 7)
    end_week = start_week + timedelta(4)
    hoy = datetime.today()
    s_pasado = hoy.day - 7
    date_filters = [Q(updated_at__gte=start_week),Q(updated_at__lte = end_week)]    

    today = datetime.today()
    # Recibos
    vencidos = Recibos.objects.filter(isActive = True, status__in = [3,4], vencimiento__lt = today).exclude(status__in = [1,2,5,6,7,0])
    vencidos_rcount = len(vencidos)

    pagados = Recibos.objects.filter(reduce(operator.and_, date_filters), status = 1)
    pagados = pagados.exclude(created_at = F("updated_at"))
    pagados_rcount = len(pagados)
    # Pólizas
    creadasp = Polizas.objects.filter(reduce(operator.and_, date_filters), status__in = [14,10], document_type__in = [1,3])
    creadasp = creadasp.filter(reduce(operator.and_, date_filters), status__in = [14,10])
    creadas_pcount = len(creadasp)

    canceladasp = Polizas.objects.filter(reduce(operator.and_, date_filters), status__in = [11], document_type__in = [1,3])
    canceladasp = canceladasp.exclude(created_at = F("updated_at"))
    canceladas_pcount = len(canceladasp)

    renovadasp = Polizas.objects.filter(reduce(operator.and_, date_filters), status__in = [12],renewed_status = 1, renewed_status=1, document_type__in = [1,3])
    renovadas = renovadasp.exclude(created_at = F("updated_at"))
    renovadas_pcount = len(renovadasp)

    norenovadasp = Polizas.objects.filter(reduce(operator.and_, date_filters), status__in = [15],renewed_status = 0, renewed_status=0, document_type__in = [1,3])
    norenovadasp = norenovadasp.exclude(created_at = F("updated_at"))
    norenovadas_pcount = len(norenovadasp)
    
    # Fianzas
    creadasf = Fianzas.objects.filter(reduce(operator.and_, date_filters), status__in = [10,14])
    creadasf = creadasf.filter(reduce(operator.and_, date_filters), status__in = [10,14])
    creadas_fcount = len(creadasf)

    canceladasf = Fianzas.objects.filter(reduce(operator.and_, date_filters), status__in = [11])
    canceladasf = canceladasf.exclude(created_at = F("updated_at"))
    canceladas_fcount = len(canceladasf)

    anuladasf = Fianzas.objects.filter(reduce(operator.and_, date_filters), status__in = [12])
    anuladasf = anuladasf.exclude(created_at = F("updated_at"))
    anuladas_fcount = len(anuladasf)
    
    # Endorsement
    creadose = Endorsement.objects.filter(reduce(operator.and_, date_filters), status__in = [1])
    creadose = creadose.filter(reduce(operator.and_, date_filters), status__in = [1])
    creados_ecount = len(creadose)
    # Siniestros
    creadoss = Siniestros.objects.filter(reduce(operator.and_, date_filters), status__in = [1])        
    creados_scount = len(creadoss)

    completadoss = Siniestros.objects.filter(reduce(operator.and_, date_filters), status__in = [3])
    # completados2 = completados.exclude(created_at__gt= since).exclude(created_at__lt= until)
    completadoss = completadoss.exclude(created_at = F("updated_at"))
    completados_scount = len(completadoss)
    # OTs
    pendientesot = Polizas.objects.filter(reduce(operator.and_, date_filters), status__in = [1],document_type__in = [1,3])
    pendientesot = pendientesot.filter(reduce(operator.and_, date_filters), status__in = [1])
    pendiente_ocount = len(pendientesot)

    canceladasot = Polizas.objects.filter(reduce(operator.and_, date_filters), status__in = [2],document_type__in = [1,3])
    canceladasot = canceladasot.filter(reduce(operator.and_, date_filters), status__in = [2])
    canceladas_ocount = len(canceladasot)
    # _______________------org name and emails admins-----__________________
    if vencidos:
        for rv in vencidos:
            organization_name = rv.org
    elif pagados:
        for rp in pagados:
            organization_name = rp.org
    elif creadasp:
        for pc in creadasp:
            organization_name = pc.org
    elif canceladasp:
        for pca in canceladasp:
            organization_name = pca.org
    elif renovadasp:
        for pr in renovadasp:
            organization_name = pr.org
    elif norenovadasp:
        for pnr in norenovadasp:
            organization_name = pnr.org
    elif creadasf:
        for fc in creadasf:
            organization_name = fc.org
    elif canceladasf:
        for fca in canceladasf:
            organization_name = fca.org
    elif anuladasf:
        for fa in anuladasf:
            organization_name = fa.org
    elif creadose:
        for ec in creadose:
            organization_name = ec.org
    elif creadoss:
        for sc in creadoss:
            organization_name = sc.org
    elif completadoss:
        for sco in completadoss:
            organization_name = sco.org
    elif pendientesot:
        for op in pendientesot:
            organization_name = op.org
    elif canceladasot:
        for oc in canceladasot:
            organization_name = oc.org


    org_ = requests.get(settings.CAS_URL + 'get-org-info/'+org.urlname)
    response_org= org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']

    emails_ = requests.get(settings.CAS_URL + 'get-emails/?org_id='+str(organization_name))
    response_emails= emails_.text
    response_m = json.loads(response_emails)
    users = response_m['data']
    receiver = []
    for email in users:
        if email['email']:
            receiver.append(email['email'])
    # organization_name = get_org(request.GET.get('org'))
    organization_name_link = 'https://'+str(organization_name)
    complement = '.miurabox.com/#/login/auth/?indicators=1'
    link_system = str(organization_name_link)+str(complement)

    # link_system = 'http://saam.localhost:3000/#/login/auth/?indicators=1'
    # email_to = ['guadalupe.becerril@miurabox.com']
    
    rem = str(organization_name)
    from_email= rem + '<no-reply@miurabox.com>'
    # from_email='Miurabox <no-reply@miurabox.com>'
    subject='Indicadores de Operación Semanal'
    message=render_to_string("email_operation.html",{
        'vencidos_rcount':vencidos_rcount,
        'pagados_rcount':pagados_rcount,
        'creadas_pcount':creadas_pcount,
        'canceladas_pcount':canceladas_pcount,
        'renovadas_pcount':renovadas_pcount,
        'norenovadas_pcount':norenovadas_pcount,
        'creadas_fcount':creadas_fcount,
        'canceladas_fcount':canceladas_fcount,
        'anuladas_fcount':anuladas_fcount,
        'creados_ecount':creados_ecount,
        'creados_scount':creados_scount,
        'completados_scount':completados_scount,
        'pendiente_ocount':pendiente_ocount ,
        'canceladas_ocount':canceladas_ocount,
        'de':start_week.strftime("%d/%m/%Y"),
        'hasta':end_week.strftime("%d/%m/%Y"),
        'link_system':link_system,
        'email':email,
        })
    val={'status':'sent'}
    email = EmailMultiAlternatives(subject, message, from_email=from_email, to=receiver)
    email.content_subtype="html"
    email.mixed_subtype = 'related'
    email.send()
    val={'status':'sent'}


