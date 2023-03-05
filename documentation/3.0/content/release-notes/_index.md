+++
title = "Release Notes"
date = 2019-02-22T15:27:38-05:00
weight = 93
pre = "<b> </b>"
+++


### Changes in Release 3.0.2
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
None

#### Bug Fixes
- #1405: Corrected some issues with the Windows shell scripts where they were not properly handling paths with spaces.
- #1409: Corrected a bug where a wallet deprecation message was still being logged as a warning.
- #1411: Corrected a bug where wallet extraction handling with multiple archive files was happening in the wrong order.

#### Known Issues
1. When running `discoverDomain` with the `-remote` flag, there are several MBeans that are not being properly handled that
   will result in `INFO` level messages that look similar to the example shown below.  These errors seem to happen only when the MBean is
   non-existent so the resulting model should still be accurate.  These issues are expected to be fixed in a future release.

```
####<Feb 16, 2023 1:40:00 PM> <INFO> <Discoverer> <_add_to_dictionary> <WLSDPLY-06106> <Unable to add ServerFailureTrigger
from location /Clusters/mycluster/OverloadProtection/mycluster to the model : Failed to convert the wlst attribute name and
value for the model at location (model_folders = ['Cluster', 'OverloadProtection'],  'name_tokens' = {'DOMAIN': 'tododomain',
'CLUSTER': 'mycluster','OVERLOADPROTECTION': 'mycluster'}) : The wlst attribute ServerFailureTrigger is not defined for the
model folder /Cluster/OverloadProtection>
```
