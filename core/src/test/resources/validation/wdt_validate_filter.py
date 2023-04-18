# Copyright (c) 2018, 2021, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
#  This is a WDT filter for handling WLS configuration overrides.
#

def filter_model(model):
  if 'domainInfo' in model:
    model['domainInfo']['AdminPassword'] = 'gumby1234'
