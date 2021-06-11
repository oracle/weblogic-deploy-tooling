---
title: "Model filters"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 1
---


WebLogic Deploy Tooling supports the use of model filters to manipulate the domain model. The Create Domain, Update Domain, and Deploy Applications Tools apply filters to the model after it is read, before it is validated and applied to the domain. The Discover Domain Tool applies filters to the model after it has been discovered, before the model is validated and written.

Model filters are written in Jython, and must be compatible with the version used in the corresponding version of WLST. A filter must implement the method `filter_model(model)`, which accepts as a single argument the domain model as a Jython dictionary. This method can make any adjustments to the domain model that are required. Filters can be stored in any directory, as long as they can be accessed by WebLogic Deploy Tooling.

The following filter example (`fix-password.py`) sets the password for two attributes in the `SecurityConfiguration` WLST folder.

```python
def filter_model(model):
   if model and 'topology' in model:
       if 'SecurityConfiguration' in model['topology']:
           model['topology']['SecurityConfiguration']['CredentialEncrypted'] = 'welcome1'
           model['topology']['SecurityConfiguration']['NodeManagerPasswordEncrypted'] = 'welcome1'
           print 'Replaced SecurityConfiguration password'
       else:
           print 'SecurityConfiguration not in the model'
```

Model filters are configured by creating a `model_filters.json` file in the `WLSDEPLOY_HOME/lib` directory. This file has separate sections for filters to be applied for specific tools.

Another option is to configure model filters in a [Custom configuration]({{< relref "/userguide/tools-config/custom_config.md" >}}) directory. Create the `model_filters.json` file in the `$WDT_CUSTOM_CONFIG` directory.

This example configures two filters for the Create Domain Tool: `fix-password.py` and `no-mail.py`, and one filter for the Discover Domain tool.

```json
{
  "create": [
    { "name": "fixPassword", "path": "/home/user/fix-password.py" },
    { "name": "noMail", "path": "/home/user/no-mail.py" }
  ],
  "deploy": [
  ],
  "discover": [
    { "name": "noMail", "path": "/home/user/no-mail.py" }
  ],
  "update": [
  ]
}
```
