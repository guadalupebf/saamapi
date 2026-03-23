from core.models import ReferenciadoresInvolved
from core.models import Shared
from core.serializers import RefInvolvedInfoSerializer
from itertools import chain
from organizations.views import get_org
from polizas.models import Polizas
from operator import __or__ as OR
from operator import __and__ as AND
from functools import reduce
from django.db.models import Q
from django.contrib.auth.models import User
from contratantes.models import Group, CelulaContractor


def polizas_por_grupo(request, only_fianzas=False):
    """
    Este metodo trae todas las polizas y fianzas, en caso que only_fianzas=True, solo filtrará las fianzas
    """

    org =  request.META['user']['org']['name']
    grups = Group.objects.filter(owner=request.user).values_list('id', flat=True)
    yo = request.user
    user_group_filters = [Q(grupo_de_contratantes__id__in=grups), Q(usuario=yo)]
    
    polizas_compartidas_y_por_usuario = Shared.objects.filter(reduce(OR, user_group_filters)).exclude(poliza=None).distinct('poliza').values_list('poliza', flat=True)

    aseguradoras_compartidas =  Shared.objects.filter(reduce(OR, user_group_filters)).exclude(aseguradora=None).distinct('aseguradora').values_list('aseguradora', flat=True)
    aseguradoras_compartidas = Polizas.objects.filter(aseguradora__in = aseguradoras_compartidas).values_list('pk', flat = True).exclude(status__in = [12,13])

    grupo_de_contratantes_compartidas =  Shared.objects.filter(reduce(OR, user_group_filters)).exclude(grupo_de_contratantes = None).distinct('grupo_de_contratantes').values_list('grupo_de_contratantes',flat = True)
    contractor_polizas = Polizas.objects.filter(contractor__group__in = grupo_de_contratantes_compartidas).values_list('pk', flat = True).exclude(status__in = [12,13])
    
    grupo_de_contratantes_compartidas = list(contractor_polizas)

    print('grupo_de_contratantes_compartidas', grupo_de_contratantes_compartidas)

    celulas = CelulaContractor.objects.filter(users_many=yo)
    polizas_por_celula = Polizas.objects.filter(celula=celulas).values_list('pk', flat = True)#.exclude(status__in = [12,13])

    contractor_compartidas = Shared.objects.filter(reduce(OR, user_group_filters)).exclude(contractor = None).distinct('contractor').values_list('contractor',flat = True)
    contractor_compartidas = Polizas.objects.filter(contractor__in = contractor_compartidas).values_list('pk', flat = True).exclude(status__in = [12,13])

    polizas_por_vendedor = ReferenciadoresInvolved.objects.filter(org_name = org, referenciador = request.user,is_changed=False).values_list('policy', flat = True)

    polizas = list(polizas_compartidas_y_por_usuario) + list(polizas_por_vendedor) + list(aseguradoras_compartidas) + list(grupo_de_contratantes_compartidas) + list(contractor_compartidas) + list(polizas_por_celula)

    # Certificados de colectividades compartidas
    polizasCertificados = Polizas.objects.filter(pk__in = polizas, document_type__in= [3, 11, 12])#.exclude(status__in = [12,13])    
#    print('polizasCertificados', polizasCertificados)

    polizasCertificados2 = Polizas.objects.filter(parent__parent__parent__id__in =polizas, document_type= 6).values_list('pk', flat = True)#.exclude(status__in = [12,13])
#    print('polizasCertificados2', polizasCertificados2)
    # Certificados de colectividades compartidas
    polizas = list(polizas) + list(polizasCertificados2)
    if only_fianzas == True:
        fianzas = Polizas.objects.filter(id__in=polizas, document_type__in=[7, 8, 9, 10]).values_list('pk', flat = True)
        return fianzas

    #Solución temporal para mbx2130, lo idoneo es crear un permiso en CAS, donde se especifique si el usuario restringido puede o no ver polizas vencidas o renovadas
    if yo.username == 'gabriela_gomez':
        return polizas

    polizas = list(Polizas.objects.filter(id__in=polizas).exclude(status__in = [12,13]).values_list('id', flat = True))


    return polizas
