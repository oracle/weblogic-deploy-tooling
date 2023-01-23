/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool;

import java.io.PrintWriter;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.tool.archive_helper.add.AddCommand;
import oracle.weblogic.deploy.tool.archive_helper.list.ListCommand;
import oracle.weblogic.deploy.tool.archive_helper.remove.RemoveCommand;
import oracle.weblogic.deploy.util.ExitCode;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.IParameterExceptionHandler;
import picocli.CommandLine.Option;
import picocli.CommandLine.ParameterException;
import picocli.CommandLine.ParseResult;
import picocli.CommandLine.UnmatchedArgumentException;

@Command(
    name = "archiveHelper",
    description = "%nA tool to create and modify a WebLogic Deploy Tooling archive file.%n",
    commandListHeading = "%nCommands:%n",
    subcommands = {
        AddCommand.class,
        ListCommand.class,
        RemoveCommand.class
    },
    sortOptions = false
)
public class ArchiveHelper {
    public static final String LOGGER_NAME = "wlsdeploy.tool.archive-helper";
    private static final String CLASS = ArchiveHelper.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper tool",
        usageHelp = true
    )
    private static boolean helpRequested = false;

    @SuppressWarnings("java:S106")
    public static void main(String[] args) {
        final String METHOD = "main";
        LOGGER.entering(CLASS, METHOD, (Object[]) args);

        int exitCode = executeCommand(new PrintWriter(System.out, true),
            new PrintWriter(System.err, true), args);

        LOGGER.exiting(CLASS, METHOD, exitCode);
        System.exit(exitCode);
    }

    static int executeCommand(PrintWriter out, PrintWriter err, String... args) {
        CommandLine cmd = new CommandLine(ArchiveHelper.class)
            .setCaseInsensitiveEnumValuesAllowed(true)
            .setToggleBooleanFlags(false)
            .setUnmatchedArgumentsAllowed(false)
            .setTrimQuotes(true)
            //.setColorScheme(CommandLine.Help.defaultColorScheme(CommandLine.Help.Ansi.AUTO))
            .setParameterExceptionHandler(new ArgParsingExceptionHandler())
            .setOut(out)
            .setErr(err);

        int exitCode = cmd.execute(args);
        if (exitCode != ExitCode.USAGE_ERROR) {
            CommandLine commandLine = getResponseCommandLine(cmd);
            CommandResponse response = commandLine.getExecutionResult();
            if (response != null) {
                exitCode = response.getStatus();
                response.printMessages(out, err);
            }
        }
        return exitCode;
    }

    private static CommandLine getResponseCommandLine(CommandLine commandLine) {
        CommandLine result = commandLine;

        ParseResult parseResult = commandLine.getParseResult().subcommand();
        if (parseResult != null) {
            result = getResponseCommandLine(parseResult.commandSpec().commandLine());
        }
        return result;
    }

    static class ArgParsingExceptionHandler implements IParameterExceptionHandler {
        @Override
        public int handleParseException(ParameterException ex, String[] args) {
            CommandLine cmd = ex.getCommandLine();
            PrintWriter writer = cmd.getErr();

            writer.println(ex.getMessage());
            UnmatchedArgumentException.printSuggestions(ex, writer);
            ex.getCommandLine().usage(writer, cmd.getColorScheme());

            return ExitCode.USAGE_ERROR;
        }
    }
}
