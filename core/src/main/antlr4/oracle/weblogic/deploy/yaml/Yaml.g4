/*
 * Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.
 * The Universal Permissive License (UPL), Version 1.0
 */
grammar Yaml;

tokens { INDENT, DEDENT }

@lexer::members {
    private java.util.LinkedList<Token> tokens = new java.util.LinkedList<>();
    private java.util.Deque<Integer> indents = new java.util.ArrayDeque<>();
    private Token lastToken = null;
    private int opened = 0;

    @Override
    public void emit(Token t) {
        super.setToken(t);
        tokens.offer(t);
    }

    @Override
    public Token nextToken() {
        // Check if the end-of-file is ahead and there are still some DEDENTS expected.
        if (_input.LA(1) == EOF && !this.indents.isEmpty()) {
            // Remove any trailing EOF tokens from our buffer.
            for (int i = tokens.size() - 1; i >= 0; i--) {
                if (tokens.get(i).getType() == EOF) {
                    tokens.remove(i);
                }
            }

            // First emit an extra line break that serves as the end of the statement.
            emit(commonToken(YamlParser.NEWLINE, System.lineSeparator()));

            // Now emit as much DEDENT tokens as needed.
            while (!indents.isEmpty()) {
                emit(createDedent());
                indents.pop();
            }

            // Put the EOF back on the token stream.
            emit(commonToken(YamlParser.EOF, "<EOF>"));
        }

        Token next = super.nextToken();

        if (next.getChannel() == Token.DEFAULT_CHANNEL) {
            // Keep track of the last token on the default channel.
            this.lastToken = next;
        }

        return tokens.isEmpty() ? next : tokens.poll();
    }

    private Token createDedent() {
        CommonToken dedent = commonToken(YamlParser.DEDENT, "");
        dedent.setLine(this.lastToken.getLine());
        return dedent;
    }

    private CommonToken commonToken(int type, String text) {
        int stop = this.getCharIndex() - 1;
        int start = text.isEmpty() ? stop : stop - text.length() + 1;
        return new CommonToken(this._tokenFactorySourcePair, type, DEFAULT_TOKEN_CHANNEL, start, stop);
    }

    private boolean atStartOfInput() {
        return super.getCharPositionInLine() == 0 && super.getLine() == 1;
    }

    private boolean atStartOfLine() {
        return super.getCharPositionInLine() == 0;
    }
}

file
    : statement* EOF
    ;

statement
    : assign WS?
    | list_item WS?
    | object WS?
    ;

assign
    : name ASSIGN_OP value COMMENT? NEWLINE
    ;

list_item
    : LIST_ITEM_OP assign                         # YamlListItemAssign
    | LIST_ITEM_OP value COMMENT? NEWLINE?        # YamlListItemValue
    | LIST_ITEM_OP object                         # YamlListItemObject
    ;

object
    : name ASSIGN_OP COMMENT? obj_block
    ;

obj_block
    : NEWLINE INDENT statement+ DEDENT
    | NEWLINE                                    // Handle an object with no attributes specified
    ;

name
    : NAME
    ;

value
    : NULL                # YamlNullValue
    | BOOLEAN             # YamlBooleanValue
    | INTEGER             # YamlIntegerValue
    | FLOAT               # YamlFloatValue
    | NAME                # YamlNameValue
    | QUOTED_STRING       # YamlQuotedStringValue
    | UNQUOTED_STRING     # YamlUnquotedStringValue
    | inline_list         # YamlInlineListValue
    ;

inline_list
    : LSQ_BRACKET (inline_list_item (INLINE_LIST_SEP inline_list_item)*)? RSQ_BRACKET
    ;

// TODO: We are not supporting inline lists with assigns or objects.
//
inline_list_item
    : (NEWLINE (INDENT)?)? value
    ;

// comments and blank lines before the first element avoid use of NEWLINE so there is no indent/dedent.
// this rule should be one of the first in this file, to override later definitions.
ATSTART
    : {atStartOfInput()}? ( (COMMENT | WS*) ('\r'? '\n' | '\r' | '\f') )+  -> skip
    ;

// comments may appear on separate lines, or on the same line as assignments or object starts.
// don't close with NEWLINE here, needed to distinguish assign from object declaration.
COMMENT
    : WS? '#' ~[\r\n\f]*  -> skip
    ;

NULL
    : NULL_TEXT WS?
    | '"' NULL_TEXT '"'
    | '\'' NULL_TEXT '\''
    ;

BOOLEAN
    : TRUE WS?
    | FALSE WS?
    ;

TRUE
    : TRUE_TEXT
    | '"' TRUE_TEXT '"'
    | '\'' TRUE_TEXT '\''
    ;

FALSE
    : FALSE_TEXT
    | '"' FALSE_TEXT '"'
    | '\'' FALSE_TEXT '\''
    ;

