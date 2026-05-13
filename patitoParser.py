import ply.yacc as yacc
from patitoLexer import PatitoLexer
from semanticCube import cube

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
        self.dir_fun = None 
        self.curr_scope = None
        self.glob_scope = None
        self.errors = []

    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, data):
        self.dir_fun = None 
        self.curr_scope = None 
        self.glob_scope = None
        self.errors = []
        self.lexer_obj.lexer.lineno = 1
        try:
            return self.parser.parse(data, lexer=self.lexer_obj.lexer)
        except PatitoSyntaxError:
            return None

    # =========================================================================
    # 1. Reglas de Precedencia - reducir ambiguedad
    # =========================================================================
    precedence = (
        ("nonassoc", "MAYOR", "MENOR", "IGUAL", "NO"),
        ("left", "+", "-"),
        ("left", "*", "/"),
    )

    # =========================================================================
    # 2. Reglas Gramaticales & semántica
    # =========================================================================

    # 2.1 Programa
    def p_programa(self, p):
        """programa : PROGRAMA ng_create_dirf ID ng_add_dirf ';' vars list_funcs INICIO cuerpo FIN ng_del
                    | PROGRAMA ng_create_dirf ID ng_add_dirf ';' list_funcs INICIO cuerpo FIN ng_del
                    | PROGRAMA ng_create_dirf ID ng_add_dirf ';' vars INICIO cuerpo FIN ng_del
                    | PROGRAMA ng_create_dirf ID ng_add_dirf ';' INICIO cuerpo FIN ng_del"""
        if len(p) == 12:
            p[0] = ('programa', p[3], p[6], p[7], p[9])
        elif len(p) == 11:
            p[0] = ('programa', p[3], None, p[6], p[8])
        else:
            p[0] = ('programa', p[3], None, None, p[7])

    def p_ng_create_dirf(self, p):
        """ng_create_dirf : """
        if self.dir_fun is None:
            self.dir_fun = {}

    def p_ng_add_dirf(self, p):
        """ng_add_dirf : """
        self.curr_scope = p[-1] 
        self.glob_scope = p[-1] 
        self.dir_fun[self.curr_scope] = {"type": "nil", "vars": {}, "params": []}

    def p_ng_del(self, p):
        """ng_del : """
        self.curr_scope = None
        self.glob_scope = None

    def p_list_funcs(self, p):
        """list_funcs : funcs list_funcs
                      | funcs"""
        if len(p) == 3:
            p[0] = [p[1]] + (p[2] if p[2] else [])
        else:
            p[0] = [p[1]]

    # 2.2 Variables
    def p_vars(self, p):
        """vars : VARS ng_add_vartable list_decl"""
        p[0] = ('vars', p[3])

    def p_ng_add_vart(self, p):
        """ng_add_vartable : """
        if "vars" not in self.dir_fun[self.curr_scope]:
            self.dir_fun[self.curr_scope]["vars"] = {}    

    def p_list_decl(self, p):
        """list_decl : decl list_decl
                     | decl"""
        if len(p) == 3:
            p[0] = [p[1]] + (p[2] if p[2] else [])
        else:
            p[0] = [p[1]]

    def p_decl(self, p):
        """decl : list_id ':' tipo ng_update_type ';'"""
        p[0] = ('decl', p[1], p[3])

    def p_ng_update_type(self, p):
        """ng_update_type : """
        for v in self.dir_fun[self.curr_scope]["vars"]:
            if self.dir_fun[self.curr_scope]["vars"][v] is None:
                self.dir_fun[self.curr_scope]["vars"][v] = p[-1]

    def p_list_id(self, p):
        """list_id : ID ng_add_var ',' list_id
                   | ID ng_add_var"""
        if len(p) == 5:
            p[0] = [p[1]] + (p[4] if p[4] else [])
        else:
            p[0] = [p[1]]

    def p_ng_add_var(self, p):
        """ng_add_var : """
        if p[-1] in self.dir_fun[self.curr_scope]["vars"]:
            self.errors.append(f"Error: Variable '{p[-1]}' ya declarada")
        else:
            self.dir_fun[self.curr_scope]["vars"][p[-1]] = None

    def p_tipo(self, p):
        """tipo : ENTERO
                | FLOTANTE"""
        if p[1] == "decimal":
            p[0] = "flotante"
        else:
            p[0] = p[1]

    # 2.3 Funciones
    def p_funcs(self, p):
        """funcs : NULA ID ng_add_fun '(' params ')' '{' vars cuerpo '}' ';' ng_del_fun
                 | NULA ID ng_add_fun '(' params ')' '{' cuerpo '}' ';' ng_del_fun
                 | tipo ID ng_add_fun '(' params ')' '{' vars cuerpo '}' ';' ng_del_fun
                 | tipo ID ng_add_fun '(' params ')' '{' cuerpo '}' ';' ng_del_fun"""
        if len(p) == 13:
            p[0] = ('func', p[1], p[2], p[5], p[8], p[9])
        else:
            p[0] = ('func', p[1], p[2], p[5], None, p[8])

    def p_ng_add_fun(self, p):
        """ng_add_fun : """
        name = p[-1]
        tipo = p[-2]
        if name in self.dir_fun:
            self.errors.append(f"Error: Funcion '{name}' ya declarada")
            self.curr_scope = f"__dup_{name}"
            self.dir_fun[self.curr_scope] = {"type": tipo, "vars": {}, "params": []}
        else:
            self.curr_scope = name
            self.dir_fun[self.curr_scope] = {"type": tipo, "vars": {}, "params":[]}

    def p_ng_del_fun(self, p):
        """ng_del_fun : """
        self.curr_scope = self.glob_scope

    def p_params(self, p):
        """params : list_params
                  | empty"""
        p[0] = p[1] if p[1] else []
        if self.curr_scope in self.dir_fun and "params" in self.dir_fun[self.curr_scope]:
            self.dir_fun[self.curr_scope]["params"].reverse()

    def p_list_params(self, p):
        """list_params : ID ng_add_var ':' tipo ng_update_type ',' list_params
                       | ID ng_add_var ':' tipo ng_update_type """
        self.dir_fun[self.curr_scope]["params"].append(p[4])
        if len(p) == 8:
            p[0] = [('param', p[1], p[4])] + (p[7] if p[7] else [])
        else:
            p[0] = [('param', p[1], p[4])]

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
                func_type = self.dir_fun[self.curr_scope]["type"]
                if not isinstance(p[2], tuple):
                    if func_type not in ['nil', 'nula', p[2]]:
                        self.errors.append(f"Error semántico: función '{self.curr_scope}' debe retornar {func_type}, no nula")
                    p[0] = ('return', p[2])
                else:
                    result_type = self.get_result_type(func_type, "=", p[2][1], special=True)
                    if result_type is None:
                        self.errors.append(f"Error semántico: función '{self.curr_scope}' retorna {p[2][1]}, pero se esperaba {func_type}")
                    p[0] = ('return', p[2][1])

    def p_asigna(self, p):
        """asigna : ID '=' expresion ';'"""
        var_type = self.get_var_type(p[1]) 
        result_type = self.get_result_type(var_type, p[2], p[3][1])
        if result_type is None:
            self.errors.append(f"Error semántico: no se puede asignar resultado nulo a '{p[1]}'")
            p[0] = ('assigna error', p[1], p[3])
        else:
            p[0] = ('assigna', p[1], p[3])

    def p_llamada(self, p):
        """llamada : ID '(' args ')'"""
        if p[1] not in self.dir_fun:
            self.errors.append(f"Error seméntico: función {p[1]} no declarada")
            p[0] = ('llamada', p[1], p[3])
            return        

        args = p[3]
        expected_args = self.dir_fun[p[1]]["params"]
        if len(args) != len(expected_args):
            self.errors.append(f"Error semántico: función '{p[1]}' espera {len(expected_args)} argumentos, recibió {len(args)}")
        
        for i in range(min(len(args), len(expected_args))):
            arg_type = args[i][1] 
            param_type = expected_args[i]

            result_type = self.get_result_type(param_type, "=", arg_type, special=True)

            if result_type is None:
                self.errors.append(f"Error semántico: argumento {i+1} de '{p[1]}' debe ser {param_type}, recibió {arg_type}")

        func_type = self.dir_fun[p[1]]["type"] if p[1] in self.dir_fun else None
        if func_type == "nil":
            p[0] = (('llamada', p[1], p[3]), None)
        else:
            p[0] = (('llamada', p[1], p[3]), func_type)

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
        if p[3][1] != "entero":
            self.errors.append(f"Error semántico: condición de 'mientras' debe ser entero, no {p[3][1]}")
        p[0] = ('mientras', p[3], p[6])

    def p_condicion(self, p):
        """condicion : SI '(' expresion ')' cuerpo ';'
                     | SI '(' expresion ')' cuerpo SINO cuerpo ';'"""

        if p[3][1] != "entero":
            self.errors.append(f"Error semántico: condición de 'si' debe ser entero, no {p[3][1]}")

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
            result_type = self.get_result_type(p[1][1], p[2], p[3][1])

            if result_type is None:
                p[0] = (None, None)
            else:
                p[0] = (
                    ('binop', p[2], p[1][0], p[3][0]),
                    result_type
                )

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
            result_type = self.get_result_type(p[1][1], p[2], p[3][1])

            if result_type is None:
                p[0] = (None, None)
            else:
                p[0] = (
                    ('binop', p[2], p[1][0], p[3][0]),
                    result_type
                )

    def p_termino(self, p):
        """termino : factor
                   | factor '*' termino
                   | factor '/' termino"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            result_type = self.get_result_type(p[1][1], p[2], p[3][1])

            if result_type is None:
                p[0] = (None, None)
            else:
                p[0] = (
                    ('binop', p[2], p[1][0], p[3][0]),
                    result_type
                )

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
            if isinstance(p[2], str):
                var_type = self.get_var_type(p[2])
                p[0] = (('unary', p[1], p[2]), var_type)
            else:
                p[0] = (('unary', p[1], p[2][0]), p[2][1])
        else:
            value = p[1]

            if isinstance(value, str):
                var_type = self.get_var_type(value)
                p[0] = (value, var_type)
            else:
                p[0] = value

    def p_cte(self, p):
        """cte : CTE_ENT
               | CTE_FLOT"""
        p[0] = (p[1], self.get_cte_type(p[1]))


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
    # 3. Helpers para semántica
    # =========================================================================

    def get_var_type(self, var_name):
        if var_name in self.dir_fun[self.curr_scope]["vars"]:
            return self.dir_fun[self.curr_scope]["vars"][var_name]

        if var_name in self.dir_fun[self.glob_scope]["vars"]:
            return self.dir_fun[self.glob_scope]["vars"][var_name]

        self.errors.append(f"Error semántico: variable '{var_name}' no declarada")
        return None

    def get_cte_type(self, value):
        if isinstance(value, int):
            return "entero"

        if isinstance(value, float):
            return "flotante"

        self.errors.append(f"Error semántico: constante inválida '{value}'")
        return None

    def get_result_type(self, left_type, operator, right_type, special=False):
        result_type = cube.get(operator, {}).get(left_type, {}).get(right_type)

        if result_type is None:
            if not special: 
                self.errors.append(f"Error semántico: operación inválida {left_type} {operator} {right_type}")
            return None

        return result_type


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
    if parser.errors:
        for err in parser.errors:
            print(err)
    else:
        pprint.pprint(ast)
        print()
        pprint.pprint(parser.dir_fun)
