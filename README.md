# Analizador Léxico - AigisC

## Alumnos
| Nombre | Código |
| :--- | :--- |
| Cristian Alejandro Flores Rosales | 222966375 |
| Roberto Daniel Iñiguez Martinez de Castro | 222362437 |
| Emmanuel Leonardo Bautista Rico | 218625253 |
| Juan Alejandro Sánchez Vázquez | 223991861 |



# AigisC — Compilador

**Autores**
- Cristian Alejandro Flores Rosales — 222966375
- Roberto Daniel Iñiguez Martínez de Castro — 222362437
- Emmanuel Leonardo Bautista Rico — 218625253
- Juan Alejandro Sánchez Vázquez — 223991861

Descripción breve
------------------
Proyecto educativo que implementa un compilador y una UI para un lenguaje tipo C/JavaScript. Incluye:

- Analizador léxico (tokenización)
- Analizador sintáctico (parser que genera AST)
- Analizador semántico (tabla de símbolos, chequeos de tipos y advertencias)
- Optimizador de código con pasadas locales, de bucle y globales
- Interfaz gráfica (editor, tabla de símbolos, errores, optimización)

Ejecución
---------
Requisitos: Python 3.x (sin paquetes externos).

Ejecutar la UI:

```powershell
python main.py
```

Estructura del proyecto
------------------------

- `main.py` — punto de entrada de la UI (`tkinter`).
- `AigisCUI.py` — interfaz gráfica: editor de código, tabla de símbolos, panel de errores y botones (Compilar/Optimizar/Revertir).
- `Lexico/` — tokenizador (`Lexico.py`) que transforma texto en `Token`.
- `Sintactico/` — parser (`Sintactico.py`) y tabla sintáctica (`TablaSintactico.py`). Produce un `Nodo('Programa')` (AST).
- `Semantico/` — análisis semántico (`Semantico.py`), tabla semántica (`TablaSemantica.py` y `TablaSimbolosExtendida.py`), optimizador (`Optimizador.py`) y manejador de errores (`ErrorSemantico.py`).
- `Objetos/` — definiciones de `Token` y `Nodo` usadas por el parser y las pasadas.

Descripción de los componentes
-----------------------------

1) Analizador Léxico (`Lexico/Lexico.py`)
    - Patrones regex para comentarios, números, cadenas, palabras reservadas, operadores y delimitadores.
    - `tokenize(code)` produce una lista ordenada de `Token` con posición (línea/columna).

2) Parser (`Sintactico/Sintactico.py`)
    - Parser recursivo-descendente que reconoce declaraciones (variables, funciones, modelos), instrucciones (if/while/for/try/catch) y expresiones.
    - Construye nodos `Nodo(tipo, valor, hijos)` para el AST.
    - Mantiene una `TablaSintactico` con símbolos globales (añadidos durante el parseo).

3) Analizador Semántico (`Semantico/Semantico.py`)
    - Construye `TablaSemantica` con metadatos de cada símbolo: tipo, categoría, ambito, inicializado, referencias, tamaño, etc.
    - Verifica tipos, declaraciones previas, duplicados, inicialización antes de uso y control de flujo (return en funciones con tipo no-void).
    - Genera errores y advertencias usando `ErrorSemantico`.
    - Opcionalmente invoca el optimizador y retorna un AST posiblemente transformado.

4) Optimizador (`Semantico/Optimizador.py`)
    - Pasadas locales:
        - Plegado de constantes (constant folding).
        - Simplificación algebraica (x+0 -> x, x*1 -> x, x*0 -> 0).
        - Propagación local de constantes (reemplazo en bloques cuando hay asignaciones a literales).
        - Eliminación de subexpresiones comunes (CSE simple).
        - Eliminación local de código muerto (if con condición constante, truncado después de `return`).
    - Optimización de bucles:
        - Desenrollado de bucles pequeños (iteraciones <= 4).
        - Fusión de `for` consecutivos con mismo rango y misma variable.
        - Extracción básica de invariantes fuera del bucle.
    - Optimización global:
        - Eliminación de funciones/variables globales no referenciadas (usa `TablaSemantica`).
    - `generar_codigo(ast)` produce una representación textual legible del AST para mostrar en la UI (preview).

5) UI (`AigisCUI.py`)
    - Editor de código (panel izquierdo), tabla de símbolos (panel derecho), área de errores (inferior).
    - Botón `Compilar` ejecuta todo el pipeline (lex → sintáctico → semántico → optimizar).
    - Botón `Optimizar` genera código optimizado y lo muestra en el editor; `Revertir` restaura el código original.

Optimización — resumen por niveles
---------------------------------

- Local: eliminación de redundancias, simplificación algebraica, plegado y propagación de constantes, CSE dentro de bloques.
- Bucles: desenrollado, fusión y extracción de invariantes simples.
- Global: eliminación de funciones/variables no usadas y eliminación de código muerto detectado por condiciones constantes.

Ejemplo para probar (pegar en editor y compilar+optimizar)
--------------------------------------------------------
```aigisC
int a = 5;
int b = 10;

int c = a + b;       // 5 + 10 = 15 → constante
int d = c * 2;       // 15 * 2 = 30 → constante

int x = 0;
int y = x + 0;       // redundancia: y = x
int z = y * 1;       // redundancia: z = y
int sumafor = 0;
int i = 0;
for(i; i > 5; i++){
	sumafor += i;
}

int misuma(int a, int b){
	return a + b;
	return 0;
}

```


