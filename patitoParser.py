import ply.yacc as yacc
from patitoLexer import PatitoLexer


class PatitoParser(object):
    """
    Parser para patito lenguaje
    """

    def __init__(self):
        self.lexer_obj = PatitoLexer()
        self.lexer_obj.build()
        self.tokens = self.lexer_obj.tokens
        self.parser = None

    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, data):
        return self.parser.parse(data, lexer=self.lexer_obj.lexer)

    # =========================================================================
    # Reglas de Precedencia - reducir ambiguedad
    # =========================================================================
    precedence = (
        ("nonassoc", "MAYOR", "MENOR", "IGUAL", "NO"),
        ("left", "+", "-"),
        ("left", "*", "/"),
    )

    # =========================================================================
    # Reglas Gramaticales
    # =========================================================================

    def p_programa(self, p):
        """programa : PROGRAMA ID ';' vars list_funcs INICIO cuerpo FIN
        | PROGRAMA ID ';' list_funcs INICIO cuerpo FIN
        | PROGRAMA ID ';' INICIO cuerpo FIN"""
        pass

    def p_list_funcs(self, p):
        """list_funcs : funcs list_funcs
        | funcs"""
        pass

    def p_vars(self, p):
        """vars : VARS list_decl"""
        pass

    def p_list_decl(self, p):
        """list_decl : decl list_decl
        | decl"""
        pass

    def p_decl(self, p):
        """decl : list_id ':' tipo ';'"""
        pass

    def p_list_id(self, p):
        """list_id : ID ',' list_id
        | ID"""
        pass

    def p_tipo(self, p):
        """tipo : ENTERO
        | FLOTANTE"""
        pass

    def p_funcs(self, p):
        """funcs : NULA ID '(' params ')' '{' vars cuerpo '}' ';'
        | NULA ID '(' params ')' '{' cuerpo '}' ';'
        | tipo ID '(' params ')' '{' vars cuerpo '}' ';'
        | tipo ID '(' params ')' '{' cuerpo '}' ';'"""
        pass

    def p_params(self, p):
        """params : list_params
        | empty"""
        pass

    def p_list_params(self, p):
        """list_params : ID ':' tipo ',' list_params
        | ID ':' tipo"""
        pass

    def p_cuerpo(self, p):
        """cuerpo : '{' list_estatuto '}'"""
        pass

    def p_list_estatuto(self, p):
        """list_estatuto : estatuto list_estatuto
        | empty"""
        pass

    def p_estatuto(self, p):
        """estatuto : asigna
        | condicion
        | ciclo
        | llamada ';'
        | imprime"""
        pass

    def p_asigna(self, p):
        """asigna : ID '=' expresion ';'"""
        pass

    def p_llamada(self, p):
        """llamada : ID '(' args ')'"""
        pass

    def p_args(self, p):
        """args : list_expresion
        | empty"""
        pass

    def p_list_expresion(self, p):
        """list_expresion : expresion ',' list_expresion
        | expresion"""
        pass

    def p_imprime(self, p):
        """imprime : ESCRIBE '(' list_imprime ')' ';'"""
        pass

    def p_list_imprime(self, p):
        """list_imprime : expresion ',' list_imprime
        | LETRERO ',' list_imprime
        | expresion
        | LETRERO"""
        pass

    def p_ciclo(self, p):
        """ciclo : MIENTRAS '(' expresion ')' HAZ cuerpo ';'"""
        pass

    def p_condicion(self, p):
        """condicion : SI '(' expresion ')' cuerpo ';'
        | SI '(' expresion ')' cuerpo SINO cuerpo ';'"""
        pass

    # =========================================================================
    # Reglas de Expresiones (Aplanadas con Precedencia)
    # =========================================================================

    def p_expresion_binop(self, p):
        """expresion : expresion MAYOR expresion
        | expresion MENOR expresion
        | expresion NO expresion
        | expresion IGUAL expresion
        | expresion '+' expresion
        | expresion '-' expresion
        | expresion '*' expresion
        | expresion '/' expresion"""
        pass

    def p_expresion_group(self, p):
        """expresion : '(' expresion ')'"""
        pass

    def p_expresion_unary(self, p):
        """expresion : '+' expresion %prec UPLUS
        | '-' expresion %prec UMINUS"""
        pass

    def p_expresion_value(self, p):
        """expresion : ID
        | CTE_ENT
        | CTE_FLOT
        | llamada"""
        pass

    # =========================================================================
    # Reglas Base
    # =========================================================================

    def p_empty(self, p):
        """empty :"""
        pass

    def p_error(self, p):
        if p:
            print(
                f"Error de sintaxis en el token '{p.value}' (Tipo: {p.type}) en la línea {p.lineno}"
            )
        else:
            print("Error de sintaxis: Fin de archivo inesperado")


if __name__ == "__main__":
    import sys

    parser = PatitoParser()
    parser.build()

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = f.read()
    else:
        data = sys.stdin().read()

    parser.parse(data)
