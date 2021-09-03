@ECHO OFF
@rem **************************************************************************
@rem createDomain.cmd
@rem
@rem Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       createDomain.cmd - WLS Deploy tool to create empty domains.
@rem
@rem     DESCRIPTION
@rem       This script creates domains with basic servers, clusters, and
@rem       machine configuration as specified by the model and the domain
@rem       templates.  Any domain types requiring RCU schemas will require
@rem       the RCU schemas to exist before running this script.
@rem
@rem This script uses the following variables:
@rem
@rem JAVA_HOME             - The location of the JDK to use.  The caller must set
@rem                         this variable to a valid Java 7 (or later) JDK.
@rem
@rem WLSDEPLOY_HOME        - The location of the WLS Deploy installation.
@rem                         If the caller sets this, the callers location will be
@rem                         honored provided it is an existing directory.
@rem                         Otherwise, the location will be calculated from the
@rem                         location of this script.
@rem
@rem WLSDEPLOY_PROPERTIES  - Extra system properties to pass to WLST.  The caller
@rem                         can use this environment variable to add additional
@rem                         system properties to the WLST environment.
@rem

SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=createDomain

SET SCRIPT_NAME=%~nx0
SET SCRIPT_ARGS=%*
SET SCRIPT_PATH=%~dp0
FOR %%i IN ("%SCRIPT_PATH%") DO SET SCRIPT_PATH=%%~fsi
IF %SCRIPT_PATH:~-1%==\ SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

call "%SCRIPT_PATH%\shared.cmd" :checkArgs %SCRIPT_ARGS%
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

SET MIN_JDK_VERSION=7
if "%USE_ENCRYPTION%" == "true" (
  SET MIN_JDK_VERSION=8
)

@rem required Java version is dependent on use of encryption
call "%SCRIPT_PATH%\shared.cmd" :javaSetup %MIN_JDK_VERSION%
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

call "%SCRIPT_PATH%\shared.cmd" :runWlst create.py
SET RETURN_CODE=%ERRORLEVEL%

:done
set SHOW_USAGE=false
if %RETURN_CODE% == 100 set SHOW_USAGE=true
if %RETURN_CODE% == 99 set SHOW_USAGE=true
if "%SHOW_USAGE%" == "false" (
    GOTO exit_script
)

:usage
ECHO.
ECHO Usage: %SCRIPT_NAME% [-help] [-use_encryption] [-run_rcu]
ECHO              [-oracle_home ^<oracle_home^>]
ECHO              [-domain_parent ^<domain_parent^> ^| -domain_home ^<domain_home^>]
ECHO              -domain_type ^<domain_type^>
ECHO              [-java_home ^<java_home^>]
ECHO              [-archive_file ^<archive_file^>]
ECHO              [-model_file ^<model_file^>]
ECHO              [-variable_file ^<variable_file^>]
ECHO              [-passphrase_env ^<passphrase_env^>]
ECHO              [-passphrase_file ^<passphrase_file^>]
ECHO              [-opss_wallet_passphrase_env ^<opss_wallet_passphrase_env^>]
ECHO              [-opss_wallet_passphrase_file ^<opss_wallet_passphrase_file^>]
ECHO              [-wlst_path ^<wlst_path^>]
ECHO              [-rcu_db ^<rcu_database^>
ECHO               -rcu_prefix ^<rcu_prefix^>
ECHO               -rcu_db_user ^<rcu_db_user^>
ECHO              ]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This is required unless the ORACLE_HOME environment
ECHO                           variable is set.
ECHO.
ECHO         domain_parent   - the parent directory where the domain should be created.
ECHO                           The domain name from the model will be appended to this
ECHO                           location to become the domain home.
ECHO.
ECHO         domain_home     - the full directory where the domain should be created.
ECHO                           This is used in cases where the domain name is different
ECHO                           from the domain home directory name.
ECHO.
ECHO         domain_type     - the type of domain (e.g., WLS, JRF).  This controls
ECHO                           the domain templates and template resource targeting.
ECHO                           Also used to locate wlst.cmd if -wlst_path not specified.
ECHO.
ECHO         java_home       - the Java Home to use for the new domain.  If not
ECHO                           specified, it defaults to the value of the JAVA_HOME
ECHO                           environment variable.
ECHO.
ECHO         archive_file    - the path to the archive file to use.  If the -model_file
ECHO                           argument is not specified, the model file in this archive
ECHO                           will be used.  This can also be specified as a
ECHO                           comma-separated list of archive files.  The overlapping contents in
ECHO                           each archive take precedence over previous archives in the list.
ECHO.
ECHO         model_file      - the location of the model file to use.  This can also be specified as a
ECHO                           comma-separated list of model locations, where each successive model
ECHO                           layers on top of the previous ones.
ECHO.
ECHO         variable_file   - the location of the property file containing the values for variables used in
ECHO                           the model. This can also be specified as a comma-separated list of property files,
ECHO                           where each successive set of properties layers on top of the previous ones.
ECHO.
ECHO         passphrase_env  - An alternative to entering the encryption passphrase at a prompt. The value is an
ECHO                           ENVIRONMENT VARIABLE name that WDT will use to retrieve the passphrase.
ECHO.
ECHO         passphrase_file - An alternative to entering the encryption passphrase at a prompt. The value is a
ECHO                           the name of a file with a string value which WDT will read to retrieve the passphrase.
ECHO.
ECHO         opss_wallet_passphrase_env  - An alternative to entering the OPSS wallet passphrase at a prompt. The value is a
ECHO                           ENVIRONMENT VARIABLE name that WDT will use to retrieve the passphrase.
ECHO.
ECHO         opss_wallet_passphrase_file - An alternative to entering the OPSS wallet passphrase at a prompt. The value is a
ECHO                           the name of a file with a string value which WDT will read to retrieve the passphrase.
ECHO.
ECHO         wlst_path       - the Oracle Home subdirectory of the wlst.cmd
ECHO                           script to use (e.g., ^<ORACLE_HOME^>\soa).
ECHO.
ECHO         rcu_database    - the RCU database connect string (if the domain
ECHO                           type requires RCU).
ECHO.
ECHO         rcu_prefix      - the RCU prefix to use (if the domain type requires
ECHO                           RCU).
ECHO.
ECHO         rcu_db_user    - the RCU dbUser to use (if the domain type requires
ECHO                           RCU.  Default SYS if not specified).  This user must have SYSDBA privilege
ECHO.
ECHO    The -use_encryption switch tells the program that one or more of the
ECHO    passwords in the model or variables files are encrypted.  The program will
ECHO    prompt for the decryption passphrase to use to decrypt the passwords.
ECHO    Please note that Java 8 or higher is required when using this feature.
ECHO.
ECHO    The -run_rcu switch tells the program to run RCU to create the database
ECHO    schemas specified by the domain type using the specified RCU prefix.
ECHO    Running RCU will drop any existing schemas with the same RCU prefix
ECHO    if they exist prior to trying to create them so be forewarned.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
