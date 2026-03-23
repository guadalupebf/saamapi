import jwt
from django.conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import smtplib, ssl
import json
import random
import base64

import urllib
from organizations.models import UserInfo
from core.models import PerfilUsuarioRestringido,EmailInfo
import ast
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from core.models import Remitente
from polizas.models import Polizas
from archivos.models import BannerFile
from recibos.models import Recibos
from siniestros.models import Siniestros, Accidentes, Autos, Vida, Danios
from archivos.presigned_url import get_presigned_url
from django.template.loader import render_to_string
from archivos.models import PolizasFile
from control.permission_functions import admin_archivos_sensibles
from forms.models import AccidentsDiseases,AutomobilesDamages,Damages
from generics.models import Personal_Information,Life
from fianzas.models import BeneficiariesContract
from organizations.views import get_org_info
import requests
from django.core.mail import EmailMessage,EmailMultiAlternatives
folder = settings.MEDIAFILES_LOCATION
import re
from control.models import Session    
from django.utils.encoding import force_text 

def decode_token(token):
    json_info = None
    try:
        json_info = jwt.decode(token,settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    except Exception as e:
        pass
    return json_info

def send_email_smtp(subject, message):
    try:

        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "no-reply@miurabox.com"
        receiver_email = ["antonio@ixulabs.com"]
        #receiver_email = ["antonio@ixulabs.com"]
        password = "xxxxxxxxxxx"

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"]  = sender_email
        msg["To"] =  ", ".join(receiver_email)


        msg.attach(MIMEText(message, 'plain'))

        message_string = msg.as_string()

        context = ssl.create_default_context()
    
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message_string)
    except Exception as e: 
        pass

def getDataForPerfilRestricted(request,org_name):
    try:
        ui = UserInfo.objects.get(user= request.user)
    except Exception as ers:
        ui = UserInfo.objects.get(user= request.owner)
    dataReturn = {}
    try:
        if ui.perfil_restringido:
            perfil = PerfilUsuarioRestringido.objects.get(pk = ui.perfil_restringido.id,org_name = org_name)
            ccpr = []
            cgpr = []
            ccepr = []
            crpr = []
            cspr = []
            # contratante_contratante
            for y in perfil.contratante_contratante:
                cs = json.loads(y)
                h = cs
                try:
                    h = eval(cs)
                except Exception as e:
                    pass
                if h['item_id']:
                    ccpr.append(h['item_id'])            
            # contratante_grupo
            for y1 in perfil.contratante_grupo:
                cs1 = json.loads(y1)
                h = cs1
                try:
                    h = eval(cs1)
                except Exception as e:
                    pass
                if h['item_id']:
                    cgpr.append(h['item_id'])            
            # contratante_celula
            for y2 in perfil.contratante_celula:
                cs2 = json.loads(y2)
                h = cs2
                try:
                    h = eval(cs2)
                except Exception as e:
                    pass
                if h['item_id']:
                    ccepr.append(h['item_id'])            
            # contratante_referenciador        
            for y3 in perfil.contratante_referenciador:
                cs3 = json.loads(y3)
                h = cs3
                try:
                    h = eval(cs3)
                except Exception as e:
                    pass
                if h['item_id']:
                    crpr.append(h['item_id'])            
            # contratante_sucursal    
            for y in perfil.contratante_sucursal:
                cs4 = json.loads(y)
                h = cs4
                try:
                    h = eval(cs4)
                except Exception as e:
                    pass
                if h['item_id']:
                    cspr.append(h['item_id'])                       
            pppr = []
            pgpr = []
            pcepr = []
            prpr = []
            pspr = []
            papr = []
            pcapr = []
            psrpr = []
            paspr = []
            pstpr = []
            # poliza_poliza
            for y in perfil.poliza_poliza:
                cs5 = json.loads(y)
                h = cs5
                try:
                    h = eval(cs5)
                except Exception as e:
                    pass
                if h['item_id']:
                    pppr.append(h['item_id'])             
            # poliza_grupo
            for y in perfil.poliza_grupo:
                cs6 = json.loads(y)
                h = cs6
                try:
                    h = eval(cs6)
                except Exception as e:
                    pass
                if h['item_id']:
                    pgpr.append(h['item_id'])             
            # poliza_celula
            for y in perfil.poliza_celula:
                cs7 = json.loads(y)
                h = cs7
                try:
                    h = eval(cs7)
                except Exception as e:
                    pass
                if h['item_id']:
                    pcepr.append(h['item_id'])             
            # poliza_referenciador
            for y in perfil.poliza_referenciador:
                cs8 = json.loads(y)
                h = cs8
                try:
                    h = eval(cs8)
                except Exception as e:
                    pass
                if h['item_id']:
                    prpr.append(h['item_id'])             
            # poliza_sucursal
            for y in perfil.poliza_sucursal:
                cs9 = json.loads(y)
                h = cs9
                try:
                    h = eval(cs9)
                except Exception as e:
                    pass
                if h['item_id']:
                    pspr.append(h['item_id'])             
            # poliza_agrupacion
            for y in perfil.poliza_agrupacion:
                cs0 = json.loads(y)
                h = cs0
                try:
                    h = eval(cs0)
                except Exception as e:
                    pass
                if h['item_id']:
                    papr.append(h['item_id'])             
            # poliza_clave_agente
            for y in perfil.poliza_clave_agente:
                cs11 = json.loads(y)
                h = cs11
                try:
                    h = eval(cs11)
                except Exception as e:
                    pass
                if h['item_id']:
                    pcapr.append(h['item_id'])             
            # poliza_subramo
            for y in perfil.poliza_subramo:
                cs12 = json.loads(y)
                h = cs12
                try:
                    h = eval(cs12)
                except Exception as e:
                    pass
                if h['item_id']:
                    psrpr.append(h['item_id'])             
            # poliza_aseguradora
            for y in perfil.poliza_aseguradora:
                cs13 = json.loads(y)
                h = cs13
                try:
                    h = eval(cs13)
                except Exception as e:
                    pas
                if h['item_id']:
                    paspr.append(h['item_id'])             
            # poliza_estatus
            for y in perfil.poliza_estatus:
                cs14 = json.loads(y)
                h = cs14
                try:
                    h = eval(cs14)
                except Exception as e:
                    pass
                if h['item_id']:
                    pstpr.append(h['item_id'])             
            
            if perfil.is_active:
                dataReturn = {
                    'ccpr': ccpr,
                    'cgpr': cgpr,
                    'ccepr': ccepr,
                    'crpr': crpr,
                    'cspr': cspr,
                    'pppr': pppr,
                    'pgpr': pgpr,
                    'pcepr': pcepr,
                    'prpr': prpr,
                    'pspr': pspr,
                    'papr': papr,
                    'pcapr': pcapr,
                    'psrpr': psrpr,
                    'paspr': paspr,
                    'pstpr': pstpr,
                    'sp': True if perfil.solo_polizas_visibles else False
                }
            else:
                dataReturn = {}
        else:
            dataReturn = {}
    except Exception as error:
        pass
    return dataReturn

