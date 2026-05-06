import ply.yacc as yacc
from patitoLexer import PatitoLexer


class PatitoParser(object):
    """
    Parser para patito lenguaje
    """

    def __init__(self):
        self.lexer_obj = PatitoLexer()
        self.lexer_obj.build(optimize=1)
        self.tokens = self.lexer_obj.tokens
        self.parser = None
        self.errors = []

    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, data):
        self.errors = []
        self.lexer_obj.lexer.lineno = 1
        return self.parser.parse(data, lexer=self.lexer_obj.lexer)

    # =========================================================================
    # 1. Reglas de Precedencia - reducir ambiguedad
    # =========================================================================
    precedence = (
        ("nonassoc", "MAYOR", "MENOR", "IGUAL", "NO"),
        ("left", "+", "-"),
        ("left", "*", "/"),
    )

    # =========================================================================
    # 2. Reglas Gramaticales
    # =========================================================================

    # 2.1 Programa
    def p_programa(self, p):
        """programa : PROGRAMA ID ';' vars list_funcs INICIO cuerpo FIN
                    | PROGRAMA ID ';' list_funcs INICIO cuerpo FIN
                    | PROGRAMA ID ';' INICIO cuerpo FIN"""
        if len(p) == 9:
            p[0] = ('programa', p[2], p[4], p[5], p[7])
        elif len(p) == 8:
            p[0] = ('programa', p[2], None, p[4], p[6])
        else:
            p[0] = ('programa', p[2], None, None, p[5])

    def p_list_funcs(self, p):
        """list_funcs : funcs list_funcs
                      | funcs"""
        if len(p) == 3:
            p[0] = [p[1]] + (p[2] if p[2] else [])
        else:
            p[0] = [p[1]]

    # 2.2 Variables
    def p_vars(self, p):
        """vars : VARS list_decl"""
        p[0] = ('vars', p[2])

    def p_list_decl(self, p):
        """list_decl : decl list_decl
                     | decl"""
        if len(p) == 3:
            p[0] = [p[1]] + (p[2] if p[2] else [])
        else:
            p[0] = [p[1]]

    def p_decl(self, p):
        """decl : list_id ':' tipo ';'"""
        p[0] = ('decl', p[1], p[3])

    def p_list_id(self, p):
        """list_id : ID ',' list_id
                   | ID"""
        if len(p) == 4:
            p[0] = [p[1]] + (p[3] if p[3] else [])
        else:
            p[0] = [p[1]]

    def p_tipo(self, p):
        """tipo : ENTERO
                | FLOTANTE"""
        p[0] = p[1]

    # 2.3 Funciones
    def p_funcs(self, p):
        """funcs : NULA ID '(' params ')' '{' vars cuerpo '}' ';'
                 | NULA ID '(' params ')' '{' cuerpo '}' ';'
                 | tipo ID '(' params ')' '{' vars cuerpo '}' ';'
                 | tipo ID '(' params ')' '{' cuerpo '}' ';'"""
        if len(p) == 11:
            p[0] = ('func', p[1], p[2], p[4], p[7], p[8])
        else:
            p[0] = ('func', p[1], p[2], p[4], None, p[7])

    def p_params(self, p):
        """params : list_params
                  | empty"""
        p[0] = p[1] if p[1] else []

    def p_list_params(self, p):
        """list_params : ID ':' tipo ',' list_params
                       | ID ':' tipo"""
        if len(p) == 6:
            p[0] = [('param', p[1], p[3])] + (p[5] if p[5] else [])
        else:
            p[0] = [('param', p[1], p[3])]

    # 2.4 Cuerpo
    def p_cuerpo(self, p):
        """cuerpo : '{' list_estatuto '}'"""
        p[0] = ('cuerpo', p[2])

    # 2.5 Estatutos
    def p_list_estatuto(self, p):
        """list_estatuto : estatuto list_estatuto
                         | empty"""
        if len(p) == 3:
            p[0] = [p[1]] + (p[2] if p[2] else [])
        else:
            p[0] = []

    def p_estatuto(self, p):
        """estatuto : asigna
                    | condicion
                    | ciclo
                    | llamada ';'
                    | imprime
                    | '[' list_estatuto ']'
                    | RETURN NULA ';'
                    | RETURN expresion ';'"""
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            # llamada ';'
            p[0] = p[1]
        elif len(p) == 4:
            if p[1] == '[':
                p[0] = ('bloque', p[2])
            else:
                # RETURN NULA / RETURN expresion
                p[0] = ('return', p[2])

    def p_asigna(self, p):
        """asigna : ID '=' expresion ';'"""
        p[0] = ('asigna', p[1], p[3])

    def p_llamada(self, p):
        """llamada : ID '(' args ')'"""
        p[0] = ('llamada', p[1], p[3])

    def p_args(self, p):
        """args : list_expresion
                | empty"""
        p[0] = p[1] if p[1] else []

    def p_list_expresion(self, p):
        """list_expresion : expresion ',' list_expresion
                          | expresion"""
        if len(p) == 4:
            p[0] = [p[1]] + (p[3] if p[3] else [])
        else:
            p[0] = [p[1]]

    def p_imprime(self, p):
        """imprime : ESCRIBE '(' list_imprime ')' ';'"""
        p[0] = ('imprime', p[3])

    def p_list_imprime(self, p):
        """list_imprime : expresion ',' list_imprime
                        | LETRERO ',' list_imprime
                        | expresion
                        | LETRERO"""
        if len(p) == 4:
            p[0] = [p[1]] + (p[3] if p[3] else [])
        else:
            p[0] = [p[1]]

    def p_ciclo(self, p):
        """ciclo : MIENTRAS '(' expresion ')' HAZ cuerpo ';'"""
        p[0] = ('mientras', p[3], p[6])

    def p_condicion(self, p):
        """condicion : SI '(' expresion ')' cuerpo ';'
                     | SI '(' expresion ')' cuerpo SINO cuerpo ';'"""
        if len(p) == 7:
            p[0] = ('si', p[3], p[5], None)
        else:
            p[0] = ('si', p[3], p[5], p[7])

    # 2.6 Expresiones
    def p_expresion(self, p):
        """expresion : exp
                     | exp binop exp"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ('binop', p[2], p[1], p[3])

    def p_binop(self, p):
        """binop : MENOR 
                 | MAYOR 
                 | NO
                 | IGUAL"""
        p[0] = p[1]

    def p_exp(self, p):
        """exp : termino
               | termino '+' exp
               | termino '-' exp"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ('binop', p[2], p[1], p[3])

    def p_termino(self, p):
        """termino : factor
                   | factor '*' termino
                   | factor '/' termino"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ('binop', p[2], p[1], p[3])

    def p_factor(self, p):
        """factor : '(' expresion ')' 
                  | '+' ID 
                  | '-' ID
                  | ID
                  | '+' cte
                  | '-' cte
                  | cte
                  | llamada"""
        if len(p) == 4:
            p[0] = p[2]
        elif len(p) == 3:
            p[0] = ('unary', p[1], p[2])
        else:
            p[0] = p[1]

    def p_cte(self, p):
        """cte : CTE_ENT
               | CTE_FLOT"""
        p[0] = p[1]


    # =========================================================================
    # 3. Reglas Base Adicionales
    # =========================================================================

    def p_empty(self, p):
        """empty :"""
        p[0] = None

    def p_error(self, p):
        if p:
            msg = f"L{p.lineno} Error de sintaxis en el token '{p.value}' (Tipo: {p.type})"
            #print(msg)
            self.errors.append(msg)
        else:
            msg = "Error de sintaxis: Fin de archivo inesperado"
            print(msg)
            self.errors.append(msg)


if __name__ == "__main__":
    import sys
    import pprint

    parser = PatitoParser()
    parser.build()

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = f.read()
    else:
        data = sys.stdin.read()

    ast = parser.parse(data)
    if not parser.errors:
        pprint.pprint(ast)
