@ECHO OFF
@rem **************************************************************************
@rem discoverDomain.cmd
@rem
@rem Copyright (c) 2017, 2024, Oracle and/or its affiliates.
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
ECHO              [-domain_home ^<domain_home^>]
ECHO              -model_file ^<model_file^>
ECHO              ^<-archive_file ^<archive_file^> ^| -skip_archive ^| -remote ^>
ECHO              [-variable_file ^<variable_file^>]
ECHO              [-domain_type ^<domain_type^>]
ECHO              [-wlst_path ^<wlst_path^>]
ECHO              [-java_home ^<java_home^>]
ECHO              [-target ^<target^>
ECHO               -output_dir ^<output_dir^>
ECHO              ]
ECHO              [-admin_url ^<admin_url^>
ECHO               -admin_user ^<admin_user^>
ECHO               -admin_pass_env ^<admin_pass_env^> ^| -admin_pass_file ^<admin_pass_file^>
ECHO              ]
ECHO              [-ssh_host ^<ssh_host^>
ECHO               -ssh_port ^<ssh_port^>
ECHO               -ssh_user ^<ssh_user^>
ECHO               -ssh_pass ^<ssh_pass^>
ECHO               -ssh_pass_env ^<ssh_pass_env^> ^| -ssh_pass_file ^<ssh_pass_file^> ^| -ssh_pass_prompt
ECHO               -ssh_private_key ^<ssh_private_key^>
ECHO               -ssh_private_key_pass_env ^<ssh_private_key_pass_env^> ^| -ssh_private_key_pass_file ^<ssh_private_key_pass_file^> ^| -ssh_private_key_pass_prompt
ECHO               -remote_oracle_home ^<remote_oracle_home^>
ECHO            ]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This argument is required unless the ORACLE_HOME
ECHO                           environment variable is set.
ECHO.
ECHO         domain_home     - the domain home directory.  This argument is
ECHO                           required if running in offline mode.
ECHO.
ECHO         model_file      - the location to write the model file.  This argument
ECHO                           is required.
ECHO.
ECHO         archive_file    - the path to the archive file to use.
ECHO.
ECHO         variable_file   - the location of the variable file to write properties
ECHO                           with the variable injector. If this argument is used,
ECHO                           by default all the credentials in the discovered model
ECHO                           will be replaced by a token and a property written to
ECHO                           this file.
ECHO.
ECHO         domain_type     - the type of domain (e.g., WLS, JRF).
ECHO                           used to locate wlst.cmd if -wlst_path not specified.
ECHO.
ECHO         wlst_path       - the Oracle Home subdirectory of the wlst.cmd
ECHO                           script to use (e.g., ^<ORACLE_HOME^>\soa).
ECHO.
ECHO         java_home       - overrides the JAVA_HOME value when discovering domain
ECHO                           values to be replaced with the java home global token.
ECHO.
ECHO         target          - the target output type. The default is wko.
ECHO.
ECHO         output_dir      - output directory for -target ^<target^>.
ECHO.
ECHO         admin_url       - the admin server URL (used for online discovery).
ECHO.
ECHO         admin_user      - the admin username (used for online discovery).
ECHO.
ECHO         admin_pass_env  - An alternative to entering the admin password at a
ECHO                           prompt. The value is an ENVIRONMENT VARIABLE name
ECHO                           that WDT will use to retrieve the password.
ECHO.
ECHO         admin_pass_file - An alternative to entering the admin password at a
ECHO                           prompt. The value is the name of a file with a
ECHO                           string value which WDT will read to retrieve the
ECHO                           password.
ECHO.
ECHO         remote_oracle_home - the full path to the Oracle Home on the remote machine.
ECHO.
ECHO         ssh_host        - the host name for admin server when SSH protocol is used to collect resources
ECHO                           from the admin server host.
ECHO.
ECHO         ssh_port        - the SSH port number for the admin server host.
ECHO.
ECHO         ssh_user        - the SSH user name for the admin server host.
ECHO.
ECHO         ssh_pass_env    - An alternative to entering the SSH password at the prompt.  The value is specified
ECHO                           in an ENVIRONMENT VARIABLE name that WDT will use to retrieve the password
ECHO.
ECHO         ssh_pass_file   - An alternative to entering the SSH password at the prompt.  The value is the name of a
ECHO                           file with a string value which WDT will read to retrieve the password.
ECHO.
ECHO         ssh_pass_prompt - Prompt for the SSH password.
ECHO.
ECHO         ssh_private_key - the private key to use for connecting to the admin server host using SSH.
ECHO.
ECHO         ssh_private_key_pass_env - An alternative to entering the SSH private keystore password at the prompt.
ECHO                                    The value is specified in an ENVIRONMENT VARIABLE name that WDT will use
ECHO                                    to retrieve the password
ECHO.
ECHO         ssh_private_key_pass_file - An alternative to entering the SSH private keystore password at the prompt.
ECHO                                     The value is the name of a file with a string value which WDT will read
ECHO                                     to retrieve the password.
ECHO.
ECHO         ssh_private_key_pass_prompt - Prompt for the SSH private keystore password.
ECHO.
ECHO    The -skip_archive argument suppresses the generation of the archive file.
ECHO    If present, the -archive_file argument will be ignored and the file
ECHO    references in the model will be the names from the discovered domain's
ECHO    local file system.
ECHO.
ECHO    The -remote argument, which only works in online mode, tells WDT to discover
ECHO    the domain from a remote server.  Since there is no access to the remote
ECHO    server's file system, no archive file will be generated.  However, the file
ECHO    references in the model will contain the values pointing into the archive
ECHO    file (which the user must construct separately).  With this option, the
ECHO    -remote_oracle_home value should be the remote server's Oracle home path.  This
ECHO    allows discover domain to tokenize any file system references containing
ECHO    the Oracle home path.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
