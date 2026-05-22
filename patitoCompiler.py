from collections import deque
from patitoParser import PatitoParser
from semanticCube import cube

class PatitoCompilerError(Exception):
    pass


class PatitoCompiler(PatitoParser):
    """
    Chequeo de semántica y generación de IR para patito lenguaje
    """

    PENDING = 111
    ERROR = 201

    def __init__(self):
        super().__init__()

        self.dir_fun = None 
        self.curr_scope = None
        self.glob_scope = None

        self.generate_quads = True

        self.poper = []
        self.pilao = []
        self.ptypes = []

        self.quads = deque()
        self.temp_count = 0


    def parse(self, data):
        self.dir_fun = None 
        self.curr_scope = None 
        self.glob_scope = None

        self.generate_quads = True

        self.poper = []
        self.pilao = []
        self.ptypes = []

        self.quads = deque()
        self.temp_count = 0

        return super().parse(data)

    # =========================================================================
    # 1. Reglas de semántica
    # =========================================================================

    # 1.1 Program init
    def p_ng_add_dirf(self, p):
        """ng_add_dirf : """
        id = p[-1]
        self.dir_fun = {}
        self.curr_scope = id 
        self.glob_scope = id 
        self.dir_fun[self.curr_scope] = {"type": "nil", "vars": {}, "params": []}

    # 1.2 Vars
    def p_ng_add_vartable(self, p):
        """ng_add_vartable : """
        if "vars" not in self.dir_fun[self.curr_scope]:
            self.dir_fun[self.curr_scope]["vars"] = {}    

    def p_ng_update_type(self, p):
        """ng_update_type : """
        var_type = p[-1]

        for var_id in self.dir_fun[self.curr_scope]["vars"]:
            if self.dir_fun[self.curr_scope]["vars"][var_id] == self.PENDING:
                self.dir_fun[self.curr_scope]["vars"][var_id] = var_type 

    def p_ng_add_var(self, p):
        """ng_add_var : """
        var_id = p[-1]

        if var_id in self.dir_fun[self.curr_scope]["vars"]:
            self.errors.append(f"Error: Variable '{var_id}' ya declarada")
        else:
            self.dir_fun[self.curr_scope]["vars"][var_id] = self.PENDING 
    
    # 1.3 Functions
    def p_funcs(self, p):
        """funcs : NULA ID ng_add_fun '(' list_params ')' '{' vars cuerpo '}' ';' ng_del_fun
                 | NULA ID ng_add_fun '(' list_params ')' '{' cuerpo '}' ';' ng_del_fun
                 | tipo ID ng_add_fun '(' list_params ')' '{' vars cuerpo '}' ';' ng_del_fun
                 | tipo ID ng_add_fun '(' list_params ')' '{' cuerpo '}' ';' ng_del_fun"""
        func_id = p[2]
        target_scope = f"__dup_{func_id}" if f"__dup_{func_id}" in self.dir_fun else func_id
        if target_scope in self.dir_fun:
            self.dir_fun[target_scope]["params"].reverse()

    def p_ng_add_fun(self, p):
        """ng_add_fun : """
        func_id = p[-1]
        func_type = p[-2]

        if func_id in self.dir_fun:
            self.errors.append(f"Error: Funcion '{func_id}' ya declarada")
            self.curr_scope = f"__dup_{func_id}"
            self.dir_fun[self.curr_scope] = {"type": func_type, "vars": {}, "params": []}
            self.generate_quads = False
        else:
            self.curr_scope = func_id 
            self.dir_fun[self.curr_scope] = {"type": func_type, "vars": {}, "params": []}

    def p_ng_del_fun(self, p):
        """ng_del_fun : """
        self.curr_scope = self.glob_scope
        self.generate_quads = True

    def p_list_params(self, p):
        """list_params : ID ng_add_var ':' tipo ng_update_type ',' list_params
                       | ID ng_add_var ':' tipo ng_update_type 
                       | empty"""
        if len(p) != 2:
            param_type = p[4]
            self.dir_fun[self.curr_scope]["params"].append(param_type)

    # 1.4 Estatutos
    def p_ng_quad_assign(self, p):
        """ng_quad_assign : """
        if not self.generate_quads:
            return

        var_id = p[-2]
        self.pilao.append(var_id)
        var_type = self._get_var_type(var_id)
        self.ptypes.append(var_type)

        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_assign_end(self, p):
        """ng_quad_assign_end : """
        if not self.generate_quads:
            return

        if self.poper and self.poper[-1] == '=':
            self._create_assign_quad()
            

    # 1.5 Expresiones
    def p_ng_quad_relop(self, p):
        """ng_quad_relop : """
        if not self.generate_quads:
            return
            
        if self.poper and self.poper[-1] in ['<', '>', '!=', '==']:
            self._create_expr_quad()

        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_term(self, p):
        """ng_quad_term : """
        if not self.generate_quads:
            return
            
        if self.poper and self.poper[-1] in ['+', '-']:
            self._create_expr_quad()

        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_fact(self, p):
        """ng_quad_fact : """
        if not self.generate_quads:
            return

        if self.poper and self.poper[-1] in ['*', '/']:
            self._create_expr_quad()

        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_id(self, p):
        """ng_quad_id : """
        if not self.generate_quads:
            return

        var_id = p[-1]
        self.pilao.append(var_id)
        var_type = self._get_var_type(var_id)
        self.ptypes.append(var_type)

    def p_ng_quad_sign_id(self, p):
        """ng_quad_sign_id : """
        if not self.generate_quads:
            return

        sign = p[-2]
        var_id = p[-1]
        var_type = self._get_var_type(var_id)

        if sign == "+":
            self.pilao.append(var_id)
            self.ptypes.append(var_type)
            return

        temp = f"t{self.temp_count}"
        self.temp_count += 1

        self.quads.append(["UMINUS", var_id, "_", temp])

        self.pilao.append(temp)
        self.ptypes.append(var_type)

    def p_ng_quad_cte(self, p):
        """ng_quad_cte : """
        if not self.generate_quads:
            return

        cte_val = p[-1]
        self.pilao.append(cte_val)
        cte_type = self._get_cte_type(cte_val)
        self.ptypes.append(cte_type)

    def p_ng_quad_sign_cte(self, p):
        """ng_quad_sign_cte : """
        if not self.generate_quads:
            return

        sign = p[-2]
        cte_val = p[-1]
        if sign == '-':
            cte_val = - cte_val

        self.pilao.append(cte_val)
        cte_type = self._get_cte_type(cte_val)
        self.ptypes.append(cte_type)


    # =========================================================================
    # 3. Helpers para semántica
    # =========================================================================

    def _get_var_type(self, var_name):
        if var_name in self.dir_fun[self.curr_scope]["vars"]:
            return self.dir_fun[self.curr_scope]["vars"][var_name]

        if var_name in self.dir_fun[self.glob_scope]["vars"]:
            return self.dir_fun[self.glob_scope]["vars"][var_name]

        self.errors.append(f"Error semántico: variable '{var_name}' no declarada")
        return self.ERROR 

    def _get_cte_type(self, value):
        if isinstance(value, int):
            return "entero"

        if isinstance(value, float):
            return "flotante"

        self.errors.append(f"Error semántico: constante inválida '{value}'")
        return self.ERROR

    def _get_result_type(self, left_type, operator, right_type):
        result_type = cube.get(operator, {}).get(left_type, {}).get(right_type)

        if result_type is None: 
            return self.ERROR 

        return result_type
    
    def _create_expr_quad(self):
        right_operand = self.pilao.pop()
        left_operand = self.pilao.pop()

        right_type = self.ptypes.pop()
        left_type = self.ptypes.pop()

        operator = self.poper.pop()

        result_type = self._get_result_type(left_type, operator, right_type)

        print(left_type, operator, right_type, "->", result_type)
        if result_type == self.ERROR:
            self.errors.append(f"Error semántico: operación inválida {left_type} {operator} {right_type}")
            return
        
        result = f't{self.temp_count}'
        quad = [operator, left_operand, right_operand, result]
        self.quads.append(quad)
        self.temp_count += 1

        self.pilao.append(result)
        self.ptypes.append(result_type)
    
    def _create_assign_quad(self):
        right_operand = self.pilao.pop()
        right_type = self.ptypes.pop()

        left_operand = self.pilao.pop()
        left_type = self.ptypes.pop()

        operator = self.poper.pop()

        result_type = self._get_result_type(left_type, operator, right_type)

        if result_type == self.ERROR:
            self.errors.append(f"Error semántico: asignación inválida {left_type} {operator} {right_type}")
            return
        
        quad = [operator, right_operand, "_", left_operand]
        self.quads.append(quad)
        
def main():
    import sys
    import argparse
    import pprint

    arg_parser = argparse.ArgumentParser(description="Patito compiler")
    arg_parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Patito source file (default: stdin)",
    )
    arg_parser.add_argument("-o", "--optimize", action="store_true", help="Generate parser optimize")
    args = arg_parser.parse_args()
    data = args.file.read()

    my_compiler = PatitoCompiler()
    my_compiler.build(optimize=args.optimize) if args.optimize else my_compiler.build()

    ok = my_compiler.parse(data)

    if not ok:
        for err in my_compiler.errors:
            print(err)
    else:
        print("Compile OK")
    pprint.pprint(my_compiler.dir_fun)
    pprint.pprint(my_compiler.quads)


if __name__ == "__main__":
    main()