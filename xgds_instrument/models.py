# __BEGIN_LICENSE__
# Copyright (c) 2015, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The xGDS platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
# __END_LICENSE__

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from geocamUtil.modelJson import modelToDict
from geocamUtil.UserUtil import getUserName
from xgds_core.couchDbStorage import CouchDbStorage


def getNewDataFileName(instance, filename):
    return settings.XGDS_INSTRUMENT_DATA_SUBDIRECTORY + filename

#
# This model describes the instruments used for data collection.  I.e. the units and
# measurements that come out of the instrument.  It is not meant to dictate presentation
# in the UI.
#
class ScienceInstrument(models.Model):
    shortName = models.CharField(max_length=32)  # Lower case, no spaces
    displayName = models.CharField(max_length=128)
    active = models.BooleanField(default=True)
    dataImportFunctionName = models.CharField(max_length=128)
    brand = models.CharField(max_length=128)
    model = models.CharField(max_length=128)
    serialNum = models.CharField(max_length=128)
    xLabel = models.CharField(max_length=64)
    yLabel = models.CharField(max_length=64)
    xUnits = models.CharField(max_length=32)
    yUnits = models.CharField(max_length=32)
    reverseX = models.BooleanField()
    reverseY = models.BooleanField()
    startUseDate = models.DateTimeField(null=True,blank=True)
    endUseDate = models.DateTimeField(null=True,blank=True)

    @classmethod
    def getInstrument(self, name):
        return ScienceInstrument.objects.get(shortName=name)

    def __unicode__(self):
        return "%s(%s): %s %s SN:%s" % (self.displayName, self.shortName, 
                                     self.brand, self.model, self.serialNum)
    
couchStore = CouchDbStorage()

class AbstractInstrumentDataProduct(models.Model):
    """ 
    A data product from a non-camera field instrument e.g. spectrometer
    """
    manufacturer_data_file = models.FileField(upload_to=getNewDataFileName, max_length=255, null=True, blank=True, storage=couchStore)
    manufacturer_mime_type = models.CharField(max_length=128,
                                             default="application/octet-stream",
                                              null=True, blank=True)
    portable_data_file = models.FileField(upload_to=getNewDataFileName, max_length=255, storage=couchStore)
    portable_mime_type = models.CharField(max_length=128, default="text/plain")
    portable_file_format_name = models.CharField(max_length=128, default="ASCII")
    acquisition_time = models.DateTimeField(null=True, blank=True)
    acquisition_timezone = models.CharField(max_length=128)
    creation_time = models.DateTimeField(null=True, blank=True) # this is the SERVER creation time, not the acquisition time
    location = models.ForeignKey(settings.GEOCAM_TRACK_PAST_POSITION_MODEL, null=True, blank=True)
    collector = models.ForeignKey(User, null=True, blank=True, related_name="%(app_label)s_%(class)s_collector") # person who collected the instrument data
    creator = models.ForeignKey(User, null=True, blank=True, related_name="%(app_label)s_%(class)s_creator") # person who entered instrument data into Minerva
    
    instrument = models.ForeignKey(ScienceInstrument)
    
    @property
    def jsonDataUrl(self):
        return reverse('instrument_data_json',  kwargs={'productModel': self.modelAppLabel + '.' + self.modelTypeName,
                                                        'productPk': str(self.pk)})

    @property
    def csvDataUrl(self):
        return reverse('instrument_data_csv',  kwargs={'productModel': self.modelAppLabel + '.' + self.modelTypeName,
                                                       'productPk': str(self.pk)})

    def thumbnail_url(self):
        return None

    def thumbnail_time_url(self, event_time):
        return self.thumbnail_url()

    def view_time_url(self, event_time):
        return self.view_url()

    def view_url(self):
        return reverse('search_map_single_object', kwargs={'modelPK':self.pk,
                                                           'modelName': self.instrument.displayName})

    @property
    def modelAppLabel(self):
        return self._meta.app_label
    
    @property
    def modelTypeName(self):
        t = type(self)
        if t._deferred:
            t = t.__base__
        return t._meta.object_name

    # Returns the instrument reading(s) for this data product (e.g. wavenumber and reflectance for a spectrum)
    @property
    def samples(self):
        return []

    def toMapDict(self):
        result = modelToDict(self, exclude=("manufacturer_data_file", "portable_data_file"))
        result['pk'] = int(self.pk)
        result['app_label'] = self.modelAppLabel
        t = type(self)
        if t._deferred:
            t = t.__base__
        result['model_type'] = t._meta.object_name

        if self.collector:
            result['collector'] = getUserName(self.collector)
        else:
            result['collector'] = ''
        del result['creator']
        result['type'] = 'InstrumentDataProduct'
        result['instrumentName'] = self.instrument.displayName
        result['acquisition_time'] = self.acquisition_time.strftime("%m/%d/%Y %H:%M")
        result['acquisition_timezone'] = str(self.acquisition_timezone)
        result['manufacturer_data_file'] = self.manufacturer_data_file.url
        result['portable_data_file'] = self.portable_data_file.url
        result['json_data'] = self.jsonDataUrl
        result['csv_data'] = self.csvDataUrl
        if self.location:
            result['lat'] = self.location.latitude
            result['lon'] = self.location.longitude
            if self.location.altitude:
                result['altitude'] = self.location.altitude
        else: 
            result['lat'] = ''
            result['lon'] = ''
            
        return result
    
    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s: %s, %s" % (self.acquisition_time, self.instrument.codeName, self.mimeType)

