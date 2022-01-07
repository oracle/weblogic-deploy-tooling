---
title: "Project structure"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 1
---

This project is structured using the Standard Directory Layout for Maven projects, with two child modules, `core` and `installer`. In addition, there is a `samples` directory with example configurations, and the `site` directory containing project documentation.

The `core` module contains the main source code for the project. This includes Jython modules and Java classes, as well as typedef files, alias definitions, and the message bundle. There are unit tests related to this module.

Alias definitions are discussed in more detail [here]({{< relref "/developer/alias-definitions.md" >}}).

The `installer` module builds the final installer ZIP file. It includes the assembly definitions, start scripts for each tool for Linux and Windows platforms, and configurations for variable injection and logging.

A single installer ZIP file is built under the `WLSDEPLOY_HOME/installer/target` directory.

There are detailed instructions for building the project [here]({{< relref "/developer/buildWDT.md" >}}).