# up amazon
def upload_to_s3(filename, org_name):
    import boto3    
    from boto3.s3.transfer import S3Transfer
    from botocore.exceptions import ClientError, NoCredentialsError

    AWS_STORAGE_BUCKET_NAME = 'miurabox'
    AWS_ACCESS_KEY_ID = 'xxxxxxxxxxxxxx'
    AWS_SECRET_ACCESS_KEY = 'xxxxxxxx'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    MEDIA_URL = "https://%s/" % (AWS_S3_CUSTOM_DOMAIN)

    JWT_SECRET_KEY = 'CaS2.0S3cReTk3y'
    JWT_ALGORITHM = 'HS256'


    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        BUCKET_FILE_NAME = "iris/pdfspolizas/%s/%s"%(org_name,filename)
        s3.upload_file( filename   , AWS_STORAGE_BUCKET_NAME, BUCKET_FILE_NAME , ExtraArgs={'ACL':'public-read'} )
        try:
            # return f"{MEDIA_URL}{BUCKET_FILE_NAME}"
            return MEDIA_URL+str(BUCKET_FILE_NAME)
        except Exception as ssss:
            return MEDIA_URL+str(BUCKET_FILE_NAME)
    except FileNotFoundError:
        return "The file was not found"
    except NoCredentialsError:
        return "Credentials not available"

