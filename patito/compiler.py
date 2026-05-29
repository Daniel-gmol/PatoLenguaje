from collections import deque
from .parser import PatitoParser
from .memory import VirtualMemory
from .semantic_cube import cube

class PatitoCompilerError(Exception):
    pass


class PatitoCompiler(PatitoParser):
    """
    Chequeo de semántica y generación de IR para patito lenguaje
    """

    PENDING = 111
    ERROR = "ERROR"

    def __init__(self, keep: bool = False):
        super().__init__()

        self.keep = keep

        self.memory = VirtualMemory() 
        self.addr_names = {}
        self.quad_scopes = []

        self.dir_fun = None 
        self.curr_scope = None
        self.glob_scope = None

        self.generate_quads = True

        self.poper = []
        self.pilao = []
        self.ptypes = []
        self.pjumps = []

        self.quads = deque()
        self.temp_count = 0

        self.param_inx = 0
        self.curr_call = None

    def parse(self, data):
        self.memory = VirtualMemory() 
        self.addr_names = {}
        self.quad_scopes = []

        self.dir_fun = None 
        self.curr_scope = None 
        self.glob_scope = None

        self.generate_quads = True

        self.poper = []
        self.pilao = []
        self.ptypes = []
        self.pjumps = []

        self.quads = deque()
        self.temp_count = 0

        self.param_inx = 0
        self.curr_call = None

        try:
            return super().parse(data)
        except PatitoCompilerError:
            return False

    # =========================================================================
    # 1. Reglas de semántica & Generación IR
    # =========================================================================

    # 1.1 Program init
    def p_ng_add_dirf(self, p):
        """ng_add_dirf : """
        id = p[-1]
        self.dir_fun = {}
        self.curr_scope = id 
        self.glob_scope = id 
        self.dir_fun[self.curr_scope] = {
            "type": "nil", 
            "resources": {
                "local_int": 0,
                "local_float": 0,
                "temp_int": 0,
                "temp_float": 0,
            },
            "vars": {}
        }
        self._add_quad(["GOTO", '_', '_', '_'])

    def p_ng_main(self, p):
        """ng_main : """
        self.quads[0][3] = len(self.quads)

    def p_ng_del_dirf(self, p):
        """ng_del_dirf : """
        if not self.keep:
            self.dir_fun = None 
            self.curr_scope = None
            self.glob_scope = None

    # 1.2 Vars
    def p_ng_add_vartable(self, p):
        """ng_add_vartable : """
        if "vars" not in self.dir_fun[self.curr_scope]:
            self.dir_fun[self.curr_scope]["vars"] = {}    

    def p_ng_update_type(self, p):
        """ng_update_type : """
        var_type = p[-1]

        for var_id, details in self.dir_fun[self.curr_scope]["vars"].items():
            if details["type"] == self.PENDING:
                segment = "global" if self.curr_scope == self.glob_scope else "local"

                address = self.memory.alloc(segment, var_type)

                details["type"] = var_type
                details["address"] = address

                self._register_name(address, var_id)
                self._add_resource("local", var_type)

    def p_ng_add_var(self, p):
        """ng_add_var : """
        var_id = p[-1]

        if var_id in self.dir_fun[self.curr_scope]["vars"]:
            self.errors.append(f"Error: Variable '{var_id}' ya declarada")
        else:
            self.dir_fun[self.curr_scope]["vars"][var_id] = {"type": self.PENDING, "address": self.PENDING}
    
    # 1.3 Functions
    def p_funcs(self, p):
        """funcs : NULA ID ng_add_fun '(' list_params ')' '{' vars cuerpo '}' ';' ng_del_fun
                 | NULA ID ng_add_fun '(' list_params ')' '{' cuerpo '}' ';' ng_del_fun
                 | tipo ID ng_add_fun '(' list_params ')' '{' vars cuerpo '}' ';' ng_del_fun
                 | tipo ID ng_add_fun '(' list_params ')' '{' cuerpo '}' ';' ng_del_fun"""
        func_id = p[2]
        target_scope = f"__dup_{func_id}" if f"__dup_{func_id}" in self.dir_fun else func_id
        self.dir_fun[target_scope]["params"].reverse()

    def p_ng_add_fun(self, p):
        """ng_add_fun : """
        func_id = p[-1]
        func_type = p[-2]
        next_dip = len(self.quads)

        if func_id in self.dir_fun: #semantics
            self.errors.append(f"Error: Funcion '{func_id}' ya declarada")
            self.curr_scope = f"__dup_{func_id}"
            self.generate_quads = False
            self.dir_fun[self.curr_scope] = {
                "type": func_type, 
                "vars": {},
                "params": [],
                "resources": {"local_int": 0, "local_float": 0, "temp_int": 0, "temp_float": 0},
                "dips": None,
                "dipe": None
            }
        else:
            if func_type != 'nil':
                func_return = '__return_' + func_id
                address = self.memory.alloc("global", func_type)
                self.dir_fun[self.glob_scope]["vars"][func_return] = {"type": func_type, "address": address}
                self._register_name(address, func_return)
                self._add_resource("local", func_type)

            self.curr_scope = func_id 
            self.dir_fun[self.curr_scope] = {
                "type": func_type, 
                "vars": {},
                "params": [],
                "resources": {"local_int": 0, "local_float": 0, "temp_int": 0, "temp_float": 0},
                "dips": next_dip,
                "dipe": None
            }

        self.memory.reset_local_temps()
        self.temp_count = 0

    def p_ng_del_fun(self, p):
        """ng_del_fun : """
        if not self.keep:
            del self.dir_fun[self.curr_scope]["vars"]
        if self.generate_quads:
            self.dir_fun[self.curr_scope]["dipe"] = len(self.quads)
            self._add_quad(["ENDFUNC", '_', '_', '_'])
        self.curr_scope = self.glob_scope
        self.generate_quads = True
        self.memory.reset_local_temps()
        self.temp_count = 0

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
        var_type = self._get_var_type(var_id)
        var_addr = self._get_var_addr(var_id)

        self.pilao.append(var_addr)
        self.ptypes.append(var_type)

        op = p[-1]
        self.poper.append(op)

    # 1.4.1 Asignación
    def p_ng_quad_assign_end(self, p):
        """ng_quad_assign_end : """
        if not self.generate_quads:
            return

        if self.poper and self.poper[-1] == '=':
            self._create_assign_quad()

    # 1.4.2 Llamadas a funciones
    def p_ng_quad_call(self, p):
        """ng_quad_call : """
        if not self.generate_quads:
            return

        func_id = p[-1]
        if self.dir_fun.get(func_id, None) is None:
            msg = f"Error: La funcion '{func_id}' no esta definida."
            self.errors.append(msg)
            raise PatitoCompilerError(msg)

        self._add_quad(['ERA', '_', '_', func_id])

        self.param_inx = 0
        self.curr_call = func_id

    def p_ng_quad_call_end(self, p):
        """ng_quad_call_end : """
        if not self.generate_quads:
            return

        fun_id = self.curr_call
        arg_size = self.param_inx
        par_size = len(self.dir_fun[fun_id]["params"])

        if arg_size != par_size:
            self.errors.append(f"Error: La funcion '{fun_id}' esperaba {par_size} argumentos y se recibieron {arg_size}")
        self._add_quad(['GOSUB', '_', '_', fun_id])

        fun_var = '__return_' + fun_id
        if self.dir_fun[fun_id]["type"] != "nil":
            fun_addr = self.dir_fun[self.glob_scope]["vars"][fun_var]["address"]
            fun_type = self.dir_fun[self.glob_scope]["vars"][fun_var]["type"]

            tmp_addr = self.memory.alloc("temp", fun_type)
            self._register_name(tmp_addr, f"t{self.temp_count}")
            self.temp_count += 1
            self._add_resource("temp", fun_type)
            self._add_quad(['=', fun_addr, '_', tmp_addr])
            self.pilao.append(tmp_addr)
            self.ptypes.append(fun_type)

        self.curr_call = None
        self.param_inx = 0

    def p_ng_quad_arg(self, p):
        """ng_quad_arg : """
        if not self.generate_quads:
            return

        arg = self.pilao.pop()
        arg_type = self.ptypes.pop()

        if self.param_inx >= len(self.dir_fun[self.curr_call]["params"]):
            self.errors.append(f"Error: Demasiados argumentos para la funcion '{self.curr_call}'")
            return

        par_type = self.dir_fun[self.curr_call]["params"][self.param_inx]

        if arg_type != par_type:
            self.errors.append(f"Error: El tipo {arg_type} del argumento no coincide con el tipo de parametro {par_type}")

        self._add_quad(["PARAM", arg, '_', self.param_inx])
        self.param_inx += 1
        
    def p_ng_quad_ret(self, p):
        """ng_quad_ret : """
        if not self.generate_quads:
            return

        is_nil_return = (p[-1] == "nil")

        if is_nil_return:
            ret_val = "nil"
            ret_type = "nil"
        else:
            ret_val = self.pilao.pop()
            ret_type = self.ptypes.pop()

        fun_type = self.dir_fun[self.curr_scope]["type"]
        if ret_type != fun_type:
            self.errors.append(f"Error: El tipo {ret_type} del valor de retorno no coincide con el tipo de funcion {fun_type}")

        if self.curr_scope == self.glob_scope:
            self._add_quad(['END', '_', '_', '_'])
            return
        
        if ret_type != 'nil':
            global_return = '__return_' + self.curr_scope
            global_return_addr = self.dir_fun[self.glob_scope]["vars"][global_return]["address"]
            self._add_quad(['RET', ret_val, '_', global_return_addr])

        self._add_quad(['GOTOEND', '_', '_', self.curr_scope])

    # 1.4.3 Imprimir
    def p_ng_add_print(self, p):
        """ng_add_print : """
        if not self.generate_quads:
            return

        print_arg = p[-1]
        if print_arg is None: 
            var_addr = self.pilao.pop()
            self.ptypes.pop()
        else:
            var_addr = self.memory.alloc_const(print_arg, "string")
            self._register_name(var_addr, print_arg) 
        
        self._add_quad(["PRINT", '_', '_', var_addr])

    # 1.4.4 Ciclos
    def p_ng_add_jump(self, p):
        """ng_add_jump : """
        if not self.generate_quads:
            return

        jump_inx = len(self.quads)
        self.pjumps.append(jump_inx)

    def p_ng_quad_while_end(self, p):
        """ng_quad_while_end : """
        if not self.generate_quads:
            return

        jmp_inx_false = self.pjumps.pop()
        jmp_inx_rep = self.pjumps.pop()
        self._add_quad(['GOTO', '_', '_', jmp_inx_rep])
        self.quads[jmp_inx_false][3] = len(self.quads)

    # 1.4.5 Condicionales
    def p_ng_quad_if(self, p):
        """ng_quad_if : """
        if not self.generate_quads:
            return

        condition = self.pilao.pop()
        self.ptypes.pop() #type condition
        jmp_inx = len(self.quads)
        self._add_quad(['GOTOF', condition, '_', '_'])
        self.pjumps.append(jmp_inx)

    def p_ng_quad_else(self, p):
        """ng_quad_else : """
        if not self.generate_quads:
            return

        jmp_inx_false = self.pjumps.pop()

        jmp_inx = len(self.quads)
        self._add_quad(['GOTO', '_', '_', '_'])

        self.quads[jmp_inx_false][3] = len(self.quads)

        self.pjumps.append(jmp_inx)
        
    def p_ng_quad_if_end(self, p):
        """ng_quad_if_end : """
        if not self.generate_quads:
            return

        end_jmp = self.pjumps.pop()
        self.quads[end_jmp][3] = len(self.quads)

    # 1.5 Expresiones
    def p_ng_add_false_bottom(self, p):
        """ng_add_false_bottom : """
        if not self.generate_quads:
            return
        self.poper.append('(')

    def p_ng_remove_false_bottom(self, p):
        """ng_remove_false_bottom : """
        if not self.generate_quads:
            return
        self.poper.pop()

    def p_ng_quad_relop(self, p):
        """ng_quad_relop : """
        if not self.generate_quads:
            return
            
        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_exp_end(self, p):
        """ng_quad_exp_end : """
        if not self.generate_quads:
            return

        if self.poper and self.poper[-1] in ['>', '<', '!=', '==']:
            self._create_expr_quad()

    def p_ng_quad_term(self, p):
        """ng_quad_term : """
        if not self.generate_quads:
            return

        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_term_end(self, p):
        """ng_quad_term_end : """
        if not self.generate_quads:
            return
            
        if self.poper and self.poper[-1] in ['+', '-']:
            self._create_expr_quad()

    def p_ng_quad_fact(self, p):
        """ng_quad_fact : """
        if not self.generate_quads:
            return

        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_fact_end(self, p):
        """ng_quad_fact_end : """
        if not self.generate_quads:
            return

        if self.poper and self.poper[-1] in ['*', '/']:
            self._create_expr_quad()

    def p_ng_quad_id(self, p):
        """ng_quad_id : """
        if not self.generate_quads:
            return

        var_id = p[-1]
        var_type = self._get_var_type(var_id)
        var_addr = self._get_var_addr(var_id)

        self.pilao.append(var_addr)
        self.ptypes.append(var_type)

    def p_ng_quad_sign_id(self, p):
        """ng_quad_sign_id : """
        if not self.generate_quads:
            return

        sign = p[-2]

        var_id = p[-1]
        var_type = self._get_var_type(var_id)
        var_addr = self._get_var_addr(var_id)

        if sign == "+":
            self.pilao.append(var_addr)
            self.ptypes.append(var_type)
            return

        result_addr = self.memory.alloc("temp", var_type)
        self._register_name(result_addr, f"t{self.temp_count}")
        self.temp_count += 1
        self._add_resource("temp", var_type)

        self._add_quad(["UMINUS", var_addr, "_", result_addr]) #TODO: es lo mejor o manejo como '-'
        self.pilao.append(result_addr)
        self.ptypes.append(var_type)

    def p_ng_quad_cte(self, p):
        """ng_quad_cte : """
        if not self.generate_quads:
            return

        cte_val = p[-1]
        cte_type = self._get_cte_type(cte_val)
        cte_address = self.memory.alloc_const(cte_val, cte_type)
        self._register_name(cte_address, cte_val)

        self.pilao.append(cte_address)
        self.ptypes.append(cte_type)

    def p_ng_quad_sign_cte(self, p):
        """ng_quad_sign_cte : """
        if not self.generate_quads:
            return

        sign = p[-2]

        cte_val = -p[-1] if sign == '-' else p[-1]
        cte_type = self._get_cte_type(cte_val)
        cte_address = self.memory.alloc_const(cte_val, cte_type)
        self._register_name(cte_address, cte_val)

        self.pilao.append(cte_address)
        self.ptypes.append(cte_type)

    # =========================================================================
    # 2. Helpers para semántica
    # =========================================================================

    def _get_var_type(self, var_name):
        if var_name in self.dir_fun[self.curr_scope]["vars"]:
            return self.dir_fun[self.curr_scope]["vars"][var_name]["type"]

        if var_name in self.dir_fun[self.glob_scope]["vars"]:
            return self.dir_fun[self.glob_scope]["vars"][var_name]["type"]

        self.errors.append(f"Error semántico: variable '{var_name}' no declarada")
        return self.ERROR 

    def _get_var_addr(self, var_name):
        if var_name in self.dir_fun[self.curr_scope]["vars"]:
            return self.dir_fun[self.curr_scope]["vars"][var_name]["address"]

        if var_name in self.dir_fun[self.glob_scope]["vars"]:
            return self.dir_fun[self.glob_scope]["vars"][var_name]["address"]

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
    
    def _register_name(self, address, name):
        if self.curr_scope not in self.addr_names:
            self.addr_names[self.curr_scope] = {}
        self.addr_names[self.curr_scope][address] = name
        
    def _add_resource(self, kind, var_type, scope=None):
        if scope is None:
            scope = self.curr_scope
        
        if kind == "temp" and var_type == "entero":
            self.dir_fun[scope]["resources"]["temp_int"] += 1
        elif kind == "temp" and var_type == "flotante":
            self.dir_fun[scope]["resources"]["temp_float"] += 1
        elif kind == "local" and var_type == "entero":
            self.dir_fun[scope]["resources"]["local_int"] += 1
        elif kind == "local" and var_type == "flotante":
            self.dir_fun[scope]["resources"]["local_float"] += 1

    def _add_quad(self, quad):
        self.quads.append(quad)
        self.quad_scopes.append(self.curr_scope)
    
    #TODO: simplify expr quad and assign quad into a single one
    def _create_expr_quad(self):
        right_operand = self.pilao.pop()
        left_operand = self.pilao.pop()

        right_type = self.ptypes.pop()
        left_type = self.ptypes.pop()

        operator = self.poper.pop()

        if left_type == self.ERROR or right_type == self.ERROR:
            self.pilao.append(self.ERROR)
            self.ptypes.append(self.ERROR)
            return

        result_type = self._get_result_type(left_type, operator, right_type)

        # print(left_type, operator, right_type, "->", result_type)
        if result_type == self.ERROR:
            self.errors.append(f"Error semántico: operación inválida {left_type} {operator} {right_type}")
            self.pilao.append(self.ERROR)
            self.ptypes.append(self.ERROR)
            return
        
        result_addr = self.memory.alloc("temp", result_type)
        self._register_name(result_addr, f't{self.temp_count}')
        self.temp_count += 1
        self._add_resource("temp", result_type)

        self._add_quad([operator, left_operand, right_operand, result_addr])
        self.pilao.append(result_addr)
        self.ptypes.append(result_type)
    
    def _create_assign_quad(self):
        right_operand = self.pilao.pop()
        right_type = self.ptypes.pop()

        left_operand = self.pilao.pop()
        left_type = self.ptypes.pop()

        operator = self.poper.pop()

        if left_type == self.ERROR or right_type == self.ERROR:
            self.pilao.append(left_operand)
            self.ptypes.append(self.ERROR)
            return

        result_type = self._get_result_type(left_type, operator, right_type)

        if result_type == self.ERROR:
            self.errors.append(f"Error semántico: asignación inválida {left_type} {operator} {right_type}")
            self.pilao.append(left_operand)
            self.ptypes.append(self.ERROR)
            return
        
        self._add_quad([operator, right_operand, "_", left_operand])
        self.pilao.append(left_operand)
        self.ptypes.append(result_type)

    # =========================================================================
    # 3. Helpers debug 
    # =========================================================================
    def _pretty_operand(self, operand, scope):
        if operand == "_" or operand is None:
            return operand
        
        if scope in self.addr_names and operand in self.addr_names[scope]:
            return self.addr_names[scope][operand]
        
        if self.glob_scope in self.addr_names and operand in self.addr_names[self.glob_scope]:
            return self.addr_names[self.glob_scope][operand]
            
        return operand

    def pretty_quads(self):
        pretty = deque()

        for i, quad in enumerate(self.quads):
            op, left, right, res = quad
            scope = self.quad_scopes[i]
            pretty.append([
                op,
                self._pretty_operand(left, scope),
                self._pretty_operand(right, scope),
                self._pretty_operand(res, scope),
            ])

        return pretty
        
def main():
    import sys
    import argparse
    import pprint

    arg_parser = argparse.ArgumentParser(description="Patito compiler")
    arg_parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="Patito source file (default: stdin)",
    )
    arg_parser.add_argument("-o", "--optimize", action="store_true", help="Generate parser optimized")
    arg_parser.add_argument("-u", "--human", action="store_true", help="Print in human friendly format")
    arg_parser.add_argument("-k", "--keep", action="store_true", help="Do not delete unncesary attributes from dirfun")
    args = arg_parser.parse_args()
    data = args.file.read()

    my_compiler = PatitoCompiler(args.keep)
    my_compiler.build(optimize=args.optimize) if args.optimize else my_compiler.build()

    ok = my_compiler.parse(data)

    if not ok:
        for err in my_compiler.errors:
            print(err)
    else:
        print("Compile OK")

    if args.keep:
        print("Dir fun")
        pprint.pprint(my_compiler.dir_fun)
        print()

    if not args.human:
        print("Real quads")
        indexed_code = list(enumerate(my_compiler.quads))
    else:
        print("Pretty quads")
        indexed_code = list(enumerate(my_compiler.pretty_quads()))

    pprint.pprint(indexed_code)



if __name__ == "__main__":
    main()