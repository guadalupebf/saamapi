# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import tempfile
import traceback
import urllib.request  # py3.5? ojo: en tu código es urllib.request; ajusta según tu runtime real
import smtplib
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from archivos.presigned_url import get_presigned_url
from forms.models import Life, AccidentsDiseases, AutomobilesDamages
from .models import Polizas, Pendients, Assign
from archivos.models import PolizasFile
from core.models import OrgInfo
from recibos.views import checkCurrency
def safe_send_one_certificate(request, org_info, caratula, cer, plantillaSeleccionada,
                              first_comment, second_comment, subjectEmail,
                              logo, logo_mini, direccion, folder):
    res = {
        'sent': False,
        'receiver_email': '',
        'error_message': '',
        'error_trace': '',
        'certificate_number': cer.certificate_number or '',
    }
    try:
        orginfo = OrgInfo.objects.filter(org_name = caratula.org_name)
    except:
        orginfo =None

    tmp_paths = []
    try:
        # 1) Determina email destino según tu lógica (ramo/subramo)
        receiver_email = None

        # EJEMPLO: ajusta a tu código real
        if caratula.ramo.ramo_code == 1:
            life = Life.objects.get(policy=cer, org_name=caratula.org_name)
            receiver_email = life.personal.email if (life and life.personal and life.personal.email) else None

        elif caratula.ramo.ramo_code == 2:
            acc = AccidentsDiseases.objects.get(policy=cer, org_name=caratula.org_name)
            receiver_email = acc.personal.email if (acc and acc.personal and acc.personal.email) else None

        elif caratula.subramo.subramo_code == 9:
            auto = AutomobilesDamages.objects.get(policy=cer, org_name=caratula.org_name)
            receiver_email = auto.email if auto and auto.email else None

        if not receiver_email:
            res['error_message'] = 'Sin email del asegurado para este certificado'
            return res

        receiver_email = receiver_email.lower().strip()
        res['receiver_email'] = receiver_email

        poliza = Polizas.objects.get(id=cer.id)

        # 2) Render HTML (usa tus mismos campos)
        data = {
            'poliza_number': poliza.poliza_number if poliza.poliza_number else poliza.certificate_number,
            'start_of_validity': poliza.start_of_validity.strftime("%d/%m/%Y"),
            'end_of_validity': poliza.end_of_validity.strftime("%d/%m/%Y"),
            'ramo': caratula.ramo.ramo_name,
            'subramo': caratula.subramo.subramo_name,
            'first_comment': first_comment,
            'second_comment': second_comment,
            'logo': logo,
            'logo_mini': logo_mini,
            'direccion': direccion,
            'certificate_number': cer.certificate_number,
            'dato_cvigencia': orginfo[0].dato_cvigencia if orginfo else True,
            'dato_caseguradora': orginfo[0].dato_caseguradora if orginfo else True,
            'dato_csubramo': orginfo[0].dato_csubramo if orginfo else True,
            'dato_cmoneda': orginfo[0].dato_cmoneda if orginfo else True,
            'dato_cfrecuenciapago': orginfo[0].dato_cfrecuenciapago if orginfo else True,
            'dato_casegurado': orginfo[0].dato_casegurado if orginfo else True,
            'dato_cptotal': orginfo[0].dato_cptotal if orginfo else True,
            'dato_cpneta': orginfo[0].dato_cpneta if orginfo else True,
            'dato_cderecho': orginfo[0].dato_cderecho if orginfo else True,
            'dato_crpf': orginfo[0].dato_crpf if orginfo else True,
            'dato_civ': orginfo[0].dato_civ if orginfo else True,
            'dato_cnumcertificado': orginfo[0].dato_cnumcertificado if orginfo else True,
            'dato_ccontratante': orginfo[0].dato_ccontratante if orginfo else True,
        }
        message = render_to_string("share_certificateNV_custom.html", data)

        # 3) Remitente
        if request.user.email:
            remitente = "{} <{}>".format(org_info['name'], request.user.email)
        elif org_info.get('email'):
            remitente = "{} <{}>".format(org_info['name'], org_info['email'])
        else:
            remitente = "{} <no-reply@miurabox.com>".format(org_info['name'])

        subject = subjectEmail if subjectEmail else (
            'Póliza: {0}, {1} {2}'.format(
                poliza.poliza_number if poliza.poliza_number else poliza.certificate_number,
                caratula.aseguradora.alias if caratula.aseguradora and caratula.aseguradora.alias else '',
                caratula.subramo.subramo_name if caratula.subramo else ''
            )
        )

        # 4) Adjuntos (CRÍTICO: usa temporales únicos para no pisarte en loop)
        r_files = PolizasFile.objects.filter(owner=cer.id)
        email = EmailMultiAlternatives(
            subject, message,
            from_email=remitente,
            to=[receiver_email],
            cc=[request.user.email]  # si luego lo haces configurable, aquí lo controlas
        )
        email.content_subtype = "html"
        email.mixed_subtype = 'related'

        for f in r_files:
            url = get_presigned_url(folder + "/{url}".format(url=f.arch), 28800).replace(" ", "+")
            # descarga a tmp
            fd, tmp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
            tmp_paths.append(tmp_path)

            with urllib2.urlopen(url) as resp:
                with open(tmp_path, 'wb') as out:
                    out.write(resp.read())

            attach_name = f.nombre or ('cert_{0}.pdf'.format(cer.id))
            email.attach(attach_name, open(tmp_path, 'rb').read(), 'application/pdf')

        # 5) Enviar
        email.send()

        # 6) SOLO si envió: marca shared / crea Assign/Pendients (para que sea “fidedigno”)
        for f in r_files:
            f.shared = True
            f.save()

        res['sent'] = True
        return res

    except smtplib.SMTPAuthenticationError:
        res['error_message'] = 'Credenciales de correo mal configuradas'
        res['error_trace'] = traceback.format_exc()
        return res
    except Exception as e:
        res['error_message'] = str(e)
        res['error_trace'] = traceback.format_exc()
        return res
    finally:
        for p in tmp_paths:
            try:
                os.remove(p)
            except Exception:
                pass

