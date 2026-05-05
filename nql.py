"""
NQL (Nexthink Query Language) parser and evaluator.

Supports a practical subset of real Nexthink NQL:

  (device) where <condition> [limit N]
  (device) select <field>[, <field>] where <condition> [limit N]

Condition grammar:
  condition   := clause (('and' | 'or') clause)*
  clause      := '(' condition ')' | comparison
  comparison  := field_path op value
  op          := '=' | '!=' | '>' | '>=' | '<' | '<=' | 'like'
  value       := string | number | 'true' | 'false'

Field paths (maps to device dict keys):
  device.name             -> device_name
  device.id               -> device_id
  device.site             -> site
  device.department       -> department
  device.country          -> country
  os.name                 -> os_name
  os.version              -> os_version
  os.build                -> os_build
  device.ram_gb           -> ram_gb
  device.disk_free_pct    -> disk_free_pct
  device.disk_total_gb    -> disk_total_gb
  device.cpu_usage        -> cpu_usage
  device.compliance       -> compliance_status
  device.last_seen        -> last_seen_days  (numeric, days)
  device.agent_version    -> agent_version
"""

import re
import shlex

# ---------------------------------------------------------------------------
# Field mapping: NQL path -> device dict key (and optional type hint)
# ---------------------------------------------------------------------------
FIELD_MAP = {
    "device.name":          ("device_name",       "str"),
    "device.id":            ("device_id",          "str"),
    "device.site":          ("site",               "str"),
    "device.department":    ("department",          "str"),
    "device.country":       ("country",             "str"),
    "os.name":              ("os_name",             "str"),
    "os.version":           ("os_version",          "str"),
    "os.build":             ("os_build",            "str"),
    "device.ram_gb":        ("ram_gb",              "num"),
    "device.disk_free_pct": ("disk_free_pct",       "num"),
    "device.disk_total_gb": ("disk_total_gb",       "num"),
    "device.cpu_usage":     ("cpu_usage",           "num"),
    "device.compliance":    ("compliance_status",   "str"),
    "device.last_seen":     ("last_seen_days",      "num"),
    "device.agent_version": ("agent_version",       "str"),
    # user fields
    "user.username":        ("user.username",       "str"),
    "user.department":      ("user.department",     "str"),
    "user.email":           ("user.email",          "str"),
    "user.display_name":    ("user.display_name",   "str"),
}

ALL_FIELDS = list(FIELD_MAP.keys())

# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------
TOKEN_RE = re.compile(
    r"""
    (?P<LPAREN>   \(              ) |
    (?P<RPAREN>   \)              ) |
    (?P<STRING>   "[^"]*"|'[^']*' ) |
    (?P<NUMBER>   -?\d+(?:\.\d+)? ) |
    (?P<OP>       >=|<=|!=|>|<|= ) |
    (?P<WORD>     [A-Za-z_][A-Za-z0-9_.]*) |
    (?P<COMMA>    ,               ) |
    (?P<WS>       \s+             )
    """,
    re.VERBOSE,
)


def tokenize(text):
    tokens = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        if kind == "WS":
            continue
        tokens.append((kind, m.group()))
    return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
