
from .parser import PatitoParser
from .memory import MemoryAloca
from .semantic_cube import cube

class PatitoCompilerError(Exception):
    pass


class PatitoCompiler(PatitoParser):
    """
    Chequeo de semántica y generación de IR para patito lenguaje
    """

    PENDING = 111

    def __init__(self, keep: bool = False):
        super().__init__()

        self.keep = keep

        self.memory = MemoryAloca() 
        self.addr_names = {}
        self.quad_scopes = []

        self.dir_fun = None 
        self.curr_scope = None
        self.glob_scope = None

        self.poper = []
        self.pilao = []
        self.ptypes = []
        self.pjumps = []

        self.quads = []
        self.temp_count = 0

        self.call_stack_meta = []

    def parse(self, data):
        self.memory = MemoryAloca() 
        self.addr_names = {}
        self.quad_scopes = []

        self.dir_fun = None 
        self.curr_scope = None 
        self.glob_scope = None

        self.poper = []
        self.pilao = []
        self.ptypes = []
        self.pjumps = []

        self.quads = []
        self.temp_count = 0

        self.call_stack_meta = []

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
            del self.dir_fun[self.glob_scope]["vars"]
        self.curr_scope = None
        self.glob_scope = None
        self._add_quad(["END", "_", "_", "_"])

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
            self._semantic_error(f"Error: Variable '{var_id}' ya declarada")
        else:
            self.dir_fun[self.curr_scope]["vars"][var_id] = {"type": self.PENDING, "address": self.PENDING}
    
    # 1.3 Functions
    def p_funcs(self, p):
        """funcs : NULA ID ng_add_fun '(' list_params ')' '{' vars cuerpo '}' ng_del_fun
                 | NULA ID ng_add_fun '(' list_params ')' '{' cuerpo '}' ng_del_fun
                 | tipo ID ng_add_fun '(' list_params ')' '{' vars cuerpo '}' ng_del_fun
                 | tipo ID ng_add_fun '(' list_params ')' '{' cuerpo '}' ng_del_fun"""
        func_id = p[2]
        self.dir_fun[func_id]["params"].reverse()

    def p_ng_add_fun(self, p):
        """ng_add_fun : """
        func_id = p[-1]
        func_type = p[-2]
        next_dip = len(self.quads)

        if func_id in self.dir_fun:
            self._semantic_error(f"Error: Funcion '{func_id}' ya declarada")

        if func_type != 'nil':
            func_return = '__return_' + func_id
            address = self.memory.alloc("global", func_type)
            self.dir_fun[self.glob_scope]["vars"][func_return] = {"type": func_type, "address": address}
            self._register_name(address, func_return)
            self._add_resource("local", func_type, scope=self.glob_scope)

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
        self.dir_fun[self.curr_scope]["dipe"] = len(self.quads)
        self._add_quad(["ENDFUNC", '_', '_', '_'])
        self.curr_scope = self.glob_scope
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
        var_id = p[-2]
        var_type, var_addr = self._lookup_var(var_id)
        self._push_operand(var_addr, var_type)
        op = p[-1]
        self.poper.append(op)

    # 1.4.1 Asignación
    def p_ng_quad_assign_end(self, p):
        """ng_quad_assign_end : """
        if self.poper and self.poper[-1] == '=':
            self._create_assign_quad()

    # 1.4.2 Llamadas a funciones
    def p_ng_quad_call(self, p):
        """ng_quad_call : """
        func_id = p[-1]
        if self.dir_fun.get(func_id, None) is None:
            self._semantic_error(f"Error: La funcion '{func_id}' no esta definida.")

        self._add_quad(['ERA', '_', '_', func_id])

        self.call_stack_meta.append({"func": func_id, "param_inx": 0})

    def p_ng_quad_call_end_expr(self, p):
        """ng_quad_call_end_expr : """
        call = self.call_stack_meta.pop()
        fun_id = call["func"]
        arg_size = call["param_inx"]
        par_size = len(self.dir_fun[fun_id]["params"])

        if arg_size != par_size:
            self._semantic_error(f"Error: La funcion '{fun_id}' esperaba {par_size} argumentos y se recibieron {arg_size}")
        self._add_quad(['GOSUB', '_', '_', fun_id])

        if self.dir_fun[fun_id]["type"] == "nil":
            self._semantic_error("Error semántico: Función nula usada dentro de una expresión")
        else:
            fun_type, fun_addr = self._lookup_var('__return_' + fun_id)
            tmp_addr = self._alloc_temp(fun_type)
            self._add_quad(['=', fun_addr, '_', tmp_addr])
            self._push_operand(tmp_addr, fun_type)


    def p_ng_quad_call_end_estatuto(self, p):
        """ng_quad_call_end_estatuto : """
        call = self.call_stack_meta.pop()
        fun_id = call["func"]
        arg_size = call["param_inx"]
        par_size = len(self.dir_fun[fun_id]["params"])

        if arg_size != par_size:
            self._semantic_error(f"Error: La funcion '{fun_id}' esperaba {par_size} argumentos y se recibieron {arg_size}")
        self._add_quad(['GOSUB', '_', '_', fun_id])

    def p_ng_quad_arg(self, p):
        """ng_quad_arg : """
        arg = self.pilao.pop()
        arg_type = self.ptypes.pop()

        call = self.call_stack_meta[-1]
        curr_call = call["func"]

        if call["param_inx"] >= len(self.dir_fun[curr_call]["params"]):
            self._semantic_error(f"Error: Demasiados argumentos para la funcion '{curr_call}'")

        par_type = self.dir_fun[curr_call]["params"][call["param_inx"]]

        if arg_type != par_type:
            self._semantic_error(f"Error: El tipo {arg_type} del argumento no coincide con el tipo de parametro {par_type}")

        self._add_quad(["PARAM", arg, '_', call["param_inx"]])
        call["param_inx"] += 1
        
    def p_ng_quad_ret(self, p):
        """ng_quad_ret : """
        is_nil_return = (p[-1] == "nil")

        if is_nil_return:
            ret_val = "nil"
            ret_type = "nil"
        else:
            ret_val = self.pilao.pop()
            ret_type = self.ptypes.pop()

        fun_type = self.dir_fun[self.curr_scope]["type"]
        if ret_type != fun_type:
            self._semantic_error(f"Error: El tipo {ret_type} del valor de retorno no coincide con el tipo de funcion {fun_type}")

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
        print_arg = p[-1]
        if print_arg is None: 
            var_addr = self.pilao.pop()
            self.ptypes.pop()
        else:
            var_addr = self.memory.alloc_const(print_arg, "string")
            self._register_name(var_addr, print_arg) 
        
        self._add_quad(["PRINT", '_', '_', var_addr])

    # 1.4.4 Leer
    def p_ng_quad_read(self, p):
        """ng_quad_read : """
        id = p[-1]
        id_type, id_addr = self._lookup_var(id)
        self._add_quad(["READ", '_', '_', id_addr])

    # 1.4.5 Ciclos
    def p_ng_add_jump(self, p):
        """ng_add_jump : """
        jump_inx = len(self.quads)
        self.pjumps.append(jump_inx)

    def p_ng_quad_while_end(self, p):
        """ng_quad_while_end : """
        jmp_inx_false = self.pjumps.pop()
        jmp_inx_rep = self.pjumps.pop()
        self._add_quad(['GOTO', '_', '_', jmp_inx_rep])
        self.quads[jmp_inx_false][3] = len(self.quads)

    # 1.4.6 Condicionales
    def p_ng_quad_if(self, p):
        """ng_quad_if : """
        condition = self.pilao.pop()
        self.ptypes.pop() #type condition
        jmp_inx = len(self.quads)
        self._add_quad(['GOTOF', condition, '_', '_'])
        self.pjumps.append(jmp_inx)

    def p_ng_quad_else(self, p):
        """ng_quad_else : """
        jmp_inx_false = self.pjumps.pop()

        jmp_inx = len(self.quads)
        self._add_quad(['GOTO', '_', '_', '_'])

        self.quads[jmp_inx_false][3] = len(self.quads)

        self.pjumps.append(jmp_inx)
        
    def p_ng_quad_if_end(self, p):
        """ng_quad_if_end : """
        end_jmp = self.pjumps.pop()
        self.quads[end_jmp][3] = len(self.quads)

    # 1.5 Expresiones
    def p_ng_add_false_bottom(self, p):
        """ng_add_false_bottom : """
        self.poper.append('(')

    def p_ng_remove_false_bottom(self, p):
        """ng_remove_false_bottom : """
        self.poper.pop()

    # 1.5.1 OR
    def p_ng_quad_or(self, p):
        """ng_quad_or : """
        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_or_end(self, p):
        """ng_quad_or_end : """
        if self.poper and self.poper[-1] == 'oo':
            self._create_expr_quad()

    #1.5.2 XOR
    def p_ng_quad_xor(self, p):
        """ng_quad_xor : """
        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_xor_end(self, p):
        """ng_quad_xor_end : """
        if self.poper and self.poper[-1] == 'xo':
            self._create_expr_quad()

    #1.5.3 AND
    def p_ng_quad_and(self, p):
        """ng_quad_and : """
        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_and_end(self, p):
        """ng_quad_and_end : """
        if self.poper and self.poper[-1] == 'yy':
            self._create_expr_quad()

    #1.5.4 Relational
    def p_ng_quad_rel(self, p):
        """ng_quad_rel : """
        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_rel_end(self, p):
        """ng_quad_rel_end : """
        if self.poper and self.poper[-1] in ['>', '<', '!=', '==', '>=', '<=']:
            self._create_expr_quad()

    #1.5.5 term
    def p_ng_quad_term(self, p):
        """ng_quad_term : """
        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_term_end(self, p):
        """ng_quad_term_end : """
        if self.poper and self.poper[-1] in ['+', '-']:
            self._create_expr_quad()

    #1.5.6 Factor
    def p_ng_quad_fact(self, p):
        """ng_quad_fact : """
        op = p[-1]
        self.poper.append(op)

    def p_ng_quad_fact_end(self, p):
        """ng_quad_fact_end : """
        if self.poper and self.poper[-1] in ['*', '/']:
            self._create_expr_quad()
    
    def p_ng_quad_no(self, p):
        """ng_quad_no : """
        operand = self.pilao.pop()
        operand_type = self.ptypes.pop()

        result_type = self._get_result_type(operand_type, "no", operand_type)
        result_addr = self._alloc_temp(result_type)

        self._add_quad(["no", operand, "_", result_addr])
        self._push_operand(result_addr, result_type)


    def p_ng_quad_id(self, p):
        """ng_quad_id : """
        var_id = p[-1]
        var_type, var_addr = self._lookup_var(var_id)

        self._push_operand(var_addr, var_type)

    def p_ng_quad_unary_plus(self, p):
        """ng_quad_unary_plus : """
        pass  # operand already on stack, nothing to do

    def p_ng_quad_unary_minus(self, p):
        """ng_quad_unary_minus : """
        operand = self.pilao.pop()
        op_type = self.ptypes.pop()

        # Constant folding: if operand is a constant, fold it directly
        if 7_000_000 <= operand <= 8_999_999:
            for (val, typ), addr in self.memory.constants.items():
                if addr == operand:
                    self._push_const(-val)
                    return

        # General case: emit UMINUS quad
        result_addr = self._alloc_temp(op_type)
        self._add_quad(["UMINUS", operand, "_", result_addr])
        self._push_operand(result_addr, op_type)

    def p_ng_quad_cte(self, p):
        """ng_quad_cte : """
        self._push_const(p[-1])

    # =========================================================================
    # 2. Helpers para semántica
    # =========================================================================

    def _semantic_error(self, msg):
        self.errors.append(msg)
        raise PatitoCompilerError(msg)

    def _lookup_var(self, var_name):
        for scope in (self.curr_scope, self.glob_scope):
            if var_name in self.dir_fun[scope]["vars"]:
                v = self.dir_fun[scope]["vars"][var_name]
                return v["type"], v["address"]
        self._semantic_error(f"Error semántico: variable '{var_name}' no declarada")

    def _get_cte_type(self, value):
        if isinstance(value, int):
            return "entero"
        if isinstance(value, float):
            return "flotante"
        self._semantic_error(f"Error semántico: constante inválida '{value}'")

    def _get_result_type(self, left_type, operator, right_type):
        result_type = cube.get(operator, {}).get(left_type, {}).get(right_type)
        if result_type is None: 
            self._semantic_error(f"Error semántico: operación inválida {left_type} {operator} {right_type}")
        return result_type

    def _alloc_temp(self, var_type):
        addr = self.memory.alloc("temp", var_type)
        self._register_name(addr, f"t{self.temp_count}")
        self.temp_count += 1
        self._add_resource("temp", var_type)
        return addr

    def _push_operand(self, addr, var_type):
        self.pilao.append(addr)
        self.ptypes.append(var_type)

    def _push_const(self, value):
        cte_type = self._get_cte_type(value)
        addr = self.memory.alloc_const(value, cte_type)
        self._register_name(addr, value)
        self._push_operand(addr, cte_type)
    
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
    
    def _create_expr_quad(self):
        right_operand = self.pilao.pop()
        left_operand = self.pilao.pop()

        right_type = self.ptypes.pop()
        left_type = self.ptypes.pop()

        operator = self.poper.pop()
        result_type = self._get_result_type(left_type, operator, right_type)

        result_addr = self._alloc_temp(result_type)
        self._add_quad([operator, left_operand, right_operand, result_addr])
        self._push_operand(result_addr, result_type)
    
    def _create_assign_quad(self):
        right_operand = self.pilao.pop()
        right_type = self.ptypes.pop()

        left_operand = self.pilao.pop()
        left_type = self.ptypes.pop()

        operator = self.poper.pop()
        self._get_result_type(left_type, operator, right_type)
        
        self._add_quad([operator, right_operand, "_", left_operand])

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
        pretty = []

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
    arg_parser.add_argument("-r", "--run", action="store_true", help="Run the compiled program using the Virtual Machine")
    arg_parser.add_argument("--debug-comp", action="store_true", help="Print compiler debug information (dir fun, quads, etc)")
    arg_parser.add_argument("--debug-vm", action="store_true", help="Run Virtual Machine in debug mode")
    args = arg_parser.parse_args()
    data = args.file.read()

    my_compiler = PatitoCompiler(args.keep)
    my_compiler.build(optimize=args.optimize) if args.optimize else my_compiler.build()

    ok = my_compiler.parse(data)

    if not ok:
        for err in my_compiler.errors:
            print(err)
    elif args.debug_comp:
        print("Compile OK")

    if args.debug_comp:
        print("Dir fun")
        pprint.pprint(my_compiler.dir_fun)
        print()

        print("Const")
        pprint.pprint(my_compiler.memory.constants)
        print()

        if not args.human:
            print("Real quads")
            indexed_code = list(enumerate(my_compiler.quads))
        else:
            print("Pretty quads")
            indexed_code = list(enumerate(my_compiler.pretty_quads()))

        pprint.pprint(indexed_code)

    if args.run and ok:
        from .vm import VirtualMachine
        vm = VirtualMachine(my_compiler)
        vm.run(debug=args.debug_vm)

if __name__ == "__main__":
    main()