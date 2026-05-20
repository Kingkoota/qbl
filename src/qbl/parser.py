"""
QBL (Qubit Language) — Lexer & Parser
A quantum programming language that fills the gaps between existing frameworks.

Tokenizes and parses .qbl source into an AST for compilation/simulation.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Union
import re


# ============================================================
# TOKENS
# ============================================================

class TokenType(Enum):
    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    
    # Keywords
    QUBIT = auto()
    CBIT = auto()
    GATE = auto()
    PULSE = auto()
    MEASURE = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    ASSERT = auto()
    ENTANGLED = auto()
    IMPORT = auto()
    DEF = auto()
    RETURN = auto()
    
    # Built-in gates
    H = auto()
    X = auto()
    Y = auto()
    Z = auto()
    CNOT = auto()
    CZ = auto()
    SWAP = auto()
    T = auto()
    S = auto()
    RX = auto()
    RY = auto()
    RZ = auto()
    TOFFOLI = auto()
    
    # Operators
    EQUALS = auto()       # =
    EQEQ = auto()        # ==
    NEQ = auto()          # !=
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    COMMA = auto()        # ,
    COLON = auto()        # :
    SEMICOLON = auto()    # ;
    DOT = auto()          # .
    ARROW = auto()        # ->
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    
    # Units
    NS = auto()           # nanoseconds
    US = auto()           # microseconds
    GHZ = auto()          # gigahertz
    MHZ = auto()          # megahertz
    
    # Special
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int


KEYWORDS = {
    'qubit': TokenType.QUBIT,
    'cbit': TokenType.CBIT,
    'gate': TokenType.GATE,
    'pulse': TokenType.PULSE,
    'measure': TokenType.MEASURE,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'assert': TokenType.ASSERT,
    'entangled': TokenType.ENTANGLED,
    'import': TokenType.IMPORT,
    'def': TokenType.DEF,
    'return': TokenType.RETURN,
    # Gates
    'H': TokenType.H,
    'X': TokenType.X,
    'Y': TokenType.Y,
    'Z': TokenType.Z,
    'CNOT': TokenType.CNOT,
    'CZ': TokenType.CZ,
    'SWAP': TokenType.SWAP,
    'T': TokenType.T,
    'S': TokenType.S,
    'RX': TokenType.RX,
    'RY': TokenType.RY,
    'RZ': TokenType.RZ,
    'TOFFOLI': TokenType.TOFFOLI,
}

UNITS = {
    'ns': TokenType.NS,
    'us': TokenType.US,
    'GHz': TokenType.GHZ,
    'MHz': TokenType.MHZ,
}


class Lexer:
    """Tokenizes QBL source code."""
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
    
    def peek(self) -> str:
        if self.pos >= len(self.source):
            return '\0'
        return self.source[self.pos]
    
    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch
    
    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self.advance()
    
    def read_number(self) -> Token:
        start_col = self.col
        num_str = ''
        is_float = False
        
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            if self.source[self.pos] == '.':
                is_float = True
            num_str += self.advance()
        
        return Token(
            type=TokenType.FLOAT if is_float else TokenType.INTEGER,
            value=num_str,
            line=self.line,
            col=start_col
        )
    
    def read_identifier(self) -> Token:
        start_col = self.col
        ident = ''
        
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            ident += self.advance()
        
        # Check for units (must follow a number token)
        if ident in UNITS:
            return Token(type=UNITS[ident], value=ident, line=self.line, col=start_col)
        
        # Check keywords/gates
        token_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
        return Token(type=token_type, value=ident, line=self.line, col=start_col)
    
    def read_string(self) -> Token:
        start_col = self.col
        self.advance()  # opening quote
        s = ''
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            s += self.advance()
        self.advance()  # closing quote
        return Token(type=TokenType.STRING, value=s, line=self.line, col=start_col)
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if self.pos >= len(self.source):
                break
            
            ch = self.peek()
            
            # Comments
            if ch == '/' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '/':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.advance()
                continue
            
            # Newlines (significant in QBL)
            if ch == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\\n', self.line, self.col))
                self.advance()
                continue
            
            # Numbers
            if ch.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Identifiers and keywords
            if ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Strings
            if ch == '"':
                self.tokens.append(self.read_string())
                continue
            
            # Two-character operators
            if ch == '=' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
                self.tokens.append(Token(TokenType.EQEQ, '==', self.line, self.col))
                self.advance(); self.advance()
                continue
            if ch == '!' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
                self.tokens.append(Token(TokenType.NEQ, '!=', self.line, self.col))
                self.advance(); self.advance()
                continue
            if ch == '-' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '>':
                self.tokens.append(Token(TokenType.ARROW, '->', self.line, self.col))
                self.advance(); self.advance()
                continue
            
            # Single-character operators
            single_ops = {
                '=': TokenType.EQUALS,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                ':': TokenType.COLON,
                ';': TokenType.SEMICOLON,
                '.': TokenType.DOT,
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.STAR,
                '/': TokenType.SLASH,
            }
            
            if ch in single_ops:
                self.tokens.append(Token(single_ops[ch], ch, self.line, self.col))
                self.advance()
                continue
            
            # Unknown character — skip
            self.advance()
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens


# ============================================================
# AST NODES
# ============================================================

@dataclass
class QubitDecl:
    """qubit q[3]"""
    name: str
    size: int

@dataclass
class CbitDecl:
    """cbit c[3]"""
    name: str
    size: int

@dataclass
class QubitRef:
    """q[0] or q"""
    name: str
    index: Optional[int] = None

@dataclass
class GateCall:
    """H(q[0]) or CNOT(q[0], q[1]) or RX(q[0], 0.5)"""
    gate_name: str
    targets: List[QubitRef]
    params: List[float] = field(default_factory=list)

@dataclass
class GateBlock:
    """gate { ... }"""
    operations: List[GateCall]

@dataclass
class PulseWaveform:
    """waveform specification"""
    shape: str  # gaussian, square, drag
    params: dict

@dataclass
class PulseBlock:
    """pulse(q[0], duration: 20ns) { ... }"""
    target: QubitRef
    duration_ns: float
    waveform: Optional[PulseWaveform] = None
    freq_ghz: Optional[float] = None
    phase: Optional[float] = None

@dataclass
class Measurement:
    """c[0] = measure(q[0])"""
    target_cbit: str
    target_index: int
    source_qubit: QubitRef

@dataclass
class Condition:
    """if c[0] == 1 { ... }"""
    cbit_name: str
    cbit_index: int
    operator: str  # == or !=
    value: int
    body: List  # list of statements
    else_body: Optional[List] = None

@dataclass
class AssertEntangled:
    """assert entangled(q[0], q[1])"""
    qubits: List[QubitRef]

@dataclass
class FunctionDef:
    """def bell_pair(q0, q1) { ... }"""
    name: str
    params: List[str]
    body: List

@dataclass
class Program:
    """Top-level AST node"""
    declarations: List[Union[QubitDecl, CbitDecl]]
    statements: List
    functions: List[FunctionDef] = field(default_factory=list)


# ============================================================
# PARSER
# ============================================================

class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"Line {token.line}, Col {token.col}: {message}")
        self.token = token


class Parser:
    """Parses QBL tokens into an AST."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TokenType.NEWLINE]
        self.pos = 0
    
    def peek(self) -> Token:
        if self.pos >= len(self.tokens):
            return Token(TokenType.EOF, '', 0, 0)
        return self.tokens[self.pos]
    
    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok
    
    def expect(self, token_type: TokenType) -> Token:
        tok = self.peek()
        if tok.type != token_type:
            raise ParseError(f"Expected {token_type.name}, got {tok.type.name} ('{tok.value}')", tok)
        return self.advance()
    
    def match(self, *types: TokenType) -> Optional[Token]:
        if self.peek().type in types:
            return self.advance()
        return None
    
    def parse_qubit_ref(self) -> QubitRef:
        name_tok = self.expect(TokenType.IDENTIFIER)
        index = None
        if self.match(TokenType.LBRACKET):
            idx_tok = self.expect(TokenType.INTEGER)
            index = int(idx_tok.value)
            self.expect(TokenType.RBRACKET)
        return QubitRef(name=name_tok.value, index=index)
    
    def parse_gate_call(self, gate_name: str) -> GateCall:
        self.expect(TokenType.LPAREN)
        targets = []
        params = []
        
        while self.peek().type != TokenType.RPAREN:
            if self.peek().type in (TokenType.FLOAT, TokenType.INTEGER):
                params.append(float(self.advance().value))
            elif self.peek().type == TokenType.IDENTIFIER:
                targets.append(self.parse_qubit_ref())
            
            self.match(TokenType.COMMA)
        
        self.expect(TokenType.RPAREN)
        return GateCall(gate_name=gate_name, targets=targets, params=params)
    
    def parse_gate_block(self) -> GateBlock:
        self.expect(TokenType.LBRACE)
        operations = []
        
        while self.peek().type != TokenType.RBRACE:
            tok = self.peek()
            gate_types = [
                TokenType.H, TokenType.X, TokenType.Y, TokenType.Z,
                TokenType.CNOT, TokenType.CZ, TokenType.SWAP,
                TokenType.T, TokenType.S, TokenType.RX, TokenType.RY,
                TokenType.RZ, TokenType.TOFFOLI
            ]
            if tok.type in gate_types:
                gate_name = self.advance().value
                operations.append(self.parse_gate_call(gate_name))
            elif tok.type == TokenType.IDENTIFIER:
                # Custom gate call
                gate_name = self.advance().value
                operations.append(self.parse_gate_call(gate_name))
            else:
                self.advance()  # skip unknown
        
        self.expect(TokenType.RBRACE)
        return GateBlock(operations=operations)
    
    def parse_measurement(self, cbit_name: str, cbit_index: int) -> Measurement:
        self.expect(TokenType.LPAREN)
        qubit_ref = self.parse_qubit_ref()
        self.expect(TokenType.RPAREN)
        return Measurement(
            target_cbit=cbit_name,
            target_index=cbit_index,
            source_qubit=qubit_ref
        )
    
    def parse_condition(self) -> Condition:
        # Parse: c[0] == 1
        cbit_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LBRACKET)
        cbit_index = int(self.expect(TokenType.INTEGER).value)
        self.expect(TokenType.RBRACKET)
        
        op_tok = self.advance()
        operator = op_tok.value
        
        value = int(self.expect(TokenType.INTEGER).value)
        
        self.expect(TokenType.LBRACE)
        body = self.parse_block_body()
        self.expect(TokenType.RBRACE)
        
        else_body = None
        if self.match(TokenType.ELSE):
            self.expect(TokenType.LBRACE)
            else_body = self.parse_block_body()
            self.expect(TokenType.RBRACE)
        
        return Condition(
            cbit_name=cbit_name,
            cbit_index=cbit_index,
            operator=operator,
            value=value,
            body=body,
            else_body=else_body
        )
    
    def parse_block_body(self) -> List:
        """Parse statements inside a block."""
        stmts = []
        while self.peek().type != TokenType.RBRACE:
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
        return stmts
    
    def parse_statement(self):
        tok = self.peek()
        
        # Qubit declaration
        if tok.type == TokenType.QUBIT:
            self.advance()
            name = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.LBRACKET)
            size = int(self.expect(TokenType.INTEGER).value)
            self.expect(TokenType.RBRACKET)
            return QubitDecl(name=name, size=size)
        
        # Cbit declaration
        if tok.type == TokenType.CBIT:
            self.advance()
            name = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.LBRACKET)
            size = int(self.expect(TokenType.INTEGER).value)
            self.expect(TokenType.RBRACKET)
            return CbitDecl(name=name, size=size)
        
        # Gate block
        if tok.type == TokenType.GATE:
            self.advance()
            return self.parse_gate_block()
        
        # If condition
        if tok.type == TokenType.IF:
            self.advance()
            return self.parse_condition()
        
        # Assert entangled
        if tok.type == TokenType.ASSERT:
            self.advance()
            self.expect(TokenType.ENTANGLED)
            self.expect(TokenType.LPAREN)
            qubits = []
            while self.peek().type != TokenType.RPAREN:
                qubits.append(self.parse_qubit_ref())
                self.match(TokenType.COMMA)
            self.expect(TokenType.RPAREN)
            return AssertEntangled(qubits=qubits)
        
        # Function definition
        if tok.type == TokenType.DEF:
            self.advance()
            name = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.LPAREN)
            params = []
            while self.peek().type != TokenType.RPAREN:
                params.append(self.expect(TokenType.IDENTIFIER).value)
                self.match(TokenType.COMMA)
            self.expect(TokenType.RPAREN)
            self.expect(TokenType.LBRACE)
            body = self.parse_block_body()
            self.expect(TokenType.RBRACE)
            return FunctionDef(name=name, params=params, body=body)
        
        # Assignment (measurement): c[0] = measure(q[0])
        if tok.type == TokenType.IDENTIFIER:
            # Look ahead for c[n] = measure(...)
            if (self.pos + 4 < len(self.tokens) and
                self.tokens[self.pos + 1].type == TokenType.LBRACKET):
                
                save_pos = self.pos
                name = self.advance().value
                self.expect(TokenType.LBRACKET)
                index = int(self.expect(TokenType.INTEGER).value)
                self.expect(TokenType.RBRACKET)
                
                if self.match(TokenType.EQUALS):
                    if self.peek().type == TokenType.MEASURE:
                        self.advance()
                        return self.parse_measurement(name, index)
                
                # Backtrack if not a measurement
                self.pos = save_pos
            
            # Gate call (custom or built-in referenced by name)
            gate_name = self.advance().value
            if self.peek().type == TokenType.LPAREN:
                return self.parse_gate_call(gate_name)
        
        # Built-in gate at top level (outside gate block)
        gate_types = [
            TokenType.H, TokenType.X, TokenType.Y, TokenType.Z,
            TokenType.CNOT, TokenType.CZ, TokenType.SWAP,
            TokenType.T, TokenType.S, TokenType.RX, TokenType.RY,
            TokenType.RZ, TokenType.TOFFOLI
        ]
        if tok.type in gate_types:
            gate_name = self.advance().value
            return self.parse_gate_call(gate_name)
        
        # Skip unrecognized
        self.advance()
        return None
    
    def parse(self) -> Program:
        declarations = []
        statements = []
        functions = []
        
        while self.peek().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt is None:
                continue
            elif isinstance(stmt, (QubitDecl, CbitDecl)):
                declarations.append(stmt)
            elif isinstance(stmt, FunctionDef):
                functions.append(stmt)
            else:
                statements.append(stmt)
        
        return Program(
            declarations=declarations,
            statements=statements,
            functions=functions
        )