def sendEmailAutomatico(self, request,data):
    org_name = data['org']
    emailAsegurado=''
    asuntoAsegurado=''
    if (settings.CAS2_URL=='https://users-api.miurabox.info/' or settings.CAS2_URL=='http://localhost:9000/') and org_name!='pruebas':
        return Response({'error':'Ambiente de Preproducción, no se enviará el correo automático.'}) 
    model = int(data['model'])
    email_to = []
    if model == 1 or model == 2 or model == 9:
        remitentes = Remitente.objects.filter(org_name = org_name, area = 2, is_active = True)
        try:
            poliza = Polizas.objects.get(pk = int(data['id']))
        except:
            return Response({'error':'No existe la poliza'})
    elif model == 3 or model == 4 or model == 11 or model == 12 or model == 13 or model == 14:
        remitentes = Remitente.objects.filter(org_name = org_name, area = 3, is_active = True)
        try:
            siniestro = Siniestros.objects.get(pk = int(data['id']))
        except:
            return Response({'error':'No existe el Siniestro'})
    elif model == 6:
        remitentes = Remitente.objects.filter(org_name = org_name, area = 1, is_active = True)
        try:
            recibo = Recibos.objects.get(pk = int(data['id']))
        except:
            return Response({'error':'No existe el Recibo'})
    elif model == 7 or model == 8:
        remitentes = Remitente.objects.filter(org_name = org_name, area = 1, is_active = True)
        try:
            nota = Recibos.objects.get(pk = int(data['id']))
        except:
            return Response({'error':'No existe la Nota'})

    elif model == 15 or model == 16 or model == 17 or model == 18:
        remitentes = Remitente.objects.filter(org_name = org_name, area = 0, is_active = True).values()
        try:
            fianza = Polizas.objects.get(pk=int(data['id']),document_type__in = [7,8])
        except:
            return Response({'error':'No existe la fianza'})
    org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
    response_org = org_.text
    org_data = json.loads(response_org)
    org_info = org_data['data']['org']
    archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
    if 'logo' in org_info.keys() and len(org_info['logo']) != 0:
        _imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
        if _imagen:
            archivo_imagen = _imagen
        else:
            archivo_imagen = archivo_imagen
    direccion =  org_info['address']
    direccion = force_text(direccion, encoding='utf-8', strings_only=True)
    if model == 1:
        subject='Aviso de creación de orden de trabajo: ' + str(poliza.internal_number)
    elif model == 2:
        subject='Se ha emitido la póliza ' + str(poliza.poliza_number)
    elif model == 3:        
        subject='Aviso de solicitud de siniestro ' + str(siniestro.numero_siniestro)
    elif model == 4:
        subject='Se ha finalizado el siniestro ' + str(siniestro.numero_siniestro)
    elif model == 9:
        subject='Se ha renovado una póliza con número: ' + str(poliza.poliza_number)
    elif model == 6:
        subject='Se ha pagado el Recibo: #' + str(recibo.recibo_numero) + ' de la póliza: ' + str(recibo.poliza.poliza_number)
    elif model == 7:
        if nota.receipt_type==3:
            # subject='Se ha creado la Nota de Crédito: ' + str(nota.folio if nota.folio else nota.recibo_numero)
            subject = 'Se ha creado la Nota de Crédito: ' + (str(nota.folio) if nota.folio is not None else (str(nota.recibo_numero) if nota.recibo_numero is not None else ''))

        else:
            subject='Se ha creado el Recibo #: ' + str(nota.recibo_numero)
    elif model == 8:
        if nota.receipt_type==3:
            subject='Se ha aplicado la Nota de Crédito: ' + str(nota.folio if nota.folio else nota.recibo_numero)
        else:
            subject='Se ha aplicado el Recibo #: ' + str(nota.recibo_numero)
            model=6
            recibo = nota
    elif model == 11:        
        subject='Aviso de Trámite de siniestro ' + str(siniestro.numero_siniestro)
    elif model == 12:        
        subject='Aviso de Cancelación de siniestro ' + str(siniestro.numero_siniestro)
    elif model == 13:        
        subject='Aviso de Rechazo de siniestro ' + str(siniestro.numero_siniestro)
    elif model == 14:        
        subject='Aviso de Espera de siniestro ' + str(siniestro.numero_siniestro)
    #CORREOS DE FIANZA
    elif model == 15:        
        subject='Aviso Trámite de Fianza ' + str(fianza.poliza_number)
    elif model == 16:        
        subject='Aviso de Fianza Vigente ' + str(fianza.poliza_number)
    elif model == 17:        
        subject='Aviso de Cancelación de Fianza ' + str(fianza.poliza_number)
    elif model == 18:        
        subject='Aviso de Cierre de Fianza ' + str(fianza.poliza_number)

    try:
        email_info = EmailInfo.objects.get(org_name = org_name, model = model)
        email_info_text = email_info.text
    except:
        email_info_text ="Información de la operación" 
    
    img_pattern = r'<img.*?src="data:image/(.*?);base64,(.*?)".*?>'
    images = re.findall(img_pattern, email_info_text)
    # print('imagesimages',images)
    if images:
        for i, (img_type, img_data) in enumerate(images):
            rnd =random.randint(1,10001)
            img_name = 'image_'+str(i+1)+'_'+str(rnd)+'.'+str(img_type) 
            # img_name = 'image_'+str(i+1)+'_.'+str(img_type) 
            s3_url = upload_to_s3_img_emails(img_data, img_name, img_type,img_name,org_name)
            search_str = 'data:image/' + img_type + ';base64,' + img_data
            width = 200
            height = 200 
            img_tag = s3_url + '" style="width:' + str(width) + 'px; height:' + str(height) + 'px; text-align:center;'
            email_info_text = email_info_text.replace(search_str, img_tag)
    banner_file = BannerFile.objects.filter(org_name=org_name) 
    if banner_file.exists():
        b_header = banner_file[0].header.url
        b_footer = banner_file[0].footer.url
        if banner_file[0].header:
            b_header = get_url_file(banner_file[0].header)
        if banner_file[0].footer:
            b_footer = get_url_file(banner_file[0].footer) 
    else:
        b_header = ''
        b_footer = ''    
  
    # OT, Póliza, Renovación
    if model == 1 or model == 2 or model == 9:
        if poliza.contractor:
            contratante = poliza.contractor.full_name
            email_to = poliza.contractor.email
        else:
            contratante = ''
            email_to =''

        if poliza.forma_de_pago == 1:
            forma_de_pago = "Mensual"
        elif poliza.forma_de_pago == 2:
            forma_de_pago = "Bimestral"
        elif poliza.forma_de_pago == 3:
            forma_de_pago = "Trimestral"
        elif poliza.forma_de_pago == 5:
            forma_de_pago = "Contado"
        elif poliza.forma_de_pago == 6:
            forma_de_pago = "Semestral"
        elif poliza.forma_de_pago == 12:
            forma_de_pago = "Anual"
        else:
            forma_de_pago = poliza.forma_de_pago
              
        org_ = requests.get(settings.CAS_URL + 'get-org-info/' + request.GET.get('org'),verify=False)
        response_org = org_.text
        org_data = json.loads(response_org)
        org_info = org_data['data']['org']
        archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
        if 'logo' in org_info.keys() and len(org_info['logo']) != 0:
            _imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
            if _imagen:
                archivo_imagen = _imagen
            else:
                archivo_imagen = archivo_imagen
        direccion =  org_info['address']

        message=render_to_string("correo_auto_2024.html",{
            'custom_txt': email_info_text,
            'num_policy':poliza.poliza_number,
            'ot':poliza.internal_number,
            'aseguradora': poliza.aseguradora.compania,
            'start_of_validity': poliza.start_of_validity.strftime("%d/%m/%y"),
            'end_of_validity': poliza.end_of_validity.strftime("%d/%m/%y"),
            'ramo':poliza.ramo.ramo_name,
            'subramo': poliza.subramo.subramo_name,
            'frecuencia_de_pago':forma_de_pago, 
            'logo': archivo_imagen,
            'direccion':direccion,
            'contratante': contratante,
            'prima_neta': '$'+ '{:,.2f}'.format(poliza.p_neta),
            'derecho': '$'+ '{:,.2f}'.format(poliza.derecho),
            'rpf': '$'+ '{:,.2f}'.format(poliza.rpf),
            'iva': '$'+ '{:,.2f}'.format(poliza.iva),
            'prima_total': '$'+ '{:,.2f}'.format(poliza.p_total),
            'b_header':b_header,
            'b_footer':b_footer,
            'colorBackground':'#e6f0f7',
            'colorLine':'#3387bf',
            }) 

        if model == 2:
            if admin_archivos_sensibles(request):
                files = PolizasFile.objects.filter(owner = poliza, org_name = org_name)
                if files:
                    for file in files:
                        # URL = settings.MEDIA_URL + str(file.arch).replace(" ", "+")
                        URL=get_presigned_url("/{url}".format(url=file.arch),28800).replace(" ", "+")
                        # URL = URL.replace("%", "%25").replace(";", "%3B").replace("#", "%23").replace("&", "%26");
                        with urllib.request.urlopen(URL) as url:
                            with open(str(file.nombre), 'wb') as f:
                                f.write(url.read())
                        email.attach(file.nombre, open(file.nombre,'rb').read(), 'application/pdf')  
    # Siniestro
    elif model == 3 or model == 4 or model == 11 or model == 12 or model == 13 or model == 14:     
        # print("deberia enviar correo")
        if siniestro.poliza.contractor:
            contratante = siniestro.poliza.contractor.full_name
            email_to = siniestro.poliza.contractor.email
        else:
            contratante = ''
            email_to = ''

        if siniestro.poliza.forma_de_pago == 1:
            forma_de_pago = "Mensual"
        elif siniestro.poliza.forma_de_pago == 2:
            forma_de_pago = "Bimestral"
        elif siniestro.poliza.forma_de_pago == 3:
            forma_de_pago = "Trimestral"
        elif siniestro.poliza.forma_de_pago == 5:
            forma_de_pago = "Contado"
        elif siniestro.poliza.forma_de_pago == 6:
            forma_de_pago = "Semestral"
        elif siniestro.poliza.forma_de_pago == 12:
            forma_de_pago = "Anual"
        else:
            forma_de_pago = siniestro.poliza.forma_de_pago

        if siniestro.tipo_siniestro_general == 2:
            tipo = "Accidentes y Enfermedades"
        elif siniestro.tipo_siniestro_general == 3:
            tipo = "Automóviles"
        elif siniestro.tipo_siniestro_general == 1:
            tipo = "Vida"
        elif siniestro.tipo_siniestro_general == 4:
            tipo = "Daños"

        if siniestro.status == 1:
            status = "Pendiente"
        elif siniestro.status == 2:
            status = "En Trámite"
        elif siniestro.status == 3:
            status = "Completado"
        elif siniestro.status == 4:
            status = "Cancelado"
        elif siniestro.status == 5:
            status = "Rechazado"
        elif siniestro.status == 6:
            status = "En Espera"


        if siniestro.fecha_ingreso:
            fecha_ingreso = siniestro.fecha_ingreso.strftime("%d/%m/%y")
     
        if siniestro.fecha_siniestro:
            fecha_sin = siniestro.fecha_siniestro.strftime("%d/%m/%y")
    
        email_to = siniestro.poliza.contractor.email
        
        siniestro_esp = siniestro

        if  model == 12 or model == 13:
            back = '#fdf1e6'
            color = '#ed8f39'
        else:
            back = '#e6faea'
            color =  '#33d456'

        emailAsegurado=''
        fullname=''
        if siniestro_esp.tipo_siniestro_general == 2:
            formulario=AccidentsDiseases.objects.filter(policy=siniestro.poliza,org_name=siniestro.org_name)
            if formulario and formulario[0] and formulario[0].personal:
                personailinfo=formulario[0].personal
            else:
                personailinfo=None
            accident = Accidentes.objects.filter(siniestro=data['id'], org_name=org_name)
            if accident[0] and accident[0].titular:
                emailAsegurado=accident[0].titular.email
                fullname=accident[0].titular.first_name +' '+str(accident[0].titular.last_name)+' '+str(accident[0].titular.second_last_name)
                asuntoAsegurado= fullname
            elif accident[0] and accident[0].dependiente:
                emailAsegurado=personailinfo.email if personailinfo else email_to
                fullname=accident[0].dependiente.first_name +' '+str(accident[0].dependiente.last_name)+' '+str(accident[0].dependiente.second_last_name)
                asuntoAsegurado= fullname
            if accident and accident[0]:
                tipo = accident[0].get_razon_siniestro_display()
  
            try:
                reclamado = accident[0].total_reclamado
                reclamado = '$'+ '{:,.2f}'.format(reclamado)
            except:
                reclamado = 0.00
            try:
                if siniestro.poliza.aseguradora:
                    asegurador = siniestro.poliza.aseguradora.compania
                else:
                    asegurador = siniestro.poliza.aseguradora
            except Exception as e:
                asegurador = ''
            if siniestro.poliza.document_type ==6:
                asegurador = getattr(
                    siniestro.poliza.parent.parent.parent.aseguradora, 'alias', 
                    getattr(siniestro.poliza.parent.parent.parent.aseguradora, 'compania', None)
                )
            else:
                asegurador=siniestro.poliza.aseguradora.compania if siniestro.poliza.aseguradora else ''
                
                        
            message=render_to_string("correo_auto_sin_2024.html",{
                'custom_txt': email_info_text,
                'num_policy':siniestro.poliza.poliza_number,
                'ot':siniestro.poliza.internal_number,
                'aseguradora': asegurador,
                'start_of_validity': siniestro.poliza.start_of_validity.strftime("%d/%m/%y"),
                'end_of_validity': siniestro.poliza.end_of_validity.strftime("%d/%m/%y"),
                'ramo':siniestro.poliza.ramo.ramo_name if siniestro.poliza.ramo else '',
                'subramo': siniestro.poliza.subramo.subramo_name if siniestro.poliza.subramo else '',
                'frecuencia_de_pago':forma_de_pago,
                'contratante': contratante,
                'estimado':asuntoAsegurado,
                'var_title':'Total Reclamado',
                'var': reclamado,
                'prima_neta': '$'+ '{:,.2f}'.format(siniestro.poliza.p_neta),
                'derecho': '$'+ '{:,.2f}'.format(siniestro.poliza.derecho),
                'rpf': '$'+ '{:,.2f}'.format(siniestro.poliza.rpf),
                'iva': '$'+ '{:,.2f}'.format(siniestro.poliza.iva),
                'prima_total': '$'+ '{:,.2f}'.format(siniestro.poliza.p_total),
                'num_siniestro': siniestro.numero_siniestro,
                'tipo_sin': tipo,
                'afectado': siniestro.affected_item,
                'reason': siniestro.reason,
                'observations': siniestro.observations,
                'status': status,
                'fecha_ingreso': fecha_ingreso,
                'fecha_sin': fecha_sin,
                'b_header':b_header,
                'b_footer':b_footer,
                'colorBackground': back,
                'colorLine': color,
                'logo': archivo_imagen,
                'direccion':direccion,
                })        
        elif siniestro_esp.tipo_siniestro_general == 3 :
            damage = Autos.objects.filter(siniestro=data['id'], org_name=org_name)    
            asuntoAsegurado=' Asegurado(a)'     
            tipo = damage[0].get_tipo_siniestro_display()   if damage and damage[0] else tipo       
            try:
                reclamado = damage[0].indemnizacion
                reclamado = '$'+ '{:,.2f}'.format(reclamado)
            except: 
                reclamado = 0.00
            if siniestro.poliza.document_type ==6:
                asegurador = getattr(
                    siniestro.poliza.parent.parent.parent.aseguradora, 'alias', 
                    getattr(siniestro.poliza.parent.parent.parent.aseguradora, 'compania', None)
                )
            else:
                asegurador=siniestro.poliza.aseguradora.compania if siniestro.poliza.aseguradora else ''
            message=render_to_string("correo_auto_sin_2024.html",{
                'custom_txt': email_info_text,
                'num_policy':siniestro.poliza.poliza_number,
                'ot':siniestro.poliza.internal_number,
                'aseguradora': asegurador,
                'start_of_validity': siniestro.poliza.start_of_validity.strftime("%d/%m/%y"),
                'end_of_validity': siniestro.poliza.end_of_validity.strftime("%d/%m/%y"),
                'ramo':siniestro.poliza.ramo.ramo_name if siniestro.poliza.ramo else '',
                'subramo': siniestro.poliza.subramo.subramo_name if siniestro.poliza.subramo else '',
                'frecuencia_de_pago':forma_de_pago,
                'contratante': contratante,
                'estimado':asuntoAsegurado,
                # 'contratante': 'Asegurado(a)',
                'var_title':'Indemnización',
                'var': reclamado,
                'prima_neta': '$'+ '{:,.2f}'.format(siniestro.poliza.p_neta),
                'derecho': '$'+ '{:,.2f}'.format(siniestro.poliza.derecho),
                'rpf': '$'+ '{:,.2f}'.format(siniestro.poliza.rpf),
                'iva': '$'+ '{:,.2f}'.format(siniestro.poliza.iva),
                'prima_total': '$'+ '{:,.2f}'.format(siniestro.poliza.p_total),
                'num_siniestro': siniestro.numero_siniestro,
                'tipo_sin': tipo,
                'afectado': siniestro.affected_item,
                'reason': siniestro.reason,
                'observations': siniestro.observations,
                'status': status,
                'fecha_ingreso': fecha_ingreso,
                'fecha_sin': fecha_sin,
                'b_header':b_header,
                'b_footer':b_footer,
                'colorBackground': back,
                'colorLine': color,
                'logo': archivo_imagen,
                'direccion':direccion,
                }) 
        elif siniestro_esp.tipo_siniestro_general == 1 :
            vida = Vida.objects.filter(siniestro=data['id'], org_name=org_name)
            asuntoAsegurado=' Asegurado(a)'  
            asegurado= vida[0].nombre_afectado if vida and vida[0] and vida[0].nombre_afectado else ''

            if not asegurado:
                form = Life.objects.filter(policy = siniestro.poliza.id,org_name=org_name)
                tipo_poliza = 'VIDA'
                if form:
                    if form[0]:
                        if form[0].personal:
                            asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
            if asegurado:
                asuntoAsegurado=asegurado
            estimado=asuntoAsegurado
            try:
                reclamado = vida[0].tipo_pago
            except:
                reclamado = "No definido"
            if reclamado == 1:
                reclamado = "Cheque"
            elif reclamado == 2:
                reclamado = "Transferencia"
            else:
                reclamado = reclamado
            if vida and vida[0]:
                tipo = vida[0].get_razon_siniestro_display()
            if siniestro.poliza.document_type ==6:
                asegurador = getattr(
                    siniestro.poliza.parent.parent.parent.aseguradora, 'alias', 
                    getattr(siniestro.poliza.parent.parent.parent.aseguradora, 'compania', None)
                )
            else:
                asegurador=siniestro.poliza.aseguradora.compania if siniestro.poliza.aseguradora else ''
            message=render_to_string("correo_auto_sin_2024.html",{
                'custom_txt': email_info_text,
                'num_policy':siniestro.poliza.poliza_number,
                'ot':siniestro.poliza.internal_number,
                'aseguradora': asegurador,
                'start_of_validity': siniestro.poliza.start_of_validity.strftime("%d/%m/%y"),
                'end_of_validity': siniestro.poliza.end_of_validity.strftime("%d/%m/%y"),
                'ramo':siniestro.poliza.ramo.ramo_name,
                'subramo': siniestro.poliza.subramo.subramo_name,
                'frecuencia_de_pago':forma_de_pago,
                'contratante': contratante,
                'estimado':asuntoAsegurado,
                'var_title':'Tipo Pago',
                'var': reclamado,
                'prima_neta': '$'+ '{:,.2f}'.format(siniestro.poliza.p_neta),
                'derecho': '$'+ '{:,.2f}'.format(siniestro.poliza.derecho),
                'rpf': '$'+ '{:,.2f}'.format(siniestro.poliza.rpf),
                'iva': '$'+ '{:,.2f}'.format(siniestro.poliza.iva),
                'prima_total': '$'+ '{:,.2f}'.format(siniestro.poliza.p_total),
                'num_siniestro': siniestro.numero_siniestro,
                'tipo_sin': tipo,
                'afectado': siniestro.affected_item,
                'reason': siniestro.reason,
                'observations': siniestro.observations,
                'status': status,
                'fecha_ingreso': fecha_ingreso,
                'fecha_sin': fecha_sin,
                'b_header':b_header,
                'b_footer':b_footer,
                'colorBackground': back,
                'colorLine': color,
                'logo': archivo_imagen,
                'direccion':direccion,
                })
        elif siniestro_esp.tipo_siniestro_general == 4 :
            damage = Danios.objects.filter(siniestro=data['id'], org_name=org_name)  
            asuntoAsegurado=' Asegurado(a)'                   
            try:
                reclamado = damage[0].indemnizacion
                reclamado = '$'+ '{:,.2f}'.format(reclamado)
            except: 
                reclamado = 0.00
            if siniestro.poliza.document_type ==6:
                asegurador = getattr(
                    siniestro.poliza.parent.parent.parent.aseguradora, 'alias', 
                    getattr(siniestro.poliza.parent.parent.parent.aseguradora, 'compania', None)
                )
            else:
                asegurador=siniestro.poliza.aseguradora.compania if siniestro.poliza.aseguradora else ''
            message=render_to_string("correo_auto_sin_2024.html",{
                'custom_txt': email_info_text,
                'num_policy':siniestro.poliza.poliza_number,
                'ot':siniestro.poliza.internal_number,
                'aseguradora': asegurador,
                'start_of_validity': siniestro.poliza.start_of_validity.strftime("%d/%m/%y"),
                'end_of_validity': siniestro.poliza.end_of_validity.strftime("%d/%m/%y"),
                'ramo':siniestro.poliza.ramo.ramo_name,
                'subramo': siniestro.poliza.subramo.subramo_name,
                'frecuencia_de_pago':forma_de_pago,
                'estimado':asuntoAsegurado,
                'contratante': contratante,
                'var_title':'Indemnización',
                'var': reclamado,
                'prima_neta': '$'+ '{:,.2f}'.format(siniestro.poliza.p_neta),
                'derecho': '$'+ '{:,.2f}'.format(siniestro.poliza.derecho),
                'rpf': '$'+ '{:,.2f}'.format(siniestro.poliza.rpf),
                'iva': '$'+ '{:,.2f}'.format(siniestro.poliza.iva),
                'prima_total': '$'+ '{:,.2f}'.format(siniestro.poliza.p_total),
                'num_siniestro': siniestro.numero_siniestro,
                'tipo_sin': tipo,
                'afectado': siniestro.affected_item,
                'reason': siniestro.reason,
                'observations': siniestro.observations,
                'status': status,
                'fecha_ingreso': fecha_ingreso,
                'fecha_sin': fecha_sin,
                'b_header':b_header,
                'b_footer':b_footer,
                'colorBackground': back,
                'colorLine': color,
                'logo': archivo_imagen,
                'direccion':direccion,
                }) 
    # Pago de recibo
    elif model == 6:
        moneda=''
        if recibo.poliza.contractor:
            contratante = recibo.poliza.contractor.full_name
        else:
            contratante =''

        if recibo.poliza.forma_de_pago == 1:
            forma_de_pago = "Mensual"
        elif recibo.poliza.forma_de_pago == 2:
            forma_de_pago = "Bimestral"
        elif recibo.poliza.forma_de_pago == 3:
            forma_de_pago = "Trimestral"
        elif recibo.poliza.forma_de_pago == 5:
            forma_de_pago = "Contado"
        elif recibo.poliza.forma_de_pago == 6:
            forma_de_pago = "Semestral"
        elif recibo.poliza.forma_de_pago == 12:
            forma_de_pago = "Anual"
        else:
            forma_de_pago = recibo.poliza.forma_de_pago

        if recibo.poliza.f_currency == 1:
            moneda = "Pesos"
        elif recibo.poliza.f_currency == 2:
            moneda = "Dólares"
        elif recibo.poliza.f_currency == 3:
            moneda = "UDI"
        elif recibo.poliza.f_currency == 4:
            moneda = "EURO"
        else:
            moneda = "Pesos"

        if recibo.receipt_type == 1:       
           tipo_rec = "Póliza"
        elif recibo.receipt_type == 2:
            tipo_rec = "Endoso"
        
        email_to = recibo.poliza.contractor.email

        if recibo.poliza.aseguradora:
            company = recibo.poliza.aseguradora.compania
        else:
            company = 'No encontrada'

        if recibo.poliza.start_of_validity:
            start = recibo.poliza.start_of_validity.strftime("%d/%m/%y")
        else:
            start = 'No encontrada'

        if recibo.poliza.end_of_validity:
            end = recibo.poliza.end_of_validity.strftime("%d/%m/%y")
        else:
            end = 'No encontrada'
        asegurado = ''
        tipo_poliza = ''
        if recibo.poliza.ramo:
            if recibo.poliza.ramo.ramo_name:
                ramo = recibo.poliza.ramo.ramo_name
            if recibo.poliza.ramo.ramo_code ==1:#vida
                form = Life.objects.filter(policy = recibo.poliza.id)
                tipo_poliza = 'VIDA'
                if form[0]:
                    if form[0].personal:
                        asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
                if not asegurado:
                    form = Personal_Information.objects.filter(policy = recibo.poliza.id)
                    if form[0]:
                        if form[0]:
                            asegurado = form[0].full_name if form[0].full_name else str(form[0].first_name)+' '+str(form[0].last_name)
                        else:
                            asegurado = ''
                    else:
                        asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==2:#acc
                tipo_poliza = 'ACCIDENTES Y ENFERMEDADES'
                form = AccidentsDiseases.objects.filter(policy = recibo.poliza.id)
                if form[0]:
                    if form[0].personal:
                        asegurado = form[0].personal.full_name if form[0].personal.full_name else str(form[0].personal.first_name)+' '+str(form[0].personal.last_name)
                    else:
                        asegurado = ''
                else:
                    asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==3 and recibo.poliza.subramo.subramo_code ==9:#aut
                tipo_poliza = 'DAÑOS/AUTOS'
                form = AutomobilesDamages.objects.filter(policy = recibo.poliza.id)
                if form:
                    asegurado = form[0].brand +' - '+ str(form[0].model)+' - ' +str(form[0].year)
                else:
                    asegurado = ''
            elif recibo.poliza.ramo.ramo_code ==3  and recibo.poliza.subramo.subramo_code !=9:#dañ
                tipo_poliza = 'DAÑOS DIVERSOS'
                form = Damages.objects.filter(policy = recibo.poliza.id)
                if form:
                    asegurado = form[0].insured_item +' - '+ str(form[0].item_details)
                else:
                    asegurado = ''
            if recibo.poliza.document_type ==3:                
                tipo_poliza = 'PÓLIZA DE GRUPO'
            if recibo.poliza.document_type ==8:                
                tipo_poliza = 'FIANZA DE GRUPO'
        else:
            ramo = ''
        if recibo.poliza.subramo:
            if recibo.poliza.subramo.subramo_name:
                subramo = recibo.poliza.subramo.subramo_name
        else:
            subramo = ''
        if recibo.endorsement:
            tipo_poliza = 'ENDOSO'
        org_ = requests.get(settings.CAS_URL + 'get-org-info/' + org_name,verify=False)
        response_org = org_.text
        org_data = json.loads(response_org)
        org_info = org_data['data']['org']
        archivo_imagen = 'https://miurabox-public.s3.amazonaws.com/cas/' + org_info['logo']
        # archivo_imagen =get_presigned_url("cas/{url}".format(url=org_info['logo']),28800) 
        if request.user:
            user = str(request.user.first_name) +' '+str(request.user.last_name)
        else:
            user = ''
        if 'custom_email' in data  and data['custom_email']:
            first_comment = data['first_comment'] if 'first_comment' in data else '' 
            second_comment = data['second_comment'] if 'second_comment' in data else '' 
        else:        
            first_comment = data['first_comment'] if 'first_comment' in data else '' 
            second_comment = data['second_comment'] if 'second_comment' in data else '' 
        message=render_to_string("correo_auto_recNV_2024.html",{
            'logo': archivo_imagen,
            'first_comment':first_comment,
            'second_comment':second_comment,
            'custom_txt': email_info_text,
            'num_policy':recibo.poliza.poliza_number,
            'ot':recibo.poliza.internal_number,
            'aseguradora': company,
            'start_of_validity': str(start),
            'end_of_validity': str(end),
            'ramo':ramo,
            'subramo': subramo,
            'frecuencia_de_pago':forma_de_pago,
            'contratante': contratante,
            'subtotal': '$'+ '{:,.2f}'.format(recibo.sub_total),
            'prima_neta': '$'+ '{:,.2f}'.format(recibo.prima_neta),
            'derecho': '$'+ '{:,.2f}'.format(recibo.derecho),
            'rpf': '$'+ '{:,.2f}'.format(recibo.rpf),
            'iva': '$'+ '{:,.2f}'.format(recibo.iva),
            'prima_total': '$'+ '{:,.2f}'.format(recibo.prima_total),
            'primaTotal': '$'+ '{:,.2f}'.format(recibo.prima_total),
            'num_recibo': recibo.recibo_numero,
            'moneda': moneda,
            'fecha_inicio' : recibo.fecha_inicio.strftime("%d/%m/%y"),
            'fecha_fin': recibo.fecha_fin.strftime("%d/%m/%y"),
            'bank':recibo.bank if recibo.bank else '',
            'vencimiento': recibo.vencimiento.strftime("%d/%m/%y"),
            'pay_doc': recibo.pay_doc,
            'tipo_rec': tipo_rec,
            'asegurado':asegurado,
            'user':user,
            'tipo_poliza':tipo_poliza,
            'org_name':recibo.org_name,
            'b_header':b_header,
            'b_footer':b_footer,
            'add_banners':True,
            'colorBackground': '#e6faea',
            'colorLine': '#33d456',
            'direccion':direccion,
          
            })
    # Creación y aplicación de nota de crédito
    elif model == 7 or model == 8:
        if nota.poliza:
            if nota.poliza.contractor.full_name:
                contratante = nota.poliza.contractor.full_name
                emailc = nota.poliza.contractor.email
            else:
                contratante = ''
                emailc = ''
            
            if nota.poliza.forma_de_pago == 1:
                forma_de_pago = "Mensual"
            elif nota.poliza.forma_de_pago == 2:
                forma_de_pago = "Bimestral"
            elif nota.poliza.forma_de_pago == 3:
                forma_de_pago = "Trimestral"
            elif nota.poliza.forma_de_pago == 5:
                forma_de_pago = "Contado"
            elif nota.poliza.forma_de_pago == 6:
                forma_de_pago = "Semestral"
            elif nota.poliza.forma_de_pago == 12:
                forma_de_pago = "Anual"
            else:
                forma_de_pago = nota.poliza.forma_de_pago

            if nota.poliza.f_currency == 1:
                moneda = "Pesos"
            elif nota.poliza.f_currency == 2:
                moneda = "Dólares"
            elif nota.poliza.f_currency == 3:
                moneda = "UDI"
            elif nota.poliza.f_currency == 4:
                moneda = "EURO"
            else:
                moneda = "Pesos"

            if nota.poliza.subramo.subramo_name == 'Vida':
                endoso = "Endoso de Vida"
            elif nota.poliza.subramo.subramo_name == 'Automóviles':
                endoso = "Endoso de Autos"
            elif nota.poliza.subramo.subramo_name == 'Gastos Médicos':
                endoso = "Endoso de Accidentes y Enfermedades"
            elif nota.poliza.ramo.ramo_name == 'Daños' and nota.poliza.subramo.subramo_name != 'Automóviles':
                endoso = str("Endoso de Daños: ") + nota.poliza.subramo.subramo_name
            else:
                endoso = 'Endoso'

            np = nota.poliza.poliza_number
            internal = nota.poliza.internal_number
            aseg = nota.poliza.aseguradora.compania
            fi = nota.poliza.start_of_validity
            fe = nota.poliza.end_of_validity
            ramo = nota.poliza.ramo.ramo_name
            sramo = nota.poliza.subramo.subramo_name

        elif nota.poliza:
            contratante = ''
            emailc = ''
            if nota.poliza.contractor:
                contratante = nota.poliza.contractor.full_name
                emailc = nota.poliza.contractor.email
            else:
                contratante = ''
                emailc = ''
            forma_de_pago = "Anual"

            if nota.poliza.f_currency == 1:
                moneda = "Pesos"
            elif nota.poliza.f_currency == 2:
                moneda = "Dólares"
            elif nota.poliza.f_currency == 3:
                moneda = "UDI"
            elif nota.poliza.f_currency == 4:
                moneda = "EURO"
            else:
                moneda = "Pesos"

            if nota.poliza.subramo.subramo_name == 'Vida':
                endoso = "Endoso de Vida"
            elif nota.poliza.subramo.subramo_name == 'Automóviles':
                endoso = "Endoso de Autos"
            elif nota.poliza.subramo.subramo_name == 'Gastos Médicos':
                endoso = "Endoso de Accidentes y Enfermedades"
            elif nota.poliza.ramo.ramo_name == 'Daños' and nota.poliza.subramo.subramo_name != 'Automóviles':
                endoso = str("Endoso de Daños: ") + nota.poliza.subramo.subramo_name
            else:
                endoso = 'Endoso'

            np = nota.poliza.poliza_number
            internal = nota.poliza.internal_number
            aseg = nota.poliza.aseguradora.compania            
            fi = nota.poliza.start_of_validity
            fe = nota.poliza.end_of_validity
            ramo = nota.poliza.ramo.ramo_name
            sramo = nota.poliza.subramo.subramo_name,

        if nota.status == 1:
            status_nc = "Cobrada"
        elif nota.status == 2:
            status_nc = "Cancelada"
        elif nota.status == 3:
            status_nc = "Prorrogada"
        elif nota.status == 4:
            status_nc = "Pendiente de pago"
        elif nota.status == 5:
            status_nc = "Liquidado"
        elif nota.status == 6:
            status_nc = "Conciliada"
        elif nota.status == 7:
            status_nc = "Cerrada"
        else:
            status_nc = 'No establecido'
        
        email_to = emailc
        if model == 8:
          colorBackground = '#e6faea'
          colorLine = '#33d456'
        else:
          colorBackground = '#e6f0f7'
          colorLine = '#3387bf'
        message=render_to_string("correo_auto_note_2024.html",{
            'custom_txt': email_info_text,
            'num_policy':np,
            'ot':internal,
            'aseguradora': aseg,
            'start_of_validity': fi.strftime("%d/%m/%y"),
            'end_of_validity': fe.strftime("%d/%m/%y"),
            'ramo':ramo,
            'subramo': sramo,
            'frecuencia_de_pago':forma_de_pago,
            'contratante': contratante,
            'subtotal': '$'+ '{:,.2f}'.format(nota.sub_total),
            'prima_neta': '$'+ '{:,.2f}'.format(nota.prima_neta),
            'rpf': '$'+ '{:,.2f}'.format(nota.rpf),
            'iva': '$'+ '{:,.2f}'.format(nota.iva),
            'prima_total': '$'+ '{:,.2f}'.format(nota.prima_total),
            'moneda': moneda,
            'fecha_emision' : nota.created_at.strftime("%d/%m/%y"),
            'folio': nota.folio,
            'endoso': endoso,
            'status': status_nc,
            'gastos': '$'+ '{:,.2f}'.format(nota.derecho),
            'b_header':b_header,
            'b_footer':b_footer,
            'logo': archivo_imagen,
            'direccion':direccion,
            'colorBackground':colorBackground,
            'colorLine':colorLine,
            })
    
    elif model == 15 or model == 16 or model == 17 or model == 18:
        
        f_beneficiarios = BeneficiariesContract.objects.filter(poliza_many=int(data['id'])).values('full_name','email');
        
        for fb in f_beneficiarios:
            email_to.append(fb['email'])
        try:
            email_to =  email_to[0]
        except Exception as e:
            email_to =  email_to
        #email_to = 'david.cantu@miurabox.com'
        message=render_to_string("fianza_email.html",{
            'custom_txt': email_info_text,
            'fianza_number':poliza.poliza_number,
            'afianzadora':poliza.aseguradora,
            'ramo': poliza.ramo,
            'subramo': poliza.subramo,
            'fianza_type':poliza.poliza_type if poliza else '',
            'b_header':b_header,
            'b_footer':b_footer,
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
    try:
        remitente=build_from_header(remitente)
    except:
        remitente=remitente
    # email_to=['guadalupe.becerril@miurabox.com']
    if emailAsegurado:
        email = EmailMultiAlternatives(subject, message, from_email=remitente, to=[emailAsegurado], cc=[request.user.email])
    else:
        email = EmailMultiAlternatives(subject, message, from_email=remitente, to=[email_to], cc=[request.user.email])
    # email = EmailMultiAlternatives(subject, message, from_email='noreply@miurabox.com', to=['guadalupe.becerril@miurabox.com'])
    
    email.content_subtype="html"
    email.mixed_subtype = 'related'
    # Esto fuerza UTF-8 en las cabeceras y el cuerpo
    email.encoding = 'utf-8'
    try:
        email.send()
        val={'status':'sent'}
        return JsonResponse(val, status=200)
    
    except smtplib.SMTPAuthenticationError:
        val = {'status':'Credenciales de correo mal configuradas. Comuniquese con su administrador'}
        return JsonResponse(val, status=400)
    
    except Exception as e:
        print('errr',e)
        val = {'status':'Error al enviar la OT'+str(e)}
        return JsonResponse(val, status=400)
    
def get_url_file(fileobj):
    if fileobj and hasattr(fileobj, 'url'):
        try:
            urloki = fileobj.url.replace('https://miurabox.s3.', 'https://miurabox-public.s3.')
        except Exception as e:
            # Log the exception if needed
            urloki = fileobj.url
    else:
        urloki = None
    return urloki

# up amazon
def upload_to_s3_signatures(file_path, bucket_name, s3_file_name,org_name):
    import boto3    
    from boto3.s3.transfer import S3Transfer
    from botocore.exceptions import ClientError, NoCredentialsError

    AWS_STORAGE_BUCKET_NAME = bucket_name
    AWS_ACCESS_KEY_ID = 'xxxxxxxxx'
    AWS_SECRET_ACCESS_KEY = 'xxxxxxxxx'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    AWS_DEFAULT_ACL = None
    MEDIA_URL = "https://%s/" % (AWS_S3_CUSTOM_DOMAIN)
    JWT_SECRET_KEY = 'CaS2.xxxxxxxxxxxx'
    JWT_ALGORITHM = 'HS256'


    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    BUCKET_FILE_NAME = "signatures/"+org_name+"/"+s3_file_name
    
    try:
        # Check if the object already exists
        s3.head_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=BUCKET_FILE_NAME)
        print("File "+str(BUCKET_FILE_NAME)+" already exists in the bucket "+str(bucket_name)+". Skipping upload.")
        return MEDIA_URL + BUCKET_FILE_NAME
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            # The object does not exist, proceed with upload
            try:
                s3.upload_file(file_path, AWS_STORAGE_BUCKET_NAME, BUCKET_FILE_NAME, ExtraArgs={'ACL':'public-read'})
                print("Upload Successful: ",BUCKET_FILE_NAME)
                return MEDIA_URL + BUCKET_FILE_NAME
            except FileNotFoundError:
                print("The file was not found")
                return ''
            except NoCredentialsError:
                print("Credentials not available")
                return ''
        else:
            # Something else has gone wrong.
            print("Error checking for object existence: ",e)
            return ''
    except NoCredentialsError:
        print("Credentials not available")
        return ''
    except FileNotFoundError:
        print("The file was not found")
        return ''
# get users from @ in the comnnets /(bitacora)
def extract_mentioned_users(comment):
    matches = re.findall(r'@(\w+ \w+)', comment)
    return matches

def is_perm_ver_referenciadores(request):
    try:
        token  = request.META['HTTP_AUTHORIZATION'].replace('Bearer ', '')
        org_request = request.GET.get('org')
        session_obj = Session.objects.get(jwt_token=token)
        headers = {
            'Content-Type': 'application/json' ,
            'Authorization': 'Token %s' % session_obj.token
        }
        r = requests.get(settings.CAS2_URL + 'user-info-saam', headers = headers)
        if r.status_code == 200:
            result_json = r.json()
            for y in result_json['permissions']['SAAM']['Referenciadores']:
                try:
                    if y['name'] =='Ver referenciadores':
                        return  y['checked']
                except Exception as h:
                    print('jjjjjjjjjjjjjjjjjjjj',h)
        return False
    except Exception as ers:
        print('eror ver Refernecic',ers)
        return False


def upload_to_s3_img_emails(image_data, image_name, image_type,filename,org_name):
    import boto3    
    from boto3.s3.transfer import S3Transfer
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_STORAGE_BUCKET_NAME = "miurabox-public"
    AWS_ACCESS_KEY_ID = 'xxxxxxxx'
    AWS_SECRET_ACCESS_KEY = 'xxxxxxxxxxx'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    MEDIA_URL = "https://%s/" % (AWS_S3_CUSTOM_DOMAIN)
    JWT_SECRET_KEY = 'CaS2.xxxxxxxxxxx'
    JWT_ALGORITHM = 'HS256'
    image_data_bytes = base64.b64decode(image_data)
    # Upload image to S3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        BUCKET_FILE_NAME = "emailstemplates/%s/%s"%(org_name,filename)
        s3.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=BUCKET_FILE_NAME,
            Body=image_data_bytes,
            ContentType='image/'+str(image_type),
            ACL='public-read' 
        )
        url = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/' + BUCKET_FILE_NAME

        return url
    except FileNotFoundError:
        return "The file was not found"
    except NoCredentialsError:
        return "Credentials not available"
    
