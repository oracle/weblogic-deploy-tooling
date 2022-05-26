@ECHO OFF
@rem **************************************************************************
@rem discoverDomain.cmd
@rem
@rem Copyright (c) 2017, 2021, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       discoverDomain.cmd - WLS Deploy tool to discover a domain.
@rem
@rem     DESCRIPTION
@rem       This script discovers the model of an existing domain and gathers
@rem       the binaries needed to recreate the domain elsewhere with all of
@rem       its applications and resources configured.
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

SET WLSDEPLOY_PROGRAM_NAME=discoverDomain

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

call "%SCRIPT_PATH%\shared.cmd" :runWlst discover.py
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
ECHO Usage: %SCRIPT_NAME% [-oracle_home ^<oracle_home^>]
ECHO              -domain_home ^<domain_home^>
ECHO              [-archive_file ^<archive_file^>]
ECHO              [-skip_archive]
ECHO              [-model_file ^<model_file^>]
ECHO              [-variable_file ^<variable_file^>]
ECHO              [-domain_type ^<domain_type^>]
ECHO              [-admin_pass_env ^<admin_pass_env^>]
ECHO              [-admin_pass_file ^<admin_pass_file^>]
ECHO              [-wlst_path ^<wlst_path^>]
ECHO              [-java_home ^<java_home^>]
ECHO              [-target ^<target^>
ECHO               -output_dir ^<output_dir^>
ECHO              ]
ECHO              [-admin_url ^<admin_url^>
ECHO               -admin_user ^<admin_user^>
ECHO              ]
ECHO.
ECHO     where:
ECHO         oracle_home    - the existing Oracle Home directory for the domain.
ECHO                          This is required unless the ORACLE_HOME environment
ECHO                          variable is set.
ECHO.
ECHO         domain_home    - the domain home directory
ECHO.
ECHO         archive_file   - the path to the archive file
ECHO.
ECHO         skip_archive   - do not generate an archive file. The archive_file option will be ignored. The file
ECHO                          references in the model are the local file names.
ECHO.
ECHO         remote         - Online only. Discover the remote domain. Do not generate an archive file. However, The file
ECHO                          references in the model are structured as if they are in an archive. A list of these files
ECHO                          will be generated.
ECHO.
ECHO         model_file     - the location to write the model file,
ECHO                          the default is to write it inside the archive
ECHO.
ECHO         variable_file  - the location to write properties for attributes that
ECHO                          have been replaced with tokens by the variable injector.
ECHO                          If this is included, all credentials will automatically
ECHO                          be replaced by tokens and the property written to this file.
ECHO.
ECHO         domain_type    - the type of domain (e.g., WLS, JRF).
ECHO                          used to locate wlst.cmd if -wlst_path not specified
ECHO.
ECHO         wlst_path      - the Oracle Home subdirectory of the wlst.cmd
ECHO                          script to use (e.g., ^<ORACLE_HOME^>\soa)
ECHO.
ECHO         java_home      - overrides the JAVA_HOME value when discovering
ECHO                          domain values to be replaced with the java home global token
ECHO.
ECHO         target         - targeting platform (k8s, etc.)
ECHO.
ECHO         output_dir     - output directory for -target ^<target^>
ECHO.
ECHO.
ECHO         admin_pass_env  - An alternative to entering the admin password at a prompt. The value is a ENVIRONMENT
ECHO                           VARIABLE name that WDT will use to retrieve the password.
ECHO.
ECHO         admin_pass_file - An alternative to entering the admin password at a prompt. The value is a the name of a
ECHO                           file that contains a password string that the tool will read to retrieve the password.
ECHO.
ECHO         admin_url      - the admin server URL (used for online discovery)
ECHO.
ECHO         admin_user     - the admin username (used for online discovery)
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
