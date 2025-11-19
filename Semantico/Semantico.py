from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import copy

from Semantico.Optimizador import OptimizadorCodigo
from Semantico.ErrorSemantico import ErrorSemantico
from Semantico.TablaSemantica import TablaSemantica

class AnalizadorSemantico:
    def __init__(self, ast, tabla_simbolos):
        """
        Inicializa el analizador semántico
        
        Args:
            ast: Árbol sintáctico abstracto generado por el parser
            tabla_simbolos: Tabla de símbolos del análisis sintáctico
        """
        self.ast = ast
        self.tabla_sintactico = tabla_simbolos
        
        # Tabla de símbolos extendida con información semántica
        self.tabla_semantica = TablaSemantica()
        
        # Pila de ámbitos para control de scope
        self.ambito_actual = ["global"]
        self.contador_ambito = 0
        
        # Sistema de errores
        self.errores = ErrorSemantico()
        
        # Tipos de datos soportados
        self.tipos_primitivos = {"void", "int", "float", "char", "bool", "string"}
        self.tipos_numericos = {"int", "float"}
        
        # Funciones declaradas y su contexto
        self.funciones = {}
        self.funcion_actual = None
        
        # Control de flujo
        self.hay_return_en_camino = False
        
        print("[Semántico] Analizador inicializado")
    
    def analizar(self):
        """Ejecuta el análisis semántico completo"""
        print("\n" + "="*70)
        print("INICIANDO ANÁLISIS SEMÁNTICO")
        print("="*70)
        
        # Fase 1: Construir tabla semántica desde la tabla sintáctica
        self._construir_tabla_semantica()
        
        # Fase 2: Recorrer el AST y validar semántica
        self._analizar_nodo(self.ast)
        
        # Fase 3: Validaciones finales
        self._validaciones_finales()
        
        # Reportar resultados
        self._generar_reporte()
        
        return self.errores.obtener_errores()
    
    def _construir_tabla_semantica(self):
        """Construye la tabla semántica desde la tabla sintáctica"""
        print("\n[Semántico] Construyendo tabla semántica...")
        
        simbolos = self.tabla_sintactico.listar()
        for simbolo in simbolos:
            info_semantica = {
                "identificador": simbolo.get("identificador"),
                "tipo": simbolo.get("tipo_dato"),
                "categoria": simbolo.get("categoria"),
                "ambito": simbolo.get("ambito", "global"),
                "linea": simbolo.get("linea"),
                "inicializado": simbolo.get("estado") == "declarado",
                "referencias": simbolo.get("referencias", 0),
                "constante": False,
                "direccion_memoria": None,
                "tamano": self._calcular_tamano_tipo(simbolo.get("tipo_dato"))
            }
            
            # Información adicional según categoría
            if simbolo.get("categoria") == "función":
                info_semantica["parametros"] = []
                info_semantica["tipo_retorno"] = simbolo.get("tipo_dato", "void")
                info_semantica["implementada"] = True
            
            self.tabla_semantica.agregar(info_semantica["identificador"], info_semantica)
        
        print(f"[Semántico] Tabla semántica construida: {len(self.tabla_semantica.simbolos)} símbolos")
    
    def _analizar_nodo(self, nodo):
        """Analiza recursivamente un nodo del AST"""
        if not nodo:
            return None
        
        tipo_nodo = nodo.tipo
        
        # Declaraciones
        if tipo_nodo == "Programa":
            return self._analizar_programa(nodo)
        elif tipo_nodo == "DeclaracionVariable":
            return self._analizar_declaracion_variable(nodo)
        elif tipo_nodo == "FuncionDeclarada":
            return self._analizar_funcion(nodo)
        elif tipo_nodo == "Modelo":
            return self._analizar_modelo(nodo)
        
        # Instrucciones
        elif tipo_nodo == "Asignacion":
            return self._analizar_asignacion(nodo)
        elif tipo_nodo == "If":
            return self._analizar_if(nodo)
        elif tipo_nodo == "While":
            return self._analizar_while(nodo)
        elif tipo_nodo == "ForRango" or tipo_nodo == "ForIter":
            return self._analizar_for(nodo)
        elif tipo_nodo == "Return":
            return self._analizar_return(nodo)
        elif tipo_nodo == "LlamadaFuncion" or tipo_nodo == "LlamadaFuncionIO":
            return self._analizar_llamada_funcion(nodo)
        
        # Expresiones
        elif tipo_nodo == "Operacion":
            return self._analizar_operacion_aritmetica(nodo)
        elif tipo_nodo == "OperacionLogica":
            return self._analizar_operacion_logica(nodo)
        elif tipo_nodo == "OperacionRelacional":
            return self._analizar_operacion_relacional(nodo)
        elif tipo_nodo == "Identificador":
            return self._analizar_identificador(nodo)
        elif tipo_nodo == "Numero":
            return self._inferir_tipo_numero(nodo.valor)
        elif tipo_nodo == "Cadena":
            return "string"
        elif tipo_nodo == "Booleano":
            return "bool"
        
        # Recorrer hijos si no se maneja específicamente
        if hasattr(nodo, 'hijos') and nodo.hijos:
            for hijo in nodo.hijos:
                self._analizar_nodo(hijo)
        
        return None
    
    
    def _verificar_tipos_compatibles(self, tipo1, tipo2, operacion="asignación"):
        """Verifica si dos tipos son compatibles para una operación"""
        if tipo1 == tipo2:
            return True
        
        # Promoción implícita: int -> float
        if tipo1 == "int" and tipo2 == "float":
            return True
        if tipo1 == "float" and tipo2 == "int":
            return True
        
        # Conversión bool <-> int
        if (tipo1 == "bool" and tipo2 == "int") or (tipo1 == "int" and tipo2 == "bool"):
            return True
        
        return False
    
    def _inferir_tipo_numero(self, valor):
        """Infiere el tipo de un número literal"""
        try:
            if '.' in str(valor):
                return "float"
            else:
                return "int"
        except:
            return "int"
    
    def _verificar_operacion_valida(self, operador, tipo1, tipo2=None):
        """Verifica si una operación es válida para los tipos dados"""
        # Operadores aritméticos: solo para numéricos
        if operador in ['+', '-', '*', '/', '%']:
            if tipo2 is None:  # Operador unario
                return tipo1 in self.tipos_numericos
            return tipo1 in self.tipos_numericos and tipo2 in self.tipos_numericos
        
        # Operadores relacionales: numéricos o strings
        if operador in ['<', '>', '<=', '>=']:
            if tipo1 in self.tipos_numericos and tipo2 in self.tipos_numericos:
                return True
            return False
        
        # Igualdad: cualquier tipo compatible
        if operador in ['==', '!=', 'is', 'is not']:
            return self._verificar_tipos_compatibles(tipo1, tipo2, "comparación")
        
        # Operadores lógicos: solo booleanos
        if operador in ['and', 'or', 'not', '&&', '||', '!']:
            if tipo2 is None:
                return tipo1 == "bool"
            return tipo1 == "bool" and tipo2 == "bool"
        
        return False
    
    def _inferir_tipo_resultado(self, operador, tipo1, tipo2=None):
        """Infiere el tipo resultante de una operación"""
        if operador in ['+', '-', '*', '/']:
            if tipo1 == "float" or tipo2 == "float":
                return "float"
            return "int"
        
        if operador == '%':
            return "int"
        
        if operador in ['<', '>', '<=', '>=', '==', '!=', 'is', 'is not']:
            return "bool"
        
        if operador in ['and', 'or', 'not', '&&', '||', '!']:
            return "bool"
        
        return tipo1

    
    def _entrar_ambito(self, nombre_ambito):
        """Entra a un nuevo ámbito"""
        self.contador_ambito += 1
        nuevo_ambito = f"{nombre_ambito}_{self.contador_ambito}"
        self.ambito_actual.append(nuevo_ambito)
        print(f"[Semántico] Entrando a ámbito: {'.'.join(self.ambito_actual)}")
    
    def _salir_ambito(self):
        """Sale del ámbito actual"""
        if len(self.ambito_actual) > 1:
            ambito_salido = self.ambito_actual.pop()
            print(f"[Semántico] Saliendo de ámbito: {ambito_salido}")
    
    def _obtener_ambito_completo(self):
        """Retorna el ámbito actual completo"""
        return ".".join(self.ambito_actual)
    
    def _verificar_declaracion_previa(self, identificador):
        """Verifica si un identificador fue declarado antes de usarse"""
        simbolo = self.tabla_semantica.buscar(identificador, self._obtener_ambito_completo())
        if not simbolo:
            # Buscar en ámbitos superiores
            for i in range(len(self.ambito_actual) - 1, -1, -1):
                ambito_parcial = ".".join(self.ambito_actual[:i+1])
                simbolo = self.tabla_semantica.buscar(identificador, ambito_parcial)
                if simbolo:
                    return True
            return False
        return True
    
    def _verificar_declaracion_duplicada(self, identificador, ambito):
        """Verifica si hay declaración duplicada en el mismo ámbito"""
        return self.tabla_semantica.existe_en_ambito(identificador, ambito)
    
    def _analizar_funcion(self, nodo):
        """Analiza declaración de función"""
        nombre_func = nodo.valor
        self.funcion_actual = nombre_func
        self.hay_return_en_camino = False
        
        # Obtener información de la función
        tipo_retorno = None
        parametros = []
        
        if hasattr(nodo, 'hijos') and nodo.hijos:
            for hijo in nodo.hijos:
                if hijo.tipo == "TipoRetorno":
                    tipo_retorno = hijo.valor
                elif hijo.tipo == "Params":
                    parametros = self._extraer_parametros(hijo)
        
        # Registrar función
        self.funciones[nombre_func] = {
            "tipo_retorno": tipo_retorno or "void",
            "parametros": parametros,
            "tiene_return": False
        }
        
        # Entrar al ámbito de la función
        self._entrar_ambito(f"func_{nombre_func}")
        
        # Agregar parámetros a la tabla semántica
        for param in parametros:
            self.tabla_semantica.agregar(param["nombre"], {
                "identificador": param["nombre"],
                "tipo": param["tipo"],
                "categoria": "parámetro",
                "ambito": self._obtener_ambito_completo(),
                "inicializado": True
            })
        
        # Analizar cuerpo
        if hasattr(nodo, 'hijos'):
            for hijo in nodo.hijos:
                if hijo.tipo not in ["TipoRetorno", "Params"]:
                    self._analizar_nodo(hijo)
        
        # Verificar que funciones con retorno tengan return
        if tipo_retorno and tipo_retorno != "void" and not self.hay_return_en_camino:
            self.errores.agregar_error(
                "función",
                f"La función '{nombre_func}' debe retornar un valor de tipo '{tipo_retorno}'",
                nodo.valor if hasattr(nodo, 'valor') else None
            )
        
        self._salir_ambito()
        self.funcion_actual = None
        return tipo_retorno
    
    def _extraer_parametros(self, nodo_params):
        """Extrae información de parámetros"""
        parametros = []
        if hasattr(nodo_params, 'hijos'):
            for param in nodo_params.hijos:
                if param.tipo == "Param":
                    tipo_param = None
                    nombre_param = param.valor
                    
                    if hasattr(param, 'hijos'):
                        for hijo in param.hijos:
                            if hijo.tipo == "Tipo":
                                tipo_param = hijo.valor
                    
                    parametros.append({
                        "nombre": nombre_param,
                        "tipo": tipo_param
                    })
        return parametros
    
    def _validar_llamada_funcion(self, nombre, argumentos):
        """Valida que una llamada a función sea correcta"""
        if nombre not in self.funciones:
            # Puede ser función de IO built-in
            if nombre in ["print", "println", "input", "readInt", "readFloat"]:
                return "void" if nombre in ["print", "println"] else "string"
            
            self.errores.agregar_error(
                "función",
                f"Función '{nombre}' no declarada",
                nombre
            )
            return None
        
        func_info = self.funciones[nombre]
        params_esperados = func_info["parametros"]
        
        # Verificar número de argumentos
        if len(argumentos) != len(params_esperados):
            self.errores.agregar_error(
                "función",
                f"La función '{nombre}' espera {len(params_esperados)} argumentos pero recibió {len(argumentos)}",
                nombre
            )
            return func_info["tipo_retorno"]
        
        # Verificar tipos de argumentos
        for i, (arg, param) in enumerate(zip(argumentos, params_esperados)):
            tipo_arg = self._analizar_nodo(arg)
            tipo_esperado = param["tipo"]
            
            if not self._verificar_tipos_compatibles(tipo_arg, tipo_esperado):
                self.errores.agregar_error(
                    "tipo",
                    f"Argumento {i+1} de '{nombre}': se esperaba '{tipo_esperado}' pero se recibió '{tipo_arg}'",
                    nombre
                )
        
        return func_info["tipo_retorno"]
    
    def _analizar_programa(self, nodo):
        """Analiza el nodo programa"""
        if hasattr(nodo, 'hijos'):
            for hijo in nodo.hijos:
                self._analizar_nodo(hijo)
    
    def _analizar_declaracion_variable(self, nodo):
        """Analiza declaración de variable"""
        nombre_var = nodo.valor
        tipo_var = None
        valor_inicial = None
        
        # Extraer tipo y valor inicial
        if hasattr(nodo, 'hijos'):
            for hijo in nodo.hijos:
                if hijo.tipo == "Tipo":
                    tipo_var = hijo.valor
                elif hijo.tipo not in ["Modificadores"]:
                    valor_inicial = hijo
        
        # Verificar declaración duplicada
        if self._verificar_declaracion_duplicada(nombre_var, self._obtener_ambito_completo()):
            self.errores.agregar_error(
                "declaración",
                f"Variable '{nombre_var}' ya declarada en este ámbito",
                nombre_var
            )
        
        # Verificar tipo del valor inicial
        if valor_inicial:
            tipo_valor = self._analizar_nodo(valor_inicial)
            if tipo_valor and not self._verificar_tipos_compatibles(tipo_var, tipo_valor):
                self.errores.agregar_error(
                    "tipo",
                    f"No se puede asignar '{tipo_valor}' a variable de tipo '{tipo_var}'",
                    nombre_var
                )
        
        # Agregar a tabla semántica
        self.tabla_semantica.agregar(nombre_var, {
            "identificador": nombre_var,
            "tipo": tipo_var,
            "categoria": "variable",
            "ambito": self._obtener_ambito_completo(),
            "inicializado": valor_inicial is not None,
            "referencias": 0
        })
        
        return tipo_var
    
    def _analizar_asignacion(self, nodo):
        """Analiza asignación"""
        # Extraer identificador y operador
        partes = nodo.valor.split() if nodo.valor else []
        if len(partes) < 2:
            return None
        
        identificador = partes[0]
        operador = partes[1]
        
        # Verificar que la variable existe
        if not self._verificar_declaracion_previa(identificador):
            self.errores.agregar_error(
                "declaración",
                f"Variable '{identificador}' no declarada",
                identificador
            )
            return None
        
        # Obtener tipo de la variable
        simbolo = self.tabla_semantica.buscar_en_ambitos(identificador, self.ambito_actual)
        if not simbolo:
            return None
        
        tipo_var = simbolo["tipo"]
        
        # Analizar expresión del lado derecho
        tipo_expresion = None
        if hasattr(nodo, 'hijos') and nodo.hijos:
            tipo_expresion = self._analizar_nodo(nodo.hijos[0])
        
        # Verificar compatibilidad de tipos
        if tipo_expresion and not self._verificar_tipos_compatibles(tipo_var, tipo_expresion):
            self.errores.agregar_error(
                "tipo",
                f"No se puede asignar '{tipo_expresion}' a '{identificador}' de tipo '{tipo_var}'",
                identificador
            )
        
        # Marcar como inicializado
        simbolo["inicializado"] = True
        simbolo["referencias"] += 1
        
        return tipo_var
    
    def _analizar_if(self, nodo):
        """Analiza estructura if"""
        if hasattr(nodo, 'hijos') and len(nodo.hijos) >= 2:
            # Analizar condición
            tipo_condicion = self._analizar_nodo(nodo.hijos[0])
            if tipo_condicion and tipo_condicion != "bool":
                self.errores.agregar_error(
                    "tipo",
                    f"La condición del if debe ser booleana, se encontró '{tipo_condicion}'",
                    "if"
                )
            
            # Analizar bloques
            for hijo in nodo.hijos[1:]:
                self._analizar_nodo(hijo)
    
    def _analizar_while(self, nodo):
        """Analiza bucle while"""
        if hasattr(nodo, 'hijos') and len(nodo.hijos) >= 2:
            # Analizar condición
            tipo_condicion = self._analizar_nodo(nodo.hijos[0])
            if tipo_condicion and tipo_condicion != "bool":
                self.errores.agregar_error(
                    "tipo",
                    f"La condición del while debe ser booleana, se encontró '{tipo_condicion}'",
                    "while"
                )
            
            # Analizar cuerpo
            self._entrar_ambito("while")
            self._analizar_nodo(nodo.hijos[1])
            self._salir_ambito()
    
    def _analizar_for(self, nodo):
        """Analiza bucle for"""
        self._entrar_ambito("for")
        if hasattr(nodo, 'hijos'):
            for hijo in nodo.hijos:
                self._analizar_nodo(hijo)
        self._salir_ambito()
    
    def _analizar_return(self, nodo):
        """Analiza instrucción return"""
        self.hay_return_en_camino = True
        
        if not self.funcion_actual:
            self.errores.agregar_error(
                "función",
                "Return fuera de una función",
                "return"
            )
            return None
        
        func_info = self.funciones.get(self.funcion_actual)
        if not func_info:
            return None
        
        tipo_retorno_esperado = func_info["tipo_retorno"]
        tipo_retorno_real = None
        
        # Analizar expresión de retorno
        if hasattr(nodo, 'hijos') and nodo.hijos and nodo.hijos[0]:
            tipo_retorno_real = self._analizar_nodo(nodo.hijos[0])
        else:
            tipo_retorno_real = "void"
        
        # Verificar compatibilidad
        if tipo_retorno_esperado == "void" and tipo_retorno_real != "void":
            self.errores.agregar_error(
                "tipo",
                f"Función '{self.funcion_actual}' no debe retornar un valor",
                self.funcion_actual
            )
        elif tipo_retorno_esperado != "void":
            if not tipo_retorno_real or tipo_retorno_real == "void":
                self.errores.agregar_error(
                    "tipo",
                    f"Función '{self.funcion_actual}' debe retornar un valor de tipo '{tipo_retorno_esperado}'",
                    self.funcion_actual
                )
            elif not self._verificar_tipos_compatibles(tipo_retorno_esperado, tipo_retorno_real):
                self.errores.agregar_error(
                    "tipo",
                    f"Tipo de retorno incompatible: se esperaba '{tipo_retorno_esperado}' pero se encontró '{tipo_retorno_real}'",
                    self.funcion_actual
                )
        
        func_info["tiene_return"] = True
        return tipo_retorno_real
    
    def _analizar_llamada_funcion(self, nodo):
        """Analiza llamada a función"""
        nombre_func = nodo.valor
        argumentos = []
        
        if hasattr(nodo, 'hijos'):
            argumentos = nodo.hijos
        
        return self._validar_llamada_funcion(nombre_func, argumentos)
    
    def _analizar_operacion_aritmetica(self, nodo):
        """Analiza operación aritmética"""
        if not hasattr(nodo, 'hijos') or len(nodo.hijos) < 2:
            return None
        
        tipo_izq = self._analizar_nodo(nodo.hijos[0])
        tipo_der = self._analizar_nodo(nodo.hijos[1])
        operador = nodo.valor
        
        if not self._verificar_operacion_valida(operador, tipo_izq, tipo_der):
            self.errores.agregar_error(
                "tipo",
                f"Operador '{operador}' no válido para tipos '{tipo_izq}' y '{tipo_der}'",
                operador
            )
            return None
        
        return self._inferir_tipo_resultado(operador, tipo_izq, tipo_der)
    
    def _analizar_operacion_logica(self, nodo):
        """Analiza operación lógica"""
        operador = nodo.valor
        
        if not hasattr(nodo, 'hijos') or not nodo.hijos:
            return None
        
        if operador in ['!', 'not', 'NOT']:
            # Operador unario
            tipo = self._analizar_nodo(nodo.hijos[0])
            if not self._verificar_operacion_valida(operador, tipo):
                self.errores.agregar_error(
                    "tipo",
                    f"Operador '{operador}' requiere operando booleano, se encontró '{tipo}'",
                    operador
                )
            return "bool"
        else:
            # Operador binario
            if len(nodo.hijos) < 2:
                return None
            
            tipo_izq = self._analizar_nodo(nodo.hijos[0])
            tipo_der = self._analizar_nodo(nodo.hijos[1])
            
            if not self._verificar_operacion_valida(operador, tipo_izq, tipo_der):
                self.errores.agregar_error(
                    "tipo",
                    f"Operador '{operador}' requiere operandos booleanos, se encontró '{tipo_izq}' y '{tipo_der}'",
                    operador
                )
            return "bool"
    
    def _analizar_operacion_relacional(self, nodo):
        """Analiza operación relacional"""
        if not hasattr(nodo, 'hijos') or len(nodo.hijos) < 2:
            return None
        
        tipo_izq = self._analizar_nodo(nodo.hijos[0])
        tipo_der = self._analizar_nodo(nodo.hijos[1])
        operador = nodo.valor
        
        if not self._verificar_operacion_valida(operador, tipo_izq, tipo_der):
            self.errores.agregar_error(
                "tipo",
                f"Operador '{operador}' no válido para tipos '{tipo_izq}' y '{tipo_der}'",
                operador
            )
        
        return "bool"
    
    def _analizar_identificador(self, nodo):
        """Analiza uso de identificador"""
        nombre = nodo.valor
        
        if not self._verificar_declaracion_previa(nombre):
            self.errores.agregar_error(
                "declaración",
                f"Variable '{nombre}' no declarada",
                nombre
            )
            return None
        
        simbolo = self.tabla_semantica.buscar_en_ambitos(nombre, self.ambito_actual)
        if not simbolo:
            return None
        
        # Verificar inicialización
        if not simbolo.get("inicializado", False):
            self.errores.agregar_error(
                "inicialización",
                f"Variable '{nombre}' usada sin inicializar",
                nombre
            )
        simbolo.setdefault("referencias", 0)
        simbolo["referencias"] += 1
        return simbolo["tipo"]
    
    def _analizar_modelo(self, nodo):
        """Analiza declaración de modelo/clase"""
        nombre_modelo = nodo.valor
        self._entrar_ambito(f"model_{nombre_modelo}")
        
        if hasattr(nodo, 'hijos'):
            for hijo in nodo.hijos:
                self._analizar_nodo(hijo)
        
        self._salir_ambito()
    

    def _validaciones_finales(self):
      
        print("\n[Semántico] Ejecutando validaciones finales...")
        
        # Verificar variables declaradas pero no usadas
        for nombre, simbolo in self.tabla_semantica.simbolos.items():
            if simbolo["categoria"] == "variable" and simbolo["referencias"] == 0:
                self.errores.agregar_advertencia(
                    f"Variable '{nombre}' declarada pero nunca usada",
                    nombre
                )
    
    def _generar_reporte(self):
        """Genera reporte de análisis semántico"""
        print("\n" + "="*70)
        print("REPORTE DE ANÁLISIS SEMÁNTICO")
        print("="*70)
        
        errores = self.errores.obtener_errores()
        advertencias = self.errores.obtener_advertencias()
        
        if errores:
            print(f"\nERRORES ENCONTRADOS: {len(errores)}")
            for error in errores:  
                print(f"   • {error}")
            if len(errores) > 10:
                print(f"   ... y {len(errores) - 10} errores más")
        else:
            print("\nNo se encontraron errores semánticos")
        
        if advertencias:
            print(f"\nADVERTENCIAS: {len(advertencias)}")
            for adv in advertencias[:5]:
                print(f"   • {adv}")
        
        print("\n" + "="*70)
    
    def _calcular_tamano_tipo(self, tipo):
        """Calcula el tamaño en bytes de un tipo"""
        tamanos = {
            "int": 4,
            "float": 4,
            "char": 1,
            "bool": 1,
            "string": 8,  
            "void": 0
        }
        return tamanos.get(tipo, 4)
    

def ejecutar_analisis_semantico(ast, tabla_simbolos, optimizar=False):
   
    analizador = AnalizadorSemantico(ast, tabla_simbolos)
    errores = analizador.analizar()
    
    ast_final = ast
    if optimizar and not analizador.errores.tiene_errores():
        optimizador = OptimizadorCodigo()
        ast_final = optimizador.optimizar(ast)
    
    return errores, ast_final, analizador.tabla_semantica

