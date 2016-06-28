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

from django import forms
from django.conf import settings
import pytz

from geocamTrack.forms import AbstractImportTrackedForm
from geocamUtil.extFileField import ExtFileField
from geocamUtil.loader import LazyGetModelByName
from django.forms import DateTimeField, ModelChoiceField
from geocamUtil.extFileField import ExtFileField


class InstrumentModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.displayName


class ImportInstrumentDataForm(AbstractImportTrackedForm):
    date_formats = list(forms.DateTimeField.input_formats) + [
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y %H:%M'
        ]
    dataCollectionTime = DateTimeField(label="Collection Time",
                                       input_formats=date_formats,
                                       required=True,
                                       )
    INSTRUMENT_MODEL = \
                LazyGetModelByName(settings.XGDS_INSTRUMENT_INSTRUMENT_MODEL)
    instrument = InstrumentModelChoiceField(INSTRUMENT_MODEL.get().objects.all(), 
                                            label="Instrument")
    portableDataFile = ExtFileField(ext_whitelist=(".spc",".txt",".csv",".asp" ),
                                    required=True,
                                    label="Portable Data File")
    manufacturerDataFile = ExtFileField(ext_whitelist=(".pdz",".a2r",".asd" ),
                                        required=True,
                                        label="Manufacturer Data File")

    def clean_dataCollectionTime(self):
        ctime = self.cleaned_data['dataCollectionTime']

        if not ctime:
            return None
        else:
            tz = self.getTimezone()
            naiveTime = ctime.replace(tzinfo=None)
            localizedTime = tz.localize(naiveTime)
            utctime = localizedTime.astimezone(pytz.utc)
            return utctime
