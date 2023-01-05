---
title: "Modeling WebLogic users, groups, and roles"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 6
description: "Establishing users, groups, and global roles as part of WebLogic domain creation."
---


WebLogic Server has the ability to establish a set of users, groups, and global roles as part of the WebLogic domain creation. The WebLogic global roles become part of the WebLogic role mapper (for example, `XACMLRoleMapper`) and are specified under `domainInfo` in the `WLSRoles` section. The users and groups become part of the Embedded LDAP server (for example, `DefaultAuthenticator`) and are specified under `topology` in the `Security` section.

#### WebLogic global roles
The model allows for the definition of WebLogic roles that can augment the well known WebLogic global roles (for example, `Admin`, `Deployer`, `Monitor`, ...) in addition to defining new roles. When updating the well known WebLogic roles, an `UpdateMode` can be specified as `{ append | prepend | replace }` with the default being `replace` when not specified. Also, when updating the well known roles, the specified `Expression` will be a logical `OR` with the default expression. The `Expression` value for the role is the same as when using the WebLogic `RoleEditorMBean` for a WebLogic security role mapping provider.

For example, the `WLSRoles` section below updates the well known `Admin`, `Deployer` and `Monitor` roles while adding a new global role with `Tester` as the role name:

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

The `Admin` role will have the expression appended to the default expression, the `Deployer` role expression will replace the default, the `Monitor` role expression will be prepended to the default expression and `Tester` will be a new role with the specified expression.

In addition, the `Expression` value can use the variable placeholder syntax specified when running the [Create Tool]({{< relref "/userguide/tools/create.md" >}}) as shown in the above example.

#### WebLogic users and groups
The model allows for the definition of a set of users and groups that will be loaded into the WebLogic Embedded LDAP Server (for example, `DefaultAuthenticator`). New groups can be specified and users can be added as members of the new groups or existing groups such as the `Administrators` group which is defaulted to be in the WebLogic `Admin` global role. Please see Known Limitations below for additional information on users and groups.

The user password can be specified with a placeholder or encrypted with the [Encrypt Tool]({{< relref "/userguide/tools/encrypt.md" >}}). An example `Security` section that adds an additional group `AppMonitors`, adds two new users and places the users into groups is as follows:

You can add user attributes that are defined for the DefaultAuthenticator. This is a limited set of attributes that go under a separate folder `UserAttribute` in the model under the `User` section.
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

#### Known limitations

- The processing of users, groups, and roles will only take place when using the [Create Domain Tool]({{< relref "/userguide/tools/create.md" >}}).
- WebLogic global roles are only supported with WebLogic Server version 12.2.1 or greater.
- WebLogic global roles are only updated for the WebLogic security XACML role mapping provider (for example, `XACMLRoleMapper`).
- The user and group processing is not complete, currently, users cannot be assigned to groups. Users created using the `Security` section are automatically added to the `Administrators` group and are not added to the groups specified. For information about a patch for this issue, see [Known issues]({{< relref "/release-notes#assigning-security-groups-to-users" >}}).
