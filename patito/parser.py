import os
import sys
import ply.yacc as yacc
from .lexer import PatitoLexer

class PatitoSyntaxError(Exception):
    pass


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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(current_dir, ".ply_cache")
        os.makedirs(cache_dir, exist_ok=True)

        if cache_dir not in sys.path:
            sys.path.insert(0, cache_dir)

        self.parser = yacc.yacc(
            module=self,
            tabmodule="parsetab",
            outputdir=cache_dir,
            **kwargs
        )

    def parse(self, data):
        self.lexer_obj.lexer.lineno = 1
        self.errors = []
        
        try:
            self.parser.parse(data, lexer=self.lexer_obj.lexer)
            return len(self.errors) == 0
        except PatitoSyntaxError:
            return False

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
        """programa : PROGRAMA ID ng_add_dirf ';' vars list_funcs INICIO cuerpo FIN
                    | PROGRAMA ID ng_add_dirf ';' list_funcs INICIO cuerpo FIN
                    | PROGRAMA ID ng_add_dirf ';' vars INICIO cuerpo FIN
                    | PROGRAMA ID ng_add_dirf ';' INICIO cuerpo FIN"""

    def p_list_funcs(self, p):
        """list_funcs : funcs list_funcs
                      | funcs"""

    # 2.2 Variables
    def p_vars(self, p):
        """vars : VARS ng_add_vartable list_decl"""

    def p_list_decl(self, p):
        """list_decl : list_id ':' tipo ng_update_type ';' list_decl
                     | list_id ':' tipo ng_update_type ';'"""

    def p_list_id(self, p):
        """list_id : ID ng_add_var ',' list_id
                   | ID ng_add_var"""

    def p_tipo(self, p):
        """tipo : ENTERO
                | FLOTANTE"""
        if p[1] == "decimal":
            p[0] = "flotante"
        else:
            p[0] = p[1]

    # 2.3 Funciones
    def p_funcs(self, p):
        """funcs : NULA ID ng_add_fun '(' list_params ')' '{' vars cuerpo '}' ';' ng_del_fun
                 | NULA ID ng_add_fun '(' list_params ')' '{' cuerpo '}' ';' ng_del_fun
                 | tipo ID ng_add_fun '(' list_params ')' '{' vars cuerpo '}' ';' ng_del_fun
                 | tipo ID ng_add_fun '(' list_params ')' '{' cuerpo '}' ';' ng_del_fun"""
    
    def p_list_params(self, p):
        """list_params : ID ng_add_var ':' tipo ng_update_type ',' list_params
                       | ID ng_add_var ':' tipo ng_update_type 
                       | empty"""

    # 2.4 Cuerpo
    def p_cuerpo(self, p):
        """cuerpo : '{' list_estatuto '}'"""

    # 2.5 Estatutos
    def p_list_estatuto(self, p):
        """list_estatuto : asigna list_estatuto
                        | condicion list_estatuto
                        | ciclo list_estatuto
                        | llamada ';' list_estatuto
                        | imprime list_estatuto
                        | '[' list_estatuto ']' list_estatuto
                        | RETURN NULA ';' list_estatuto
                        | RETURN expresion ';' list_estatuto
                        | empty"""

    def p_asigna(self, p):
        """asigna : ID '=' ng_quad_assign expresion ';' ng_quad_assign_end"""

    def p_llamada(self, p):
        """llamada : ID '(' list_expresion ')'"""

    def p_list_expresion(self, p):
        """list_expresion : expresion ',' list_expresion
                          | expresion
                          | empty"""

    def p_imprime(self, p):
        """imprime : ESCRIBE '(' list_imprime ')' ';'"""

    def p_list_imprime(self, p):
        """list_imprime : expresion ng_add_print ',' list_imprime
                        | LETRERO ng_add_print ',' list_imprime
                        | expresion ng_add_print
                        | LETRERO ng_add_print"""

    def p_ciclo(self, p):
        """ciclo : MIENTRAS ng_add_jump '(' expresion ')' ng_quad_if HAZ cuerpo ng_quad_while_end ';'"""

    def p_condicion(self, p):
        """condicion : SI '(' expresion ')' ng_quad_if cuerpo ';' ng_quad_if_end
                     | SI '(' expresion ')' ng_quad_if cuerpo SINO ng_quad_else cuerpo ';' ng_quad_if_end"""

    # 2.6 Expresiones
    def p_expresion(self, p):
        """expresion : exp ng_quad_exp_end
                     | exp ng_quad_exp_end relop ng_quad_relop exp ng_quad_exp_end"""

    def p_relop(self, p):
        """relop : MENOR
                 | MAYOR
                 | NO
                 | IGUAL"""
        p[0] = p[1]

    def p_exp(self, p):
        """exp : termino ng_quad_term_end
               | termino ng_quad_term_end '+' ng_quad_term exp
               | termino ng_quad_term_end '-' ng_quad_term exp"""

    def p_termino(self, p):
        """termino : factor ng_quad_fact_end
                   | factor ng_quad_fact_end '*' ng_quad_fact termino
                   | factor ng_quad_fact_end '/' ng_quad_fact termino"""

    def p_factor(self, p):
        """factor : '(' expresion ')' 
                  | '+' ID ng_quad_sign_id
                  | '-' ID ng_quad_sign_id
                  | ID ng_quad_id
                  | '+' cte ng_quad_sign_cte
                  | '-' cte ng_quad_sign_cte
                  | cte ng_quad_cte
                  | llamada"""

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
            self.errors.append(msg)
        else:
            msg = "Error de sintaxis: Fin de archivo inesperado"
            self.errors.append(msg)
        raise PatitoSyntaxError(msg)

    # =========================================================================
    # 4. Funciones de puntos neurálgicos 
    # =========================================================================
    # (SOLO SE DEFINEN PARA NO CAUSAR ERROR CUANDO SE EJECUTA EL PARSER INDIVIDUALMENTE)

    _hidden_rules = {
        "p_ng_add_dirf": "ng_add_dirf : ",
        "p_ng_add_vartable": "ng_add_vartable : ",

        "p_ng_update_type": "ng_update_type : ",
        "p_ng_add_var": "ng_add_var : ",

        "p_ng_add_fun": "ng_add_fun : ",
        "p_ng_del_fun": "ng_del_fun : ",

        "p_ng_quad_assign": "ng_quad_assign : ",
        "p_ng_quad_assign_end": "ng_quad_assign_end : ",

        "p_ng_add_print": "ng_add_print : ",

        "p_ng_add_jump": "ng_add_jump : ",
        "p_ng_quad_while_end": "ng_quad_while_end : ",

        "p_ng_quad_if": "ng_quad_if : ",
        "p_ng_quad_else": "ng_quad_else : ",
        "p_ng_quad_if_end": "ng_quad_if_end : ",

        "p_ng_quad_exp_end": "ng_quad_exp_end : ",
        "p_ng_quad_relop": "ng_quad_relop : ",

        "p_ng_quad_term": "ng_quad_term : ",
        "p_ng_quad_term_end": "ng_quad_term_end : ",

        "p_ng_quad_fact": "ng_quad_fact : ",
        "p_ng_quad_fact_end": "ng_quad_fact_end : ",

        "p_ng_quad_id": "ng_quad_id : ",
        "p_ng_quad_sign_id": "ng_quad_sign_id : ",
        "p_ng_quad_cte": "ng_quad_cte : ",
        "p_ng_quad_sign_cte": "ng_quad_sign_cte : ",
    }

    for _name, _doc in _hidden_rules.items():
        def _dummy(self, p): pass
        _dummy.__doc__ = _doc
        locals()[_name] = _dummy

    del _name, _doc, _dummy, _hidden_rules



def main():
    import argparse

    arg_parser = argparse.ArgumentParser(description="Patito parser")
    arg_parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="Patito source file (default: stdin)",
    )
    arg_parser.add_argument("-o", "--optimize", action="store_true", help="Generate parser optimize")
    args = arg_parser.parse_args()
    data = args.file.read()

    my_parser = PatitoParser()
    my_parser.build(optimize=args.optimize) if args.optimize else my_parser.build()

    ok = my_parser.parse(data)

    if not ok:
        for err in my_parser.errors:
            print(err)
    else:
        print("Syntax OK")

if __name__ == "__main__":
    main()