# utils_share.py
import traceback
import smtplib
import urllib.request
import urllib.error
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

def _get_receiver_email_email_only(caratula, cer, org_name):
    """
    Regresa el email destino según ramo/subramo.
    Lanza Exception si no existe email.
    """
    receiver_email = None

    if caratula.ramo and caratula.ramo.ramo_code == 1:
        life = Life.objects.get(policy=cer, org_name=org_name)
        if life and life.personal and life.personal.email:
            receiver_email = life.personal.email

    elif caratula.ramo and caratula.ramo.ramo_code == 2:
        acc = AccidentsDiseases.objects.get(policy=cer, org_name=org_name)
        if acc and acc.personal and acc.personal.email:
            receiver_email = acc.personal.email

    elif caratula.subramo and caratula.subramo.subramo_code == 9:
        auto = AutomobilesDamages.objects.get(policy=cer, org_name=org_name)
        if auto and auto.email:
            receiver_email = auto.email

    if not receiver_email:
        raise Exception('Sin email del asegurado para este certificado')

    return receiver_email.lower().strip()


def safe_send_one_certificate_email_only(
    request,
    org_info,
    caratula,
    cer,
    plantillaSeleccionada,
    first_comment,
    second_comment,
    subjectEmail,
    logo,
    logo_mini,
    direccion,
    folder,
):
    """
    Envía 1 certificado por correo. Devuelve dict con sent/error, sin romper el batch.
    """
    res = {
        'sent': False,
        'receiver_email': '',
        'error_message': '',
        'error_trace': '',
        'certificate_number': cer.certificate_number or '',
    }

    try:
        org_name = caratula.org_name
        try:
            orginfo = OrgInfo.objects.filter(org_name = caratula.org_name)
        except:
            orginfo =None

        receiver_email = _get_receiver_email_email_only(caratula, cer, org_name)
        res['receiver_email'] = receiver_email

        poliza = Polizas.objects.get(id=cer.id)
        parCurrency = checkCurrency(caratula.f_currency)

        status_txt = "Certificado Activo"
        contratante = caratula.contractor.full_name if caratula.contractor else ''

        data = {
            'poliza_number': poliza.poliza_number if poliza.poliza_number else poliza.certificate_number,
            'start_of_validity': poliza.start_of_validity.strftime("%d/%m/%Y"),
            'end_of_validity': poliza.end_of_validity.strftime("%d/%m/%Y"),
            'ramo': caratula.ramo.ramo_name if caratula.ramo else '',
            'subramo': caratula.subramo.subramo_name if caratula.subramo else '',
            'status': status_txt,
            'frecuencia_de_pago': caratula.get_forma_de_pago_display() if hasattr(caratula, 'get_forma_de_pago_display') else '',
            'contratante': contratante,
            'aseguradora': (
                caratula.aseguradora.alias if caratula.aseguradora and caratula.aseguradora.alias
                else caratula.aseguradora.compania if caratula.aseguradora and caratula.aseguradora.compania
                else ''
            ),
            'prima_neta': '$' + '{:,.2f}'.format(poliza.p_neta if poliza.p_neta else 0),
            'prima_total': '$' + '{:,.2f}'.format(poliza.p_total if poliza.p_total else 0),
            'derecho': '$' + '{:,.2f}'.format(poliza.derecho if poliza.derecho else 0),
            'rpf': '$' + '{:,.2f}'.format(poliza.rpf if poliza.rpf else 0),
            'iva': '$' + '{:,.2f}'.format(poliza.iva if poliza.iva else 0),
            'title': 'Email',
            'first_comment': first_comment or '',
            'second_comment': second_comment or '',
            'logo': logo,
            'logo_mini': logo_mini,
            'direccion': direccion or '',
            'moneda': parCurrency,
            'certificate_number': cer.certificate_number,

            # Toggles por plantilla
            'dato_cvigencia': orginfo[0].dato_cvigencia if orginfo else True,
            'dato_caseguradora': orginfo[0].dato_caseguradora if orginfo else True,
            'dato_csubramo': orginfo[0].dato_csubramo if orginfo else True,
            'dato_cmoneda': orginfo[0].dato_cmoneda if orginfo else True,
            'dato_cfrecuenciapago': orginfo[0].dato_cfrecuenciapago if orginfo else True,
            'dato_casegurado': orginfo[0].dato_casegurado if orginfo else True,
            'dato_cptotal': orginfo[0].dato_cptotal if orginfo else True,
            'dato_cpneta': orginfo[0].dato_cpneta if orginfo else True,
            'dato_cderecho': orginfo[0].dato_cderecho if orginfo else True,
            'dato_crpf': orginfo[0].dato_crpf if orginfo else True,
            'dato_civ': orginfo[0].dato_civ if orginfo else True,
            'dato_cnumcertificado': orginfo[0].dato_cnumcertificado if orginfo else True,
            'dato_ccontratante': orginfo[0].dato_ccontratante if orginfo else True,
        }

        message = render_to_string("share_certificateNV_custom.html", data)

        # From
        if request.user.email:
            remitente = "{} <{}>".format(org_info['name'], request.user.email)
        elif org_info.get('email'):
            remitente = "{} <{}>".format(org_info['name'], org_info['email'])
        else:
            remitente = "{} <no-reply@miurabox.com>".format(org_info['name'])

        subject = subjectEmail if subjectEmail else (
            'Póliza: {0}, {1} {2}'.format(
                poliza.poliza_number if poliza.poliza_number else poliza.certificate_number,
                caratula.aseguradora.alias if caratula.aseguradora and caratula.aseguradora.alias else '',
                caratula.subramo.subramo_name if caratula.subramo else ''
            )
        )

        email = EmailMultiAlternatives(
            subject, message,
            from_email=remitente,
            to=[receiver_email],
            cc=[request.user.email] if request.user.email else []
        )
        email.content_subtype = "html"
        email.mixed_subtype = 'related'

        # Adjuntos (en memoria)
        r_files = PolizasFile.objects.filter(owner=cer.id)
        for f in r_files:
            URL = get_presigned_url(folder + "/{url}".format(url=f.arch), 28800).replace(" ", "+")
            try:
                pdf_bytes = urllib.request.urlopen(URL, timeout=30).read()
                attach_name = f.nombre or ('cert_{0}.pdf'.format(cer.id))
                email.attach(attach_name, pdf_bytes, 'application/pdf')
            except (urllib.error.HTTPError, urllib.error.URLError):
                # falla un adjunto, pero NO tumbes el envío completo
                continue
            except Exception:
                continue

        # ENVÍO
        res['receiver_email']=receiver_email
        email.send()

        # ✅ Solo si envió: marca shared
        for f in r_files:
            f.shared = True
            f.save()

        # ✅ Si en esta vista quieres Pendients SOLO cuando envió:
        try:
            Pendients.objects.create(
                email=receiver_email,
                poliza=poliza,
                is_owner=True,
                active=True
            )
        except Exception:
            pass

        res['sent'] = True
        return res

    except smtplib.SMTPAuthenticationError:
        res['error_message'] = 'Credenciales de correo mal configuradas'
        res['error_trace'] = traceback.format_exc()
        return res
    except Exception as e:
        res['error_message'] = str(e)
        res['error_trace'] = traceback.format_exc()
        return res
