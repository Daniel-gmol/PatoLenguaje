_arith_entry = {
    "entero": {
        "entero": "entero",
        "flotante": "flotante"
    },
    "flotante": {
        "entero": "flotante",
        "flotante": "flotante"
    }
}

_rel_entry = {
    "entero": {
        "entero": "entero",
        "flotante": "entero"
    },
    "flotante": {
        "entero": "entero",
        "flotante": "entero"
    }
}

cube = {}

for op in ("+", "-", "*", "/"):
    cube[op] = _arith_entry

for op in ("<", ">", "<=", ">=", "==", "!=", "yy", "oo", "no", "xo"):
    cube[op] = _rel_entry

cube["="] = {
    "entero": {
        "entero": "entero",
    },
    "flotante": {
        "entero": "flotante",
        "flotante": "flotante"
    }
}