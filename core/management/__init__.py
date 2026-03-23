from django.db.models.signals import post_syncdb
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

def add_view_permissions(sender, **kwargs):
    """
    This syncdb hooks takes care of adding a view permission too all our 
    content types.
    """
    # for each of our content types
    #    ct_core, ct_core_created = ContentType.objects.get_or_create(app_label = 'core', model = 'reports')
    # ct_polizas,ct_polizas_created = ContentType.objects.get_or_create(app_label = 'polizas', model = 'renovations')
    try:
        ct_recibos = ContentType.objects.get(app_label = 'recibos', model = 'commissions')
        ct_polizas = ContentType.objects.get(app_label = 'polizas', model = 'polizas')
        for content_type in ContentType.objects.all():
            # build our permission slug
            codename = "view_%s" % content_type.model

            # if it doesn't exist..
            if not Permission.objects.filter(content_type=content_type, codename=codename):
                # add it
                Permission.objects.create(content_type=content_type,
                                          codename=codename,
                                          name="Can view %s" % content_type.name)
                print()
                print ("Added view permission for %s" % content_type.name)


        
        codename_report = 'edit_receipt_validity'    
        codename_polizas = 'cancel_polizas'    
        codename_c_recibos = 'conciliate_recibos'
        codename_l_recibos = 'close_recibos'
        codename_p_recibos = 'edit_paid_receipts'
        codename_q_recibos = 'undo_receipts'
         
        if not Permission.objects.filter(content_type=ct_recibos, codename=codename_report):
            Permission.objects.create(content_type=ct_recibos,
                                      codename=codename_report,
                                      name="Can edit receipt validity")

        if not Permission.objects.filter(content_type=ct_recibos, codename=codename_p_recibos):
          Permission.objects.create(content_type=ct_recibos,
                                    codename=codename_p_recibos,
                                    name="Can edit paid receipts")

        if not Permission.objects.filter(content_type=ct_recibos, codename=codename_q_recibos):
            Permission.objects.create(content_type=ct_recibos,
                                      codename=codename_q_recibos,
                                      name="Can undo receipts")

        if not Permission.objects.filter(content_type=ct_polizas, codename=codename_polizas):
            Permission.objects.create(content_type=ct_polizas,
                                      codename=codename_polizas,
                                      name="Can cancel polizas")
        if not Permission.objects.filter(content_type=ct_recibos, codename=codename_l_recibos):
            Permission.objects.create(content_type=ct_recibos,
                                      codename=codename_l_recibos,
                                      name="Can close recibos")
            print('Can close recibos permission added')

        if not Permission.objects.filter(content_type=ct_recibos, codename=codename_c_recibos):
            Permission.objects.create(content_type=ct_recibos,
                                      codename=codename_c_recibos,
                                      name="Can conciliate recibos")
            print('Can conciliate recibos permission added')
    except:
        print('vuelva a correr: python manage.py migrate...')
# check for all our view permissions after a syncdb
post_syncdb.connect(add_view_permissions)
