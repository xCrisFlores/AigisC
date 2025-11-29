

class Simbolo:
    def __init__(self, nombre, categoria, tipo, ambito, linea, direccion=None, valor=None):
        self.nombre = nombre
        self.categoria = categoria  # variable, funcion, etc.
        self.tipo = tipo            # int, string, etc.
        self.ambito = ambito
        self.linea = linea
        self.direccion_memoria = direccion
        self.valor = valor
        self.inicializado = False
        self.es_constante = False
        self.referencias = 0
        self.params = [] # Para funciones
        self.tipo_retorno = None # Para funciones

class TablaSimbolosExtendida:
    def __init__(self):
        # Pila de ámbitos. El índice 0 es global.
        self.scopes = [{}] 
        self.scope_history = [] # Para visualización
        self.direccion_relativa = 0

    def entrar_ambito(self):
        self.scopes.append({})

    def salir_ambito(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declarar(self, simbolo):
        scope_actual = self.scopes[-1]
        if simbolo.nombre in scope_actual:
            return False, f"Error: Variable '{simbolo.nombre}' ya declarada en este ámbito."
        
        # Asignar dirección relativa simple (simulada)
        simbolo.direccion_memoria = self.direccion_relativa
        if simbolo.categoria == "variable":
            self.direccion_relativa += 4 # Asumiendo 4 bytes por var
            
        scope_actual[simbolo.nombre] = simbolo
        return True, None

    def buscar(self, nombre, linea_ref):
        # Búsqueda desde el ámbito actual hacia el global (Shadowing)
        log_busqueda = f"Line {linea_ref}: Buscando '{nombre}'... "
        
        for i in range(len(self.scopes) - 1, -1, -1):
            scope = self.scopes[i]
            ambito_nombre = "Global" if i == 0 else f"Local Nivel {i}"
            
            log_busqueda += f"[{ambito_nombre}: "
            if nombre in scope:
                log_busqueda += "ENCONTRADO]\n"
                self.scope_history.append(log_busqueda)
                scope[nombre].referencias += 1 # Contador de referencias
                return scope[nombre]
            else:
                log_busqueda += "NO ESTÁ] -> "
        
        log_busqueda += "NO DECLARADO\n"
        self.scope_history.append(log_busqueda)
        return None

    def obtener_todos(self):
        # Aplana todos los scopes para mostrar en la tabla UI
        todos = []
        for scope in self.scopes:
            todos.extend(scope.values())
        return todos