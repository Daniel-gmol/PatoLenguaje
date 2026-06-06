# Proyecto Patito

Un proyecto para el lenguaje **Patito** que incluye un analizador léxico, sintáctico, generador de código intermedio (cuádruplos) y una máquina virtual para su ejecución.

![Pingüino](misc/pinguino3334.png)

---

## Características de Patito

El lenguaje **Patito** es un lenguaje imperativo con soporte para:
* **Tipos de datos**: Entero (`entero`) y Flotante (`decimal`).
* **Variables**: Bloque de declaración `val var1, var2: entero;`.
* **Funciones**: Declaradas con tipo de retorno (`entero`, `decimal`) o vacías (`nil`).
* **Estructuras de Control**:
  * Condicionales: `si (condicion) { ... }` y `si (condicion) { ... } sino { ... }`.
  * Ciclos: Estructura `esperaque (condicion) \/ { ... }` donde `\/` representa la instrucción de ejecución (*haz*).
* **Entrada/Salida**: Lectura de valores por consola (`dame(var)`) e impresión en pantalla (`dale("Mensaje: ", var, "\n")`).
* **Expresiones**: Soporte completo para operadores aritméticos (`+`, `-`, `*`, `/`), relacionales (`<`, `>`, `<=`, `>=`, `==`, `!=`) y lógicos (`yy`, `oo`, `no`, `xo`).

---

## Estructura del Proyecto

La organización del código y los módulos es la siguiente:

```text
patito/
├── patito/
│   ├── lexer.py
│   ├── parser.py
│   ├── compiler.py
│   ├── memory.py
│   ├── semantic_cube.py
|   |── vm.py
│
├── tests/
│   ├── shared/
│   ├── lexer/
│   ├── parser/
│   ├── semantic/
│   └── compiler/

│
├── tests_runners/
│   ├── test_runner.py
│   ├── lexer_tester.py
│   ├── parser_tester.py
│   └── compiler_tester.py
│
└── requirements.txt
```

---

## Arquitectura de Memoria

El compilador divide la memoria en rangos numéricos bien definidos para agilizar la resolución de direcciones en tiempo de compilación y ejecución:

| Segmento | Tipo de Dato | Rango de Dirección |
| :--- | :--- | :--- |
| **Global** | `entero` (Integer) | `1,000,000` a `1,999,999` |
| **Global** | `flotante` (Float) | `2,000,000` a `2,999,999` |
| **Local** | `entero` (Integer) | `3,000,000` a `3,999,999` |
| **Local** | `flotante` (Float) | `4,000,000` a `4,999,999` |
| **Temporal**| `entero` (Integer) | `5,000,000` a `5,999,999` |
| **Temporal**| `flotante` (Float) | `6,000,000` a `6,999,999` |
| **Constante**| `entero` (Integer) | `7,000,000` a `7,999,999` |
| **Constante**| `flotante` (Float) | `8,000,000` a `8,999,999` |
| **Constante**| `string` | `9,000,000` a `9,999,999` |

---

## Configuración y Requisitos

El proyecto utiliza un entorno virtual de Python. Para comenzar, ejecuta los siguientes comandos desde la raíz del proyecto:

```bash
# Crear entorno virtual
python -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate       # En Unix/macOS
# .venv\Scripts\activate        # En Windows

# Instalar dependencias requeridas
pip install -r requirements.txt
```

---

## Ejecución de Módulos Directamente

Cada módulo dentro de `patito/` se puede invocar de forma independiente desde la raíz del proyecto (con el entorno virtual activo). Todos aceptan una ruta de archivo como argumento; si se omite, leerán desde **stdin**.

### 1. Analizador Léxico (Lexer)

Tokeniza el archivo de entrada y muestra el flujo de tokens identificados.

```bash
python -m patito.lexer <archivo_origen.pt>
# O mediante tubería:
echo "programa foo; fin" | python -m patito.lexer
```

### 2. Analizador Sintáctico (Parser)

