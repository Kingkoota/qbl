"""
QBL Exceptions — Structured Error Hierarchy

All QBL errors inherit from QBLError. Each layer of the stack has its own
exception class for precise error handling and reporting.
"""


class QBLError(Exception):
    """Base exception for all QBL errors."""
    def __init__(self, message: str, location: str = None):
        self.location = location
        prefix = f"[{location}] " if location else ""
        super().__init__(f"{prefix}{message}")


# ============================================================
# PARSE ERRORS
# ============================================================

class QBLSyntaxError(QBLError):
    """Malformed QBL source code."""
    def __init__(self, message: str, line: int = None, col: int = None):
        self.line = line
        self.col = col
        loc = f"line {line}" if line else None
        if col:
            loc += f", col {col}"
        super().__init__(message, loc)


class QBLTokenError(QBLSyntaxError):
    """Invalid or unexpected token."""
    pass


# ============================================================
# TYPE ERRORS
# ============================================================

class QBLTypeError(QBLError):
    """Type system violation."""
    pass


class NoCloneViolation(QBLTypeError):
    """Attempted to copy a quantum state (no-cloning theorem)."""
    def __init__(self, variable: str, first_use: str = None):
        msg = f"No-clone violation: '{variable}' already consumed"
        if first_use:
            msg += f" (first used at: {first_use})"
        super().__init__(msg)


class DimensionMismatch(QBLTypeError):
    """Gate/operation applied to wrong dimension."""
    def __init__(self, expected: int, got: int, context: str = ""):
        msg = f"Dimension mismatch: expected d={expected}, got d={got}"
        if context:
            msg += f" in {context}"
        super().__init__(msg)


class PostMeasurementUse(QBLTypeError):
    """Attempted to use a qudit after measurement."""
    def __init__(self, variable: str):
        super().__init__(f"Post-measurement use: '{variable}' was already measured and consumed")


# ============================================================
# RUNTIME ERRORS
# ============================================================

class QBLRuntimeError(QBLError):
    """Runtime execution error."""
    pass


class InvalidStateError(QBLRuntimeError):
    """State vector is invalid (not normalized, wrong size, etc.)."""
    pass


class QuditIndexError(QBLRuntimeError):
    """Index out of bounds for qudit register."""
    def __init__(self, index: int, num_qudits: int):
        super().__init__(f"Qudit index {index} out of range [0, {num_qudits-1}]")


class InvalidGateError(QBLRuntimeError):
    """Gate is not unitary or has invalid parameters."""
    def __init__(self, gate_name: str, reason: str):
        super().__init__(f"Invalid gate '{gate_name}': {reason}")


class SimulationLimitError(QBLRuntimeError):
    """Simulation exceeds resource limits."""
    def __init__(self, dimension: int, num_qudits: int, memory_bytes: int):
        memory_gb = memory_bytes / (1024**3)
        super().__init__(
            f"Simulation of {num_qudits} qudits (d={dimension}) requires "
            f"{memory_gb:.1f} GB — exceeds safe limit"
        )


# ============================================================
# COMPILATION ERRORS
# ============================================================

class QBLCompileError(QBLError):
    """Compilation/backend error."""
    pass


class UnsupportedBackendError(QBLCompileError):
    """Requested backend doesn't support this operation."""
    def __init__(self, backend: str, operation: str):
        super().__init__(f"Backend '{backend}' does not support: {operation}")


class DecompositionError(QBLCompileError):
    """Cannot decompose gate into target gate set."""
    def __init__(self, gate_name: str, target_set: str):
        super().__init__(f"Cannot decompose '{gate_name}' into {target_set} gate set")


# ============================================================
# SECURITY ERRORS
# ============================================================

class QBLSecurityError(QBLError):
    """Security boundary violation."""
    pass


class ResourceExhaustion(QBLSecurityError):
    """Attempted to allocate excessive resources (DoS protection)."""
    def __init__(self, resource: str, requested: int, limit: int):
        super().__init__(
            f"Resource exhaustion: requested {requested} {resource}, limit is {limit}"
        )


class InputSanitizationError(QBLSecurityError):
    """Input contains disallowed content."""
    def __init__(self, field: str, reason: str):
        super().__init__(f"Input sanitization failed for '{field}': {reason}")
