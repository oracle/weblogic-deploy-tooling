/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
 *
 * Credits:
 *     - Adapted from https://github.com/antlr/grammars-v4/tree/master/json
 *     - Taken from "The Definitive ANTLR 4 Reference" by Terence Parr
 *     - Derived from http://json.org
 */
grammar JSON;

json
   : value
   ;

obj
   : '{' pair (',' pair)* '}'
   | '{' '}'
   ;

pair
   : STRING ':' value
   ;

array
   : '[' value (',' value)* ']'
   | '[' ']'
   ;

value
   : STRING  #JsonString
   | NUMBER  #JsonNumber
   | obj     #JsonObject
   | array   #JsonArray
   | 'true'  #JsonTrue
   | 'false' #JsonFalse
   | 'null'  #JsonNull
   ;


STRING
   : '"' (ESC | ~ ["\\])* '"'
   ;
fragment ESC
   : '\\' (["\\/bfnrt] | UNICODE)
   ;
fragment UNICODE
   : 'u' HEX HEX HEX HEX
   ;
fragment HEX
   : [0-9a-fA-F]
   ;
NUMBER
   : '-'? INT ('.' [0-9] +)? EXP?
   ;
fragment INT
   : '0' | [1-9] [0-9]*
   ;
// no leading zeros
fragment EXP
   : [Ee] [+\-]? INT
   ;
// \- since - means "range" inside [...]
WS
   : [ \t\n\r] + -> skip
   ;
