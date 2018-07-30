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
import json
import pandas as pd
import pytz
import httplib

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from xgds_instrument.forms import ImportInstrumentDataForm
from requests.api import request
from django.core.urlresolvers import reverse
from geocamUtil.loader import LazyGetModelByName


def lookupImportFunctionByName(moduleName, functionName):
    importModule = __import__(moduleName)
    function = getattr(getattr(importModule, moduleName.split(".")[-1]),
                       functionName)
    return function

def cleanValue(s):
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None

def isNumber(s):
    if not s:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False

def editInstrumentDataPosition(dataProduct, newLatitude, newLongitude, newAltitude):
    cleanLatitude = cleanValue(newLatitude)
    cleanLongitude = cleanValue(newLongitude)
    cleanAltitude = cleanValue(newAltitude)
    if not newLatitude or not newLongitude:
        return
    
    
    ''' create or update the user position for an instrument data reading '''
    if cleanLatitude != dataProduct.lat or cleanLongitude != dataProduct.lon or cleanAltitude != dataProduct.alt:
        if dataProduct.user_position is None:
            LOCATION_MODEL = LazyGetModelByName(settings.GEOCAM_TRACK_PAST_POSITION_MODEL)
            dataProduct.user_position = LOCATION_MODEL.get().objects.create(serverTimestamp = datetime.datetime.now(pytz.utc),
                                                                            timestamp = dataProduct.acquisition_time,
                                                                            latitude = cleanLatitude,
                                                                            longitude = cleanLongitude, 
                                                                            altitude = cleanAltitude)
        else:
            dataProduct.user_position.latitude = cleanLatitude
            dataProduct.user_position.longitude = cleanLongitude
            dataProduct.user_position.altitude = cleanAltitude
            dataProduct.user_position.save()
        dataProduct.save()

def editInstrumentData(request, instrument_name, pk):
    form = ImportInstrumentDataForm()
    errors = form.errors
    return render(
        request,
        'xgds_instrument/editInstrumentData.html',
        {
            'form': form,
            'errorstring': errors,
        },
    )


def instrumentDataImport(request):
    errors = None
    status = httplib.OK
    if request.method == 'POST':
        form = ImportInstrumentDataForm(request.POST, request.FILES)
        if form.is_valid():
            instrument = form.cleaned_data["instrument"]
            importFxn = lookupImportFunctionByName(
                settings.XGDS_INSTRUMENT_IMPORT_MODULE_PATH,
                instrument.dataImportFunctionName)
            object_id = None
            if 'object_id' in form.cleaned_data:
                object_id = int(form.cleaned_data['object_id'])
            return importFxn(instrument=instrument,
                             portableDataFile=request.FILES["portableDataFile"],
                             manufacturerDataFile=request.FILES["manufacturerDataFile"],
                             utcStamp=form.cleaned_data["dataCollectionTime"],
                             timezone=form.getTimezone(),
                             vehicle=form.getVehicle(),
                             user=request.user,
                             latitude=form.cleaned_data['lat'],
                             longitude=form.cleaned_data['lon'],
                             altitude=form.cleaned_data['alt'],
                             collector=form.cleaned_data["collector"],
                             object_id=object_id)
        else:
            errors = form.errors
            status = status=httplib.NOT_ACCEPTABLE
    else:
        form = ImportInstrumentDataForm()
    return render(
        request,
        'xgds_instrument/importInstrumentData.html',
        {
            'form': form,
            'errorstring': errors,
            'instrumentDataImportUrl': reverse('instrument_data_import'),
            'instrumentType': 'Science Instruments'
        },
        status=status
    )


def getInstrumentDataJson(request, productModel, productPk):
    INSTRUMENT_DATA_PRODUCT_MODEL = LazyGetModelByName(productModel)
    dataProduct = get_object_or_404(INSTRUMENT_DATA_PRODUCT_MODEL.get(), pk=productPk)
    sampleList = dataProduct.samples
    return HttpResponse(json.dumps(sampleList), content_type='application/json')


def getInstrumentDataCsvResponse(request, productModel, productPk):
    INSTRUMENT_DATA_PRODUCT_MODEL = LazyGetModelByName(productModel)
    dataProduct = get_object_or_404(INSTRUMENT_DATA_PRODUCT_MODEL.get(), pk=productPk)
    filename, dataframe = dataProduct.getInstrumentDataCsv()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=' + filename
    dataframe.to_csv(response, index=False)
    return response
