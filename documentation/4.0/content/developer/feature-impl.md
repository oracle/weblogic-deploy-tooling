---
title: "Feature implementation"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
---
This document describes how specific features of WebLogic Deploy Tooling are implemented in the source code.

#### Creator and Deployer class hierarchies

The creation of individual folders and attributes within the `topology` section of the domain model is accomplished using subclasses of the Jython class `Creator`, in the module `wlsdeploy.tool.create.creator.py`.  The `Creator` class provides base methods to recurse through nested folders in the domain model, create or update those folders, and set or update their attributes. Each subclass can override these methods to account for variations in behavior for different functional areas.

For example, the `SecurityProviderCreator` subclass overrides the method `_create_named_subtype_mbeans` with special processing to remove all existing security providers, and re-create them from the data in the model.

The update of folders and attributes in the `resources` section of the domain model follows a similar pattern, but the base class for these modules is `Deployer` in the module `wlsdeploy.tool.deploy.deployer.py`.

The class `TopologyUpdater` is a special subclass of `Deployer` that is used to update elements in the `topology` section after their initial creation.
