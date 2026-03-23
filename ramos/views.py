from aseguradoras.serializers import ProviderRamoSerializer
from rest_framework import permissions, viewsets
from contratantes.permissions import IsOwnerOrReadOnly
from ramos.models import Ramos, SubRamos, FianzaType
from ramos.serializers import *
from core.views import custom_get_queryset, custom_org_create
from organizations.views import get_org
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from control.permissions import IsAuthenticatedV2, IsOrgMemberV2


class RamosViewSet(viewsets.ModelViewSet):
    serializer_class = RamosHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            obj = serializer.save(owner=self.request.user, org=get_org(self.request.POST.get('org')))

    def get_queryset(self):
        return custom_get_queryset(self.request, Ramos)


class SubramosViewSet(viewsets.ModelViewSet):
    serializer_class = SubramoHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            obj = serializer.save(owner=self.request.user, org=get_org(self.request.POST.get('org')))

    def get_queryset(self):
        return custom_get_queryset(self.request, SubRamos)

@api_view(['GET','POST'])
@permission_classes((IsAuthenticatedV2, ))
def subramos_all(request):
    if request.method == 'GET':
        ramos = Ramos.objects.filter(org_name=request.GET.get('org')).order_by('ramo_code').distinct('ramo_code')
        subramos = SubRamos.objects.filter(ramo = ramos, org_name=request.GET.get('org')).order_by('subramo_code').distinct('subramo_code')
        serializer = SubramoHyperResumeSerializer(subramos,context={'request':request},many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        provider=request.data['provider']
        ramos = Ramos.objects.filter(org_name=request.GET.get('org'),provider=provider).order_by('ramo_code').distinct('ramo_code')
        subramos = SubRamos.objects.filter(ramo = ramos, org_name=request.GET.get('org')).order_by('subramo_code').distinct('subramo_code')
        serializer = SubramoHyperResumeSerializer(subramos,context={'request':request},many=True)
        return Response(serializer.data)

class FianzaTypeViewSet(viewsets.ModelViewSet):
    serializer_class = FianzaTypeHyperSerializer
    permission_classes = (IsAuthenticatedV2, IsOrgMemberV2)

    def perform_create(self, serializer):
        try:
            obj = serializer.save(owner=self.request.user, org_name = self.request.GET.get('org'))
        except:
            obj = serializer.save(owner=self.request.user, org=get_org(self.request.POST.get('org')))

    def get_queryset(self):
        return custom_get_queryset(self.request, FianzaType)

@api_view(['GET','POST'])
@permission_classes((IsAuthenticatedV2, ))
def ramos_by_provider(request,provider_id):
    if request.method == 'GET':
        ramos = Ramos.objects.filter(provider = provider_id, org_name=request.GET.get('org'))
        serializer = RamosResumeHyperSerializer(ramos,context={'request':request},many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        ramos = Ramos.objects.filter(provider = provider_id, org_name=request.POST.get('org'))
        serializer = RamosResumeHyperSerializer(ramos,context={'request':request},many=True)
        return Response(serializer.data)

@api_view(['GET','POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def subramos_by_ramo(request,ramo_id):
    if request.method == 'GET':
        subramos = SubRamos.objects.filter(ramo = ramo_id, org_name=request.GET.get('org'))
        serializer = SubramoResumeHyperSerializer(subramos,context={'request':request},many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        subramos = SubRamos.objects.filter(ramo = ramo_id, org_name=request.POST.get('org'))
        serializer = SubramoResumeHyperSerializer(subramos,context={'request':request},many=True)
        return Response(serializer.data)

@api_view(['GET','POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def subramos_by_ramo_code(request,ramo_id):
    if request.method == 'GET':
        subramos = SubRamos.objects.filter(ramo__ramo_code = ramo_id, org_name=request.GET.get('org')).distinct('subramo_code')
        serializer = SubramoResumeHyperSerializer(subramos,context={'request':request},many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        subramos = SubRamos.objects.filter(ramo__ramo_code = ramo_id, org_name=request.POST.get('org')).distinct('subramo_code')
        serializer = SubramoResumeHyperSerializer(subramos,context={'request':request},many=True)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def RamoInfoViewSet(request,id):
    ramos = Ramos.objects.get(id=id)
    serializer = RamosResumeCleanHyperSerializer(ramos,context={'request':request},many=False)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes((IsAuthenticatedV2, ))
def SubramoInfoViewSet(request,id):
    subramos = SubRamos.objects.get(id=id)
    serializer = SubramoResumeHyperSerializer(subramos,context={'request':request},many=False)
    return Response(serializer.data)


from aseguradoras.models import *
@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def create_ramos_provider(request):
    provider_id = int(request.data['provider_id'])
    vida = request.data['vida']
    accidentes = request.data['accidentes']
    autos = request.data['autos']
    danios = request.data['danios']

    try:
        provider = Provider.objects.get(pk = provider_id)
    except Provider.DoesNotExist:
        return Response({'status':'error', 'detail' : 'Provider does not exist'})

    if vida:
        ramo, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Vida' ,
            ramo_code = 1,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Vida' ,
            subramo_code = 1 ,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

    if accidentes:
        ramo, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Accidentes y Enfermedades' ,
            ramo_code = 2,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )
        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Salud' ,
            subramo_code = 4 ,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )
        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Gastos Médicos' ,
            subramo_code = 3 ,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )
        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Accidentes Personales' ,
            subramo_code = 2 ,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

    if autos: 
        ramo_autos, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Daños' ,
            ramo_code = 3,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Automóviles' ,
            subramo_code = 9 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

    if danios: 
        ramo_autos, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Daños' ,
            ramo_code = 3,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Responsabilidad Civil y Riesgos Profesionales' ,
            subramo_code = 5 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Marítimo y Transportes' ,
            subramo_code = 6 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Incendio' ,
            subramo_code = 7 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Agrícola y de Animales' ,
            subramo_code = 8 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Crédito' ,
            subramo_code = 10 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Crédito a la Vivienda' ,
            subramo_code = 11 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Garantía Financiera' ,
            subramo_code = 12 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Diversos' ,
            subramo_code = 13 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Terremoto y Otros Riesgos Catastróficos' ,
            subramo_code = 14 ,
            ramo = ramo_autos ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )


    return Response(True)




@api_view(['POST'])
@permission_classes((IsAuthenticatedV2, IsOrgMemberV2))
def create_ramos_afianzadora(request):
    provider_id = int(request.data['provider_id'])
    fidelidad = request.data['fidelidad']
    judiciales = request.data['judiciales']
    administrativas = request.data['administrativas']
    credito = request.data['credito']
    fideicomiso = request.data['fideicomiso']

    try:
        provider = Provider.objects.get(pk = provider_id)
    except Provider.DoesNotExist:
        return Response({'status':'error', 'detail' : 'Provider does not exist'})

    if fidelidad:
        ramo, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Fidelidad' ,
            ramo_code = 4,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Individual' ,
            subramo_code = 15 ,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Empleados Administrativos' ,
            type_code = 1,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Vendedores Comisionistas' ,
            type_code = 2,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Agentes de Seguros y Fianzas' ,
            type_code = 3,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Colectivas' ,
            subramo_code = 16 ,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Globales (Tarifas base)' ,
            type_code = 4,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Cédula personal administrativo' ,
            type_code = 5,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Cédula vendedores y comisionistas' ,
            type_code = 6,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

    if judiciales:
        ramo, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Judicial' ,
            ramo_code = 5,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )
        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Penales' ,
            subramo_code = 17 ,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Libertades' ,
            type_code = 7,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Reparación del daño' ,
            type_code = 8,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Sanción pecuniaria' ,
            type_code = 9,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'No penales' ,
            subramo_code = 18,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo = FianzaType.objects.create(
            type_name = 'Daños y perjuicios derivados de juicios en materia civil' ,
            type_code = 62,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
                        )
        tipo = FianzaType.objects.create(
            type_name = 'Daños y perjuicios derivados de juicios en materia mercantil' ,
            type_code = 63,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
                        )
        tipo = FianzaType.objects.create(
            type_name = 'Daños y perjuicios derivados de juicios en materia mercantil' ,
            type_code = 64,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
                        )
        tipo = FianzaType.objects.create(
            type_name = 'Daños y perjuicios derivados de juicios en materia laboral' ,
            type_code = 65,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
                        )
        tipo = FianzaType.objects.create(
            type_name = 'Daños y perjuicios derivados de juicios en materia de amparo' ,
            type_code = 66,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
                        )
        tipo = FianzaType.objects.create(
            type_name = 'Suspensión Definitiva' ,
            type_code = 67,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
                        )
        tipo = FianzaType.objects.create(
            type_name = 'Suspensión Provisional' ,
            type_code = 68,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
                        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Pensión Alimenticia' ,
            type_code = 10,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Daños y perjuicios' ,
            type_code = 11,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Amparo a Conductores' ,
            subramo_code = 19 ,
            ramo = ramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

    if administrativas: 
        ramo_admin, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Administrativas' ,
            ramo_code = 6,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Obra' ,
            subramo_code = 20 ,
            ramo = ramo_admin ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo = FianzaType.objects.create(
            type_name = 'Indemnización y/o Penas Convencionales' ,
            type_code = 70,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        tipo = FianzaType.objects.create(
            type_name = 'Cumplimiento y Penas convencionales' ,
            type_code = 59,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Concurso, Licitación' ,
            type_code = 12,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Anticipo' ,
            type_code = 13,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Cumplimiento' ,
            type_code = 14,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Cumplimiento / Buena Calidad' ,
            type_code = 33,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Buena Calidad' ,
            type_code = 15,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Penas convencionales' ,
            type_code = 34,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Pasivos contingentes' ,
            type_code = 35,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Proveeduria' ,
            subramo_code = 21,
            ramo = ramo_admin ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo = FianzaType.objects.create(
            type_name = 'Cumplimiento y Buena Calidad' ,
            type_code = 71,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
        )

        tipo = FianzaType.objects.create(
            type_name = 'Indemnización y/o Penas Convencionales' ,
            type_code = 60,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
        )

        tipo = FianzaType.objects.create(
            type_name = 'Cumplimiento y Penas convencionales' ,
            type_code = 61,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Concurso, Licitación' ,
            type_code = 16,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Anticipo' ,
            type_code = 17,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Cumplimiento' ,
            type_code = 18,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Buena Calidad' ,
            type_code = 19,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Penas convencionales' ,
            type_code = 36,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Pasivos contingentes' ,
            type_code = 37,
            subramo = subramo , 
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Fiscales' ,
            subramo_code = 22,
            ramo = ramo_admin ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo = FianzaType.objects.create(
            type_name = 'Convenios de pagos en parcialidades ante el IMSS' ,
            type_code = 55,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        tipo = FianzaType.objects.create(
            type_name = 'Convenios de pagos en parcialidades ante Infonavit' ,
            type_code = 56,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        tipo = FianzaType.objects.create(
            type_name = 'Otras fiscales (clausura de negocios, devolución de I.V.A, etc)' ,
            type_code = 57,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        tipo = FianzaType.objects.create(
            type_name = 'Otros convenios de pagos en parcialidades' ,
            type_code = 58,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Inconformidad fiscal' ,
            type_code = 20,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Convenio de pagos' ,
            type_code = 21,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Arrendamiento' ,
            subramo_code = 23,
            ramo = ramo_admin ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )


        tipo = FianzaType.objects.create(
            type_name = 'Arrendamiento Inmobiliario' ,
            type_code = 43,
            subramo = subramo ,
            org_name = request.GET.get('org'),
            owner = request.user
        )

        tipo = FianzaType.objects.create(
            type_name = 'Otras Fianzas de Arrendamiento' ,
            type_code = 44,
            subramo = subramo ,
            org_name = request.GET.get('org'),
            owner = request.user
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Inmuebles' ,
            type_code = 22,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Maquinaria y Equipo' ,
            type_code = 23,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Otras' ,
            subramo_code = 24,
            ramo = ramo_admin ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Concesiones' ,
            type_code = 24,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Permisos y Concesiones Varias',
            type_code = 72,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Boletaje IATA' ,
            type_code = 25,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Agentes Aduanales, Corredores Públicos, Notarios Públicos' ,
            type_code = 38,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )
        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Comisión Mercantil' ,
            type_code = 39,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )
        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Sorteos y Rifas' ,
            type_code = 40,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )
        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Uso de Suelo' ,
            type_code = 41,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )
        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Otras Administrativas' ,
            type_code = 42,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') 
        )

    if credito: 
        ramo_credito, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Crédito' ,
            ramo_code = 7,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Suministro' ,
            subramo_code = 25,
            ramo = ramo_credito ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo = FianzaType.objects.create(
            type_name = 'Otros suministros',
            type_code = 69,
            subramo = subramo,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Mex-Lub ASA CFE' ,
            type_code = 26,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Estaciones de Servicio Gasolineras' ,
            type_code = 27,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Lubricantes' ,
            type_code = 28,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Gas' ,
            type_code = 29,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Refinación' ,
            type_code = 30,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Petroquímica' ,
            type_code = 31,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Compra Venta' ,
            subramo_code = 26,
            ramo = ramo_credito ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        tipo, tipo_created = FianzaType.objects.get_or_create(
            type_name = 'Distribución' ,
            type_code = 32,
            subramo = subramo ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Otras' ,
            subramo_code = 27,
            ramo = ramo_credito ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

    if fideicomiso: 
        ramo_fideicomiso, ramo_created = Ramos.objects.get_or_create(
            ramo_name = 'Fideicomiso' ,
            ramo_code = 8,
            provider = provider ,
            owner = request.user,
            org_name = request.GET.get('org')
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Relación con fianza' ,
            subramo_code = 28,
            ramo = ramo_fideicomiso ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )

        subramo, subramo_created = SubRamos.objects.get_or_create(
            subramo_name = 'Sin relación con fianza' ,
            subramo_code = 29,
            ramo = ramo_fideicomiso ,
            owner = request.user,
            org_name = request.GET.get('org') ,
        )
    


        
        
        
    
    return Response(ProviderRamoSerializer(provider, context = {'request':request}, many=False).data)
