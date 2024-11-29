import sys
import json


class Assembler:
    def __init__(self):
        self.instructions = {
            "LOAD_CONSTANT": 0xA4,  # Код для загрузки константы
            "LOAD_MEMORY": 0x90,     # Код для чтения из памяти
            "STORE_TO_MEMORY": 0x1D, # Код для записи в память
            "SHIFT_LEFT": 0x4A       # Код для побитового сдвига влево
        }

    def assemble(self, source_code):
        machine_code = []
        log = []

        for line_no, line in enumerate(source_code.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith(";"):  # Пропуск пустых строк и комментариев
                continue

            parts = line.split()
            command = parts[0]

            if command not in self.instructions:
                raise ValueError(f"Unknown instruction '{command}' on line {line_no}")

            opcode = self.instructions[command]

            if command == "LOAD_CONSTANT":
                if len(parts) != 3:
                    raise ValueError(f"LOAD_CONSTANT requires 2 arguments on line {line_no}")
                _, reg, value = parts
                reg = int(reg)
                value = int(value)
                encoded = (opcode << 24) | (reg << 16) | value
                machine_code.append(encoded)
                log.append({"line": line_no, "instruction": line, "binary": f"{encoded:08X}"})

            elif command == "STORE_TO_MEMORY":
                if len(parts) != 3:
                    raise ValueError(f"STORE_TO_MEMORY requires 2 arguments on line {line_no}")
                _, reg, address = parts
                reg = int(reg)
                address = int(address)

                # Проверка допустимых значений
                if not (0 <= reg < 32):
                    raise ValueError(f"Invalid register number: {reg}")
                if not (0 <= address < (1 << 24)):
                    raise ValueError(f"Invalid address: {address}")

                # Кодирование команды
                encoded = (opcode << 24) | (reg << 16) | address
                machine_code.append(encoded)
                log.append({"line": line_no, "instruction": line, "binary": f"{encoded:08X}"})

            elif command == "LOAD_MEMORY":
                if len(parts) != 3:
                    raise ValueError(f"LOAD_MEMORY requires 2 arguments on line {line_no}")
                _, reg, offset = parts
                reg = int(reg)
                offset = int(offset)
                encoded = (opcode << 24) | (reg << 16) | offset
                machine_code.append(encoded)
                log.append({"line": line_no, "instruction": line, "binary": f"{encoded:08X}"})

            elif command == "SHIFT_LEFT":
                if len(parts) != 3:
                    raise ValueError(f"SHIFT_LEFT requires 2 arguments on line {line_no}")
                _, reg, address = parts
                reg = int(reg)
                address = int(address)
                encoded = (opcode << 24) | (reg << 16) | address
                machine_code.append(encoded)
                log.append({"line": line_no, "instruction": line, "binary": f"{encoded:08X}"})

            else:
                raise ValueError(f"Unhandled instruction '{command}' on line {line_no}")

        return machine_code, log


class Interpretator:
    def __init__(self):
        self.stack = []  # Стек
        self.memory = [0] * 256  # Память (256 ячеек)
        self.log = []  # Лог выполнения команд

    def execute(self, machine_code):
        for index, instruction in enumerate(machine_code):
            opcode = (instruction >> 24) & 0xFF
            if opcode == 0xA4:  # LOAD_CONSTANT
                reg = (instruction >> 16) & 0xFF
                value = instruction & 0xFFFF
                self.memory[reg] = value
                self.log.append(f"[{index}] LOAD_CONSTANT: Loaded {value} into register {reg}.")

            elif opcode == 0x90:  # LOAD_MEMORY
                reg = (instruction >> 16) & 0xFF
                offset = instruction & 0xFFFF
                address = self.memory[reg] + offset
                if address < 0 or address >= len(self.memory):
                    raise RuntimeError(f"LOAD_MEMORY failed: Invalid address {address}.")
                value = self.memory[address]
                self.memory[reg] = value
                self.log.append(f"[{index}] LOAD_MEMORY: Loaded value {value} from memory[{address}] into register {reg}.")

            elif opcode == 0x1D:  # STORE_TO_MEMORY
                reg = (instruction >> 16) & 0xFF
                address = instruction & 0xFFFF
                value = self.memory[reg]
                if address < 0 or address >= len(self.memory):
                    raise RuntimeError(f"STORE_TO_MEMORY failed: Invalid address {address}.")
                self.memory[address] = value
                self.log.append(f"[{index}] STORE_TO_MEMORY: Stored value {value} to memory[{address}].")

            elif opcode == 0x4A:  # SHIFT_LEFT
                reg = (instruction >> 16) & 0xFF
                value = self.memory[reg]
                shifted_value = (value << 1) & 0xFFFFFFFF  # Побитовый сдвиг влево
                self.memory[reg] = shifted_value
                self.log.append(f"[{index}] SHIFT_LEFT: Shifted value in register {reg} to {shifted_value}.")

            else:
                raise RuntimeError(f"Unknown opcode {opcode} at index {index}.")

    def get_memory_dump(self):
        """Возвращает содержимое памяти в виде словаря."""
        return {f"address_{i}": value for i, value in enumerate(self.memory)}


def main():
    if len(sys.argv) != 5:
        print("Usage: python script.py <input_file> <output_bin> <log_file> <result_json>")
        sys.exit(1)

    input_file, binary_file, log_file, result_file = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

    with open(input_file, "r") as f:
        source_code = f.read()

    assembler = Assembler()
    machine_code, log = assembler.assemble(source_code)

    # Запись бинарного файла
    with open(binary_file, "wb") as f:
        for instruction in machine_code:
            f.write(instruction.to_bytes(4, byteorder='big'))
    print(f"Binary file saved to {binary_file}")

    # Запись файла лога
    with open(log_file, "w") as f:
        json.dump(log, f, indent=4)
    print(f"Log file saved to {log_file}")

    # Выполнение машинного кода
    vm = Interpretator()
    try:
        vm.execute(machine_code)
        # Сохранение памяти в result.json
        memory_dump = vm.get_memory_dump()
        with open(result_file, "w") as f:
            json.dump(memory_dump, f, indent=4)
        print(f"Memory dump saved to {result_file}")

    except RuntimeError as e:
        print(f"Execution error: {e}")


if __name__ == "__main__":
    main()
