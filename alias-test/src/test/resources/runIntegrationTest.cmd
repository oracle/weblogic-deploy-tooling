SET VERSION=12213
SET WLS_VERSION=12.2.1.3.0
SET PORT=7001

SET TEST_HOME=c:\Users\crountre\workspace\weblogic-deploy-tooling\alias-test\src\test
SET PYTHON_HOME=c:\jython2.7.2
@REM SET JAVA_HOME=d:\jcs1036\jdk1.7.0_80
SET JAVA_HOME=\jdk1.8.0_201
@REM SET JAVA_HOME=\jdk-11.0.4
@REM SET JAVA_HOME=C:\weblogic\dev\auto_download\x86_64\jdk180211b12\jdk1.8.0_211
SET BASE_HOME=C:\oracle\wls
SET ORACLE_HOME=%BASE_HOME%%VERSION%
@REM SET ORACLE_HOME=C:\Users\crountre\src123100_build\Oracle_Home
@REM SET ORACLE_HOME=D:\jcs1036\mwhome
@REM SET WLST_PATH_DIR=%ORACLE_HOME%\oracle_common
@REM SET WLST_PATH_DIR=%ORACLE_HOME%\wlserver_10.3
SET DOMAIN_HOME=%ORACLE_HOME%\user_projects\domains\system_test_domain
SET TESTFILES=c:\Users\crountre\temp\testfiles-12.2.1.4
SET ADMIN_USER=weblogic
SET ADMIN_PASSWORD=welcome1
SET ADMIN_URL=t3://localhost:7001
SET WLSDEPLOY_HOME=c:\Users\crountre\temp\weblogic-deploy

echo "%TEST_HOME%\resources\doGenerateSC.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -testfiles_path %TESTFILES% -admin_user %ADMIN_USER% -admin_pass %ADMIN_PASSWORD% -admin_url %ADMIN_URL%"
CALL %TEST_HOME%\resources\doGenerateSC.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -testfiles_path %TESTFILES% -admin_user %ADMIN_USER% -admin_pass %ADMIN_PASSWORD% -admin_url %ADMIN_URL%

echo "%TEST_HOME%\resources\doGenerateOnline.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -testfiles_path %TESTFILES% -admin_user %ADMIN_USER% -admin_pass %ADMIN_PASSWORD% -admin_url %ADMIN_URL%"
CALL %TEST_HOME%\resources\doGenerateOnline.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -testfiles_path %TESTFILES% -admin_user %ADMIN_USER% -admin_pass %ADMIN_PASSWORD% -admin_url %ADMIN_URL%

echo "%TEST_HOME%\resources\doVerifyOnline.cmd -testfiles_path %TESTFILES% -wls_version %WLS_VERSION%"
CALL %TEST_HOME%\resources\doVerifyOnline.cmd -testfiles_path %TESTFILES% -wls_version %WLS_VERSION%

echo "%TEST_HOME%\resources\doGenerateOffline.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -testfiles_path %TESTFILES% -admin_user %ADMIN_USER% -admin_pass %ADMIN_PASSWORD% -admin_url %ADMIN_URL%"
CALL %TEST_HOME%\resources\doGenerateOffline.cmd -oracle_home %ORACLE_HOME% -domain_home %DOMAIN_HOME% -testfiles_path %TESTFILES% -admin_user %ADMIN_USER% -admin_pass %ADMIN_PASSWORD% -admin_url %ADMIN_URL%

echo "%TEST_HOME%\resources\doVerifyOffline.cmd -testfiles_path %TESTFILES% -wls_version %WLS_VERSION%"
CALL %TEST_HOME%\resources\doVerifyOffline.cmd -testfiles_path %TESTFILES% -wls_version %WLS_VERSION%

