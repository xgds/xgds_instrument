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

import datetime
import pytz
from django import forms
from django.conf import settings
from django.utils.functional import lazy

from dal import autocomplete

from geocamUtil.extFileField import ExtFileField
from geocamUtil.loader import LazyGetModelByName
from django.forms import DateTimeField, ModelChoiceField
from geocamUtil.extFileField import ExtFileField
from geocamUtil.forms.AbstractImportForm import getTimezoneChoices

from xgds_core.forms import SearchForm, AbstractImportVehicleForm
from xgds_core.models import XgdsUser


class InstrumentModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.displayName


class ImportInstrumentDataForm(AbstractImportVehicleForm):
    date_formats = list(forms.DateTimeField.input_formats) + [
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y %H:%M'
        ]
    dataCollectionTime = DateTimeField(label="Collection Time",
                                       input_formats=date_formats,
                                       required=True,
                                       )
    collector = forms.ModelChoiceField(XgdsUser.objects.all(), 
                                       widget=autocomplete.ModelSelect2(url='select2_model_user'),
                                       required=False)

    INSTRUMENT_MODEL = LazyGetModelByName(settings.XGDS_INSTRUMENT_INSTRUMENT_MODEL)
    instrument = InstrumentModelChoiceField(INSTRUMENT_MODEL.get().objects.all(), 
                                            label="Instrument")
    portableDataFile = ExtFileField(ext_whitelist=(".spc",".txt",".csv",".asp" ),
                                    required=True,
                                    label="Portable Data File")
    manufacturerDataFile = ExtFileField(ext_whitelist=(".pdz",".a2r",".asd" ),
                                        required=False,
                                        label="Manufacturer Data File")

    lat = forms.FloatField(label="Latitude", required=False)
    lon = forms.FloatField(label="Longitude", required=False)
    alt = forms.FloatField(label="Altitude", required=False)
    
    def editingSetup(self, dataProduct):
        self.fields['portableDataFile'].widget = forms.HiddenInput()
        self.fields['manufacturerDataFile'].widget = forms.HiddenInput()
        self.fields['portableDataFile'].initial = dataProduct.portable_data_file
        self.fields['manufacturerDataFile'].initial = dataProduct.manufacturer_data_file
        
    def handleFileUpdate(self, dataProduct, key):
        pass
    
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
        
    def save(self, commit=True):
        instance = super(ImportInstrumentDataForm, self).save(commit=False)
        if (('lat' in self.changed_data) and ('lon' in self.changed_data)) or ('alt' in self.changed_data):
            if instance.user_position is None:
                LOCATION_MODEL = LazyGetModelByName(settings.GEOCAM_TRACK_PAST_POSITION_MODEL)
                instance.user_position = LOCATION_MODEL.get().objects.create(serverTimestamp = datetime.datetime.now(pytz.utc),
                                                                             timestamp = instance.acquisition_time,
                                                                             latitude = self.cleaned_data['lat'],
                                                                             longitude = self.cleaned_data['lon'], 
                                                                             altitude = self.cleaned_data['alt'])
            else:
                instance.user_position.latitude = self.cleaned_data['lat']
                instance.user_position.longitude = self.cleaned_data['lon']
                instance.user_position.altitude = self.cleaned_data['alt']
                instance.user_position.save()

        if commit:
            instance.save()
        return instance


class SearchInstrumentDataForm(SearchForm):
    min_acquisition_time = forms.DateTimeField(input_formats=settings.XGDS_CORE_DATE_FORMATS,
                                               required=False, label='Min Time',
                                               widget=forms.DateTimeInput(attrs={'class': 'datetimepicker'}))
    max_acquisition_time = forms.DateTimeField(input_formats=settings.XGDS_CORE_DATE_FORMATS,
                                               required=False, label='Max Time',
                                               widget=forms.DateTimeInput(attrs={'class': 'datetimepicker'}))
    
    acquisition_timezone = forms.ChoiceField(required=False, choices=lazy(getTimezoneChoices, list)(empty=True), 
                                             label='Time Zone', help_text='Required for Min/Max Time')
    
    collector = forms.ModelChoiceField(XgdsUser.objects.all(), 
                                       widget=autocomplete.ModelSelect2(url='select2_model_user'),
                                       required=False)

    
    # populate the times properly
    def clean_min_acquisition_time(self):
        return self.clean_time('min_acquisition_time', self.clean_acquisition_timezone())

    # populate the times properly
    def clean_max_acquisition_time(self):
        return self.clean_time('max_acquisition_time', self.clean_acquisition_timezone())
    
    def clean_acquisition_timezone(self):
        if self.cleaned_data['acquisition_timezone'] == 'utc':
            return 'Etc/UTC'
        else:
            return self.cleaned_data['acquisition_timezone']
        return None

    def clean(self):
        cleaned_data = super(SearchInstrumentDataForm, self).clean()
        acquisition_timezone = cleaned_data.get("acquisition_timezone")
        min_acquisition_time = cleaned_data.get("min_acquisition_time")
        max_acquisition_time = cleaned_data.get("max_acquisition_time")

        if min_acquisition_time or max_acquisition_time:
            if not acquisition_timezone:
                self.add_error('event_timezone',"Time Zone is required for min / max times.")
                raise forms.ValidationError(
                    "Time Zone is required for min / max times."
                )

    def buildQueryForField(self, fieldname, field, value, minimum=False, maximum=False):
        if fieldname == 'description' or fieldname == 'name':
            return self.buildContainsQuery(fieldname, field, value)
        return super(SearchInstrumentDataForm, self).buildQueryForField(fieldname, field, value, minimum, maximum)

    class Meta:
        abstract = True
