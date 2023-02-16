/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper;

import java.io.PrintWriter;
import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.ResourceBundle;

public class CommandResponse {
    private static final ResourceBundle RESOURCE_BUNDLE =
        ResourceBundle.getBundle("oracle.weblogic.deploy.messages.wlsdeploy_rb");

    private int status;
    private final List<String> messages = new ArrayList<>();
    private final List<Object[]> messageParamsList = new ArrayList<>();

    public CommandResponse(int status) {
        this.status = status;
    }

    public CommandResponse(int status, String message, Object... messageParams) {
        this.status = status;
        this.messages.add(message);
        this.messageParamsList.add(messageParams);
    }

    public int getStatus() {
        return status;
    }

    public void setStatus(int status) {
        this.status = status;
    }

    public String[] getMessages() {
        String[] formattedMessages = new String[this.messages.size()];

        for (int index = 0; index < this.messages.size(); index++) {
            String message = this.messages.get(index);
            if (RESOURCE_BUNDLE.containsKey(message)) {
                message = MessageFormat.format(RESOURCE_BUNDLE.getString(message), this.messageParamsList.get(index));
            }
            formattedMessages[index] = message;
        }
        return formattedMessages;
    }

    public void addMessage(String message, Object... messageParams) {
        this.messages.add(message);
        this.messageParamsList.add(messageParams);
    }

    public void addMessages(List<String> messages) {
        this.messages.addAll(messages);
        for (int i = 0; i < messages.size(); i++) {
            this.messageParamsList.add(new Object[0]);
        }
    }

    public void printMessages(PrintWriter out, PrintWriter err) {
        PrintWriter location = out;
        if (status != 0) {
            location = err;
        }

        for (String message : getMessages()) {
            location.println(message);
        }
    }
}
