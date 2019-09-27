/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.util.BitSet;

import oracle.weblogic.deploy.logging.PlatformLogger;

import org.antlr.v4.runtime.DiagnosticErrorListener;
import org.antlr.v4.runtime.Parser;
import org.antlr.v4.runtime.RecognitionException;
import org.antlr.v4.runtime.Recognizer;
import org.antlr.v4.runtime.atn.ATNConfigSet;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.misc.Interval;

/**
 * The common listener code shared between the JSON and YAML parsers.
 */
public abstract class ParsingErrorListener  extends DiagnosticErrorListener {

    private String fileName;
    private int errorCount;

    protected ParsingErrorListener(String fileName) {
        super();
        this.fileName = fileName;
    }

    protected ParsingErrorListener(String fileName, boolean exactOnly) {
        super(exactOnly);
        this.fileName = fileName;
    }

    protected abstract PlatformLogger getLogger();

    /**
     * Get the error count associated with this parse.
     *
     * @return the error count
     */
    public int getErrorCount() {
        return errorCount;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void syntaxError(Recognizer<?, ?> recognizer, Object offendingSymbol, int line, int charPositionInLine,
        String msg, RecognitionException e) {
        errorCount++;

        getLogger().severe("WLSDPLY-18018", e, fileName, line, charPositionInLine, msg);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void reportAmbiguity(Parser recognizer, DFA dfa, int startIndex,
        int stopIndex, boolean exact, BitSet ambigAlts, ATNConfigSet configs) {

        if (exactOnly && !exact) {
            return;
        }

        String decision = getDecisionDescription(recognizer, dfa);
        BitSet conflictingAlts = getConflictingAlts(ambigAlts, configs);
        String text = recognizer.getTokenStream().getText(Interval.of(startIndex, stopIndex));
        getLogger().warning("WLSDPLY-18019", decision, conflictingAlts, text, fileName);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void reportAttemptingFullContext(Parser recognizer, DFA dfa, int startIndex,
        int stopIndex, BitSet conflictingAlts, ATNConfigSet configs) {

        String decision = getDecisionDescription(recognizer, dfa);
        String text = recognizer.getTokenStream().getText(Interval.of(startIndex, stopIndex));
        getLogger().warning("WLSDPLY-18020", decision, text, fileName);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void reportContextSensitivity(Parser recognizer, DFA dfa, int startIndex,
        int stopIndex, int prediction, ATNConfigSet configs) {

        String decision = getDecisionDescription(recognizer, dfa);
        String text = recognizer.getTokenStream().getText(Interval.of(startIndex, stopIndex));
        getLogger().warning("WLSDPLY-18021", decision, text, fileName);
    }
}