INTEGER
    : INT_TEXT EXP_TEXT? WS?
    | '"' INT_TEXT EXP_TEXT? '"'
    | '\'' INT_TEXT EXP_TEXT? '\''
    ;

FLOAT
    : FLOAT_TEXT EXP_TEXT? WS?
    | '"' FLOAT_TEXT EXP_TEXT? '"'
    | '\'' FLOAT_TEXT EXP_TEXT? '\''
    ;

NAME
    : ID_START ID_CONTINUE* WS?
    | '""' WS?
    | '\'\'' WS?
    | '\'' QUOTED_ID_START QUOTED_ID_CONTINUE* '\'' WS?
    | '"' QUOTED_ID_START QUOTED_ID_CONTINUE* '"' WS?
    ;

UNQUOTED_STRING
    // Only allow unquoted strings to start and end with specific characters
    //
    : UNQUOTED_STRING_CHARS_START UNQUOTED_STRING_CHARS_CONTINUE* UNQUOTED_STRING_CHARS_START*
    ;

QUOTED_STRING
    : '"' DQUOTED_STRING_CHARS* '"'
    | '\'' SQUOTED_STRING_CHARS* '\''
    ;

NEWLINE
    : (  {atStartOfInput()}? SPACES
    | ( '\r'? '\n' | '\r' | '\f' ) SPACES?
    )
    {
        String newLine = getText().replaceAll("[^\r\n\f]+", "");
        String spaces = getText().replaceAll("[\r\n\f]+", "");

        int next = _input.LA(1);

        // if opened > 0, we're in a square-bracket list.
        // if next character is end-of-line, this was a blank line.
        // if next character is #, this is a comment line.
        // for these cases, don't check for indent, dedent.
        if (opened > 0 || next == '\r' || next == '\n' || next == '\f' || next == '#') {
            skip();
        } else {
            emit(commonToken(NEWLINE, newLine));

            int currentIndent = spaces.length();
            int previousIndent = indents.isEmpty() ? 0 : indents.peek();
            if (currentIndent == previousIndent) {
                emit(commonToken(WS, spaces));
            } else if (currentIndent > previousIndent) {
                indents.push(currentIndent);
                emit(commonToken(YamlParser.INDENT, spaces));
            } else {  // currentIndent < previousIndent
                while (!indents.isEmpty() && indents.peek() > currentIndent) {
                    emit(createDedent());
                    indents.pop();
                }
            }
        }
    }
    ;

LSQ_BRACKET
    : '[' WS?
    { opened++; }
    ;

RSQ_BRACKET
    : WS? ']'
    { opened--; }
    ;

INLINE_LIST_SEP
    : WS? ',' WS?
    ;

LIST_ITEM_OP
    : '- ' WS?
    ;

ASSIGN_OP
    : WS? ':' WS?
    ;

SPACES
    : [ ]+
    ;

WS
    : [ \t]+ -> skip
    ;

fragment NULL_TEXT
    : [nN] [uU] [lL] [lL]
    ;

fragment TRUE_TEXT
    : [tT] [rR] [uU] [eE];

fragment FALSE_TEXT
    : [fF] [aA] [lL] [sS] [eE]
    ;

fragment INT_TEXT
    : [+-]? [1-9] [0-9]*
    ;

fragment FLOAT_TEXT
    : [+-]? ('0' | INT_TEXT) '.' [0-9]*
    ;

fragment EXP_TEXT
    : [eE] [+-] INT_TEXT
    ;

fragment ID_START
    : [_]
    | [A-Z]
    | [a-z]
    | [0-9]
    | '!'
    | '$'
    ;

fragment ID_CONTINUE
    : ID_START
    | [0-9]
    | [. ()/]
    ;

// to support variables in IDs that will need to be quoted because of the curly braces
fragment QUOTED_ID_START
    : ID_START
    | '@'
    ;

fragment QUOTED_ID_CONTINUE
    : ID_CONTINUE
    | [@&*#\-(){}[\]:/]
    ;

fragment SQUOTED_STRING_CHARS
    : (~['] | '\'\'')
    ;

fragment DQUOTED_STRING_CHARS
    : (~["] | '""')
    ;

fragment UNQUOTED_STRING_CHARS_START
    : ~(':' | '{' | '}' | '[' | ']' | ',' | '&' | '*' | '#' | '?' | '|' | '-'
    | '<' | '>' | '=' | '!' | '%' | '@' | '`' | ' ' | '\t' | '\r' | '\n' | '\f' | '\'' | '"')
    ;

fragment UNQUOTED_STRING_CHARS_CONTINUE
    : UNQUOTED_STRING_CHARS_START
    | [ \t]
    | ['] [']
    | ["] ["]
    ;
