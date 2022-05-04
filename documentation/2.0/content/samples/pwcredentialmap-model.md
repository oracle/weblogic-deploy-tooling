---
title: "Modeling WebLogic user password credential mapping"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 7
description: "A model for creating user password credential mappings."
---



The Create Domain Tool can be used to create user password credential mappings for use with the `DefaultCredentialMapper` security provider.
Information in the model will be used to create a credential mapping file that will be imported the first time the Administration Server is started. This example shows how mappings are represented in the model:
```yaml
domainInfo:
   WLSUserPasswordCredentialMappings:
       CrossDomain:
           map1:
               RemoteDomain: otherDomain
               RemoteUser: otherUser
               RemotePassword: '@@PROP:other.pwd@@'
       RemoteResource:
           map2:
               Protocol: http
               RemoteHost: remote.host
               RemotePort: 7020
               Path: /app/buy
               Method: POST
               User: user1
               RemoteUser: remoteUser
               RemotePassword: '@@PROP:remote.pwd@@'
           map3:
               Protocol: https
               RemoteHost: remote2.host
               RemotePort: 7030
               Path: /app/sell
               Method: GET
               User: user1,user2
               RemoteUser: remoteUser2
               RemotePassword: '@@PROP:remote2.pwd@@'
```
In this example, the mapping `map1` creates a cross-domain credential mapping that provides access from this domain to the remote domain `otherDomain` as the user `otherUser` with the configured password.

The mapping `map2` creates a remote resource credential mapping that will give the local user `user1` access to a single remote resource on `remote.host` as the user `remoteUser` with the configured password. The mapping `map3` is similar, but provides access to a different remote resource for two local users, `user1` and `user2`.

The names of the mapping sections in the model, such as `map1` and `map2`, are used to group the attributes for each mapping in the model and are not part of the resulting credential mappings. These names should be unique for each mapping of a particular type.
