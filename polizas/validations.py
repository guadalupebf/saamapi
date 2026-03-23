# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from control.permissions import IsAuthenticatedV2  # ajusta import

def _parse_iso_to_date(value):
    """
    "2025-12-19T08:00:00.000Z" -> date(2025,12,19)
    Compatible Python 3.5
    """
    if not value:
        return None

    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value

    try:
        s = value.strip()

        if s.endswith('Z'):
            s = s[:-1]

        if '.' in s:
            s = s.split('.')[0]

        if 'T' in s:
            s = s.split('T')[0]

        dt = datetime.datetime.strptime(s, "%Y-%m-%d")
        return dt.date()
    except Exception:
        return None


def _get_recibo1_fecha_inicio(payload):
    recibos = payload.get('recibos_poliza') or []
    if not isinstance(recibos, list) or not recibos:
        return None

    # Busca recibo_numero == 1
    for r in recibos:
        try:
            if int(r.get('recibo_numero') or 0) == 1:
                return r.get('fecha_inicio')
        except Exception:
            pass

    # fallback: primer recibo
    try:
        return (recibos[0] or {}).get('fecha_inicio')
    except Exception:
        return None


def _es_invertida_ddmm(ini_pol, ini_rec):
    if not ini_pol or not ini_rec:
        return False
    if ini_pol == ini_rec:
        return False
    if ini_pol.year != ini_rec.year:
        return False
    return (ini_pol.day == ini_rec.month) and (ini_pol.month == ini_rec.day)


@api_view(['POST'])
@permission_classes((IsAuthenticatedV2,))
def EvaluarVigencyPolicie(request):
    """
    Valida usando SOLO el JSON enviado (aún no se crea en BD).
    Compara:
      payload.start_of_validity vs recibos_poliza[recibo_numero=1].fecha_inicio
    - Si NO hay recibos => NO warning (no hay comparación posible).
    - Si hay recibos y falta recibo 1 o su fecha => warning.
    - Si hay ambos y no coinciden => warning.
    """
    payload = request.data or {}

    poliza_start_raw = payload.get('start_of_validity')
    ini_pol = _parse_iso_to_date(poliza_start_raw)

    # ✅ Detectar si el payload trae recibos (ajusta keys según tu JSON real)
    recibos = (
        payload.get('recibos_poliza')
        or payload.get('receipts')
        or payload.get('recibos')
        or []
    )

    # ✅ Si NO hay recibos, no hay comparación posible => NO warning
    if not recibos:
        return Response({
            "ok": True,
            "warning": False,
            "code": "NO_RECEIPTS_TO_COMPARE",
            "message": "No se validó vigencia contra recibos porque no se enviaron recibos en el payload.",
            "data": {
                "policy_start_raw": poliza_start_raw,
                "policy_start": str(ini_pol) if ini_pol else None
            }
        }, status=status.HTTP_200_OK)

    # ✅ Ya hay recibos: intentamos obtener recibo 1
    recibo1_start_raw = _get_recibo1_fecha_inicio(payload)
    ini_rec = _parse_iso_to_date(recibo1_start_raw)

    # Si falta start_of_validity, aquí sí tiene sentido warning porque hay recibos para comparar
    if not ini_pol:
        return Response({
            "ok": True,
            "warning": True,
            "code": "POLICY_START_MISSING",
            "message": "No se pudo validar la vigencia: falta start_of_validity.",
            "data": {
                "policy_start_raw": poliza_start_raw,
                "receipt1_start_raw": recibo1_start_raw
            }
        }, status=status.HTTP_200_OK)

    # Si falta fecha del recibo 1 (pero sí hay recibos), warning porque no se puede comparar correctamente
    if not ini_rec:
        return Response({
            "ok": True,
            "warning": True,
            "code": "RECEIPT1_START_MISSING",
            "message": "No se pudo validar la vigencia: hay recibos pero falta fecha_inicio del recibo 1.",
            "data": {
                "policy_start_raw": poliza_start_raw,
                "receipt1_start_raw": recibo1_start_raw,
                "policy_start": str(ini_pol),
                "receipt1_start": None
            }
        }, status=status.HTTP_200_OK)

    # ✅ Comparación normal
    if ini_pol != ini_rec:
        code = "VIGENCIA_MISMATCH"
        extra = {}
        if _es_invertida_ddmm(ini_pol, ini_rec):
            code = "VIGENCIA_MISMATCH_INVERTIDA_DDMM"
            extra["hint"] = "Parece inversión DD/MM vs MM/DD."

        data = {
            "policy_start": str(ini_pol),
            "receipt1_start": str(ini_rec)
        }
        data.update(extra)

        return Response({
            "ok": True,
            "warning": True,
            "code": code,
            "message": "El inicio de vigencia de la póliza no coincide con el inicio de vigencia del recibo 1.",
            "data": data
        }, status=status.HTTP_200_OK)

    return Response({"ok": True, "warning": False}, status=status.HTTP_200_OK)
# def EvaluarVigencyPolicie(request):
#     """
#     Valida usando SOLO el JSON enviado (aún no se crea en BD).
#     Compara:
#       payload.start_of_validity vs recibos_poliza[recibo_numero=1].fecha_inicio
#     Si NO coincide día/mes/año => warning.
#     """
#     payload = request.data or {}

#     poliza_start_raw = payload.get('start_of_validity')
#     recibo1_start_raw = _get_recibo1_fecha_inicio(payload)

#     ini_pol = _parse_iso_to_date(poliza_start_raw)
#     ini_rec = _parse_iso_to_date(recibo1_start_raw)

#     if not ini_pol or not ini_rec:
#         return Response({
#             "ok": True,
#             "warning": True,
#             "code": "VIGENCIA_MISSING",
#             "message": "No se pudo validar la vigencia: falta start_of_validity o fecha_inicio del recibo 1.",
#             "data": {
#                 "policy_start_raw": poliza_start_raw,
#                 "receipt1_start_raw": recibo1_start_raw,
#                 "policy_start": str(ini_pol) if ini_pol else None,
#                 "receipt1_start": str(ini_rec) if ini_rec else None
#             }
#         }, status=status.HTTP_200_OK)

#     if ini_pol != ini_rec:
#         code = "VIGENCIA_MISMATCH"
#         extra = {}
#         if _es_invertida_ddmm(ini_pol, ini_rec):
#             code = "VIGENCIA_MISMATCH_INVERTIDA_DDMM"
#             extra["hint"] = "Parece inversión DD/MM vs MM/DD."

#         data = {
#             "policy_start": str(ini_pol),
#             "receipt1_start": str(ini_rec)
#         }
#         data.update(extra)

#         return Response({
#             "ok": True,
#             "warning": True,
#             "code": code,
#             "message": "El inicio de vigencia de la póliza no coincide con el inicio de vigencia del recibo 1.",
#             "data": data
#         }, status=status.HTTP_200_OK)

#     return Response({"ok": True, "warning": False}, status=status.HTTP_200_OK)
