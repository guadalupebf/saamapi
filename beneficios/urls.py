 # -*- coding: utf-8 -*-
from django.conf.urls import include, url, patterns
from rest_framework.routers import DefaultRouter, SimpleRouter
from django.contrib import admin
from django.conf import settings
from organizations.views import UsersViewSet, UserInfoViewSet, OrgInfoViewSet
from aseguradoras.views import *
from contratantes.views import *
from coberturas.views import *
from contactos.views import *
from archivos.views import *
from paquetes.views import *
from generics.views import *
from polizas.send_emails import *
from recibos.views import *
from polizas.views import *
from ramos.views import *
from core.views import *
from forms.views import *
from generics.searcher import *
from generics.pdfs import *
from generics.pdf_finiquito import *
from generics.pdf_liquidacion import *
from generics.pdf_conciliacion import *
from generics.pdf_cotizacion import *
from generics.delivery_pdf import *
from endorsements.views import *
from endosos.views import *
from siniestros.views import *
from claves.views import *
from vendedores.views import *
from fianzas.views import *
from campaigns.views import *
from ibis.views import *
from delivery.views import *
from providers import *
from carpeta.views import *
from providers.report_service import *
from organizations.views import saveConfigTableFieldsReports
from polizas.validations import EvaluarVigencyPolicie
router = DefaultRouter()
# router = SimpleRouter() TODO Replace Default to hide Api root
router.register(r'usuarios', UserViewSet)
router.register(r'usuarios-general', UserGeneralViewSet)

router.register(r'usuarios-siis', UserViewSetSIIS, 'users-siis')
router.register(r'campaigns', CampaignsViewSet, 'campaign')
router.register(r'campaigns-table', CampaignsTableViewSet, 'campaign-table')
router.register(r'notificaciones', NotificationsViewSet, 'notifications')
router.register(r'expenses', ExpensesViewSet, 'expenses')
router.register(r'cedula', CedulaViewSet, 'cedula')
router.register(r'goal', GoalViewSet, 'goal')
router.register(r'responsables', ResponsablesViewSet, 'responsablesinvolved')
router.register(r'cotizacion', CotizacionViewSet, 'cotizacion')
router.register(r'primas-cotizacion', AsegCotPrimaView, 'aseguradorascotizacionprimas')
#router.register(r'cotizacion-to-show', CotizacionShowViewSet, 'cotizacion-show')
router.register(r'sucursal', SucursalViewSet, 'sucursales')
router.register(r'sucursales-to-show', SucursalShowViewSet, 'sucursal-show')
router.register(r'sucursales-to-show-unpag', SucursalShowUnpagViewSet, 'sucursal-show-unpag')
router.register(r'bonos', BonosViewSet, 'bonos')
router.register(r'bonos-to-show', BonosShowViewSet, 'bonos-show')
router.register(r'polizas-file', PolizasMainFileViewSet, 'polizasfile')
router.register(r'cotizaciones-file', CotizacionesMainFileViewSet, 'cotizacionesfile')
router.register(r'notification-file', NotificationsMainFileViewSet, 'notificationfile')
#router.register(r'natural-person-file', NaturalPersonMainFileViewSet, 'naturalpersonfile')
#router.register(r'juridical-file', JuridicalMainFileViewSet, 'juridicalfile')
router.register(r'contractor-file', ContractorMainFileViewSet, 'contractorfile')
router.register(r'group-file', GroupMainFileViewSet, 'groupfile')
router.register(r'fianzas-file', FianzasMainFileViewSet, 'fianzafile')
router.register(r'claims-file', ClaimsMainFileViewSet, 'claimsfiles')
router.register(r'siniestros-file', SiniestrosMainFileViewSet, 'siniestrosfile')
router.register(r'endosos-file', EndorsementMainFileViewSet, 'endorsementfile')
router.register(r'recibos-file', RecibosMainFileViewSet, 'recibosfile')
router.register(r'liquidacion-file',LiquidacionMainFileViewSet, 'liquidacionfile')
router.register(r'events-file',EventsMainFileViewSet, 'eventsfile')

router.register(r'facturas-file', FacturasMainFileViewSet, 'facturasfile')
router.register(r'cartas-file', CartasMainFileViewSet, 'cartasfile')
router.register(r'estadocuenta-file', EstadoCuentaMainFileViewSet, 'estadoscuentafile')

router.register(r'user-info', UserInfoViewSet)
router.register(r'vendedor-polizas',PolizasVendedorViewSet, 'polizas-vendedor')
router.register(r'vendedor-fianzas',FianzasVendedorViewSet, 'fianzas-vendedor')

#Esta url apuntaba a una vista del modelo de fianzas y todavia esta en uso en SAAM-FRONTEND
#router.register(r'vendedor-fianzas',FianzasVendedorViewSet, 'fianzas-vendedor')

router.register(r'cartas', CartaViewSet, 'cartas')
router.register(r'schedule', ScheduleViewSet, 'schedule')
router.register(r'perfil-usuario-restringido', PerfilUsuarioRestringidoViewSet, 'perfilusuariorestringido')

#router.register(r'orgs', OrganizationsViewSet, 'organization')
router.register(r'orginfo', OrgInfoViewSet, 'orginfo')
router.register(r'emailinfo', EmailInfoViewSet, 'emailinfo')
router.register(r'emailinforeminder', EmailInfoReminderViewSet, 'emailinforeminder')
# URLs de modelos fusionados en Contractor
router.register(r'contractor', ContractorViewSet, 'contractor')
# Email Template Only text
router.register(r'emailtemplate', EmailTemplateViewSet, 'emailtemplate')
router.register(r'smstemplate', SmsTemplateViewSet, 'smstemplate')
router.register(r'whatsappwebtemplate', whatsappwebtemplateViewSet, 'whatsappwebtemplate')
router.register(r'whatsappwebtemplate-unpag', whatsappwebtemplateUnpagViewSet, 'whatsappwebtemplate-Unpag')
router.register(r'smstemplate-unpag', SmsTemplateUnpagViewSet, 'smstemplate-unpag')
router.register(r'emailtemplate-unpag', EmailTemplateUnpagViewSet, 'emailtemplate-unpag')
router.register(r'configkbi', ConfigKbiViewSet, 'configkbi')
# router.register(r'fisicas-app', NaturalAppViewSet, 'naturalperson')
# router.register(r'morales-app', JuridicalAppViewSet, 'juridical'))
router.register(r'contractors-app', ContractorAppViewSet, 'contractor')

# router.register(r'fisicas-resume', NaturalResumeViewSet, 'naturalpersonresume')
# router.register(r'morales-resume', JuridicalResumeViewSet, 'juridicalresume')
router.register(r'contractor-resume', ContractorResumeViewSet, 'contractorresume')

# router.register(r'fisicas-resume-dash', NaturalDashResumeViewSet, 'naturalpersonresume')
# router.register(r'morales-resume-dash', JuridicalDashResumeViewSet, 'juridicalresume')
router.register(r'contractor-resume-dash', ContractorDashResumeViewSet, 'contractorresume')

router.register(r'afianzadoras', AfianzadorasViewSet, 'afianzadoras')
router.register(r'fianzas', FianzasViewSet, 'fianzas')
router.register(r'contract', ContractViewSet, 'contract')
router.register(r'beneficiaries-contract', BeneficiariesContractViewSet, 'beneficiariescontract')
router.register(r'beneficiaries_contract_policy', BeneficiariesContractPolicyViewSet, 'beneficiariescontract')
#router.register(r'leer-fianzas-info', FianzaInfoViewSet, 'fianza-info')

router.register(r'leer-fianzas-edit', FianzasEditViewSet, 'leerfianzas-edit')
#Esta url apuntaba a una vista del modelo de fianzas
#router.register(r'create-old-fianza', OldFianzaReexpedicion, 'create-oldfianzas')
#Esta url apuntaba a una vista del modelo de fianzas
#router.register(r'old-fianza', OldFianzaReexpedicion, 'oldfianzas')
#Esta url apuntaba a una vista del modelo de fianzas
#router.register(r'historic-fianzas', HistoricoFianzasViewSet, 'historic-fianzas')
router.register(r'claims', ClaimsViewSet, 'claim')
#Esta url apuntaba a una vista del modelo de fianzas
router.register(r'claims-list', ClaimsListViewSet, 'claim-list')

# NEW FIANZAS
router.register(r'fianzas_collective', FianzasCollectViewSet, 'polizas')


router.register(r'phone-vendedor', VendedorPhoneViewSet, 'phone')
router.register(r'referenciadores-involved', ReferenciadoresViewSet, 'referenciadoresinvolved')
router.register(r'subramos-vendedor', SubramosVendedorViewSet, 'subramosvendedor')
router.register(r'vendedores', VendedorInfoViewSet, 'vendedor')
router.register(r'direct-vendedores', VendedorFromSAAMViewSet, 'vendedor-direct')
router.register(r'estado-cuenta', AccountStateViewSet, 'accountstate')
router.register(r'estado-cuenta-table', AccountStateTableViewSet, 'accountstate-table')
router.register(r'conceptos-generales-referenciador',ConceptosGeneralesViewSet, 'conceptosgenerales')

router.register(r'estado-cuenta-referenciador', AccountStateReferenciadorViewSet, 'accountstate-referenciador')



router.register(r'certificados-reporte', ReporteCertificadoViewSet, 'ReporteCertificadoViewSet')



#router.register(r'fisicas-resume-medium', NaturalMediumViewSet, 'naturalpersonmedium')
#router.register(r'morales-resume-medium', JuridicalMediumViewSet, 'juridicalmedium')
router.register(r'contractors-resume-medium', ContractorMediumViewSet, 'contractormedium')

#router.register(r'fisicas-resume-name', NaturalNameViewSet, 'naturalpersonname')
#router.register(r'morales-resume-name', JuridicalNameViewSet, 'juridicalname')
router.register(r'contractor-resume-name', ContractorNameViewSet, 'contractorname')

router.register(r'get-provider-contact', GetContactProvider, 'GetContactProvider')
router.register(r'provider-contact', ContactProvider, 'ContactProvider')
router.register(r'provider-contact-email', ContactEmailProvider, 'ContactEmailProvider')

router.register(r'caratula-pack', CaratulaPackageViewSet, 'CaratulaPackageViewSet')

router.register(r'grupos', GroupViewSet, 'group')
router.register(r'crear-grupo', GroupCompleteViewSet, 'group-create')
router.register(r'groupinglevel', GroupingLevelViewSet, 'groupinglevel')
router.register(r'classification', ClassificationViewSet, 'classification')
router.register(r'celula_contractor', CelulacontractorViewSet, 'celulacontractor')
router.register(r'medicoscelulas', MedicosCelulacontractorViewSet, 'medicoscelulas')
router.register(r'grupos-table-resume', GroupTableResumeViewSet, 'group-resume')
router.register(r'grupos-list-resume', GroupListResumeViewSet, 'group-list')
router.register(r'grupos-full', GroupFullViewSet, 'group-full')

router.register(r'contactos', ContactViewSet, 'contactinfo')

router.register(r'proveedores', ProviderViewSet, 'provider')
router.register(r'proveedores-resume', ProviderReadViewSet, 'provider-resume')
router.register(r'proveedores-table-resume', ProviderTableReadListViewSet, 'proveedores-table-resume')
router.register(r'proveedores-for-endorsement', ProviderForEndorsementViewSet, 'proveedores-for-endorsement')



router.register(r'states-viewset', StatesSuperViewSet, 'StatesSuperViewSet')
router.register(r'cities-viewset', CitiesSuperViewSet, 'CitiesSuperViewSet')
router.register(r'package-custom', CustomPackageViewSet, 'CustomPackageViewSet')
router.register(r'internal-number', InternalNumber, 'InternalNumber')


# -------------- Buscador -------------------------
router.register(r'seeker-provider', seekerProvider, 'seekerProvider')
# router.register(r'seeker-groups', seekerGroups, 'seekerGroups')
router.register(r'seeker-sinisters', seekerSinister, 'seekerSinister')
router.register(r'seeker-policies', seekerPolicy, 'seekerPolicy')
router.register(r'seeker-certs', seekerCerts, 'seekerPolicy')
router.register(r'seeker-policies-subramos', seekerPolicySubramos, 'seekerPolicySubramos')
router.register(r'seeker-fianzas', seekerFianzas, 'seekerFianzas')
router.register(r'seeker-naturals', seekerContractorNaturals, 'seekerContractorNaturals')
router.register(r'seeker-juridicals', seekerContractorJuridicals, 'seekerContractorJuridicals')
router.register(r'seeker-contractors', seekerContractors, 'seekerContractors')
router.register(r'search-receipts', searchReceipts, 'searchReceipts')
router.register(r'search-packages', searchPackages, 'searchPackages')
router.register(r'search-certificates', searchCertificates, 'searchCertificates')
router.register(r'search-polizascaratula', searchPolizasCaratulas, 'searchPolizasCaratulas')
router.register(r'search-ots', searchOTs, 'searchOTs')
router.register(r'search-caratulas', searchCaratulas, 'searchCaratulas')
# filtro by user
router.register(r'filter-djangogroups', seekerDjangoGroups, 'seekerDjangoGroups')
router.register(r'filter-users', seekerUsuarios, 'seekerUsuarios')
# ------------
router.register(r'group-subgroups/', seekerGroupsSubgroups, 'seekerGroupsSubgroups')#Grupos-subgrupos-subsubgrupos
router.register(r'search_certs_collectivfianza', searchCertificatesCollectivefianza, 'searchCertificatesCollectivefianza')
# router.register(r'filtros-polizas', PolicyFilters, 'policyFilters')
router.register(r'filtros-fianza', FianzaFilters, 'fianzaFilters')
router.register(r'filtros-fianza-ot', FianzaOTFilters, 'fianzaFilters')
# router.register(r'filtros-polizas-ot', PolicyOTFilters, 'policyOTFilters')
router.register(r'filtros-renovaciones', FiltrosRenovaciones, 'FiltrosRenovaciones')

router.register(r'receipt-states', GetReceiptsByFolio, 'receipt-states')