from email.header import Header
from email.utils import parseaddr, formataddr
import logging,unicodedata


logger = logging.getLogger(__name__)
def ascii_sin_acentos(texto):
    if texto is None:
        return ""
    # quita acentos y caracteres no-ASCII
    return (unicodedata.normalize('NFKD', str(texto))
            .encode('ascii', 'ignore')
            .decode('ascii'))
# def build_from_header(remitente):
#     # remitente puede ser "Nombre con acentos <correo@dominio.com>"
#     name, addr = parseaddr(remitente or "")
#     # Codifica el nombre (con acentos) como header RFC
#     safe_name = str(Header(name, 'utf-8')) if name else ""
#     return formataddr((safe_name, addr))
def build_from_header(remitente):
    raw = (remitente or "").strip()
    # 1) Si trae <...> y el nombre tiene coma, pon el display-name entre comillas
    #    para que parseaddr no lo corte.
    if "<" in raw and ">" in raw:
        display = raw.split("<", 1)[0].strip()
        rest = "<" + raw.split("<", 1)[1].strip()
        if "," in display and not (display.startswith('"') and display.endswith('"')):
            display = '"' + display.replace('"', '') + '"'
        raw = display + " " + rest

    # 2) parseaddr
    name, addr = parseaddr(raw)

    # 3) Fallback por si addr vino vacío o raro
    if not addr:
        m = EMAIL_RE.search(raw)
        if not m:
            raise ValueError("Remitente sin email válido: {0}".format(remitente))
        addr = m.group(1)

    # 4) Si el nombre quedó vacío (o demasiado corto), reconstruye desde raw
    if not name:
        name = raw.replace(addr, "")
        name = name.replace("<", " ").replace(">", " ")
        name = re.sub(r"\s+", " ", name).strip().strip('"')

    # 5) RFC2047 para UTF-8 (acentos)
    safe_name = str(Header(name, "utf-8")) if name else ""

    return formataddr((safe_name, addr))
def remitente_ascii(remitente):
    name, addr = parseaddr(remitente or "")
    return "{} <{}>".format(ascii_sin_acentos(name), ascii_sin_acentos(addr))
