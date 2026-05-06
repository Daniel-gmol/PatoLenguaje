import codecs
from ply import lex
from typing import Generator


class PatitoLexer(object):
    """
    Lexer para patito lenguaje
    """

    # =========================================================================
    # 1. CONFIGURACION (Tokens & Reserved & Literals)
    # =========================================================================
    reserved: dict[str, str] = {
        # Iniciales
        "init": "PROGRAMA",
        "arranca": "INICIO",
        "acaba": "FIN",
        # Tipos y declaraciones
        "val": "VARS",
        "entero": "ENTERO",
        "decimal": "FLOTANTE",
        "nil": "NULA",  # funcs solo
        # Control de flujo
        "si": "SI",
        "sino": "SINO",
        "esperaque": "MIENTRAS",
        # Misc
        "dale": "ESCRIBE",
        "regresa": "RETURN",
    }

    tokens: list[str] = [
        # Identificador
        "ID",
        # Valores CTE
        "LETRERO",
        "CTE_ENT",
        "CTE_FLOT",
        # Control de flujo EXTRA
        "HAZ",
        # Operadores relacionles
        "MENOR",
        "MAYOR",
        "NO",
        "IGUAL",
    ]
    tokens = list(set(tokens) | set(reserved.values()))  # CUIDADO

    literals: list[str] = [
        ",",
        ":",
        ";",
        "[",
        "]",
        "(",
        ")",
        "{",
        "}",
        "*",
        "/",
        "+",
        "-",  #  aritmeticos
        "=",
    ]

    # =========================================================================
    # 2. API pública
    # =========================================================================
    def __init__(self) -> None:
        self.lexer: lex.Lexer | None = None
        self.errors: list[str] = []

    def build(self, **kwargs) -> None:
        self.lexer = lex.lex(module=self, **kwargs)

    # =========================================================================
    # 2.1 Contrato para yacc parser
    # =========================================================================
    def input(self, data: str) -> None:
        self.lexer.input(data)

    def token(self) -> lex.LexToken | None:
        return self.lexer.token()

    # =========================================================================
    # 2.2 Métodos para debug
    # =========================================================================
    def tokenize(self) -> Generator[lex.LexToken, None, None]:
        while True:
            t = self.token()
            if not t:
                break
            yield t

    def test(self, data: str) -> None:
        self.input(data)
        while True:
            t = self.token()
            if not t:
                break
            print(t)

    # =========================================================================
    # 3. API privada
    # =========================================================================
    def _find_column(self, input: str, token: lex.LexToken):
        """
        Encuentra la columna del token relativa al último newline (\n)
        Busca en reversa desde el token hasta el inicio del input.
        """
        line_start = input.rfind("\n", 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1

    # =========================================================================
    # 4. Reglas regex
    # =========================================================================
    def t_LETRERO(self, t):
        r'"[^"]*"'
        t.value = codecs.decode(t.value[1:-1], "unicode_escape")
        return t

    def t_CTE_FLOT(self, t):
        r"[0-9]+(_[0-9]+)*\.[0-9]+(_[0-9]+)*([eE][+-]?[0-9]+(_[0-9]+)*)?"
        t.value = t.value.replace("_", "")
        return t

    def t_CTE_ENT(self, t):
        r"[0-9]+(_[0-9]+)*"
        t.value = t.value.replace("_", "")
        return t

    def t_ID(self, t):
        r"[A-Za-z][A-Za-z0-9_]*"
        key = t.value.lower()
        t.type = self.reserved.get(key, "ID")
        return t

    t_HAZ = r"\\\/"
    t_MENOR = r"<"
    t_MAYOR = r">"
    t_NO = r"!="
    t_IGUAL = r"=="

    # =========================================================================
    # 5. Ayudantes aka Tokens especiales de PLY
    # =========================================================================
    def t_NEWLINE(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)

    t_ignore = " \t"

    def t_error(self, t):
        column = self._find_column(t.lexer.lexdata, t)
        error_msg = f"Error L-{t.lineno} C-{column}: Carácter ilegal '{t.value[0]}'"
        # print(error_msg) Debería usar logging o verbose
        self.errors.append(error_msg)
        t.lexer.skip(1)


if __name__ == "__main__":
    import sys

    mylex = PatitoLexer()
    mylex.build()

    # Recibe codigo de stdin, archivo o redireccion de archivo
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = f.read()
    else:
        data = sys.stdin.read()

    mylex.test(data)
