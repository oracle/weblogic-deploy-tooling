@REM
@REM  VERSION     - version of oracle install.
@REM  RUN_HOME    - location of this script and the domain yaml, archive files
@REM  TEST_HOME   - workspace where the integration project will be cloned into from orahub
@REM  TESTFILES   - location to store the generated online json file
@REM  JAVA_HOME   - valid java version for the oracle install
@REM  BASE_HOME   - (optional) I use this as a directory and base name for all my oracle installs.
@REM  ORACLE_HOME - (don't set if BASE_HOME is set - BASE_HOME is concatenated with version) oracle install home          
@REM
@REM

SETLOCAL
SET VERSION=12214
SET RUN_HOME=C:\Users\crountre\temp\runscripts
SET TEST_HOME=c:\Users\crountre\workspace
SET TESTFILES=c:\Users\crountre\temp\testfiles-12.2.1.4
@REM SET JAVA_HOME=C:\jdk-11.0.4
@REM SET JAVA_HOME=D:\jcs1036\jdk1.7.0_80
SET JAVA_HOME=\jdk1.8.0_201
@REM SET JAVA_HOME=C:\weblogic\dev\auto_download\x86_64\jdk180211b12\jdk1.8.0_211

@REM in my environment, I name all my installs the same, with version and concatenate version
SET BASE_HOME=C:\oracle\wls
SET ORACLE_HOME=%BASE_HOME%%VERSION%

SET CREATE_YAML=%RUN_HOME%\system-test-domain.yaml
SET CREATE_ARCHIVE=%RUN_HOME%\system-test.zip
SET DOMAIN_TYPE=WLS
SET INTEGRATION_PROJECT=wls-deploy-integration-test
SET SOURCE_HOME=%TEST_HOME%\%INTEGRATION_PROJECT%\system-test\src\test
SET DOMAIN_HOME=%ORACLE_HOME%\user_projects\domains\system_test_domain
SET ADMIN_NAME=AdminServer
SET ADMIN_USER=weblogic
SET ADMIN_PASSWORD=welcome1
SET ADMIN_URL=t3://localhost:7001
SET WLSDEPLOY_HOME=%TESTFILES%\weblogic-deploy

@REM rmdir /Q /S %TEST_HOME%\%INTEGRATION_PROJECT%
@REM git clone git@orahub.oraclecorp.com:weblogic-cloud/wls-deploy-integration-test.git %TEST_HOME%\%INTEGRATION_PROJECT%

rmdir /S /Q %DOMAIN_HOME%
SETLOCAL
CALL %TESTFILES%\weblogic-deploy\bin\createDomain.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -model_file %CREATE_YAML% -archive_file %CREATE_ARCHIVE% -domain_type %DOMAIN_TYPE%
ENDLOCAL

ECHO.
ECHO start %ADMIN_NAME%
@REM SETLOCAL
@REM CALL %DOMAIN_HOME%\bin\setDomainEnv
@REM CALL %DOMAIN_HOME%\startWebLogic 
@REM ENDLOCAL

@REM childPID=$!
@REM echo "wait for admin to start"
@REM wait $childPID


@REM echo "%SOURCE_HOME%\resources\doGenerateOnline.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -testfiles_path %TESTFILES% -admin_user %ADMIN_USER% -admin_pass %ADMIN_PASSWORD% -admin_url %ADMIN_URL%"
@REM CALL %SOURCE_HOME%\resources\doGenerateOnline.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -testfiles_path %TESTFILES% -admin_user %ADMIN_USER% -admin_pass %ADMIN_PASSWORD% -admin_url %ADMIN_URL%
@REM ENDLOCAL