Valida la sintaxis del programa de entrada.

```bash
python -m patito.parser <archivo_origen.pt>
```

### 3. Compilador y Máquina Virtual (Compiler + VM)

El compilador realiza el análisis sintáctico, comprobación de tipos semánticos y la generación de cuádruplos de código intermedio. Adicionalmente, cuenta con la opción de ejecutar el programa a través de su Máquina Virtual integrada.

```bash
python -m patito.compiler <archivo_origen.pt>
```

#### Opciones de la CLI del Compilador

| Bandera | Atajo | Descripción |
| :--- | :--- | :--- |
| `--run` | `-r` | Ejecuta el programa compilado inmediatamente en la Máquina Virtual. |
| `--debug-comp` | | Imprime información detallada de la compilación (directorio de funciones, constantes y cuádruplos). |
| `--debug-vm` | | Activa el modo debug en la Máquina Virtual para mostrar paso a paso el puntero de instrucción (IP), el estado de la memoria global y la pila de llamadas. |
| `--human` | `-u` | Cuando se imprimen cuádruplos de depuración, los muestra usando nombres de variables y funciones en vez de direcciones físicas. |
| `--optimize` | `-o` | Compila el parser con el flag de optimización de PLY habilitado. |
| `--keep` | `-k` | Evita eliminar las variables temporales/locales del directorio de funciones al concluir la compilación (útil para inspeccionar metadatos). |

**Ejemplo: Compilar y ejecutar un programa mostrando cuádruplos amigables y diagnóstico de VM:**

```bash
python -m patito.compiler -r --debug-comp --debug-vm -u tests/fibo_iter.pt
```

---

## Ejecución de Suites de Pruebas

Los scripts de pruebas se encuentran en `tests_runners/`. Para resolver correctamente las dependencias e importaciones relativas, deben ejecutarse como módulos de Python desde el directorio raíz del proyecto:

### 1. Pruebas del Analizador Léxico

```bash
python -m tests_runners.lexer_tester
```

### 2. Pruebas del Analizador Sintáctico

```bash
python -m tests_runners.parser_tester
```

### 3. Pruebas de Compilación y Semántica

```bash
python -m tests_runners.compiler_tester
```

### 4. Pruebas Completas de Compilación y Ejecución en VM

Este ejecutor corre la compilación y realiza la simulación en la Máquina Virtual, verificando que los programas ejecuten sin errores lógicos ni de memoria.

```bash
python -m tests_runners.full_compiler_tester
```

---

## Opciones Disponibles para los Ejecutores de Pruebas

Todos los ejecutores de pruebas en `tests_runners/` aceptan los siguientes parámetros desde la consola:

| Bandera | Atajo | Descripción |
| :--- | :--- | :--- |
| `--verbose` | `-v` | Muestra el tiempo de ejecución detallado de cada test, así como los detalles de aprobados/reprobados. |
| `--optimize`| `-o` | Construye el lexer y parser con la optimización interna de PLY habilitada. |

**Ejemplo: Correr las pruebas completas de integración con optimización y salida detallada:**

```bash
python -m tests_runners.full_compiler_tester -o -v
```

---

## Código de Ejemplo en Patito

A continuación se muestra un ejemplo de un programa escrito en el lenguaje **Patito** para calcular recursivamente el término $N$ de la serie de Fibonacci:

```text
init fibo_rec;

entero fib(x : entero){
    val a, b, tmp: entero;
    {
        a = 0;
        b = 1;
        esperaque (x > 0) \/ {
           tmp = a + b; 
           a = b;
           b = tmp;
           x = x - 1;
        }
        regresa a;
    }
}

arranca{
    dale("fib(0) = ", fib(0), "\n");
    dale("fib(1) = ", fib(1), "\n");
    dale("fib(2) = ", fib(2), "\n");
    dale("fib(3) = ", fib(3), "\n");
    dale("fib(10) = ", fib(10), "\n");
}
acaba
```
