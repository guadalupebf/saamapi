from django.contrib.auth.models import User
from rest_framework import serializers
from django.forms import widgets
from ramos.models import Ramos, SubRamos, FianzaType
from paquetes.serializers import PackageHyperSerializer



class SubramosCasSerializer(serializers.HyperlinkedModelSerializer):
    item_text = serializers.SerializerMethodField()
    item_id = serializers.SerializerMethodField()

    def get_item_text(self, obj):
        return obj.subramo_name

    def get_item_id(self, obj):
        return obj.subramo_code

    class Meta:
        model = SubRamos
        fields = ('item_id', 'item_text')


class FianzaTypeHyperSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = FianzaType
        fields = ('url', 'id', 'owner', 'org_name', 'subramo',
                  'type_name', 'type_code')

class SubramoHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    package_subramo = PackageHyperSerializer(many=True, read_only=True)
    type_subramo = FianzaTypeHyperSerializer(many = True, read_only = True)

    class Meta:
        model = SubRamos
        fields = ('url', 'id', 'owner', 'org_name', 'type_subramo',
                  'subramo_name', 'subramo_code', 'ramo', 'package_subramo',
                  'created_at', 'updated_at')


class RamosHyperSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    subramo_ramo = SubramoHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Ramos
        fields = ('url', 'id' ,'owner', 'org_name',
                 'ramo_name', 'ramo_code', 'provider', 'subramo_ramo',
                 'created_at', 'updated_at')

class SubramoResumeHyperSerializer(serializers.HyperlinkedModelSerializer):
    type_subramo = FianzaTypeHyperSerializer(read_only = True, many = True)
    
    class Meta:
        model = SubRamos
        fields = ('url', 'id', 'owner', 'org_name','subramo_name', 'subramo_code', 'type_subramo')
        

class RamosResumeHyperSerializer(serializers.HyperlinkedModelSerializer):
    subramo_ramo = SubramoResumeHyperSerializer(many=True, read_only=True)

    class Meta:
        model = Ramos
        fields = ('url', 'id' ,'ramo_name', 'ramo_code','subramo_ramo','provider','org_name')


class RamosResumeCleanHyperSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Ramos
        fields = ('url', 'id' ,'ramo_name', 'ramo_code')


class RamosResumeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Ramos
        fields = ( 'id' ,'ramo_name', 'ramo_code', 'url')

class RamoResumeMiniSerializer(serializers.HyperlinkedModelSerializer):
    provider = serializers.ReadOnlyField(source='provider.alias')
    class Meta:
        model = SubRamos
        fields = ('id','provider',)

class SubramoResumeSerializer(serializers.HyperlinkedModelSerializer):
    ramo = RamoResumeMiniSerializer(read_only = True)
    class Meta:
        model = SubRamos
        fields = ('id','subramo_name', 'subramo_code', 'url', 'ramo')


class SubramoHyperResumeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SubRamos
        fields = ('id','subramo_name', 'subramo_code', 'url')