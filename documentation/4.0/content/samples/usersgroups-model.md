---
title: "Modeling WebLogic users, groups, roles, and policies"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 6
description: "Establishing users, groups, global roles, and policies as part of WebLogic domain creation."
---


WebLogic Server has the ability to establish a set of users, groups, global roles, and policies as part of the WebLogic
domain creation. The users and groups become part of the Embedded LDAP server (for example, `DefaultAuthenticator`) and
are specified under `topology` in the `Security` section.  The WebLogic global roles become part of the WebLogic role
mapper (for example, `XACMLRoleMapper`) and are specified under `domainInfo` in the `WLSRoles` section.  The WebLogic
policies become part of the WebLogic authorizer (that is, `XACMLAuthorizer`).


#### WebLogic users and groups
The model allows for the definition of a set of users and groups that will be loaded into the WebLogic Embedded LDAP
Server (for example, `DefaultAuthenticator`). New groups can be specified and users can be added as members of the new
groups or existing groups, such as the `Administrators` group, which is defaulted to be in the WebLogic `Admin` global
role.  For additional information on users and groups, see [Known Limitations]({{< relref "#known-limitations" >}}).

You can specify the user password with a placeholder or encrypt it with the
[Encrypt Tool]({{< relref "/userguide/tools/encrypt.md" >}}). An example `Security` section that adds an additional
group `AppMonitors`, adds two new users and places the users into groups is shown in the example.  You can add user
attributes that are defined for the DefaultAuthenticator. This is a limited set of attributes that go under a separate
folder `UserAttribute` in the model under the `User` section.

```yaml
topology:
  Security:
    Group:
      AppMonitors:
        Description: Application Monitors
    User:
      john:
         Password: welcome1
         GroupMemberOf: [ AppMonitors, Administrators ]
      joe:
         Password: welcome1
         GroupMemberOf: [ AppMonitors ]
         UserAttribute:
             mail: joe@mycompany.com
```

#### WebLogic global roles
The model allows for the definition of WebLogic roles that can augment the well-known WebLogic global roles (for
example, `Admin`, `Deployer`, `Monitor`, and such) in addition to defining new roles. When updating the well-known WebLogic
roles, you can specify an `UpdateMode` as `{ append | prepend | replace }` with the default being `replace` when not
specified. Also, when updating the well-known roles, the specified `Expression` will be a logical `OR` with the default
expression. The `Expression` value for the role is the same as when using the WebLogic `RoleEditorMBean` for a WebLogic
security role mapping provider.

For example, the `WLSRoles` section below updates the well-known `Admin`, `Deployer` and `Monitor` roles while adding a
new global role with `Tester` as the role name:

```yaml
domainInfo:
  WLSRoles:
    Admin:
      UpdateMode: append
      Expression: "?weblogic.entitlement.rules.IDCSAppRoleName(AppAdmin,@@PROP:AppName@@)"
    Deployer:
      UpdateMode: replace
      Expression: "?weblogic.entitlement.rules.AdministrativeGroup(@@PROP:Deployers@@)"
    Monitor:
      UpdateMode: prepend
      Expression: "?weblogic.entitlement.rules.AdministrativeGroup(AppMonitors)"
    Tester:
      Expression: "?weblogic.entitlement.rules.IDCSAppRoleName(AppTester,@@PROP:AppName@@)"
```

The `Admin` role will have the expression appended to the default expression, the `Deployer` role expression will
replace the default, the `Monitor` role expression will be prepended to the default expression and `Tester` will be a
new role with the specified expression.

In addition, the `Expression` value can use the variable placeholder syntax specified when running the
[Create Tool]({{< relref "/userguide/tools/create.md" >}}) as shown in the previous example.

#### WebLogic policies
The model allows for the definition of additional authorization policies on WebLogic resources.  Note that WDT does not
currently support editing the default authorization policies shipped out of the box.  

To define a new policy for a particular resource, you must make up a logical name for the policy and provide the
`ResourceID` and `Policy` expression fields as shown in the example.  Note that this name is important should you want
to use multiple model files were one file needs to override the policy defined in an earlier model.

```yaml
domainInfo:
  WLSPolicies:
    MyQueueSendPolicy:
      ResourceID: 'type=<jms>, application=MyJmsModule, destinationType=queue, resource=MyQueue, action=send'
      Policy: 'Grp(Administrators)|Grp(Operators)|Grp(Monitors)'
```

To determine the correct `ResourceID` and `Policy` model values for a policy, try using the 
[WebLogic Remote Console](https://oracle.github.io/weblogic-remote-console/) and its Security Data Tree to create the
desired policy and then use the Advanced tab to view the `Resource Id` and `Policy` field values.  The value of these
fields in the WebLogic Remote Console can be copied directly into the `ResourceID` and `Policy` attributes in the model.
Don't forget that the values of these fields may need to be enclosed in quotes in the YAML model. 

#### Known limitations

- The processing of users, groups, and roles will only take place when using the [Create Domain Tool]({{< relref "/userguide/tools/create.md" >}}).
- WebLogic global roles are only supported with WebLogic Server version 12.2.1 or greater.
- WebLogic global roles are only updated for the WebLogic security XACML role mapping provider (for example, `XACMLRoleMapper`).
- The user and group processing is not complete, currently, users cannot be assigned to groups. Users created using the `Security` section are automatically added to the `Administrators` group and are not added to the groups specified. For information about a patch for this issue, see [Known issues]({{< relref "/release-notes#assigning-security-groups-to-users" >}}).
- Currently, WDT does not support modifying the default WebLogic authorization policies. 