---
title: "Variable Injector Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 10
description: "Adds token to a model with variables."
---


The Variable Injector Tool is a standalone tool used to tokenize a model with variables. The values for these variables are written to an external variable properties file. This facilitates using the same domain model to create new domains in different environments. 

The Variable Injector Tool uses the default configuration for variable injectors. For more details about this configuration, see [Variable Injectors]({{% relref "/userguide/tools-config/variable_injectors.md" %}}).

In addition to variable injector processing, the tool will automatically tokenize any credential attributes found in the model. These variables associated with those attributes will be included in the variable properties file.


### Parameter table for `injectVariables`
| Parameter | Definition                                                                                                                                                                                                                                                                                                               | Default |
| ---- |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| ---- |
| `-archive_file` | The path to the archive file that contains a model in which the variables will be injected. If the `-model_file` argument is used, this argument will be ignored.                                                                                                                                                        |    |
| `-model_file` | The location of the model file in which variables will be injected. If not specified, the tool will look for the model in the archive file. Either the `-model_file` or the `-archive_file` argument must be provided.                                                                                                   |    |
| `-oracle_home` | Home directory for the Oracle WebLogic installation. This is required unless the `ORACLE_HOME` environment variable is set.                                                                                                                                                                                              |    |
| `-variable_injector_file` | The location of the variable injector file which contains the variable injector list for this model injection run. If this argument is not provided, the `model_variable_injector.json` file must exist in the `lib` directory in the `$WLSDEPLOY_HOME` location.                                                        |    |
| `-variable_file` | The location of the property file in which to store any variable names injected into the model. If this command-line argument is not specified, the variable will be located and named based on the model file name and location. If the file exists, the file will be updated with new variable values. |    |
