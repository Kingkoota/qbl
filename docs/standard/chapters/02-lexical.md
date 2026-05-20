# Chapter 2: Lexical Structure

## 2.1 Source Encoding

QBL source files use UTF-8 encoding with `.qbl` extension.

## 2.2 Line Structure

QBL uses newlines as statement terminators. Statements can span multiple lines when enclosed in braces `{ }` or parentheses `( )`.

## 2.3 Comments

```
// Single-line comment
/* Multi-line
   comment */
```

## 2.4 Keywords

### 2.4.1 Declaration Keywords

```
qubit    qudit    cbit     cdit
gate     pulse    def      return
import   module   const    type
```

### 2.4.2 Control Flow Keywords

```
if       else     while    for
match    break    continue
```

### 2.4.3 Quantum Keywords

```
measure    assert    entangled    teleport
protect    feedback  barrier
```

### 2.4.4 Built-in Gate Names

```
// Dimension-agnostic (work for any d)
SHIFT    CLOCK    QFT      WEYL
SUM      CPHASE   DSWAP    MULT
ROT      PHASE    INC      DEC

// Qubit-specific (d=2 only)
H        X        Y        Z
CNOT     CZ       SWAP     T
S        RX       RY       RZ
TOFFOLI  FREDKIN
```

## 2.5 Identifiers

```
identifier := [a-zA-Z_][a-zA-Z0-9_]*
```

Identifiers are case-sensitive. Gate names are conventionally UPPERCASE.

## 2.6 Literals

### 2.6.1 Integer Literals

```
42       // decimal
0x2A     // hexadecimal
0b101010 // binary
0o52     // octal
```

### 2.6.2 Float Literals

```
3.14
1.0e-7
0.5
```

### 2.6.3 Dimension Literals

```
<2>      // qubit dimension
<13>     // qudit dimension (primary)
<d>      // generic dimension parameter
```

## 2.7 Operators

```
// Arithmetic
+  -  *  /  %  **

// Comparison
==  !=  <  >  <=  >=

// Assignment
=  +=  -=

// Quantum
->       // state transfer / teleport target
|>       // pipeline (gate composition)
<|       // adjoint pipeline
⊗        // tensor product (or 'x' in ASCII mode)

// Grouping
( )  [ ]  { }  < >
```

## 2.8 Delimiters

```
,        // argument separator
:        // type annotation / label
;        // optional statement terminator
.        // member access
..       // range
```

## 2.9 Physical Units (for pulse-level programming)

```
ns   us   ms   s       // time
GHz  MHz  kHz  Hz      // frequency
rad  deg  mrad         // angle
mV   uV                // voltage
```

## 2.10 Grammar Summary (EBNF)

```ebnf
program       := declaration* statement*
declaration   := qubit_decl | qudit_decl | cbit_decl | cdit_decl | func_def
qubit_decl    := 'qubit' IDENT '[' INT ']'
qudit_decl    := 'qudit' '<' INT '>' IDENT '[' INT ']'
cbit_decl     := 'cbit' IDENT '[' INT ']'
cdit_decl     := 'cdit' '<' INT '>' IDENT '[' INT ']'
statement     := gate_call | measurement | condition | assertion | block
gate_call     := GATE_NAME '(' arg_list ')'
measurement   := IDENT '[' INT ']' '=' 'measure' '(' qubit_ref ')'
condition     := 'if' expr '{' statement* '}' ('else' '{' statement* '}')?
assertion     := 'assert' assertion_kind '(' arg_list ')'
block         := 'gate' '{' gate_call* '}' | 'pulse' '(' ... ')' '{' ... '}'
qubit_ref     := IDENT ('[' INT ']')?
arg_list      := (expr (',' expr)*)?
```
