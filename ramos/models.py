from core.models import TimeStampedModel
from django.db import models


class Ramos(TimeStampedModel):
    ramo_name = models.CharField(max_length=500)
    ramo_code = models.SmallIntegerField(blank=True, null=True)
    provider = models.ForeignKey('aseguradoras.Provider', related_name='ramo_provider', null=True)
    owner = models.ForeignKey('auth.User', related_name='ramos', null = True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)

    def __str__(self):
        return "%s" % (self.ramo_name)


class SubRamos(TimeStampedModel):
    subramo_name = models.CharField(max_length=500)
    subramo_code = models.SmallIntegerField(blank=True, null=True)
    ramo = models.ForeignKey(Ramos, related_name='subramo_ramo', null=True)
    owner = models.ForeignKey('auth.User', related_name='subramos', null=True)
    org_name = models.CharField(max_length=50, null=True, db_index=True)

    def __str__(self):
        return "%s" % (self.subramo_name)

class FianzaType(TimeStampedModel):
    type_name = models.CharField(max_length=500)
    type_code = models.SmallIntegerField(blank=True, null=True)
    subramo = models.ForeignKey(SubRamos, related_name='type_subramo', null=True)
    owner = models.ForeignKey('auth.User', related_name='types')
    org_name = models.CharField(max_length=50, null=True, db_index=True)

    def __str__(self):
        return "%s" % (self.type_name)