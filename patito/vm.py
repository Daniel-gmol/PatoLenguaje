class MemoryRuntime:
    def __init__(self, constants):
        self.global_mem = {}
        self.const_mem = {addr: val_tuple[0] for val_tuple, addr in constants.items()}
        self.call_stack = [{}]

    def get_value(self, address):
        val = None
        if 1_000_000 <= address <= 2_999_999:
            val = self.global_mem.get(address)
        elif 3_000_000 <= address <= 6_999_999:
            val = self.call_stack[-1].get(address)
        elif 7_000_000 <= address <= 9_999_999:
            val = self.const_mem.get(address)
        else:
            raise Exception(f"Invalid memory address: {address}")

        if val is None:
            if 2_000_000 <= address <= 2_999_999 or 4_000_000 <= address <= 4_999_999 or 6_000_000 <= address <= 6_999_999 or 8_000_000 <= address <= 8_999_999:
                return 0.0
            return 0
        return val

    def set_value(self, address, value):
        if 1_000_000 <= address <= 2_999_999:
            self.global_mem[address] = value
        elif 3_000_000 <= address <= 6_999_999:
            self.call_stack[-1][address] = value
        else:
            raise Exception(f"Cannot set value for address: {address}")

    def push_frame(self, frame):
        self.call_stack.append(frame)

    def pop_frame(self):
        self.call_stack.pop()

    def get_expected_type(self, address):
        if 1_000_000 <= address <= 1_999_999 or 3_000_000 <= address <= 3_999_999 or 5_000_000 <= address <= 5_999_999 or 7_000_000 <= address <= 7_999_999:
            return 'entero'
        elif 2_000_000 <= address <= 2_999_999 or 4_000_000 <= address <= 4_999_999 or 6_000_000 <= address <= 6_999_999 or 8_000_000 <= address <= 8_999_999:
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

    def get_param_address(self, func_id, param_idx):
        int_count = 0
        float_count = 0
        
        for i in range(param_idx):
            if self.dir_fun[func_id]["params"][i] == 'entero':
                int_count += 1
            else:
                float_count += 1
                
        target_type = self.dir_fun[func_id]["params"][param_idx]
        if target_type == 'entero':
            return 3_000_000 + int_count
        else:
            return 4_000_000 + float_count
    
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

    def run(self):
        while self.ip < len(self.quads):
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
                self.pending_calls.append({"func_id": res, "frame": {}})
                self.ip += 1
            elif op == 'PARAM':
                val = self.memory.get_value(left)
                call = self.pending_calls[-1]
                param_idx = res
                target_addr = self.get_param_address(call["func_id"], param_idx)
                call["frame"][target_addr] = val
                self.ip += 1
            elif op == 'GOSUB':
                call = self.pending_calls.pop()
                self.memory.push_frame(call["frame"])
                self.call_stack_ip.append(self.ip + 1)
                self.ip = self.dir_fun[res]["dips"]
            elif op == 'RET':
                val = self.memory.get_value(left)
                global_return_addr = res
                self.memory.set_value(global_return_addr, val)
                self.ip += 1
            elif op == 'GOTOEND':
                self.ip = self.dir_fun[res]["dipe"]
            elif op == 'ENDFUNC':
                self.memory.pop_frame()
                self.ip = self.call_stack_ip.pop()
            elif op == 'END':
                break
            else:
                raise Exception(f"Unknown operation: {op}")

