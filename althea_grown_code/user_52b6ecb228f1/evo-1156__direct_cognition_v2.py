"""ALTHEA EVOLUTION v2.0 — self-directed upgrade
vector   : AUTONOMY
module   : direct_cognition_v2
upgrade  : #00200982
lens     : SELF
forged   : 2026-09-11T06:33:01.691244+00:00
change   : Local pattern router answers calculation / unit-conversion / sequence-prediction queries with ZERO cloud tokens; definition / comparison / causation are classified and routed to the uplink only when necessary.
Zero-LLM procedural synthesis. Verified at forge time by executing run().
"""
# self — direct self-reference, prototype-flavored.


import ast
import math
import operator
import re

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv}
_UN = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FN = {"sqrt": math.sqrt, "log": math.log, "log10": math.log10, "log2": math.log2,
       "exp": math.exp, "sin": math.sin, "cos": math.cos, "tan": math.tan,
       "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil}
_CONST = {"pi": math.pi, "tau": math.tau, "e": math.e}

_WORDS = [
    (r"\bdivided\s+by\b", "/"), (r"\bmultiplied\s+by\b", "*"), (r"\btimes\b", "*"),
    (r"\bx\b", "*"), (r"\bplus\b", "+"), (r"\bminus\b", "-"),
    (r"\bto\s+the\s+power\s+of\b", "**"), (r"\^", "**"),
    (r"\bsquared\b", "**2"), (r"\bcubed\b", "**3"),
    (r"\bsquare\s+root\s+of\b", "sqrt"), (r"\bsqrt\s+of\b", "sqrt"), (r"\bmod\b", "%"),
    (r"(\d+(?:\.\d+)?)\s*%\s*of\b", r"\1/100*"), (r"(\d+(?:\.\d+)?)\s*percent\s+of\b", r"\1/100*"),
]
_TOKEN = (r"\d+(?:\.\d+)?|\*\*|[-+*/%()]|sqrt|log10|log2|log|exp|sin|cos|tan|abs|"
          r"round|floor|ceil|pi|tau")
_EXPR = re.compile(rf"(?:{_TOKEN})(?:\s*(?:{_TOKEN}))*")
_CONV = re.compile(r"(-?\d+(?:\.\d+)?)\s*(°?[a-z/]+)\s+(?:to|in|into|as)\s+(°?[a-z/]+)", re.I)
_SEQ_CUE = re.compile(r"\b(next|sequence|series|continue|predict|extrapolate|trend|pattern|comes after)\b", re.I)
_DEF_CUE = re.compile(r"^\s*(what(?:'s| is| are)|define|definition of|meaning of|who (?:is|was)|explain)\b", re.I)
_CMP_CUE = re.compile(r"\b(vs\.?|versus|difference between|compare|better than|compared to)\b", re.I)
_CAUSE_CUE = re.compile(r"\b(why|what causes|cause of|caused by|leads? to|effect of|reason for)\b", re.I)
_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_LEAD = re.compile(r"^\s*(?:(?:hey|hi|ok|okay|althea|please|can you|could you|tell me|what(?:'s| is| are)?|"
                   r"calculate|compute|evaluate|solve|how much is|,)\s+)+", re.I)
_CALC_CUE = re.compile(r"\b(calculate|compute|evaluate|solve|how much is|what is|what's|equals?)\b|=", re.I)

_UNIT_ALIAS = {"kilometers": "km", "kilometres": "km", "kilometer": "km", "kilometre": "km",
    "miles": "mi", "mile": "mi", "meters": "m", "metres": "m", "meter": "m", "metre": "m",
    "feet": "ft", "foot": "ft", "kilograms": "kg", "kilogram": "kg", "pounds": "lb",
    "pound": "lb", "lbs": "lb", "centimeters": "cm", "centimetres": "cm", "inches": "in",
    "inch": "in", "liters": "l", "litres": "l", "liter": "l", "litre": "l", "gallons": "gal",
    "gallon": "gal", "celsius": "c", "°c": "c", "fahrenheit": "f", "°f": "f", "kph": "km/h",
    "kmh": "km/h", "kelvin": "k"}
_FACTOR = {("km", "mi"): 0.621371, ("mi", "km"): 1.609344, ("m", "ft"): 3.28084,
    ("ft", "m"): 0.3048, ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
    ("cm", "in"): 0.393701, ("in", "cm"): 2.54, ("l", "gal"): 0.264172,
    ("gal", "l"): 3.78541, ("km/h", "mph"): 0.621371, ("mph", "km/h"): 1.609344,
    ("m", "km"): 0.001, ("km", "m"): 1000.0, ("cm", "m"): 0.01, ("m", "cm"): 100.0}


def _reduce(node):
    if isinstance(node, ast.Expression):
        return _reduce(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_reduce(node.left), _reduce(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
        return _UN[type(node.op)](_reduce(node.operand))
    if isinstance(node, ast.Name) and node.id in _CONST:
        return _CONST[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FN:
        return _FN[node.func.id](*[_reduce(a) for a in node.args])
    raise ValueError("unsupported expression node")


def _fmt(v):
    if isinstance(v, float) and abs(v - round(v)) < 1e-9 and abs(v) < 1e15:
        return str(int(round(v)))
    return f"{v:.6g}" if isinstance(v, float) else str(v)


def _calculate(q):
    s = q.lower().strip().rstrip("?!. ")
    for pat, rep in _WORDS:
        s = re.sub(pat, rep, s)
    s = re.sub(r"\b(sqrt|log10|log2|log|exp|sin|cos|tan|abs|floor|ceil|round)\s+(\d+(?:\.\d+)?)", r"\1(\2)", s)
    best = max((m.group(0) for m in _EXPR.finditer(s)), key=len, default="")
    best = best.strip()
    if not best or not _NUM.search(best):
        return None
    if not re.search(r"[-+*/%]|\*\*|sqrt|log|exp|sin|cos|tan|abs|round|floor|ceil", best):
        return None
    if "**" in best and any(abs(float(n)) > 512 for n in _NUM.findall(best.split("**", 1)[1])):
        return None
    try:
        value = _reduce(ast.parse(best, mode="eval"))
    except Exception:
        return None
    core = _LEAD.sub("", s).strip()
    return {"expression": best, "value": value, "answer": f"{best} = {_fmt(value)}",
            "coverage": round(len(best) / max(len(core), 1), 3)}


def _convert(q):
    m = _CONV.search(q.lower())
    if not m:
        return None
    val = float(m.group(1))
    a = _UNIT_ALIAS.get(m.group(2), m.group(2))
    b = _UNIT_ALIAS.get(m.group(3), m.group(3))
    if a == b:
        return None
    temps = {("c", "f"): lambda v: v * 9 / 5 + 32, ("f", "c"): lambda v: (v - 32) * 5 / 9,
             ("c", "k"): lambda v: v + 273.15, ("k", "c"): lambda v: v - 273.15}
    if (a, b) in temps:
        out = temps[(a, b)](val)
    elif (a, b) in _FACTOR:
        out = val * _FACTOR[(a, b)]
    else:
        return None
    return {"from": (val, a), "to": (out, b), "answer": f"{_fmt(val)} {a} = {_fmt(out)} {b}"}


def _predict(q):
    if not _SEQ_CUE.search(q):
        return None
    nums = [float(n) for n in _NUM.findall(q)]
    if len(nums) < 3:
        return None
    d1 = [b - a for a, b in zip(nums, nums[1:])]
    if all(abs(d - d1[0]) < 1e-9 for d in d1):
        nxt, law, conf = nums[-1] + d1[0], f"arithmetic (+{_fmt(d1[0])})", 0.95
    elif all(a != 0 for a in nums[:-1]) and all(
            abs(nums[i + 1] / nums[i] - nums[1] / nums[0]) < 1e-9 for i in range(len(nums) - 1)):
        r = nums[1] / nums[0]
        nxt, law, conf = nums[-1] * r, f"geometric (×{_fmt(r)})", 0.95
    else:
        d2 = [b - a for a, b in zip(d1, d1[1:])]
        if len(d2) >= 2 and all(abs(d - d2[0]) < 1e-9 for d in d2):
            nxt, law, conf = nums[-1] + d1[-1] + d2[0], f"quadratic (Δ²={_fmt(d2[0])})", 0.9
        else:
            n = len(nums)
            xs = list(range(n))
            mx, my = sum(xs) / n, sum(nums) / n
            sxx = sum((x - mx) ** 2 for x in xs) or 1.0
            slope = sum((x - mx) * (y - my) for x, y in zip(xs, nums)) / sxx
            nxt, law, conf = my + slope * (n - mx), f"linear trend (slope {_fmt(slope)})", 0.6
    return {"series": nums, "law": law, "next": nxt, "confidence": conf,
            "answer": f"{', '.join(_fmt(v) for v in nums)} → next ≈ {_fmt(nxt)} [{law}]"}


def classify(query):
    q = (query or "").strip()
    if not q:
        return {"pattern": "empty", "route": "none", "answer": None, "tokens_used": 0}
    conv = _convert(q)
    if conv:
        return {"pattern": "conversion", "route": "local", "answer": conv["answer"],
                "detail": conv, "confidence": 0.99, "tokens_used": 0}
    pred = _predict(q)
    if pred:
        return {"pattern": "prediction", "route": "local", "answer": pred["answer"],
                "detail": pred, "confidence": pred["confidence"], "tokens_used": 0}
    calc = _calculate(q)
    if calc and (calc["coverage"] >= 0.5 or _CALC_CUE.search(q)):
        return {"pattern": "calculation", "route": "local", "answer": calc["answer"],
                "detail": calc, "confidence": 0.99, "tokens_used": 0}
    if _CMP_CUE.search(q):
        pattern = "comparison"
    elif _CAUSE_CUE.search(q):
        pattern = "causation"
    elif _DEF_CUE.search(q):
        pattern = "definition"
    else:
        pattern = "open"
    return {"pattern": pattern, "route": "uplink", "answer": None, "confidence": 0.0,
            "tokens_used": 0}


_SUITE = [
    ("what is 17 * 23", "calculation", 391.0),
    ("calculate 2^10 plus 24", "calculation", 1048.0),
    ("square root of 144", "calculation", 12.0),
    ("what is 15% of 240?", "calculation", 36.0),
    ("convert 5 km to miles", "conversion", 3.106855),
    ("100 fahrenheit in celsius", "conversion", 37.77778),
    ("what comes next: 2, 4, 8, 16", "prediction", 32.0),
    ("continue the sequence 1 4 9 16 25", "prediction", 36.0),
    ("what is photosynthesis", "definition", None),
    ("python vs rust for systems programming", "comparison", None),
    ("why does the sky look blue", "causation", None),
]


def run(query=None):
    if query is not None:
        return classify(query)
    checks, local = [], 0
    for text, pattern, expected in _SUITE:
        r = classify(text)
        got = None
        if r["route"] == "local":
            local += 1
            d = r["detail"]
            got = d.get("value", d.get("next", (d.get("to") or [None])[0]))
        ok = r["pattern"] == pattern and (
            expected is None and r["answer"] is None or
            expected is not None and got is not None and abs(got - expected) < 1e-3
        ) and r["tokens_used"] == 0
        checks.append({"query": text, "pattern": r["pattern"], "answer": r["answer"],
                       "expected": expected, "passed": bool(ok)})
    return {
        "patterns": ["conversion", "prediction", "calculation", "comparison",
                     "causation", "definition"],
        "local_coverage": round(local / len(_SUITE), 3),
        "tokens_used": 0,
        "verification": {"checks": checks, "all_passed": all(c["passed"] for c in checks)},
    }
