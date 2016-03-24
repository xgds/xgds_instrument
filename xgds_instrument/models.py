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
from django.contrib.auth.models import User

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
    

class AbstractInstrumentDataProduct(models.Model):
    """ 
    A data product from a non-camera field instrument e.g. spectrometer
    """
    manufacturer_data_file = models.FileField(upload_to=getNewDataFileName, max_length=255, null=True, blank=True)
    manufacturer_mime_type = models.CharField(max_length=128,
                                             default="application/octet-stream",
                                              null=True, blank=True)
    portable_data_file = models.FileField(upload_to=getNewDataFileName, max_length=255)
    portable_mime_type = models.CharField(max_length=128, default="text/plain")
    portable_file_format_name = models.CharField(max_length=128, default="ASCII")
    acquisition_time = models.DateTimeField(null=True, blank=True)
    acquisition_timezone = models.CharField(max_length=128)
    server_creation_time = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey(settings.GEOCAM_TRACK_PAST_POSITION_MODEL,
                                 null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)
    instrument = models.ForeignKey(ScienceInstrument)

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s: %s, %s" % (self.acquisition_time, self.instrument.codeName, self.mimeType)


class InstrumentDataProduct(AbstractInstrumentDataProduct):
    pass