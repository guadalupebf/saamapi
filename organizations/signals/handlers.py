from django.dispatch import receiver
from django_cas_ng.signals import cas_user_authenticated
from organizations.models import UserInfo

def cas_auth_handler(sender, user, created, attributes, ticket, service, **kwargs):
    try:
        orgname = attributes['orgname']
        orgurl = attributes['orgurl']
        orgactive = attributes['active']
    except KeyError:
        # print('ERROR')
        return
    try:
        org = Organization.objects.get(name=orgname, urlname=orgurl)
    except Organization.DoesNotExist:
        org = Organization(
            name=orgname,
            urlname=orgname,
            # owner=1,
        )
        org.save()

    org.active = orgactive

    if created:
        ui = UserInfo(user=user, org=org)
        ui.save()

# connect signals
cas_user_authenticated.connect(cas_auth_handler)