router.register(r'graphic', GraphicsViewSet, 'graphic')

router.register(r'signature', SignatureViewSet, 'signature')
router.register(r'birthdate-template', BirthdateTemplateViewSet, 'birthdate-template')
router.register(r'banner', BannerFileViewSet, 'bannerfile')

router.register(r'get-policy-endorsement', PolizaEndosoInfoViewSet, 'PolizaEndosoInfoViewSet')
router.register(r'get-fianza-endorsement', FianzaEndosoInfoViewSet, 'FianzaEndosoInfoViewSet')

router.register(r'ramos', RamosViewSet, 'ramos')
router.register(r'subramos', SubramosViewSet, 'subramos')
router.register(r'fianza-type', FianzaTypeViewSet, 'fianzatype')

router.register(r'paquetes', PackageViewSet, 'package')
router.register(r'coberturas-configuraciones', CoverageGrupoViewSet, 'CoverageGrupoViewSet')
router.register(r'paquetes-resume', PackageResumeViewSet, 'package-resume')
router.register(r'v1/paquetes/information', PackageInfoViewSet, 'packageinfo')
router.register(r'coberturas', CoverageViewSet, 'coverage')
router.register(r'coberturas-polizas', CoverageInPolicyViewSet, 'coverageinpolicy')
router.register(r'sumas-aseguradas', SumInsuredViewSet, 'suminsured')
router.register(r'deducibles', DeductibleViewSet, 'deductible')
router.register(r'coinsurance', CoinsuranceViewSet, 'coinsurance')
router.register(r'topecoinsurance', TopeCoinsuranceViewSet, 'topecoinsurance')
router.register(r'claves', ClavesViewSet, 'claves')
router.register(r'comisiones', ComisionesViewSet, 'comisiones')
router.register(r'areas', AreasViewset, 'areas')
router.register(r'areas-responsability', AreasResViewset, 'areasresponsability')


router.register(r'polizas', PolizasViewSet, 'polizas')
router.register(r'bigbot/recibos', BigBotRecibosViewSet, 'bigbot-polizas')
#router.register(r'certificados-caratula', CertificadosCaratulaViewSet, 'certificados-caratula')
router.register(r'renovation', RenovationViewSet, 'renovation')
router.register(r'historic-policies', HistoricoPolicyViewSet, 'historic-policies')
router.register(r'get-renovation', GetRenovation, 'get-renovation')
router.register(r'renew-polizas', RenewPolizasViewSet, 'renew-polizas')
# ------------------------------ Colectividades ---------------------------------------------
router.register(r'massive-certificates', CreateMassiveCertificates, 'CreateMassiveCertificates')
router.register(r'get-caratula', GetCaratulaViewSet, 'GetCaratulaViewSet')
router.register(r'caratulas', SetCaratulaViewSet, 'SetCaratulaViewSet')
# ----------------Carátula pólizas Ancora-Otros---------------------------
router.register(r'colectividades_polizas', SetColectividadesPolizasViewSet, 'SetColectividadesPolizasViewSet')
# ------------------------------------------------------------------------
# router.register(r'caratula-complete', saveCaratulaComplete,'saveCaratulaComplete'), 


router.register(r'subgrupos', SubGroupViewSet, 'SubGroupViewSet')

router.register(r'categories', CategoryViewSet, 'CategoryViewSet')
# ---------------------------------------------------------------------------/Colectividades

router.register(r'v1/polizas/viejas', OldPolicyViewSet, 'oldpolicies')
router.register(r'recibos', ReciboViewSet, 'recibos')
router.register(r'pagos', PagosViewSet, 'pagos')

router.register(r'shared', SharedApiViewSet, 'SharedApiViewSet')
router.register(r'djangogroups', DjangoGroupsViewSet, 'DjangoGroups')
# router.register(r'djangousersgroups', DjangoUserGroupsViewSet, 'DjangoUserGroups')

router.register(r'recibos-track', ReciboTrackViewSet, 'recibos-track')
router.register(r'bancos-viewset', BancosViewSet, 'bancos')
router.register(r'folios-pago', FoliosPagoViewSet, 'foliospago')
router.register(r'leer-folios-pago', FoliosPagoConsulta, 'foliospago')
router.register(r'leer-polizas-resume', PolizasReadResumeViewSet, 'leerpolizas-resume')
router.register(r'leer-ots-resume', OTReadResumeViewSet, 'leerpolizas-resume')
router.register(r'leer-rpolizas-resume', PolizasRenovationResumeViewSet, 'leerRpolizas-resume')
router.register(r'leer-polizas-info', PolizasInfoViewSet, 'leerpolizas-info')
router.register(r'leer-polizas-edit', PolizasEditViewSet, 'leerpolizas-edit')
router.register(r'leer-polizas-ibis', PolizasIbisViewSet, 'leerpolizas-ibis')
router.register(r'leer-polizas', PolizasReadViewSet, 'leerpolizas')
router.register(r'poliza-resume-renew', PolizaResumeRenewViewSet, 'polizas-resume-renew')

router.register(r'leer-cotizacion-info', CotizacionIdViewSet, 'CotizacionIdViewSet')

router.register(r'poliza-app', PolizasAppViewSet, 'poliza-app')

router.register(r'count-receipts', ReciboCountViewSet, 'receipts')

router.register(r'leer-recibos', ReciboReadViewSet, 'leerrecibos')
router.register(r'recibo/info', ReciboInfoViewSet, 'reciboinfo')
router.register(r'v1/address', AddressViewSet, 'address')

# router.register(r'get-cobranza', GetCobranzaViewSet, 'get-cobranza')


router.register(r'emails', EmailsViewSet, 'emails')
router.register(r'phones', PhonesViewSet, 'phones')

# ------------ Menu contratante -----------------
# router.register(r'get-cobranza-natural', GetCobranzaNaturalViewSet, 'get-cobranza-natural')
# router.register(r'get-cobranza-juridical', GetCobranzaJuridicalViewSet, 'get-cobranza-juridical')
router.register(r'get-cobranza-contractor', GetCobranzaContractorViewSet, 'get-cobranza-contractor')
# router.register(r'get-siniestros-natural', GetSinisterNaturalViewSet, 'get-sinister-natural')
# router.register(r'get-siniestros-juridical', GetSinisterJuridicalViewSet, 'get-sinister-juridical')
router.register(r'get-siniestros-contractor', GetSinisterContractorViewSet, 'get-sinister-contractor')
# router.register(r'get-polizas-natural', GetPoliciesNaturalViewSet, 'get-policies-natural')
# router.register(r'get-polizas-juridical', GetPoliciesJuridicalViewSet, 'get-spolicie-juridical')
router.register(r'get-polizas-contractor', GetPoliciesContractorViewSet, 'get-spolicie-contractor')

router.register(r'filesestadocuenta', EstadoCuentaFileSuperViewSet, 'estadoscuentafile')
router.register(r'filescampaign', CampaignFileSuperViewSet, 'campaignfile')
router.register(r'fileshtmlcampaign', CampaignFileSuperHtmlViewSet, 'campaignhtmlfile')
router.register(r'fileshtmlbirthdate', BirthdateFileSuperHtmlViewSet, 'birthdatehtmlfile')
router.register(r'plantillashtmlfile', PlantillasFileSuperHtmlViewSet, 'plantillashtmlfile')
router.register(r'emailsatm-htmlfile', EmailsHtmlFileSuperViewSet, 'emailshtmlfile')

router.register(r'ticket-file', TicketFileViewSet, 'ticketfile')



router.register(r'lectura-archivos', LecturaArchivosViewSet  , 'lecturaarchivos')
router.register(r'lectura-general-archivos', LecturaArchivosGeneralViewSet  , 'lecturaarchivosgeneral')
router.register(r'lectura-archivos-edit', LecturaArchivosEditViewSet  , 'lecturaarchivos')
router.register(r'tag-lectura-archivos', TagsLecturaArchivosViewSet  , 'tagslecturaarchivos')
# ----------------- Archives -------------------------
#router.register(r'fisicas/(?P<id>\d+)/archivos', NaturalPersonFileViewSet, 'fisicas-archivos')
#router.register(r'morales/(?P<id>\d+)/archivos', JuridicalFileViewSet, 'morales-archivos')
router.register(r'contractors/(?P<id>\d+)/archivos', ContractorFileViewSet, 'contractors-archivos')
router.register(r'grupos/(?P<id>\d+)/archivos', GroupFileViewSet, 'grupos-archivos')
router.register(r'ticket/(?P<id>\d+)/archivos', TicketFileViewSet, 'ticket-archivos')
router.register(r'polizas/(?P<id>\d+)/archivos', PolizasFileViewSet, 'polizas-archivos')
router.register(r'cotizaciones/(?P<id>\d+)/archivos', CotizacionesFileViewSet, 'cotizaciones-archivos')
router.register(r'claims/(?P<id>\d+)/archivos', ClaimsFileViewSet, 'claims-archivos')
router.register(r'endosos/(?P<id>\d+)/archivos', EndorsementFileViewSet, 'endosos-archivos')
router.register(r'recibos/(?P<id>\d+)/archivos', RecibosFileViewSet, 'recibos-archivos')
router.register(r'siniestros/(?P<id>\d+)/archivos', SiniestrosFileViewSet, 'siniestros-archivos')
router.register(r'facturas/(?P<id>\d+)/archivos', FacturasFileViewSet, 'facturas-archivos')
router.register(r'cartas/(?P<id>\d+)/archivos', CartasFileViewSet, 'cartas-archivos')
router.register(r'estado-cuenta/(?P<id>\d+)/archivos', EstadoCuentaFileViewSet, 'estadocuenta-archivos')
router.register(r'fianzas/(?P<id>\d+)/archivos', FianzaFileViewSet, 'fianzas-archivos')
router.register(r'fianzas-cancel/(?P<id>\d+)/archivos', FianzaCancelFileViewSet, 'fianzas-cancel-archivos')
router.register(r'liquidacion/(?P<id>\d+)/archivos', LiquidacionFileViewSet, 'liquidacion-archivos')
router.register(r'campaigns/(?P<id>\d+)/archivos', CampaignFileViewSet, 'campaigns-archivos')
router.register(r'archivos/editables', EditablesFileViewSet, 'editablesfile')
router.register(r'archivos/editablesapp', EditablesFileAppViewSet, 'editablesfile-app')
router.register(r'campaigns-html', CampaignHtmlFileViewSet, 'campaignshtml-archivos')
router.register(r'birthdates-html', BirthdateHtmlFileViewSet, 'birthdateshtml-archivos')
router.register(r'cobranzamodal-html', CobranzaModalHtmlFileViewSet, 'cobranzamodalhtml-archivos')
router.register(r'plantillas-html', PlantillasHtmlFileViewSet, 'plantillashtml-archivos')
router.register(r'emailsatm-html', EmailsHtmlFileViewSet, 'emailsatmhtml-archivos')
# notificaciones app
router.register(r'notifications/(?P<id>\d+)/archivos', NotificationsFileViewSet, 'notifications-archivos')
router.register(r'events/(?P<id>\d+)/archivos', EventsFileViewSet, 'events-archivos')
# carpeta adjuntos
router.register(r'carpeta/(?P<id>\d+)/archivos', AdjuntosInternosViewSet, 'adjuntosinternos')
# https://miurabox.atlassian.net/browse/DES-875
# router.register(r'condiciones-generales', CondicionGeneralViewSet, 'condiciones-generales')
router.register(r'condiciones-generales', CondicionGeneralViewSet, 'condiciongeneral')
router.register(r'polizas/(?P<id>\d+)/condiciones-generales', PolizaCondicionGeneralViewSet, 'polizas-condiciones-generales')
# https://miurabox.atlassian.net/browse/DES-875
# urls.py
url(r'^polizas/(?P<id>\d+)/adjuntos/$', PolizaAdjuntosView.as_view(), name='poliza-adjuntos'),

# ------------- Core ------------------
router.register(r'states', StatesSuperViewSet, 'states')
router.register(r'cities', CitiesSuperViewSet, 'cities')
router.register(r'internal-number', InternalNumber, 'InternalNumber')

router.register(r'v1/personal-informations', PersonalInformationViewSet, 'personal_information')
router.register(r'v1/beneficiaries', BeneficiariesViewSet, 'beneficiaries')
router.register(r'v1/relationships', RelationshipViewSet, 'relationship')

router.register(r'v1/forms/lifes', LifeViewSet, 'life')
router.register(r'v1/forms/lifes/(?P<id>\d+)/informations', LifeInfoViewSet, 'lifeinfo')
router.register(r'v1/forms/disease', AccidentsViewSet, 'accidentsdiseases')
router.register(r'v1/forms/disease/(?P<id>\d+)/informations', AccidentInfoViewSet, 'accidentsinfo')
router.register(r'v1/forms/damages', DamagesViewSet, 'damages')
router.register(r'v1/forms/damages/(?P<id>\d+)/informations', DamageInfoViewSet, 'damagesinfo')
router.register(r'v1/forms/automobile-damages', AutomobilesViewSet, 'automobilesdamages')
router.register(r'automobile-damages-update', AutomobilesUpdateViewSet, 'automobilesdamages-update')
router.register(r'v1/forms/automobile-damages/(?P<id>\d+)/informations', AutomobileInfoViewSet, 'automobilesdamagesinfo')

router.register(r'get-endorsements-certificates', CertificatesForEndorsementsViewSet, 'CertificatesForEndorsementsViewSet')

# ------------ Siniestros --------------------

#RUTAS - DAVID
router.register(r'SiniestroLista',SiniestroLista, 'SiniestrosLista') #Nuevo
router.register(r'FacturaLista', FacturasLista, 'FacturaLista') #Nuevo
router.register(r'PadecimientoLista', PadecimientosLista, 'PadecimientoLista') #Nuevo
router.register(r'AccidentesLista', AccidenteLista, 'AccidentesLista') #Nuevo

router.register(r'siniestros-accidentes-create',SiniestrosAccidentesCreate, 'SiniestrosAccidentesCreate') #Nuevo
router.register(r'accidentes-create', AccidentesCreate, 'AccidentesCreate')
router.register(r'facturas-create', FacturasCreate, 'FacturasCreate')

