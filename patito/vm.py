class MemoryRuntime:
    def __init__(self, constants):
        self.global_mem = {}
        self.const_mem = {addr: val_tuple[0] for val_tuple, addr in constants.items()}
        self.call_stack = [{}]

    def get_value(self, address):
        segment = address // 1_000_000
        val = None
        if segment == 1 or segment == 2:
            val = self.global_mem.get(address)
        elif 3 <= segment <= 6:
            val = self.call_stack[-1].get(address)
        elif 7 <= segment <= 9:
            val = self.const_mem.get(address)
        else:
            raise Exception(f"Invalid memory address: {address}")

        if val is None:
            if segment in (2, 4, 6, 8):
                return 0.0
            return 0
        return val

    def set_value(self, address, value):
        segment = address // 1_000_000
        if segment == 1 or segment == 2:
            self.global_mem[address] = value
        elif 3 <= segment <= 6:
            self.call_stack[-1][address] = value
        else:
            raise Exception(f"Cannot set value for address: {address}")

    def push_frame(self, frame):
        self.call_stack.append(frame)

    def pop_frame(self):
        self.call_stack.pop()

    def get_expected_type(self, address):
        segment = address // 1_000_000
        if segment in (1, 3, 5, 7):
            return 'entero'
        elif segment in (2, 4, 6, 8):
            return 'flotante'
        else:
            raise Exception(f"Invalid memory address: {address}")


class VirtualMachine:
    def __init__(self, compiler):
        self.quads = compiler.quads
        self.dir_fun = compiler.dir_fun
        self.memory = MemoryRuntime(compiler.memory.constants)
        
        self.ip = 0
        self.call_stack_ip = []
        self.pending_calls = []
        
        self._prepass()

    def _prepass(self):
        param_addresses = {}
        for func_id, func_data in self.dir_fun.items():
            if "params" not in func_data:
                continue
            param_addresses[func_id] = []
            int_count = 0
            float_count = 0
            for p_type in func_data["params"]:
                if p_type == 'entero':
                    param_addresses[func_id].append(3_000_000 + int_count)
                    int_count += 1
                else:
                    param_addresses[func_id].append(4_000_000 + float_count)
                    float_count += 1

        active_eras = []
        for quad in self.quads:
            op = quad[0]
            if op == 'ERA':
                active_eras.append(quad[3])
            elif op == 'PARAM':
                func_id = active_eras[-1]
                param_idx = quad[3]
                quad[3] = param_addresses[func_id][param_idx] 
            elif op == 'GOSUB':
                func_id = quad[3]
                quad[3] = self.dir_fun[func_id]["dips"]
                active_eras.pop()
            elif op == 'GOTOEND':
                func_id = quad[3]
                quad[3] = self.dir_fun[func_id]["dipe"]

    
    def _runtime_type_check(self, usr_i, id_addr):
        expected_type = self.memory.get_expected_type(id_addr)
        try:
            if expected_type == 'entero':
                return int(usr_i)
            elif expected_type == 'flotante':
                return float(usr_i)
            else:
                raise Exception("Runtime type error")
        except ValueError:
            raise Exception(f"Type mismatch: cannot convert '{usr_i}' to {expected_type}")

    BINARY_OPS = {
        '+':  lambda l, r: l + r,
        '-':  lambda l, r: l - r,
        '*':  lambda l, r: l * r,
        '/':  lambda l, r: l // r if isinstance(l, int) and isinstance(r, int) else l / r,
        '<':  lambda l, r: int(l < r),
        '>':  lambda l, r: int(l > r),
        '<=': lambda l, r: int(l <= r),
        '>=': lambda l, r: int(l >= r),
        '==': lambda l, r: int(l == r),
        '!=': lambda l, r: int(l != r),
        'yy': lambda l, r: int(bool(l) and bool(r)),
        'oo': lambda l, r: int(bool(l) or bool(r)),
        'xo': lambda l, r: int(bool(l) ^ bool(r)),
    }

    def run(self, debug=False):
        while self.ip < len(self.quads):
            if debug:
                print(f"\nIP={self.ip}")
                print(f"Quad: {self.quads[self.ip]}")
                print(f"Call Stack: {self.memory.call_stack}")
                print(f"Global Mem: {self.memory.global_mem}")
                print(f"Constants Mem: {self.memory.const_mem}")
            
            quad = self.quads[self.ip]
            op = quad[0]
            left = quad[1]
            right = quad[2]
            res = quad[3]

            if op in self.BINARY_OPS:
                l_val = self.memory.get_value(left)
                r_val = self.memory.get_value(right)
                self.memory.set_value(res, self.BINARY_OPS[op](l_val, r_val))
                self.ip += 1
            elif op == 'no':
                l_val = self.memory.get_value(left)
                self.memory.set_value(res, int(not bool(l_val)))
                self.ip += 1
            elif op == '=':
                r_val = self.memory.get_value(left)
                self.memory.set_value(res, r_val)
                self.ip += 1
            elif op == 'UMINUS':
                l_val = self.memory.get_value(left)
                self.memory.set_value(res, -l_val)
                self.ip += 1
            elif op == 'PRINT':
                val = self.memory.get_value(res)
                print(val, end='')
                self.ip += 1
            elif op == 'READ':
                usr_input = input()
                converted_input = self._runtime_type_check(usr_input, res)
                self.memory.set_value(res, converted_input)
                self.ip += 1
            elif op == 'GOTO':
                self.ip = res
            elif op == 'GOTOF':
                cond = self.memory.get_value(left)
                if not cond:
                    self.ip = res
                else:
                    self.ip += 1
            elif op == 'GOTOT':
                cond = self.memory.get_value(left)
                if cond:
                    self.ip = res
                else:
                    self.ip += 1
            elif op == 'ERA':
                self.pending_calls.append({"frame": {}})
                self.ip += 1
            elif op == 'PARAM':
                val = self.memory.get_value(left)
                call = self.pending_calls[-1]
                target_addr = res
                call["frame"][target_addr] = val
                self.ip += 1
            elif op == 'GOSUB':
                call = self.pending_calls.pop()
                self.memory.push_frame(call["frame"])
                self.call_stack_ip.append(self.ip + 1)
                self.ip = res 
            elif op == 'RET':
                val = self.memory.get_value(left)
                global_return_addr = res
                self.memory.set_value(global_return_addr, val)
                self.ip += 1
            elif op == 'GOTOEND':
                self.ip = res
            elif op == 'ENDFUNC':
                self.memory.pop_frame()
                self.ip = self.call_stack_ip.pop()
            elif op == 'END':
                break
            else:
                raise Exception(f"Unknown operation: {op}")

