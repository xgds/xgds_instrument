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

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from xgds_instrument.forms import ImportInstrumentDataForm

def lookupImportFunctionByName(moduleName, functionName):
    importModule = __import__(moduleName)
    function = getattr(getattr(importModule, moduleName.split(".")[-1]),
                       functionName)
    return function

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
    return render(
        request,
        'xgds_instrument/importInstrumentData.html',
        {
            'form': ImportInstrumentDataForm(),
            'errorstring': errors
        },
    )
