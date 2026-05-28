class VirtualMemory:
    def __init__(self):
        self.memory_division = {
            ("global", "entero"): (1_000_000, 1_999_999),
            ("global", "flotante"): (2_000_000, 2_999_999),
            ("local", "entero"): (3_000_000, 3_999_999),
            ("local", "flotante"): (4_000_000, 4_999_999),
            ("temp", "entero"): (5_000_000, 5_999_999),
            ("temp", "flotante"): (6_000_000, 6_999_999),
            ("const", "entero"): (7_000_000, 7_999_999),
            ("const", "flotante"): (8_000_000, 8_999_999),
            ("const", "string"): (9_000_000, 9_999_999),
        }
        
        self.counters = {key: value[0] for key, value in self.memory_division.items()}
        self.constants = {}

    def alloc(self, segment, typ):
        key = (segment, typ)

        if key not in self.counters:
            raise ValueError(f"Invalid memory segment/type: {segment} {typ}")

        address = self.counters[key]
        
        if address > self.memory_division[key][1]:
            raise MemoryError(f"Out of memory for {segment} {typ}")

        self.counters[key] += 1
        return address

    def alloc_const(self, value, typ):
        key = (value, typ)

        if key in self.constants:
            return self.constants[key]

        address = self.alloc("const", typ)
        self.constants[key] = address
        return address

    def reset_local_temps(self):
        self.counters[("local", "entero")] = self.memory_division[("local", "entero")][0]
        self.counters[("local", "flotante")] = self.memory_division[("local", "flotante")][0]
        self.counters[("temp", "entero")] = self.memory_division[("temp", "entero")][0]
        self.counters[("temp", "flotante")] = self.memory_division[("temp", "flotante")][0]


def main():
    vm = VirtualMemory()
    print(vm.alloc("global", "entero"))
    print(vm.alloc("global", "entero"))     # 1_000_001
    print(vm.alloc("global", "entero"))     # 1_000_002
    print(vm.alloc("global", "flotante"))   # 2_000_000

    print(vm.alloc("local", "entero"))      # 3_000_000

    print(vm.alloc("temp", "entero"))         # 5_000_000

    print(vm.get_constant(5, "entero"))     # 7_000_000
    print(vm.get_constant(5, "entero"))     # 7_000_000
    print(vm.get_constant(10, "entero"))    # 7_000_001

    print(vm.get_constant(5.5, "flotante")) # 8_000_000

if __name__ == "__main__":
    main()