class NQLError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, kind=None, value=None):
        tok = self.peek()
        if tok is None:
            raise NQLError("Unexpected end of query")
        if kind and tok[0] != kind:
            raise NQLError(f"Expected {kind}, got {tok[0]} ({tok[1]!r})")
        if value and tok[1].lower() != value.lower():
            raise NQLError(f"Expected {value!r}, got {tok[1]!r}")
        self.pos += 1
        return tok

    def maybe(self, kind=None, value=None):
        tok = self.peek()
        if tok is None:
            return None
        if kind and tok[0] != kind:
            return None
        if value and tok[1].lower() != value.lower():
            return None
        self.pos += 1
        return tok

    def parse_query(self):
        """
        query := '(' entity ')' ['select' fields] ['where' condition] ['limit' N]
        """
        self.consume("LPAREN")
        entity_tok = self.consume("WORD")
        entity = entity_tok[1].lower()
        if entity not in ("device", "user"):
            raise NQLError(f"Unknown entity {entity!r}. Supported: device, user")
        self.consume("RPAREN")

        select_fields = None
        condition = None
        limit = None

        while self.peek():
            tok = self.peek()
            word = tok[1].lower() if tok[0] == "WORD" else None

            if word == "select":
                self.consume()
                select_fields = self.parse_field_list()
            elif word == "where":
                self.consume()
                condition = self.parse_condition()
            elif word == "limit":
                self.consume()
                n_tok = self.consume("NUMBER")
                limit = int(float(n_tok[1]))
            else:
                raise NQLError(f"Unexpected token {tok[1]!r}")

        return {
            "entity": entity,
            "select": select_fields,
            "condition": condition,
            "limit": limit,
        }

    def parse_field_list(self):
        fields = []
        fields.append(self.parse_field_path())
        while self.maybe("COMMA"):
            fields.append(self.parse_field_path())
        return fields

    def parse_field_path(self):
        tok = self.consume("WORD")
        path = tok[1]
        if path.lower() not in FIELD_MAP:
            raise NQLError(
                f"Unknown field {path!r}. Valid fields: {', '.join(sorted(FIELD_MAP))}"
            )
        return path.lower()

    def parse_condition(self):
        left = self.parse_clause()
        while self.peek() and self.peek()[0] == "WORD" and self.peek()[1].lower() in ("and", "or"):
            op_tok = self.consume()
            right = self.parse_clause()
            left = ("logical", op_tok[1].lower(), left, right)
        return left

    def parse_clause(self):
        if self.peek() and self.peek()[0] == "LPAREN":
            self.consume("LPAREN")
            cond = self.parse_condition()
            self.consume("RPAREN")
            return cond
        return self.parse_comparison()

    def parse_comparison(self):
        field_tok = self.consume("WORD")
        field = field_tok[1].lower()
        if field not in FIELD_MAP:
            raise NQLError(
                f"Unknown field {field!r}. Valid fields: {', '.join(sorted(FIELD_MAP))}"
            )
        op_tok = self.consume("OP")
        op = op_tok[1]

        val_tok = self.peek()
        if val_tok is None:
            raise NQLError("Expected value after operator")

        if val_tok[0] == "STRING":
            self.consume()
            value = val_tok[1][1:-1]  # strip quotes
        elif val_tok[0] == "NUMBER":
            self.consume()
            value = float(val_tok[1])
        elif val_tok[0] == "WORD" and val_tok[1].lower() in ("true", "false"):
            self.consume()
            value = val_tok[1].lower() == "true"
        else:
            raise NQLError(f"Expected value, got {val_tok[1]!r}")

        return ("comparison", field, op, value)


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------
def _get_field(device, nql_field):
    """Resolve a dot-notation NQL field to a value from the device dict."""
    key, _ = FIELD_MAP[nql_field]
    if "." in key:
        parts = key.split(".", 1)
        obj = device.get(parts[0], {})
        return obj.get(parts[1])
    return device.get(key)


def _eval_condition(device, node):
    if node is None:
        return True

    kind = node[0]

    if kind == "logical":
        _, op, left, right = node
        if op == "and":
            return _eval_condition(device, left) and _eval_condition(device, right)
        else:
            return _eval_condition(device, left) or _eval_condition(device, right)

    if kind == "comparison":
        _, field, op, value = node
        actual = _get_field(device, field)
        if actual is None:
            return False

        # Normalise for string comparisons
        if isinstance(actual, str) and isinstance(value, str):
            actual_cmp = actual.lower()
            value_cmp = value.lower()
        else:
            actual_cmp = actual
            value_cmp = value

        if op == "=":
            return actual_cmp == value_cmp
        if op == "!=":
            return actual_cmp != value_cmp
        if op == ">":
            return actual > value
        if op == ">=":
            return actual >= value
        if op == "<":
            return actual < value
        if op == "<=":
            return actual <= value

    return False


def _project(device, fields):
    """Return only the requested fields from a device."""
    if not fields:
        return device
    result = {}
    for f in fields:
        result[f] = _get_field(device, f)
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def execute_nql(query_text, fleet):
    """
    Execute an NQL query against the fleet.
    Returns dict with keys: entity, results, count, error (if any).
    """
    try:
        tokens = tokenize(query_text.strip())
        parser = Parser(tokens)
        ast = parser.parse_query()
    except NQLError as e:
        return {"error": str(e), "results": [], "count": 0}

    entity = ast["entity"]
    condition = ast["condition"]
    select_fields = ast["select"]
    limit = ast["limit"]

    # Filter fleet
    matched = [d for d in fleet if _eval_condition(d, condition)]

    # Apply limit
    if limit is not None:
        matched = matched[:limit]

    # Project fields
    results = [_project(d, select_fields) for d in matched]

    return {
        "entity": entity,
        "results": results,
        "count": len(results),
        "fields": select_fields or list(FIELD_MAP.keys()),
        "error": None,
    }


def get_field_reference():
    """Return the NQL field reference for the UI."""
    return {
        nql_path: {
            "maps_to": key,
            "type": typ,
        }
        for nql_path, (key, typ) in FIELD_MAP.items()
    }
