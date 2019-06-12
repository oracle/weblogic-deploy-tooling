The following list are known issues. The issue may contain a work-around or an associated Issue number.

**ISSUE**:
   The createDomain and updateDomain tools cannot target non-JRF product resources to dynamic clusters because
   WebLogic WLST will not assign resources associated with extension or custom template user server groups
   to dynamic clusters. Resources associated to JRF user server groups defined in the domain typedef
   (i.e. JRF, RestrictedJRF) will be targeted to the dynamic cluster by the WDT tools using the FMW WLST function
   applyJRF.

   If you have only non-JRF user server groups targeted to a dynamic cluster, you will see the following message:

    WLSDPLY-12238: Unable to target non-JRF template server groups for domain type <your domain typedef> to dynamic cluster(s).

   You will not see this message if you have a mix of non-JRF and JRF user server groups targeted to the dynamic
   cluster. WDT cannot detect if a user server group is associated to JRF, and therefore, whether the applyJRF will
   target the user group resources to the dynamic cluster.

**ACTION**:

   You must contact WebLogic support to assist you with a solution for this targeting dilemma. You can perform
   the following action as a temporary work-around to the described issue.

   1. Add a configured managed server to your dynamic cluster and re-run the createDomain or updateDomain tool.
      The dynamic cluster becomes a "mixed" cluster once the managed server is added. When the WDT tool targets the
      user server groups to the configured managed server, the resources are automatically targeted to the cluster
      by WebLogic, which includes both the managed server and the dynamic servers.

**ISSUE**:
   The discoverDomain STDOUT contains many SEVERE messages about cd() and ls() when it is run against a 12.2.1 domain.
   The discover tool navigates through the domain MBeans using wlst to determine which MBeans are present in a
   domain. When it tests an MBean that is not present, the erroneous message is logged by Weblogic WLST.
   There is no 12.2.1 PSU available to address this WLST problem. It is resolved in 12.2.1.1.

**ACTION**:
   Ignore the following messages logged during discover of a 12.2.1 domain.

   ####<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: cd() failed.>
   ####<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: ls() failed.>


**ISSUE**:
   The createDomain tool cannot run rcu for 11g JRF domains. The tool will issue error messages in the log, and
   terminate the create process.

**ACTION**:
   Run RCU before executing createDomain for JRF domains
   
**ISSUE**:
   The discoverDomain or createDomain tool cannot handle object name with slashes and finished with  
   warnings.  For example:
   
    2. WLSDPLY-06140: Unable to cd to the expected path /SelfTuning/NO_NAME_0/WorkManager/wm/SOAWorkManager 
    constructed from location context model_folders = ['SelfTuning', 'WorkManager'],  'name_tokens' = 
    {'SELFTUNING': 'NO_NAME_0','DOMAIN': 'basesoa','WORKMANAGER': 'wm/SOAWorkManager'}; the current folder and 
    its sub-folders cannot be discovered : wlst.cd(/SelfTuning/NO_NAME_0/WorkManager/wm/SOAWorkManager) in 
    offline mode failed: com.oracle.cie.domain.script.ScriptException: No such element WorkManager named wm

   The reason for this warning is because of the slash(es) in the object name. In this case the object name is 
   wm/SOAWorkManager
   
**ACTION**:
   Contact Oracle Support to obtain the patch for the bug number 25790276 for your weblogic version 
   before running the tool.
      
