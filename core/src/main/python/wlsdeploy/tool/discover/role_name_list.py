ROLE_NAME_LIST = {
    "AppTester": '?weblogic.entitlement.rules.OwnerIDDGroup(AppTesters)',
    'Operator':  '?weblogic.entitlement.rules.AdministrativeGroup(Operators)',
    'Admin':  '?weblogic.entitlement.rules.AdministrativeGroup(Administrators)',
    'Deployer':  '?weblogic.entitlement.rules.AdministrativeGroup(Deployers)',
    'Monitor':   '?weblogic.entitlement.rules.AdministrativeGroup(Monitors)',
    'OracleSystemRole': 'Grp(OracleSystemGroup)',
    'CrossDomainConnector':  '?weblogic.entitlement.rules.OwnerIDDGroup(CrossDomainConnectors)',
    'Anonymous':  'Grp(everyone)',
    'AdminChannelUser':  '?weblogic.entitlement.rules.OwnerIDDGroup(AdminChannelUsers)'

}