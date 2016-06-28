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

import json
import csv
import pytz

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404, HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth.decorators import login_required
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


@login_required
def instrumentDataImport(request):
    errors = None
    if request.method == 'POST':
        form = ImportInstrumentDataForm(request.POST, request.FILES)
        if form.is_valid():
            instrument = form.cleaned_data["instrument"]
            importFxn = lookupImportFunctionByName(
                settings.XGDS_INSTRUMENT_IMPORT_MODULE_PATH,
                instrument.dataImportFunctionName)
            return importFxn(instrument, request.FILES["portableDataFile"],
                             request.FILES["manufacturerDataFile"],
                             form.cleaned_data["dataCollectionTime"],
                             form.getTimezone(), form.getResource(),
                             request.user)
        else:
            errors = form.errors
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
    )


def getInstrumentDataJson(request, productModel, productPk):
    INSTRUMENT_DATA_PRODUCT_MODEL = LazyGetModelByName(productModel)
    dataProduct = get_object_or_404(INSTRUMENT_DATA_PRODUCT_MODEL.get(), pk=productPk)
    sampleList = dataProduct.samples
    return HttpResponse(json.dumps(sampleList), content_type='application/json')


def getInstrumentDataCsv(request, productModel, productPk):
    INSTRUMENT_DATA_PRODUCT_MODEL = LazyGetModelByName(productModel)
    dataProduct = get_object_or_404(INSTRUMENT_DATA_PRODUCT_MODEL.get(), pk=productPk)
    sampleList = dataProduct.samples
    labels = settings.XGDS_MAP_SERVER_JS_MAP[dataProduct.instrument.displayName]['plotLabels']
    stringtime = dataProduct.acquisition_time.astimezone(pytz.timezone(dataProduct.acquisition_timezone)).strftime('%Y_%m_%d_%H%M')
    filename = "%s_%s.csv" % (dataProduct.instrument.displayName, stringtime) 
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=' + filename

    csvWriter = csv.writer(response, quoting=csv.QUOTE_NONNUMERIC)
    csvWriter.writerow(labels)
    for s in sampleList:
        csvWriter.writerow(s)
        
    return response