#BUSCAR AFECTADOS POR NUM DE POLIZA
router.register(r'buscar_afectado', BuscarAfectadoPorNumPoliza, 'BuscarAfectadoPorNumPoliza')
#BUSCAR SINIESTROS PARA LOS COMPLEMENTOS
router.register(r'SelectForComplementos', SelectForComplementos, 'SelectForComplementos')
#FIN - RUTAS - DAVID

router.register(r'contactauto', ContactAutoSiniesterViewSet, 'contactauto')
router.register(r'contactdanios', ContactDaniosSiniesterViewSet, 'contactodanios')
router.register(r'siniestros', SiniestrosViewSet, 'siniestros')
router.register(r'facturas', FacturasViewSet, 'facturas')
router.register(r'accidentes', AccidentesViewSet, 'accidentes')
router.register(r'padecimientos-viewset', PadecimientosViewSet, 'padecimientos')
router.register(r'hospital-viewset', HospitalsViewSet, 'hospitales')

router.register(r'siniestros-vida', SiniestrosVidaViewSet, 'SiniestrosVidaViewSet')
router.register(r'siniestros-autos', SiniestrosAutosViewSet, 'SiniestrosAutosViewSet')
router.register(r'portal-siniestros', PortalSiniestrosLista, 'PortalSiniestrosLista')
router.register(r'siniestros-danios', SiniestrosDaniosViewSet, 'SiniestrosDaniosViewSet')
router.register(r'danios-siniesters', SiniestrosSubDaniosViewSet, 'danios')
router.register(r'autos-siniesters', SiniestrosSubAutosViewSet, 'autos')
router.register(r'vida-siniesters', SiniestrosSubVidaViewSet, 'vida')
router.register(r'siniestros-vida-info', SiniestrosInfoVidaViewSet, 'SiniestrosVidaViewSet')

router.register(r'get-siniestro-inicial', Get_siniestro_inicial, 'get-siniestro-inicial')
router.register(r'get-siniestro-complementos', Get_siniestro_complementos, 'get-siniestro-complementos')

router.register(r'certificados', CertificadoViewSet, 'CertificadoViewSet')
router.register(r'get-certificates', GetCertificadosViewset, 'GetCertificadosViewset')
router.register(r'get-allcertificates', GetAllCertificadosViewset, 'GetAllCertificadosViewset')
router.register(r'get-certificates-flotilla', GetCertificadosFlotillaViewset, 'GetCertificadosFlotillaViewset')
router.register(r'polizas-custom', PolizasCustomViewSet, 'PolizasCustomViewSet')
router.register(r'polizas-colectivas', PolizasColectivasViewSet, 'PolizasColectivasViewSet')

# router.register(r'get-comissions', Commissions, 'get-comissions')

router.register(r'get-comissions-conciliate', CommissionsConciliateViewSet, 'get-comissions')

router.register(r'comments', CommentViewSet, 'comments')
router.register(r'commentsById', CommentByIdViewSet, 'comments-by-id')
router.register(r'accounts', AccountsViewSet, 'accounts')

#router.register(r'fisicas-resume-by-group', NaturalByGroupResumeViewSet, 'fisicas-resume-by-group')
#router.register(r'morales-resume-by-group', JuridicalByGroupResumeViewSet, 'morales-resume-by-group')
router.register(r'contractor-resume-by-group', ContractorByGroupResumeViewSet, 'contractor-resume-by-group')

router.register(r'banks-match', BanksMatch, 'banks-match'), 

# ---------- Claves ------------
router.register(r'claves', ClavesViewSet, 'claves')
router.register(r'claves-resume', ClavesReadViewSet, 'claves-resume')

# -------------------- Mensajeria ---------------------------
router.register(r'tasks', TaskViewSet, 'tasks')
router.register(r'get-tasks', GetTasks, 'get-tasks')

router.register(r'ticket', TicketViewSet, 'ticket')
router.register(r'save-ticket', TicketSaveViewSet, 'ticket-save')
router.register(r'save-ticket-mc', TicketSaveViewSetMc, 'ticket-save')
router.register(r'get-ticket', GetTickets, 'get-ticket')


# -------------------- Endosos Nuevo ---------------------------
router.register(r'endorsement', EndososViewSet, 'endorsement')
router.register(r'endorsement-list', EndososListViewSet, 'endorsement-list')
router.register(r'endorsement-single', EndosoSingleViewSet, 'endorsement-single')
router.register(r'endorsement-info', EndososInfoViewSet, 'endorsement-info')
router.register(r'notas-endorsement', NotasEndosoViewSet, 'notas-endoso')
router.register(r'search-endorsments', searchEndorsment, 'searchEndorsment')
router.register(r'endorsement-certs', EndorsementCertsViewSet, 'endorsementcerts')
# router.register(r'endorsement-beneficiarie-relationship', EndorsementBRViewSet, 'endorsementbenrel')

# Siniestros
router.register(r'policies-by-ramo', policy_by_ramo_id, 'policy_by_ramo_id')
router.register(r'policies-siniester', policies_siniester, 'policies_siniester')

router.register(r'match-Beneficiaries-Contract', matchBeneficiariesContract, 'match-Beneficiaries-Contract')
#Esta url apuntaba a una vista del modelo de fianzas
#router.register(r'relacion-beneficiario-fianza', relacion_beneficiario_fianza, 'relacion-beneficiario-fianza')
router.register(r'BeneficiariesExistentes', BeneficiariesExistentes, 'BeneficiariesExistentes')

#Rutas para programa de proveedores
router.register(r'GetFianzasUsuario', GetFianzasUsuario, 'GetFianzasUsuario')
#Esta url apuntaba a una vista del modelo de fianzas
#router.register(r'PortalFianzaInfoViewSet', PortalFianzaInfoViewSet, 'PortalFianzaInfoViewSet')
router.register(r'ReporteFianzaPortal', ReporteFianzaPortal, 'ReporteFianzaPortal')
#Esta url apuntaba a una vista del modelo de fianzas
#router.register(r'GerReclamacionesUsuario', GerReclamacionesUsuario, 'GerReclamacionesUsuario')
#Esta url apuntaba a una vista del modelo de fianzas
#router.register(r'PortalReclamacionesInfo', PortalReclamacionesInfo, 'PortalReclamacionesInfo')

#Rutas para el portal
router.register(r'match-Beneficiaries-Contract', matchBeneficiariesContract, 'match-Beneficiaries-Contract')
#Esta url apuntaba a una vista del modelo de fianzas
#router.register(r'relacion-beneficiario-fianza', relacion_beneficiario_fianza, 'relacion-beneficiario-fianza')
router.register(r'GetFianzasUsuario', GetFianzasUsuario, 'GetFianzasUsuario')
#router.register(r'PortalFianzaInfoViewSet', PortalFianzaInfoViewSet, 'PortalFianzaInfoViewSet')
router.register(r'ReporteFianzaPortal', ReporteFianzaPortal, 'ReporteFianzaPortal')
#router.register(r'GerReclamacionesUsuario', GerReclamacionesUsuario, 'GerReclamacionesUsuario')
#router.register(r'PortalReclamacionesInfo', PortalReclamacionesInfo, 'PortalReclamacionesInfo')

router.register(r'referenciadores-policy', ReferenciadoresViewSet, 'referenciadoresinvolved')

# ------------- IBIS ------------------
router.register(r'polizas/(?P<id>\d+)/archivos-siis', PolizasFileViewSetSIIS, 'polizas-archivos-siis')
router.register(r'siniestros/(?P<id>\d+)/archivos-siis', SiniestrosFileViewSet, 'siniestros-archivos-siis')
router.register(r'red-medica', ProveedoresIbisViewSet, 'red-medica')
router.register(r'directorio', DirectorioViewSet, 'directorio')
router.register(r'formatos', FormatosViewSet, 'formatos')
router.register(r'save-cotizacion-portal', CotizacionPortalViewSetSave, 'CotizacionPortalViewSetSave')
router.register(r'general-cotizacion-portal', ContactoCotizacionPortalViewSet, 'ContactoCotizacionPortalViewSet')

router.register(r'cotizacionportal', CotizacionPortalViewSet, 'cotizacionportal')
#chat bot SAAM
router.register(r'findPoliciesByNumber', findPolicies, 'findPolicies')
router.register(r'findEndosoByPolicie', findEndosoByP, 'findEndosoByP')
router.register(r'findContractors', findContractors, 'findContractors')
#router.register(r'findCobranzaByFolio', findCobranzaByFolio, 'findCobranzaByFolio')

router.register(r'repositorio-de-pago', RepositorioPagoViewSet, 'repositoriopago')
router.register(r'config-provider-scrapper', ConfigProviderScrapperViewSet, 'configproviderscrapper')
router.register(r'promotoria-tablero', PromotoriaTableroViewSet, 'promotoriatablero')
# adjuntos internos carpetas
router.register(r'carpeta', CarpetasViewSet, 'carpeta')
router.register(r'adjuntointerno-libre', AdjuntosInternosLibreViewSet, 'adjuntointerno-file')
router.register(r'adjuntointerno-carpeta', AdjuntosInternosViewSet, 'adjuntointerno-file')
router.register(r'adjuntointernos', AdjuntosInternosViewSet, 'adjuntosinternos')

from core.views import ObtainAuthToken

