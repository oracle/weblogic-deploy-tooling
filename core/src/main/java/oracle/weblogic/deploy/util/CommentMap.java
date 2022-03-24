/*
 * Copyright (c) 2022, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Maps dictionary keys to lists of comments, for use in output formatting.
 */
public class CommentMap {
    public static final String BLANK_LINE_KEY = "__BLANK_LINE__";

    private final Map<String, List<String>> internalCommentMap = new HashMap<>();

    public void addBlankLine(String key) {
        getOrCreateComments(key).add(BLANK_LINE_KEY);
    }

    public void addComment(String key, String comment) {
        getOrCreateComments(key).add(comment);
    }

    public List<String> getComments(String key) {
        List<String> comments = internalCommentMap.get(key);
        return (comments == null) ? Collections.<String>emptyList() : comments;
    }

    private List<String> getOrCreateComments(String key) {
        List<String> comments = internalCommentMap.get(key);
        if(comments == null) {
            comments = new ArrayList<>();
            internalCommentMap.put(key, comments);
        }
        return comments;
    }
}
