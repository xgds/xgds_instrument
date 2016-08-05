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

"""
This app may define some new parameters that can be modified in the
Django settings module.  Let's say one such parameter is FOO.  The
default value for FOO is defined in this file, like this:

  FOO = 'my default value'

If the admin for the site doesn't like the default value, they can
override it in the site-level settings module, like this:

  FOO = 'a better value'

Other modules can access the value of FOO like this:

  from django.conf import settings
  print settings.FOO

Don't try to get the value of FOO from django.conf.settings.  That
settings object will not know about the default value!
"""

from geocamUtil.SettingsUtil import getOrCreateArray, getOrCreateDict

BOWER_INSTALLED_APPS = getOrCreateArray('BOWER_INSTALLED_APPS')
BOWER_INSTALLED_APPS += ['flot',
                         'flot-axislabels']

XGDS_INSTRUMENT_INSTRUMENT_MODEL = 'xgds_instrument.ScienceInstrument'
XGDS_INSTRUMENT_IMPORT_MODULE_PATH = 'xgds_instrument.instrumentDataImporters'
XGDS_INSTRUMENT_DATA_SUBDIRECTORY = "xgds_instrument/"

# Include a dictionary of name to url for imports if you wish to include import functionality
XGDS_DATA_IMPORTS = getOrCreateDict('XGDS_DATA_IMPORTS')
XGDS_DATA_IMPORTS["Science Instruments"]= '/xgds_instrument/instrumentDataImport'

SCIENCE_INSTRUMENT_DATA_IMPORTERS = []

XGDS_MAP_SERVER_JS_MAP = getOrCreateDict('XGDS_MAP_SERVER_JS_MAP')
# XGDS_MAP_SERVER_JS_MAP['InstrumentDataProduct'] = {'ol': 'xgds_instrument/js/olInstrumentDataProduct.js',
#                                                    'model': XGDS_INSTRUMENT_DATA_PRODUCT_MODEL,
#                                                    'hiddenColumns': []}