urlpatterns = [
	url(r'^recordatorios/', include('recordatorios.urls')), 
	url(r'^v2/polizas/', include('polizas.urls')), 
	url(r'^v2/recibos/', include('recibos.urls')), 
	url(r'^v2/siniestros/', include('siniestros.urls')), 
	url(r'^v2/core/', include('core.urls')), 
	url(r'^v2/endosos/', include('endosos.urls')),
    url(r'^v2/fianzas/', include('fianzas.urls')),
    url(r'^v2/contratantes/', include('contratantes.urls')),
    url(r'^v2/aseguradoras/', include('aseguradoras.urls')),
    url(r'^v2/claves/', include('claves.urls')),
    url(r'^', include(router.urls)),    
    url(r'^v2/notifications-module/', include('notifications.urls')),
    url(r'^export/csv/$', export_users_xls, name='export_users_csv'),
    url(r'^comments-export/$', export_comments_excel, name='comments-export-excel'),
    url(r'^change-vendor/$', ChangeVendorFianzas, name='change_vendor'),
    url(r'^log/$', LogViewSet, name = 'log-vieset'),     
    url(r'^log-email/(?P<log_id>[-\w]+)/(?P<type>[-\w]+)/$', LogEmailViewSet, name = 'log-email-viewset'),     
    url(r'^send-log', send_log_public, name = 'send_log_public'),
    url(r'^send_log_specific', send_log_public_specific, name = 'send_log_public_specific'),
    url(r'^delete-contractor', delete_contractor, name = 'delete-contractor'),  
    url(r'^existrfc', exist_rfc, name = 'existrfc'),
    url(r'^exist-fianza-number', exist_fianza_number, name = 'existfianzanumber'),
    url(r'^exist-number-endorsement', exist_number_endorsement, name = 'exist_number_endorsement'),
    url(r'^create-ramos-provider', create_ramos_provider, name = 'create-ramos-provider'), 
    url(r'^create-ramos-afianzadora', create_ramos_afianzadora, name = 'create-ramos-afianzadora'), 
    url(r'^get-emails', get_clients_emails, name = 'get-emails'), 
    url(r'^get-usersemail-operatives', usersemail_operatives, name='usersemail_operatives'),
    url(r'^send-campaign', send_campaign, name = 'send-campaign'), 
    url(r'^policy-endorsements', searchEndorsmentReceipt, name = 'searchEndorsmentReceipt'),
    url(r'^fianza-endorsements', searchEndorsmentReceiptFianza, name = 'searchEndorsmentReceiptFianza'),
    url(r'^groups-match', groups_match, name = 'groups-match'), 
    url(r'^get-permisos', get_permisos, name = 'get-permisos'), 
    
    url(r'^aseguradoras-lectura-documentos', aseguradoras_lectura_documentos, name = 'aseguradoras_lectura_documentos'), 
    url(r'^lectura-documentos', lectura_documentos, name = 'lectura_documentos'), 
    url(r'^cotizaciones-graphql', cotizaciones_graphql, name = 'cotizaciones_graphql'), 
    
    url(r'^enviar-correo-contacto', send_email_contact, name = 'enviar-correo-contaco'), 
    url(r'^verificar-captcha', verificar_captcha, name = 'verificar-captcha'),
    url(r'^get-certificate/$', getCertificate, name = 'getCertificate'), 
    url(r'^get-polizacaratula_files/$', getPolizaCaratula, name = 'getPolizaCaratula'), 
    url(r'^get-receiptstoup-files/$', getReceiptsToUpFiles, name = 'getReceiptsToUpFiles'), 
    url(r'^get-certificate-by-id/$', getCertificateById, name = 'getCertificateById'), 
    url(r'^validate-polizas-to-cancel/$', validatePolizasToCancel, name = 'validatePolizasToCancel'), 
    url(r'^cancelar-polizas-por-layout/$', cancelarPolizasPorLaoyout, name = 'cancelarPolizasPorLaoyout'), 
    url(r'^get-receipts-by-id/$', getReceiptById, name = 'getReceiptById'),
    url(r'^get-contractors-by-id/$', getContractortById, name = 'getContractortById'),

    url(r'^reporte-certificados-excel$', ReporteCertificadosExcel, name = 'ReporteCertificadosExcel'),
    url(r'^claims-list-report/$', ReporteReclamacionesExcel, name = 'ReporteReclamacionesExcel'),
    url(r'^cobranza-liquidacion-masiva$', CobranzaLiquidacionMasiva, name = 'CobranzaLiquidacionMasiva'),
    url(r'^check-cobranza-liquidacion-masiva$', CheckCobranzaLiquidacionMasiva, name = 'CheckCobranzaLiquidacionMasiva'),
    url(r'^cobranza-id-liquidacion-masiva$', CobranzaLiquidacionMasivaId, name = 'CobranzaLiquidacionMasiva'),
    url(r'^check-cobranza-id-liquidacion-masiva$', CheckCobranzaLiquidacionMasivaId, name = 'CheckCobranzaLiquidacionMasiva'),
    url(r'^cobranza-id-pago-masivo$', CobranzaPagoMasivoId, name = 'CobranzaLiquidacionMasiva'),
    url(r'^check-cobranza-id-pago-masivo$', CheckCobranzaPagoMasivoId, name = 'CheckCobranzaLiquidacionMasiva'),
    url(r'^cobranza-pago-masiva$', CobranzaPagoMasiva, name = 'CobranzaPagoMasiva'),
    url(r'^validate-certificates-massive$', validarcertificados, name = 'validarcertificados'),
    url(r'^validate-pgrupoinfo-massive$', validarinfopolizasgrupo, name = 'validarinfopolizasgrupo'),

    url(r'^check-cobranza-id-conciliacion-masivo$', checkConciliacionMassiveId, name = 'checkConciliacionMassiveId'),
    url(r'^cobranza-conciliacion-masiva-id$', ConciliacionMassiveId, name = 'ConciliacionMassiveId'),
    
    url(r'^get-user-permisos', get_user_permisos, name = 'get-user-permisos'), 
    url(r'^get_user_by_username', get_user_by_username, name = 'get_user_by_username'), 
    url(r'^get-user-areas', get_user_areas, name = 'get-user-areas'), 
    url(r'^responsability-areas', get_areas_responsability, name = 'get_areas_responsability'), 
    url(r'^no_assigned_get_user_areas', no_assigned_get_user_areas, name = 'no_assigned_get_user_areas'), 
    url(r'^get-endosos-sinister', getEndorsementAndSinisters, name = 'get-endosos-sinister'), 

    url(r'^get-endosos-by-policy', getEndorsementByPolicy, name = 'get-endosos-by-policy'), 
    url(r'^get-sinister-by-policy', getSiniestersByPolicy, name = 'get-sinister-by-policy'), 
    
    url(r'^get-endosos-colect', getEndorsementColectForAdjust, name = 'get-endosos-colect'), 
    url(r'^view-endosos', getEndorsementView, name = 'get-endosos-sinister'), 
    url(r'^view-sinister', getSinistersView, name = 'get-endosos-sinister'), 
    url(r'^get-endosos-policies', getEndososPolicies, name = 'get-endosos-policies'), 
    url(r'^delete-manual', deleteFileManual, name = 'delete-manual' ),
    url(r'^delete-file-carpeta', deleteFileCarpetaManual, name = 'delete-file-carpeta' ),
    
    url(r'^cancel-fianza/', CancelFianza, name = "cancel-fianza"),
    url(r'^anular-fianza/', AnularFianza, name = "anular-fianza"),
    url(r'^get-polizas-count', get_polizas_count, name = "polizas_count"),
    url(r'^verify-package', verify_package, name = 'verify-package'),     
    url(r'^patch-package-coverage', patchPackagePolicy, name='patchPackagePolicy'),
    url(r'^cartas-by-model', cartas_by_model, name = 'cartas-by-model'), 
    url(r'^reset-receipts-accountstate', reset_receipts, name = 'reset-receipts-accountstate'), 
    url(r'^get-specific-log', get_specific_log, name = 'get-specific-log'), 
    url(r'^complete-task', CompleteTask, name = 'complete-task'), 
    # url(r'^endorsement-beneficiarie-relationship', EndorsementBRViewSet, name = 'endorsement-ben-rel'), 
    url(r'^getTasksExcel/$', GetTasksExcel, name = 'GetTasksExcel'),

    url(r'^provider-name/(?P<provider_id>[-\w]+)$', ProviderCasName, name = 'provider-name'), 
    url(r'^get-pagos/(?P<recibo_id>[-\w]+)$', GetPagos, name = 'get-pagos'), 
    url(r'^get-pagos-subsecuentes/(?P<recibo_id>[-\w]+)$', get_pago_subsecuente, name = 'get-pagos-subsecuentes'), 

    url(r'^notifications-count$', NotificationsCount, name = 'notifications-count'), 
    url(r'^notifications-test$', NotificationsTest, name = 'notifications-test'), 
    url(r'^notifications-app$', NotificationsApp, name = 'notifications-app'),
    
    url(r'^leer-fianzas-info/(?P<pk>[-\w]+)$', fianza_info, name = 'fianza_info'),
    url(r'^grupos-table-resume/$', grouptableresume, name = 'grouptableresume'),#GroupTableResumeViewSet

    url(r'^send-push-message$', SendChatMessage, name = 'send_push_message'), 

    url(r'^save-reminder$', saveReminder, name = 'save-reminder'), 


    url(r'^save-cotizacion$', saveCotizacion, name = 'save-cotizacion'), 
    url(r'^send-historic-email$', sendHistoricEmail, name = 'send-historic-email'), 
    url(r'^emailsUsers$', getEmailsUsers, name = 'get-emailsUsers'), 
    
    url(r'^seeker-groups/$', seekerGroups, name = 'seekerGroups'), 
    
    # (?# router.register(r'seeker-groups', seekerGroups, 'seekerGroups'))
    
    #portal de proveedores

	url(r'^Portal-reporte-afianzadora/$', Portal_reporte_afianzadora, name = 'Portal-reporte-afianzadora'),
	url(r'^Portal-reporte-excel/$', Portal_Reporte_Excel, name = 'Portal-reporte-excel'),
    # carga masiva de pdf a certificados
    url(r'^polizas-grupo/(?P<policy_id>\d+)/massive-pdfs/$', MassivePDFUploadView.as_view()),
    # url(r'^polizas-grupo/massive-pdfs/export/(?P<batch_id>\d+)/$', export_massive_pdfs_excel),
    # urls.py
    url(r'^polizas-grupo/massive-pdfs/export/(?P<batch_id>\d+)/$', export_massive_pdfs_excel),

    url(r'^polizas-grupo/(?P<policy_id>\d+)/massive-pdfs/batches/$', MassivePDFBatchListView.as_view()),
    url(r'^polizas-grupo/massive-pdfs/batches/(?P<batch_id>\d+)/$', MassivePDFBatchDetailView.as_view()),
    # -carga PDFs masiva


    # ------------ Permisos -------------------
    url(r'^change-perm', change_permisos, name = 'change-permisos'), 
    url(r'^change-massive-perm', change_massive_permisos, name = 'change-massive-permisos'), 
    # Carátuña new
    url(r'caratula-complete', saveCaratulaComplete,name='saveCaratulaComplete'), 
    url(r'get_caratula_complete/$', getCaratulaComplete,name='getCaratulaComplete'), 
    url(r'get_caratula_colectiva/$', getCaratulaColectiva,name='getCaratulaColectiva'), 
    url(r'get_caratula_colectiva_childs/$', getCaratulaColectivaChilds,name='getCaratulaColectivaChilds'), 
    url(r'^mass-certificates/', CreateMassiveCertificatesComplete, name = 'CreateMassiveCertificatesComplete'),
    url(r'^certificates-evaluate/', EvaluateMassiveCertificatesComplete, name = 'EvaluateMassiveCertificatesComplete'),
    url(r'^receipts-certificate/', createReceiptsCertificates, name = 'createReceiptsCertificates'),
    url(r'^info_certificados_Collective/', certificadosCollectivityInfoViewSet, name = 'certificadosCollectivityInfoViewSet'),
    url(r'^update_receiptscollective/', updateReceiptsCollective, name = 'updateReceiptsCollective'),
	
    url(r'receipts-by-policy/$', getReceiptByPolicy,name='receipts-by-policy'), 
    url(r'receipts-by-policy-endosos/$', getReceiptByPolicyEndosos,name='receipts-by-policy-endosos'), 
    url(r'packagecreate_new', createPacakageNew,name='createPacakageNew'), 
    # ---Caratula polizas    
    url(r'^cancel-caratula_polizas/$', CancelCaratulaPolizasManual, name='CancelcaratulaPolizasManual'),
    
    url(r'^certificados-caratula/$', CertificadosCaratulaViewSet, name = 'certificados-caratula'),

    url(r'get_caratula_polizas/$', getCaratulaPolizas,name='getCaratulaPolizas'), 

    url(r'^get-all-caratulas/$', CollectsForSearchViewSet, name = 'get-all-caratulas'),  
    url(r'save_caratula_polizas/$', saveCaratulaPolizas,name='saveCaratulaPolizas'), 
    
    url(r'massives-polizas/', savepolizasmasivasgrupo,name='savepolizasmasivasgrupo'), 
    url(r'massives-certificados/', savepgrupomasivoscertificados,name='savepgrupomasivoscertificados'), 
    url(r'check-certificados-masivos/', checkpgrupomasivoscertificados,name='checkpgrupomasivoscertificados'), 
    url(r'massives-flotillas/', savepolizasmasivasflotilla,name='savepolizasmasivasflotilla'), 
    url(r'massives-polizasflotillas/', savepolizasmasivaspflotilla,name='savepolizasmasivaspflotilla'), 
    url(r'massives-contractors/', savecontractorsmassives,name='savecontractorsmassives'), 
    url(r'massives-polizas-individuales/', savepolizasmasivasindividuales,name='savepolizasmasivasindividuales'), 
    url(r'massives-norenovacion-polizas/', savepolizasmasivasnorenovacionid,name='savepolizasmasivasnorenovacionid'), 
    url(r'read-excel-policies/', readFileToUpPolizas,name='readFileToUpPolizas'), 
    url(r'^get-relations-by-id', getRelationsPolicy, name='get_relations_id'),
    
    # ---------Caratula polizas
    url(r'^deactivate-user', deactivate_user, name = 'deactivate-user'), 
    url(r'^get-orgs/', get_orgs, name = 'get-orgs'), 
    url(r'^notas-by-contractor', GetNotaCreditoContractor, name = 'get-notas-by-contrator'),
    url(r'^folio', GetFolio, name = 'folio'),      
    url(r'^delete-colectivity', DeleteColectivity, name = 'delete-policy'), 
    url(r'^conciliate-states', ConciliateStates, name = 'conciliate-states'), 
    url(r'^get-receipt-conciliate-data/', GetConciliateReceiptInfo, name = 'get-receipt-conciliate-data'),        
    url(r'^fisicas-listwop', NaturalListWop, name = 'fisicas-listwop'), #Adapted contractor type_person =1 
    url(r'^morales-listwop', JuridicalListWop, name = 'morales-listwop'),#Adapted contractor type_person =2
    url(r'^contractor-listwop', ContractorListWop, name = 'contractor-listwop'),#Adapted contractor alls
    
    # --------- Mensajeria ------------------------
    url(r'^get-delivery', get_mnsj, name='get_mnsj'),
    url(r'^create-delivery', create_delivery, name='create_delivery'),
   
   # ---------- Vendedores ---------
    url(r'^get-vendors/$', get_vendors, name='get_vendors'),
    url(r'^get-vendors-mc/$', get_vendors_mc, name='get_vendors_mc'),

    url(r'^userslist_admin', get_userslist_admin, name='get_userslist_admin'),
    url(r'^get-comission-amount/', CommissionsAmount, name = 'get-comission-amount'), 
    url(r'^get-vendedores-receipts/$', VendedoresReceiptsAll, name = 'get-vendedores-receipts'), 
    url(r'^get-vendedores-receipts-excel/$', VendedoresReceiptsAllExcel, name = 'get-vendedores-receipts-excel'), 
    url(r'^send-email-vendor-state/$', SendStateEmail, name='sendStateEmail'),  
    
    url(r'^listaPolizasShare', listaPolizasShare, name='listaPolizasShare'),
    url(r'^get-contractorsList$', contratantesPolizas, name = 'contratantesPolizas'),
    url(r'^compartir-a-app/$', compartirAlaApp, name = 'compartirAlaApp'),
    url(r'^get-referenciador-receipts/$', ReferenciadoresReceiptsAll, name = 'get-referenciador-receipts'), 
    
   # ---------- Endosos colectivos -------------
    url(r'^get-endorsements-collect/$', CollectForEndorsementsViewSet, name = 'get-endorsements-collect'),  
    url(r'^get-certificatesforendoso/$', CertifictaeForEndorsementsViewSet, name = 'get-certificatesforendoso'),  
    url(r'^get-certificatesforsiniestro/$', CertifictaeForSiniestrosViewSet, name = 'get-certificatesforsiniestro'),  
    url(r'^get-endorsements-policies/$', PolizasForEndorsementsViewSet, name = 'get-endorsements-policies'),
    url(r'^get-policies-ind-flotillas/$', PolizasForRenovateViewSet, name = 'get-policies-indflotilla'),
    url(r'^get-endorsements-fianzas/$', FianzasForEndorsementsViewSet, name = 'get-endorsements-fianzas'),
    url(r'^info-certificate-endorsement/$', CertificateEndosoInfoViewSet, name = 'get-certificate-endorsement'), 
    url(r'^massive-endorsements-altas/', CreateMassiveAltasEndorsements, name = 'CreateMassiveAltasEndorsements'),
    url(r'^massive-endorsements-bajas/', CreateMassiveBajasEndorsements, name = 'CreateMassiveBajasEndorsements'),
    url(r'^get-certificados', getCertificados.as_view({'get': 'list'}), name = 'getCertificados'),
    url(r'^get-ots/$', get_ots_container, name = 'get-ots'),
    url(r'^get-endorsement-certificates', getCertificates, name = 'getCertificates'),
    url(r'^deleted-certs', deletedCerts, name = 'deletedCerts'),
    url(r'^added-certs', addCerts, name = 'addCerts'),
    url(r'^edited-certs', editCert, name = 'editCerts'),
    url(r'^get-relation', getRelation, name = 'getRelation'),
    url(r'^relationBeneficiarios', getRelationBeneficiarie, name = 'getRelationBeneficiarie'),
    url(r'^relationDependiente', getRelationDependiente, name = 'getRelationDependiente'),
    url(r'^activate-cert', activateCert, name = 'activateCert'),
    # endoso manual masivo
    url(r'^get-certificates-for-endoso/$', CertificateForEndososViewSet, name = 'get-certificates-for-endoso'),
    # ----------Actualización de autos flotillas certificados--------------
    url(r'^get-polizas-colectividad/', GetPolizasColectividad, name = 'GetPolizasColectividad'),
    
    url(r'^massive-certificateUpdate/', massiveUpdateCertsInfoAdicional, name = 'massiveUpdateCertsInfoAdicional'),
    url(r'^relation-certificados-endosos/', EndosoCertificadoRelationSet, name = 'EndosoCertificadoRelationSet'),
    url(r'^bancos', BancosWOPViewSet, name = 'BancosWOPViewSet'),   
    url(r'^get-aseguradoras-clave', get_aseguradoras_clave, name = 'get_aseguradoras_clave'),
    url(r'^get-provider-clave', get_providers_clave, name = 'get_providers_clave'),
    url(r'^get-afianzadoras-clave', get_afianzadoras_clave, name = 'get_afianzadoras_clave'),
    url(r'^proveedores-resume-list', ProviderReadListViewSet, name = 'provider-resume-list'),
    url(r'^v1/configurations/states', StatesViewSet, name = 'states_filter'),
    url(r'^v1/configurations/cities', CitiesViewSet, name = 'cities_filter'),
    url(r'^grupos-resume', GroupResumeViewSet, name = 'GroupResumeViewSet'),
    url(r'^gruposSubgrupos-resume', GroupSubgroupsResumeViewSet, name = 'GroupSubgroupsResumeViewSet'),#Subgrupos
    url(r'^groupingLevel-resume', GroupingLevelResumeViewSet, name = 'GroupingLevelResumeViewSet'),#Subgrupos
    url(r'^get-contractor-personal-info/(?P<id>[-\w]+)', getContractorInfo, name = 'get-contractor-personal-info'),
    url(r'^leer-folios-pago-consult', FoliosPagoLiqConsultaModulo, name = 'foliospagoliq'),  
    url(r'^leer-folios-pago-recibos', FoliosPagoLiqRecibos, name = 'foliospagoliqrec'),  
    url(r'^leer-folios-conciliacion-recibos', FoliosConciliacionRecibos, name = 'foliosconciliacionrecibos'),  
    
    url(r'^copy-data/', copyData, name = 'copyData'),
    url(r'^copy-data-renewal/', CopyDataRenewal, name = 'CopyDataRenewal'),
    
    #------------- REPORTES -----------------------
    url(r'^reporte-cobranzaAll$', ReporteCobranzaModuloAll, name = 'ReporteCobranzaAll'),
    url(r'^reporte-aseguradoras/$', ReporteAseguradoras, name = 'ReporteAseguradoras'),
    url(r'^reporte-grupos/$', GroupResumeReport, name = 'GroupResumeReport'),
    url(r'^reporte-paquetes/$', ReportePaquetes, name = 'ReportePaquetes'),
    url(r'^reporte-seekerNaturals/$', ReporteSeekerNaturals, name = 'ReporteSeekerNaturals'),#Adapted contractor type_person =1 
    url(r'^reporte-seekerJuridicals/$', ReporteSeekerJuridicals, name = 'ReporteSeekerJuridicals'),#Adapted contractor type_person =2 
    # url(r'^reporte-seekerGrupos/$', ReporteSeekerGroups, name = 'ReporteSeekerGroups'),
    url(r'^reporte-seekerPackages/$', ReporteSeekerPackages, name = 'ReporteSeekerPackages'),
    url(r'^reporte-seekerProviders/$', ReporteSeekerAseguradoras, name = 'ReporteSeekerAseguradoras'),
    url(r'^reporte-comision/$', ReportComission, name = 'ReportComission'),
    url(r'^reporte-siniestros-gastos/$', ReporteSiniestrosGastos, name = 'ReporteSiniestrosGastos'),
    url(r'^reporte-siniestros-modulo/$', ReporteSiniestrosModulo, name = 'ReporteSiniestrosModulo'),
    # ----cob-notas
    url(r'^get-comissions-aseguradoras/$', CommissionsAseguradoras, name = 'CommissionsAseguradoras'),
    url(r'^get-comissions/$', Commissions, name = 'Commissions'),
    url(r'^bonos-to-excel/$', ReporteBonos, name = 'ReporteBonos'),
	#Numero de poliza post 
    url(r'^v1/policies/exist_number', exist_policy_number, name = 'exist_policy'),
    # -------------- Filtros Reportes -------------------------
    url(r'^filtros-contractor/$', FiltrosContractor, name = 'FiltrosContractor'),
    # --------------- Modulo Reportes ----------------------
    url(r'^reporte-cobranza$', ReporteCobranza, name = 'ReporteCobranza'),   
    url(r'^reporte-polizas$', PolicyReporteFilters, name ='PolicyReporteFilters'),
    url(r'^reporte-renovaciones$', ReporteRenovaciones, name = 'ReporteRenovaciones'),
    url(r'^reporte-siniestros$', ReporteSiniestros, name = 'ReporteSiniestros'),
    # Reportes modulo
	url(r'^calcular-estado-cuenta/$', AccountCalcularInfoViewSet, name = 'accountstateinfocalcular'),
	url(r'^estado-cuenta-table-info/$', AccountStateInfoViewSet, name = 'accountstateInfo'),
    url(r'^reporte-auditoria-rep/$', GetReportAuditoriaViewSet, name = 'GetReportAuditoriaViewSet'),
    url(r'^reporte-cobranza-rep/$', GetReportCobranzaViewSet, name = 'GetReportCobranzaViewSet'),
    # jira 838
    url(r'^polizas-autocomplete/?$', PolizaAutocompleteView.as_view(), name='polizas_autocomplete'),
    # jira 838 end
	url(r'^reporte-cobranzafianza-rep/$', GetReportCobranzaFianzaViewSet, name = 'GetReportCobranzaFianzaViewSet'),
	url(r'^reporte-poliza-rep/$', GetReportePolizaRep, name = 'GetReportePolizaRep'),
	url(r'^reporte-polizaenproceso-rep/$', GetReportePolizaEnProcesoRep, name = 'GetReportePolizaEnProcesoRep'),
	url(r'^reporte-otsendosos-rep/$', GetReporteOtsEndososRep, name = 'GetReporteOtsEndososRep'),
    url(r'^reporte-fianzas-rep/$', GetReporteFianzaRep, name = 'GetReporteFianzaRep'),
	url(r'^reporte-fianzasben-rep/$', GetReporteFianzaBenRep, name = 'GetReporteFianzaBenRep'),
	url(r'^reporte-renovaciones-rep/$', GetReportRenovacionesViewSet, name = 'GetReportRenovacionesViewSet'),
	url(r'^reporte-endosos/$', ReporteEndosos, name = 'ReporteEndosos'),
	url(r'^reporte-siniestros-rep/$', GetReportSiniestrosViewSet, name = 'GetReportSiniestrosViewSet'),
    url(r'^reporte-log/$', GetReportLog, name = 'GetReportLog'),
	url(r'^reporte-tasks/$', GetTasksReporte, name = 'GetTasksReporte'),
	url(r'^reporte-edoclientes/$', GetReportEdoClientes, name = 'GetReportEdoClientes'),
	url(r'^reporte-ventacruzada/$', GetReportVentaCruzada, name = 'GetReportVentaCruzada'),
    url(r'^reporte-poliza-gastos-medicos/$', GetReportePolizaGM, name = 'GetReportePolizaGM'),
	url(r'^reporte-adjuntos/$', GetReportAdjuntos, name = 'GetReportAdjuntos'),
    url(r'^reporte-asegurados/$', GetAseguradosReporte, name = 'GetAseguradosReporte'),
    url(r'^reporte-polizacontrib-rep/$', GetReportePolizasContribRep, name = 'GetReportePolizasContribRep'),
	# Módulo Pólizas
	url(r'^filtros-polizas/$', PolicyFilters, name = 'policyFilters'),
	url(r'^filtros-polizas-ot/$', PolicyOTFilters, name = 'policyOTFilters'),
    #fianza
    url(r'^filtros-fianzas_new/$', FianzaFiltersNew, name = 'fianzaFiltersNew'),
    url(r'^filtros-fianzas-ot_new/$', FianzaOTFiltersNew, name = 'fianzaOTFiltersNew'),
    # Módulo cobranza
    url(r'^get-cobranza/$', GetCobranzaViewSet, name = 'get-cobranza'),
    url(r'^pay-cobranza-massive/$', PayCobranzaMassiveViewSet, name = 'pay-cobranza'),
    url(r'^conciliar-cobranza-massive/$', ConciliarCobranzaMassiveViewSet, name = 'conciliar-cobranza'),
    url(r'^get-recibos-folio-pago-liquidacion/$', GetCobranzaFolioViewSet, name = 'pay-cobranza'),   

    url(r'^get-beneficiarios-fianzas/$', GetBeneficiarioFianza, name = 'GetBeneficiarioFianza'),
    
    url(r'^reporte-folios/$', ReporteCobranzaFolios, name = 'ReporteCobranzaFolio'),
    url(r'^report-sinister-excel$', ReportSinisterExcel, name = 'ReportSinistersExcel'),
	url(r'^listaSiniestosExcel/$', ListaSiniestosExcel, name = 'ListaSiniestosExcel'),

    url(r'^cotizacion-to-show/$', CotizacionShowViewSet, name = 'CotizacionShowViewSet'),
    url(r'^reporte-cotizaciones$', ReporteCotizaciones, name = 'ServiceReporteCotizaciones'),

    # --------------- Reportes excel ---------------reporte-recibos-subsec-excel
    url(r'^reporte-endosos-excel$', EndosoReporteFiltersExcel, name = 'EndosoReporteFiltersExcel'),
    url(r'^reporte-siniestros-excel/$', ReporteSiniestrosExcel, name = 'ReporteSiniestrosExcel'),
    # Deleted by no use already in report service
    # url(r'^reporte-fianzas-excel$', FianzaReporteFiltersExcel, name = 'FianzaReporteFiltersExcel'),
    # url(r'^reporte-renovaciones-excel$', ReporteRenovacionesExcel, name = 'ReporteRenovacionesExcel'),
    # Delete by no use imprt already to report service
    # url(r'^reporte-recibos-subsec-excel/$', ReporteRecibosSubsecuetntes, name = 'ReporteRecibosSubsecuetntes'),
    # url(r'^reporte-cobranza-excel$', ReporteCobranzaExcel, name = 'ReporteCobranzaExcel'),
    url(r'^claves-excel$', ClavesExcel, name = 'ClavesExcel'),
    url(r'^vendors-report$', VendorsExcel, name = 'VendorsExcel'),
    url(r'^reporte-operacion-excel$', ReporteOperacionToExcel, name = 'ReporteOperacionToExcel'),
    url(r'^reporte-task$', ReporteTaskToExcel, name = 'ReporteTaskToExcel'),
    url(r'^reporte-log-excel$', GetReportExcelLog, name = 'GetReportExcelLog'),
    url(r'^reporte-tasks-excel$', GetTasksReporteExcel, name = 'GetTasksReporteExcel'),
    url(r'^reporte-edoClientes-excel$', GetReportExcelEdoClientes, name = 'GetReportExcelEdoClientes'),
    url(r'^reporte-ventacruzada-excel$', GetReportExcelVentaCruzada, name = 'GetReportExcelVentaCruzada'),
    url(r'^reporte-cumpleanios-excel$', ReportExcelWeekBirthdays, name = 'ReportExcelWeekBirthdays'),
    url(r'^reporte-recibos-subsecuentes/$', ReporteReciboaSubsViewSet, name = 'reporte-recibos-subsecuentes'),
    url(r'^reporte-otsendosos-excel/$', ReporteOTSEndososExcel, name = 'reporte-otsendosos-excel'),
    url(r'^edos-cuenta-by-referenciador/$', ReporteEdoCuentasExcel, name = 'reporte-edocuentas referenciador-excel'),
    # bsucar referenciador
    url(r'^buscar-vendedores/$', BuscarReferenciadorLista, name = 'buscarreferenciador'),
    # Reporte cotizaciones excel
    # Deñleted by no use already in report service
    # url(r'^reporte-quotations/$', dataToExcelQuotations, name = 'dataToExcelQuotations'),
    url(r'^reporte-poliza-gastos-medicos-excel$', ReportePolizaGMExcel, name = 'ReportePolizaGMExcel'),
    # Stadistics
	url(r'^reporte-stadistics/$', GetReportStadistics, name = 'GetReportStadistics'),
	url(r'^reporte-stadistics2/$', GetReportStadistics2, name = 'GetReportStadistics2'),
	url(r'^reporte-stadistics3/$', GetReportStadistics3, name = 'GetReportStadistics3'),
    # --------------- Sumas Reportes ----------------------
    url(r'^get-sumas-policies$', getSumasPolicy, name = 'getSumasPolicy'),
    url(r'^get-sumas-cobranza$', getSumasCobranza, name = 'getSumasCobranza'),
    url(r'^get-sumas-renovaciones$', getSumasRenewals, name = 'getSumasRenewals'),

    url(r'^get-area/(?P<_id>[-\w]+)$', get_areas, name = 'get-area'), 

    # Filtro por usuario
    url(r'^get-shared-by-group-user/$', GetSharedGroupUser, name = 'get-shared-by-group-user'), 
    url(r'^get-group-user/$', GetGroupUser, name = 'get-group-user'), 
    # -------------------
    url(r'^v1/policies/(?P<pk>[-\w]+)$', policy_by_number_detail, name = 'policy_by_number_detail'),
    url(r'^v1/policies-detail-app/(?P<pk>[-\w]+)$', policy_detail_app, name = 'policy_detail_app'),
    url(r'^verify-defaults-covs/$', verify_covs_default, name = 'verify-defaults-covs'),
    url(r'^v1/policies/urls/(?P<pk>[-\w]+)$', policy_by_number_uri, name = 'policy_by_number_uri'),
    url(r'^v1/packages/(?P<pk>[-\w]+)/coverages', coverages_by_package, name = 'coverages_by_package'),
    url(r'^v1/policies/endorsements/(?P<pk>[-\w]+)/', exist_endorsement, name = 'exist_endorsement'),
    url(r'^v1/policies/(?P<pk>[-\w]+)/exist', exist_policy, name = 'exist_policy'),
    url(r'^serial/(?P<pk>[-\w]+)/exist-renovacion/(?P<idpoliza>[-\w]+)', exist_serial_renew, name = 'exist_serial_renew'),
    url(r'^serial/(?P<pk>[-\w]+)/exist', exist_serial, name = 'exist_serial'),
    url(r'^ok-to-delete/(?P<pk>[-\w]+)/', exist_policy_address, name = 'exist_policy_address'),
    url(r'^poliza-by-user-app/(?P<username>[-\w]+)$', PolizasByUser, name = 'PolizasByUser'),
    url(r'^poliza-by-user-app/$', PolizasByUser, name = 'PolizasByUser'),
    url(r'^poliza-by-user-app-paginado/$', PolizasByUserPaginado, name = 'PolizasByUserPaginado'),
    url(r'^poliza-by-user-app-portal/$', PolizasPortalByUser, name = 'PolizasByUser'),
    url(r'^provider-by-user-app/(?P<username>[-\w]+)$', obtenerProveedoresUsuarioApp, name = 'PolizasByUser'),
    url(r'^provider-by-subramo/(?P<subramo>[-\w]+)$', obtenerProveedoresBySubramo, name = 'PolizasByUser'),
    url(r'^editablesformat-by-user-app/(?P<username>[-\w]+)$', obtenerEditablesUsuarioAppAncora, name = 'obtenerEditablesUsuarioAppAncora'),
    url(r'^editablesformat-by-user-app-ancora/(?P<username>[-\w]+)$', obtenerEditablesUsuarioApp, name = 'obtenerEditablesUsuarioApp'),
    url(r'^dataForNotifications-by-user-app/(?P<username>[-\w]+)$', obtenerDataForNotsUsuarioApp, name = 'obtenerDataForNotsUsuarioApp'),
    url(r'^dataNotificationsSpecific-by-user-app/(?P<username>[-\w]+)$', obtenerDataNotsSpecificUsuarioApp, name = 'obtenerDataNotsSpecificUsuarioApp'),
    url(r'^delete-assign_notification_app/$', delete_notification_app, name='delete_notification_app'),
    url(r'^update_notification_app/$', update_notification_app, name='update_notification_app'),
    
    url(r'^search-ot-endorsments/$', searchEndorsmentOT, name = 'searchEndorsmentOT'),
    url(r'^v1/policies/folio/(?P<pk>[-\w]+)/exist/$', exist_folio, name = 'exist_folio'),
    
    # ------- GRAFICAS ----------
    url(r'^graficas-polizas/$', providers_graphic, name = 'graficas_polizas' ),
    url(r'^leer-ots-resume-dash/$', OTReadResume, name = 'leer-ots-resume-dash' ),
    url(r'^graficas-endosos/$', endo_graphic, name = 'endo_polizas' ),
    url(r'^graficas-recibos/$', receipts_graphic.as_view({'get': 'list'}), name = 'graficas_recibos' ),
    url(r'^graficas-renovaciones/$', renewals_graphic.as_view({'get': 'list'}), name = 'graficas_renovaciones' ),
    url(r'^graficas-siniestros/$', sinister_graphic.as_view({'get': 'list'}), name = 'graficas_siniestros' ),
    url(r'^graficas-tasks/$', tasks_graphic, name = 'graficas_tasks' ),
    url(r'^graficas-quotations/$', quotations_graphic, name = 'graficas_quotations' ),
    
    url(r'^chart-polizas/$', providers_initial, name = 'chart_polizas' ),
    url(r'^chart-recibos/$', receipts_initial, name = 'chart_recibos' ),
    url(r'^chart-renovaciones/$', renewals_initial, name = 'chart_renovaciones' ),
    url(r'^chart-siniestros/$', sinister_initial, name = 'chart_siniestros' ),
    url(r'^chart-tasks/$', tasks_initial, name = 'chart_tasks' ),
    url(r'^chart-quotations/$', quotations_initial, name = 'chart_quotations' ),
    
    url(r'^search-ot-dash$', searchOTsDash, name = 'search_graficas_polizas' ),
    url(r'^search-receipt-dash$', searchReceiptsDash.as_view({'get': 'list'}), name = 'search_graficas_recibos' ),
    url(r'^search-renew-dash$', searchRenewDash.as_view({'get': 'list'}), name = 'search_graficas_renew' ),
    url(r'^search-sinister-dash$', searchSinisterDash.as_view({'get': 'list'}), name = 'search_graficas_sinister' ),
    url(r'^excel-graficas-sinister-search/$', ReporteSearchSinisterDashSearch, name = 'ReporteSearchSinisterDashSearch-all' ),

    url(r'^filtros-subramos-dash/$', filtros_subramos_dash, name = 'filtros_subramos_dash'),
    url(r'^filtros-subramos-cotizaciones/$', filtros_subramos_cotizaciones, name = 'filtros_subramos_cotizaciones'),

    # ------- Excel graficas --------
    url(r'^excel-graficas-polizas/$', ReportePolizasDashboard, name = 'reporte_graficas_polizas' ),
    url(r'^excel-graficas-endosos/$', ReporteEndososDashboard, name = 'reporte_graficas_endosos' ),
    # Deleted by no use already in report service
    # url(r'^excel-graficas-otsendosos/$', ReportePolizasEndososDashboard, name = 'reporte_graficas_otsendosos' ),
    # url(r'^excel-graficas-renewal-all/$', ReporteRenewalDashboardAll, name = 'reporte_graficas_renewal_all' ),
    # url(r'^excel-graficas-renewal/$', ReporteRenewalDashboard, name = 'reporte_graficas_renewal' ),
    url(r'^excel-graficas-sinister/$', ReporteSinisterDashboard, name = 'reporte_graficas_sinister' ),
    url(r'^excel-graficas-sinister-all/$', ReporteSinisterDashboardAll, name = 'reporte_graficas_sinister-all' ),
    
    # NEW COLLECTIVE SURETY
    url(r'^categories_collectivesurety/', CategoryCollsuretyViewSet, name = 'CategoryCollsuretyViewSet'),
    url(r'^certificates_collectivesurety/', CertificatesCollsuretyViewSet, name = 'CertificatesCollsuretyViewSet'),
    url(r'^information_collectivesurety/', informationCollsuretyViewSet, name = 'informationCollsuretyViewSet'),
    url(r'^information_certCollSurety/', certificadosCollsuretyViewSet, name = 'certificadosCollsuretyViewSet'),
    url(r'^information_certCollSurety_info/', certificadosCollsuretyInfoViewSet, name = 'certificadosCollsuretyInfoViewSet'),
    url(r'^fianzacollectiveValidateCertificate/', certificadoCollsuretyExist, name = 'certificadoCollsuretyExist'),
    # Endosos
    url(r'^massive_upCertsByEndoso_fianza/', CreateMassiveAltasFianzaEndorsements, name = 'CreateMassiveAltasFianzaEndorsements'),
    url(r'^massive_downCertsByEndoso_fianza/', CreateMassiveBajasFianzaEndorsements, name = 'CreateMassiveBajasFianzaEndorsements'),

    url(r'^excel-certificates/$', GetCertificadosExcel, name = 'excel_certificates' ),
    url(r'^excel-certificates-all/$', GetAllCertificadosExcel, name = 'excel_all_certificates' ),
    url(r'^reporte-certificates-flotilla/$', GetCertificadosFlotillaExcel, name = 'GetCertificadosFlotillaExcel' ),

    url(r'^caratula-childs/(?P<pk>[-\w]+)', get_caratula_childs, name = 'get_caratula_childs' ),
    url(r'^subgrupo-categories/(?P<pk>[-\w]+)', get_category_subg, name = 'get_category_subg' ),
    url(r'^calculate-receipts/$', calculate_receipts, name = 'calculate_receipts' ),
    url(r'^leer-polizas-endorsements/$', PolizasForEndorsementsViewSet, name = 'leer-polizas-endorsements'),
    url(r'^cars-match/$', getCarsMatch, name='get-car-match'),    
    url(r'^contractors-match/$', getContractorsMatch, name='get-contractor-match'),
    url(r'^contractors-match-fianzas/$', getContractorsFianzasMatch, name='get-contractorfianzas-match'),
    url(r'^contractors-pp-fianzas/$', getContractorsPPFianzasMatch, name='get-contractorppfianzas-match'),
    url(r'^contractors-contact/$', getContractorContact, name='get-contractor-contact'),
    url(r'^grupos-match/$', getGroupsMatch, name='getGroupsMatch'),
    url(r'^groupinglevel-match/$', getGroupinglevelMatch, name='getGroupinglevelMatch'),
    url(r'^celula_contractor_info/$', getCelulaContractorInfo, name='getCelulaContractorInfo'),
    url(r'^medicoscelulascontractor_info/$', getMedicoCelulaContractorInfo, name='get_medicoscelulascontractor_info'),
    url(r'^medicoscelulascontractor_default/$', getMedicoDefaultExist, name='get_medicoscelulascontractor_default'),
    url(r'^contratantes-lista/$', ContratantesLista, name='ContratantesLista'),
    url(r'^classification-match/$', getClassificationMatch, name='getClassificationMatch'),
    url(r'^subgrupos-match/$', getSubGroupsMatch, name='getSubGroupsMatch'),
    url(r'^subsubgrupos-match/$', getSubsubGroupsMatch, name='getSubsubGroupsMatch'), 
    url(r'^subagrupaciones-match/$', getSubAgrupacionesMatch, name='getSubAgrupacionesMatch'),
    url(r'^bens-match/$', getFianzasMatch, name='getFianzasMatch'),
    url(r'^vendors-match/$', getVendorsMatch, name='get-vendor-match'),
    #url(r'^payment-reminder-manual/$', payment_reminder_manual, name='payment_reminder_manual'),
    url(r'^admin-email-reminder/$', admin_email_reminder, name='admin_email_reminder'),
    #url(r'^share-policy-manual/$', SharePolicyEmail, name='SharePolicyEmail'),
    url(r'^send-to-provider/$', SendToProvider, name='SendToProvider'),
    url(r'^cancel-policy-manual/$', CancelPolicyEmail, name='CancelPolicyEmail'),
    url(r'^send-email/$', SendEmail, name='SendEmail'),
    url(r'^send-email-admins-deletes/$', SendEmailAdmins, name='SendEmailAdmins'),
    url(r'^send-email-prueba/$', SendEmailPrueba, name='SendEmailPrueba'),
    url(r'^send-email-reminder-policy/$', SendEmailReminderPolicy, name='SendEmailReminderPolicy'),
    url(r'^send-email-reminder-recibos/$', reminder_receipts, name = 'reminder_receipts' ),
    url(r'^send-email-renovacion/$', SendEmailRec, name = 'SendEmailRec' ),
    url(r'^get-birthdays/$', GetBirthdays, name='GetBirthdays'),
    url(r'^reportew-birthdays/$', ReportWeekBirthdays, name='ReportWeekBirthdays'),
    url(r'^patch-policy-file/(?P<file_id>[-\w]+)$', patchPolicyFile, name='patchPolicyFile'),
    url(r'^v1/ot/(?P<pk>[-\w]+)/exist', exist_ot, name='exist_ot'),
    url(r'^v1/policies/clean/', clean_policies, name='clean_policies'),
    url(r'^v1/folios/(?P<id>[-\w]+)/', get_folio, name='get_folio'),
    # url(r'^v1/receipts', ReceiptsResumeViewSet.as_view(), name='receipts_policy'),
    url(r'^v1/receipts', ReceiptsResumeViewSet, name='receipts_policy'),    
    url(r'^v1/notasCredito-info', ReceiptsNotasInfo, name='receipts_info_nota'),
    url(r'^siniestros/get_specific/(?P<id>[-\w]+)/(?P<poliza_id>[-\w]+)', get_specific_siniestros, name='get_specific_siniestros'),
    url(r'^accidentes/get_specific/(?P<id>[-\w]+)', get_specific_accidents, name='get_specific_accidents'),
    url(r'^siniestros-match/$', getSinMatch, name='get-siniestros-match'),
    url(r'^count_siniestros_afectado/$', count_siniestros_afectado, name = 'count_siniestros_afectado' ),
    url(r'^siniestros-definidos/(?P<ramo_number>[-\w]+)', get_defined_sieniesters, name='get_defined_sieniesters'),
    url(r'^siniestros-conteos/', get_sinisters_accidentes_conteo, name='get_sieniesters_conteos'),
    url(r'^siniestros-conteos-contractor/', get_sinisters_accidentes_conteo_contractor, name='get_sieniesters_conteos'),
    url(r'^siniestros-conteos-contractors/', get_sinisters_accidentes_conteo_contractors, name='get_sieniesters_contractors_conteos'),
    url(r'^siniestros-infotable/', get_siniesters_info.as_view({'get': 'list'}), name='get_sieniesters_info'),
    url(r'^accidentes-infotable/', get_sinisters_accidentes.as_view({'get': 'list'}), name='get_sieniesters_accidentes'),
    url(r'^siniester_get_by_id/(?P<id>[-\w]+)', get_siniester_by_id, name='get_siniester_by_id'),
    url(r'^siniester_get_by_id_app/(?P<id>[-\w]+)', get_siniester_by_id_app, name='get_siniester_by_id_app'),
    
    url(r'^siniestros-danios-info/(?P<id>[-\w]+)', SiniestroDaniosInfo, name='SiniestroDaniosInfo'),
    url(r'^proveedores-info/(?P<id>[-\w]+)$', ProviderInfoViewSet, name='provider-info-id'),
    url(r'^ramo-by-id/(?P<id>[-\w]+)$', RamoInfoViewSet, name='ramo-by-id'),
    url(r'^subramo-by-id/(?P<id>[-\w]+)$', SubramoInfoViewSet, name='subramo-by-id'),
    url(r'^paquete-by-id/(?P<id>[-\w]+)$', PaqueteInfoViewSet, name='paquete-by-id'),
    url(r'^paquete-single-by-id/(?P<id>[-\w]+)$', GetPaqueteInfoViewSet, name='paquete-single-by-id'),
    url(r'^assign-pendient/$', PendientsViewSet, name='assign-pendient'),
    url(r'^ramos-by-provider/(?P<provider_id>[-\w]+)$', ramos_by_provider, name='ramos_by_provider'),
    url(r'^subramos-todos-or-provider/$', subramos_all, name='subramos_all'),
    url(r'^subramos-by-ramo/(?P<ramo_id>[-\w]+)$', subramos_by_ramo, name='subramos_by_ramo'),
    url(r'^subramos-by-ramo_code/(?P<ramo_id>[-\w]+)$', subramos_by_ramo_code, name='subramos_by_ramo_code'),
    url(r'^padecimientos-by-substring/(?P<pk>[-\w]+)$', get_match_list_diseases, name='diseases_by_substring'),
    url(r'^hospitales-by-substring/(?P<pk>[-\w]+)$', get_match_list_hospital, name='hospital_by_substring'),
    url(r'^contractor-by-substring/(?P<pk>[-\w]+)$', get_contractors_match_list, name='contractors_by_substring'),
    url(r'^get-current-receipt/(?P<poliza_id>[-\w]+)$', get_current_receipt_status, name='get_current_receipt'),
    url(r'^get-org/(?P<org_id>[-\w]+)$', get_org, name='get_org'),
    url(r'^create-code$', create_code, name='create_code'),
    url(r'^create-comission$', create_comission, name='create_comission'),
    url(r'^delete-code/(?P<code_id>[-\w]+)$', delete_code, name='delete_code'),
    url(r'^create-user/$', create_cas_user, name='create_cas_user'),
    url(r'^delete-package/$', DeletePaquete, name='delete-package'),
    url(r'^paquetes-by-subramo/$', PackageResumeBySubViewSet, name='paquetes-by-subramo'),
    url(r'^covs-by-package/$', CoverageByPackageViewSet, name='covs-by-package'),
    url(r'^get-assign/$', get_assign, name='get_assign'),
    url(r'^delete-assign/$', delete_assign, name='delete_assign'),
    url(r'^paquetes-data-by-subramo/$', PackageBySubViewSet, name='paquetes-data-by-subramo'),
    url(r'^get-receipt-children/(?P<receipt_id>[-\w]+)$', get_receipt_children, name='get-receipt-children'),
    url(r'^claves-by-provider/(?P<provider_id>[-\w]+)$', ClavesReadListViewSet, name='claves-by-provider'),
    url(r'^receipt-pay-data/(?P<receipt_id>[-\w]+)$', receipt_pay_data, name='receipt-pay-data'),
    url(r'^proveedores-ramo/(?P<provider_id>[-\w]+)$', ProviderRamoViewSet, name='provider-ramo'),
    url(r'^usuarios-responsables/$', usuarios_responsables, name='usuarios_responsables'),
    # Share certificates all To APP ok
    url(r'^shareCertificatesToApp/$', shareCertificatesToApp, name='shareCertificatesToApp'),
    url(r'^shareCertificatesToEmail/$', shareCertificatesToEmail_862, name='shareCertificatesToEmail'),
    url(r'^shareCertificatesToAppEmail/$', shareCertificatesToAppEmail, name='shareCertificatesToAppEmail'),
    # revision de enviaos d ecertificados
    url(r'^share-certificates/batches/$', share_certificates_batches, name='share_certificates_batches'),
    url(r'^share-certificates/batch-items/(?P<batch_id>\d+)/$', share_certificates_batch_items, name='share_certificates_batch_items'),
    url(r'^share-certificates/batch-retry-failed/(?P<batch_id>\d+)/$', share_certificates_batch_retry_failed, name='share_certificates_batch_retry_failed'),
    url(r'^share-certificates/batch-retry-item/(?P<item_id>\d+)/$', share_certificates_batch_retry_item, name='share_certificates_batch_retry_item'),
    # share app-correo Póliza colectividades
    url(r'^shareToAppPC/$', shareCertificatesToAppPC, name='shareCertificatesToAppPC'),
    url(r'^shareToEmailPC/$', shareCertificatesToEmailPC, name='shareCertificatesToEmailPC'),
    url(r'^shareToAppEmailPC/$', shareCertificatesToAppEmailPC, name='shareCertificatesToAppEmailPC'),
    
    url(r'^emails-certificates/$', emailCertificates, name='emailCertificates'),
    url(r'^diagnostic/$', diagnostic, name='diagnostic'),
    # Email actividad user filtrado saam to admins
    url(r'^email-to-admin-filter/$', email_to_admin_filter, name='email_to_admin_filter'),   
    # -------- Claves ----------
    url(r'^v1/claves$', clave_by_id, name='clave_by_id'),
    url(r'^claves-match/$', getClavesMatch, name='get-claves-match'),
    url(r'^update-code$', update_code, name='update_code'),
    url(r'^cas-providers-request', 'aseguradoras.views.get_cas_request'),
    url(r'report-siniester$', report_siniester,name='report_siniester'),
    url(r'report-siniester-prevex', report_siniester_prevex,name='report_siniester_prevex'),    
    url(r'send-contact-info', send_email_contact,name='send_email_contact'),    
    url(r'^reporte-operacion-email', ReporteOperacionEmail, name = 'ReporteOperacionEmail'),
    url(r'^reporte-operacion', ReporteOperacion, name = 'ReporteOperacion'),
    url(r'^datavalidate', 'organizations.views.data_validate'), 
    url(r'^add-orginfo', 'organizations.views.add_orginfo'),
    url(r'^add-userinfo', 'organizations.views.add_userinfo'),
    url(r'^data_validate_area', 'organizations.views.data_validate_area'), 
    url(r'^update_area', 'organizations.views.update_area'), 
    url(r'^app-datavalidate', 'organizations.views.app_datavalidate'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^token-auth/', ObtainAuthToken.as_view()),
    url(r'^admin/', include(admin.site.urls)),    
    url(r'count-policy-by-contractor', ContractorCountViewSet,name='ContractorCountViewSet'), 
    # auth get session 
    url(r'exist-session-saam', authenticateInSaamFromMC,name='authenticateInSaamFromMC'),     
    # ------Cédula excel
    url(r'^reporte-cedula/', ReporteCedulaExcel, name = 'ReporteCedulaExcel'),
	# router.register(r'colectivityByNumber', colectivity_by_number_detail, 'colectivity_by_number_detail')
	url(r'^colectivityByNumber/$', ColectByNumber, name = 'colectivity_by_number_detail'),
    # --------- Buscador ---------
    url(r'^seeker/$', seeker, name='seeker'), 
    # --------- kbi ---------
    url(r'^kbi/$', KBI, name='kbi'),  
    url(r'^kbi-subramos/$', kbisubramos, name='kbisubramos'),  
    url(r'^group-manager/$', GroupManagerView, name='group-manager') ,
    # --------- PDFs ---------
    url(r'^get-pdf-ot/$', PDF_OT, name='PDF_OT'),
    url(r'^get-pdf-poliza-iris/$', PDF_OT_IRIS, name='PDF_OT_IRIS'),
    url(r'^get-pdf-endorsement-new/$', endorsement_pdf_new, name='endorsement_pdf_new'),
    url(r'^get-pdf-siniester/$', siniester_pdf, name='siniester_pdf'),
    url(r'^get-pdf-finiquito/$', finiquito_pdf, name='finiquito_pdf'),
    url(r'^get-pdf-liquidacion/$', liquidacion_pdf, name='liquidacion_pdf'),
    url(r'^get-pdf-conciliacion/$', conciliacion_pdf, name='conciliacion_pdf'),
    url(r'^get-pdf-itinerario/$', itinerario_pdf, name='itinerario_pdf'),
    url(r'^get-pdf/', getPdf, name='getPdf'),
    url(r'^get-pdf-form/$', get_pdf_form, name='get_pdf_form'),
    url(r'^get-carta-siniestros/$', get_pdf_form_siniestros, name='get_pdf_form_siniestros'),
    url(r'^get-pdf-agentes/$', get_pdf_agentes, name='get_pdf_agentes'),
    url(r'^get-pdf-cotizacion/$', pdf_cotizacion, name='pdf_cotizacion'),
    

    url(r'^rehabilitar-poliza/$', RehabilitarPoliza, name='rehabilitar-poliza'),
    
    url(r'^get-pdf-edocuenta/$', PDF_EDOCUENTA_CONTRACTOR_1, name='PDF_EDOCUENTA_CONTRACTOR_1'),

    
    # Filtrado usuario
    url(r'^djangousersgroups', DjangoUserGroupsViewSet, name='DjangoUserGroupsViewSet'), 
    url(r'^get-djangousersgroups', GetDjangoUserGroupsViewSet, name='GetDjangoUserGroupsViewSet'), 
    url(r'^del-shared-user-group', DelSharedUserAndGroup, name='DelSharedUserAndGroup'), 
    # ------------------IRIS SOYIRIS

    url(r'^poliza-by-user-iris/$', PolizasByEmaiIris, name = 'PolizasByEmaiIris'),
    # ---------- IBIS
    url(r'^token-auth-siis/', ObtainAuthTokenSIIS.as_view()),
    url(r'^get-policies-siss/', GetPoliciesSISS, name='get-policies-siss'),    
    url(r'^guardar-firebase-token', updateFirebaseToken, name='guardar-firebase-token'),
    url(r'^external_contact/$', external_contact, name='external_contact'),
	url(r'^validate-ibis-siss/', ValidateEmailSISS, name='validate-ibis-email'),
    url(r'^contactEmailIBIS/$', contactEmailIBIS, name='contactEmailIBIS'),
    # ------------contatco general
    url(r'^contactEmailIBISGeneral/$', contactEmailIBISGeneral, name='contactEmailIBISGeneral'),

    # -------------------- SISS ---------------------------
    url(r'^get-anios-subsecuentes/$', getAniosSubsecuentes, name='get-anios-subsecuentes'),
    #whatsapp sms
    url(r'^send-email-reminder-recibos-whatsappsms/$', reminder_receipts_whatsapp_sms, name = 'reminder_receipts_whatsapp_sms' ),
    url(r'^payment-reminder-whatsapp/(?P<id>[-\w]*)$', payment_reminder_whatsapp, name='payment_reminder_whatsapp'),
	url(r'^get-data-to-whatsapp/$', dataToWhatsapp, name='dataToWhatsapp'),
    url(r'^update-contractors-phonemsj-id/$', updateContractorsPhoneMSJ, name = 'updateContractorsPhoneMSJ'),

	 # ---Service Excel------VERSIÓN 1-------
    # Delete for new model both Contractor
    # url(r'^service_reporte-natural-excel$', Service_ReporteNaturalExcel, name = 'Service_ReporteNaturalExcel'),
    # url(r'^service_reporte-juridical-excel$', Service_ReporteJuridicalExcel, name = 'Service_ReporteJuridicalExcel'),
    url(r'^service_reporte-contractor-excel$', Service_ReporteContractorExcel, name = 'Service_ReporteContractorExcel'),
    url(r'^service_reporte-contractorpp-excel$', Service_ReporteContractorPPExcel, name = 'Service_ReporteContractorPPExcel'),
    url(r'^service_reporte-grupo-excel$', Service_ReporteGrupoExcel, name = 'Service_ReporteGrupoExcel'),
    url(r'^service_reporte-seekerGrupos-excel$', Service_ReporteSeekerGruposExcel, name = 'Service_ReporteSeekerGruposExcel'),
    url(r'^service_reporte-poliza-excel$', Service_PolizasExcel, name = 'Service_PolizasExcel'),
    url(r'^export-bajas-certificados/$', bajasLayoutPrimas, name = 'bajasLayoutPrimas'),
    url(r'^service_reporte-poliza-excel_ot$', Service_PolizasOtExcel, name = 'Service_PolizasOtExcel'),
    url(r'^service_reporte-renovaciones-excel$', Service_RenovacionesExcel, name = 'Service_RenovacionesExcel'),
    url(r'^service_reporte-cobranzalist-excel$', Service_CobranzaExcel, name = 'Service_CobranzaExcel'),
    url(r'^service_reporte-folioslist-excel$', Service_FoliosExcel, name = 'Service_FoliosExcel'),
    url(r'^service_reporte-bono-excel$', Service_BonosExcel, name = 'Service_BonosExcel'),
    url(r'^service_reporte-claves-excel$', Service_ClavesExcel, name = 'Service_ClavesExcel'),
    url(r'^service_reporte-aseguradoras-excel$', Service_AseguradorasExcel, name = 'Service_AseguradorasExcel'),
    url(r'^service_reporte-seekerAseguradoras-excel$', Service_seekerAseguradorasExcel, name = 'Service_seekerAseguradorasExcel'),
    url(r'^service_reporte-paquetes-excel$', Service_PaquetesExcel, name = 'Service_PaquetesExcel'),
    url(r'^service_reporte-siniestros-excel$', Service_SiniestrosExcel, name = 'Service_SiniestrosExcel'),
    url(r'^service_reporte-comision-excel$', Service_ComisionExcel, name = 'Service_ComisionExcel'),
    url(r'^service_reporte-conciliados-excel$', Service_ConciliadosExcel, name = 'Service_ConciliadosExcel'),
    url(r'^service_reporte-recibosVendedor-excel$', Service_VendedorReceiptsExcel, name = 'Service_VendedorReceiptsExcel'),
    url(r'^service_reporte-vendedores-excel$', Service_VendedoresExcel, name = 'Service_VendedoresExcel'),
    url(r'^service_reporte-otsEndososDash-excel$', Service_OtsEndososExcel, name = 'Service_OtsEndososExcel'),
    url(r'^service_reporte-recibosDash-excel$', Service_RecibosDashExcel, name = 'Service_recibosDashExcel'),
    url(r'^service_reporte-renovacionesDash-excel$', Service_RenovacionesDashExcel, name = 'Service_RenovacionesDashExcel'),
    url(r'^service_reporte-siniestrosDash-excel$', Service_SiniestrosDashExcel, name = 'Service_SiniestrosDashExcel'),
    url(r'^service_reporte-cobranzaReport-excel$', Service_ReporteCobranzaExcel, name = 'Service_ReporteCobranzaExcel'),
    url(r'^service_reporte-cobranzafianzasReport-excel$', Service_ReporteCobranzaFianzasExcel, name = 'Service_ReporteCobranzaFianzasExcel'),
    url(r'^service_reporte-cobranzaReport-1-excel$', Service_ReporteCobranza1Excel, name = 'Service_ReporteCobranza1Excel'),
    url(r'^service_reporte-renovacionesReport-excel$', Service_ReporteRenovacionesExcel, name = 'Service_ReporteRenovacionesExcel'),
    url(r'^service_reporte-endososReport-excel$', Service_ReporteEndososExcel, name = 'Service_ReporteEndososExcel'),
    url(r'^service_reporte-polizasReport-excel$', Service_ReportePolizasExcel, name = 'Service_ReportePolizasExcel'),
    url(r'^service_reporte-polizascontribReport-excel$', Service_ReportePolizasContribExcel, name = 'Service_ReportePolizasContribExcel'),
    url(r'^service_reporte-siniestrosReport-excel$', Service_ReporteSiniestrosExcel, name = 'Service_ReporteSiniestrosExcel'),
    url(r'^service-report-portal-siniestros-excel$', PortalSiniestrosReporte, name = 'Service_ReporteSiniestrosExcel'),
    url(r'^service_reporte-fianzasReport-excel$', Service_ReporteFianzasExcel, name = 'Service_ReporteFianzasExcel'),
    url(r'^service_reporte-fianzasBenReport-excel$', Service_ReporteFianzasBenExcel, name = 'Service_ReporteFianzasBenExcel'),
    url(r'^service_reporte-logReport-excel$', Service_ReporteLogExcel, name = 'Service_ReporteLogExcel'),
    url(r'^service_reporte-tareasReport-excel$', Service_ReporteTaskExcel, name = 'Service_ReporteTaskExcel'),
    url(r'^service_reporte-cumpleReport-excel$', Service_ReporteCumpleExcel, name = 'Service_ReporteCumpleExcel'),
    url(r'^service_reporte-recibosSubsReport-excel$', Service_ReporteRecibosSubsExcel, name = 'Service_ReporteRecibosSubsExcel'),
    url(r'^service_reporte-otsEndososReport-excel$', Service_ReporteOtsEndososExcel, name = 'Service_ReporteOtsEndososExcel'),
    url(r'^service_reporte-quotations-excel$', Service_QuotationsExcel, name = 'Service_QuotationsExcel'),
    url(r'^reporte-cotizaciones-excel/$', pdf_cotizacion_excel, name='pdf_cotizacion_excel'),
    url(r'^service_reporte-certificate-excel$', Service_CertificadosExcel, name = 'Service_CertificadosExcel'),
    url(r'^service_reporte-caratulapolizas-excel$', Service_CaratulapolizasExcel, name = 'Service_CaratulapolizasExcel'),
    url(r'^service_reporte-certificateFlotilla-excel$', Service_CertificadosFlotillaExcel, name = 'Service_CertificadosFlotillaExcel'),
    url(r'^service_reporte-vendedorEdoCuenta-excel$', Service_VendedorEdoCuentaExcel, name = 'Service_VendedorEdoCuentaExcel'),
    url(r'^service_reporte-taskMnsj-excel$', Service_TaskMnsjExcel, name = 'Service_TaskMnsjExcel'),
    url(r'^service_reporte-taskReport-excel$', Service_TaskReportExcel, name = 'Service_TaskReportExcel'),
    url(r'^service_reporte-cedula-excel$', Service_CedulaExcel, name = 'Service_CedulaExcel'),
    url(r'^service_reporte-certificatesFianza-excel$', Service_CertificadosfianzaExcel, name = 'Service_CertificadosfianzaExcel'),
    url(r'^service_reporte-stadistics1-excel$', Service_ReporteEstadistica1Excel, name = 'Service_ReporteEstadistica1Excel'),
    url(r'^service_reporte-aseguradosReport-excel$', Service_AseguradoReportExcel, name = 'Service_AseguradoReportExcel'),
    url(r'^service-cobranzacontractor-excel$', Service_contractorcobranza_Excel, name = 'Service_contractorcobranza_Excel'),
    url(r'^service-polizascontractor-excel$', Service_contractorpoliza_Excel, name = 'Service_contractorpoliza_Excel'),
    
    url(r'^service_reporte-auditoriareporte-excel$', Service_ReporteAuditoriaExcel, name = 'Service_ReporteAuditoriaExcel'),
    url(r'^service_reporte-ventacruzada-excel$', Service_ReporteVentaCruzadaExcel, name = 'Service_ReporteVentaCruzadaExcel'),

    url(r'^service_reporte-taskdashReport-excel$', Service_TaskDashReportExcel, name = 'Service_TaskDashReportExcel'),
    url(r'^service-reporte-quotationsDashReport-excel$', Service_QuotationsDashReportExcel, name = 'Service_QuotationsDashReportExcel'),
 
    url(r'^service_reporte-cobranzaReportAIA-excel$', Service_ReporteCobranzaAIAExcel, name = 'Service_ReporteCobranzaAIAExcel'),
    url(r'^service_reporte-renovacionesReportAIA-excel$', Service_ReporteRenovacionesAIAExcel, name = 'Service_ReporteRenovacionesAIAExcel'),
    url(r'^service_reporte-polizasReportAIA-excel$', Service_ReportePolizasAIAExcel, name = 'Service_ReportePolizasAIAExcel'),
    url(r'^service_reporte-fianzasReportAIA-excel$', Service_ReporteFianzasAIAExcel, name = 'Service_ReporteFianzasAIAExcel'),
    url(r'^service_reporte-endososReportAIA-excel$', Service_ReporteEndososAIAExcel, name = 'Service_ReporteEndososAIAExcel'),
    url(r'^service_reporte-siniestrosReportAIA-excel$', Service_ReporteSiniestrosAIAExcel, name = 'Service_ReporteSiniestrosAIAExcel'),
    
    url(r'^notifications-test-task/$', NotificationsTestTask, name = 'notifications-test-task'), 
    url(r'^service-kbi-excel$', Service_KBI_Excel, name = 'Service_KBI_Excel'),
    url(r'^findCobranzaByFolio/$', findCobranzaByFolio, name = 'findCobranzaByFolio'),
    #url(r'^findEndosoByPolicie/$', findEndosoByP, name = 'findEndosoByP'),
    url(r'^service_reporte-catalogos-excel$', Service_ReporteCatalogosExcel, name = 'Service_ReporteCatalogosExcel'),
    url(r'^service_reporte-adjuntos-excel$', Service_ReporteAdjuntosExcel, name = 'Service_ReporteAdjuntosExcel'),
    # ==================================================
    url(r'^save-config-fields-reports/$', saveConfigTableFieldsReports, name = 'save-configtable-field-reports'),
    
    # ==================================================
    # ==================================================
    # ==================   CAS 2.0 =====================
    # ==================================================
    
    url(r'^provider-cas/$', ProvidersCas, name='ProvidersCas'),
    url(r'^provider-casPerfil/$', ProvidersCasPerfil, name='ProvidersCasPerfil'),
    url(r'^ramos-cas/(?P<aseguradora_id>[-\w]*)$', RamosCas, name='RamosCas'),
    url(r'^subramos-cas/(?P<aseguradora_id>[-\w]*)/(?P<ramo_id>[-\w]*)$', SubramosCas, name='SubramosCas'),
    url(r'^claves-general-cas/$', ClavesGeneralCas, name='ClavesGeneralCas'),
    url(r'^clave-cas/$', ClaveCas, name='ClaveCas'),
    url(r'^comision-cas/$', ComisionCas, name='ComisionCas'),
    url(r'^comisiones-cas/(?P<clave_id>[-\w]*)$', ComisionesCas, name='ClaveCas'),
    url(r'^usuario-restringido/$', PerfilUsuarioRestringidoView, name='usuariorestringido'),
    url(r'^contratantes-cas/$', ContratantesCas, name='contratantescas'),
    url(r'^grupos-cas/$', GruposCas, name='GruposCas'),
    url(r'^celulas-cas/$', CelulasCas, name='CelulasCas'),
    url(r'^sucursales-cas/$', SucursalesCas, name='SucursalesCas'),
    url(r'^referenciadores-cas/$', ReferenciadoresCas, name='ReferenciadoresCas'),
    url(r'^agrupaciones-cas/$', AgrupacionesCas, name='AgrupacionesCas'),
    url(r'^agentes-cas/$', AgentesCas, name='AgentesCas'),
    url(r'^subramos-general-cas/$', SubramosGeneralCas, name='SubramosGeneralCas'),
    url(r'^existe-perfil-restringido-cas/$', ExistePerfilRestringido, name='ExistePerfilRestringido'),
    url(r'^perfil-restringido-cas/$', GuardarPerfilRestringido, name='GuardarPerfilRestringido'),
    url(r'^polizas-listado-cas/$', PolizasListadoSaam, name='PolizasListadoSaam'),
    url(r'^perfil-usuario-restringido-cas/$', PerfilByUsuarioRestringidoView, name='PolizasListadoSaam'),
    url(r'^perfil-usuario-restringidoname-cas/$', PerfilByUsuarioRestringidoNameView, name='PerfilByUsuarioRestringidoNameView'),
    url(r'^perfil-usuario-restringido-array-cas/$', PerfilByUsuarioRestringidoArrayView, name='PerfilByUsuarioRestringidoArrayView'),

    url(r'^get-carousel-from-cas/$', GetCarouselFromCas, name='GetCarouselFromCas'),
    # ==================================================
    url(r'^getrepositoriopago/$', getRepositorioPago, name = 'getRepositorioPago'),
    url(r'^getConfigsProviderScrapper/$', getConfigsProviderScrapper, name = 'getConfigsProviderScrapper'),
    # ==================================================
    #URLs Emails
    url(r'^external_contactNV/$', external_contactNV, name='external_contactNV'),
    url(r'^send-to-providerNV/$', SendToProviderNV, name='SendToProviderNV'),
    url(r'^cancel-policy-manualNV/$', CancelPolicyEmailNV, name='CancelPolicyEmailNV'),
    url(r'^send-emailNV/$', SendEmailNV, name='SendEmailNV'),
    url(r'^payment-reminder-manual/(?P<id>[-\w]*)$', payment_reminder_manualNV, name='payment_reminder_manual'),
    
    #GRUPOGPI**
    url(r'^send-email-cotizacion-request/$', sendEmailGpiCotization, name='sendEmailGpiCotization'),
    # GPI contact
    url(r'^send-emai-contact-gpi/$', sendEmailGpiContact, name='sendEmailGpiContact'),
    #conexión agentes get registros
    url(r'^get-registros-from-agent/$', getDataFromAgent, name='getDataFromAgent'),

    url(r'^share-policy-manual/(?P<id>[-\w]*)$', SharePolicyEmailNV, name='SharePolicyEmailNV'),
    url(r'^share-siniestro-manual/(?P<id>[-\w]*)$', ShareSiniestroEmailNV, name='ShareSiniestroEmailNV'),
    url(r'^share-siniestro-whatsapp/(?P<id>[-\w]*)$', ShareSiniestroWsp, name='ShareSiniestroWsp'),
    url(r'^share-certificate-manual/(?P<id>[-\w]*)$', ShareCertificateEmailNV, name='ShareCertificateEmailNV'),
    url(r'^share-endoso-manual/(?P<id>[-\w]*)$', ShareEndosoEmailNV, name='ShareEndosoEmailNV'),
    url(r'^share-cotizacion-manual/(?P<id>[-\w]*)$', ShareCotizacionEmail, name='ShareCotizacionEmail'),
    url(r'^get-files/$', get_files_types, name='get_files_types'),
    url(r'^get-recibos-files/$', get_recibos_files, name='get_recibos_files'),
    url(r'^verify-user/$', verify_user, name='verify-user'),
    url(r'^promesa-pago/$', set_promesa_pago, name='set_promesa_pago'),
    url(r'^config-smtp/$', config_smtp, name = 'config_smtp'),
    url(r'^config-smtp2/$', config_smtp_org, name = 'config_smtp_org'),
    # Promotoria tablero  

    url(r'^fsubramos-tablero/$', fsubramos_tablero, name = 'fsubramos_tablero'),  
    url(r'^get-data-promotoria-initial/$', getPromotoriaOTsInitial, name = 'getPromotoriaOTsInitial'),
    url(r'^get-data-promotoria/$', getPromotoriaOTsByRamos, name = 'getPromotoriaOTsByRamos'),
    # Extra info
    url(r'^get-info-extra$', get_info_org, name = 'get_info_org'),
    #URLs IA
    url(r'^ia/', include('ia.urls')),    
    # ----------------------------------------
    # CAS V2
    url(r'^control/', include('control.urls')),
    # LOG SYSTEM
    url(r'^get-logs-system$', get_log_system, name = 'get_log_system'),
    url(r'^smstemplates-list/$', GetTemplatesList, name = 'GetTemplatesList'),
    # Crear notificación reportes 
    url(r'^crear-notificacion-reportes/$', crear_notificacion_reportes, name='crear_notificacion_reportes'),  
    url(r'^check-user/$', check_user_name_exists, name='check_user_name_exists'),  
    # validations polizas vigency
    url(r'^validaciones/evaluar-vigencia-json/$', EvaluarVigencyPolicie, name='evaluar_vigencia_json'),
    # subir archivos a bucket publico
    url(r'^upload-public-file/$', uploadPublicFile, name='uploadPublicFile'),
    # https://miurabox.atlassian.net/browse/DES-875
    url(r'^polizas/(?P<id>\d+)/adjuntos/$', PolizaAdjuntosView.as_view(), name='polizas-adjuntos'),
    url(r'^asignar-condiciones-generales-poliza/$', AsignarCondicionesGeneralesPolizaView.as_view(),
        name='asignar-condiciones-generales-poliza'),
    url(r'^condiciones-generales/(?P<pk>\d+)/usage/$', CondicionGeneralUsageView.as_view(),
        name='condiciongeneral-usage'),
    # https://miurabox.atlassian.net/browse/DES-875
]
