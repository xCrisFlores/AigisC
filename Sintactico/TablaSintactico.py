import json
import os

class TablaSimbolos:
    def __init__(self, limite_memoria_bytes=100):
        self.memoria_principal = {}
        self.archivo_swap = "tabla_simbolos_swap.json"
        self.limite_memoria = limite_memoria_bytes
        self.memoria_actual = 0
        
        # Limpiar swap anterior al iniciar
        if os.path.exists(self.archivo_swap):
            os.remove(self.archivo_swap)
            with open(self.archivo_swap, 'w') as f:
                json.dump({}, f)

    def agregar(self, simbolo):
        ident = simbolo.get("identificador")
        if not ident:
            return

        tamano_nuevo = self.calcular_tamano(simbolo)
        
        # Verificar si cabe en memoria
        if self.memoria_actual + tamano_nuevo > self.limite_memoria:
            self.desbordar_a_disco()
            
        # Agregar a memoria principal
        self.memoria_principal[ident] = simbolo
        self.memoria_actual += tamano_nuevo

    def buscar(self, identificador):
        # 1. Buscar en memoria principal (Rápido)
        if identificador in self.memoria_principal:
            return self.memoria_principal[identificador]
        
        # 2. Si no está, buscar en disco (Lento)
        return self.buscar_en_disco(identificador)

    def desbordar_a_disco(self):
        # Mover todo el contenido actual de memoria al archivo swap para liberar espacio
        # (Estrategia simple de vaciado completo para cumplir requisito de 100 bytes)
        contenido_disco = {}
        
        # Leer lo que ya había en disco
        if os.path.exists(self.archivo_swap):
            try:
                with open(self.archivo_swap, 'r') as f:
                    contenido_disco = json.load(f)
            except:
                contenido_disco = {}
        
        # Mezclar memoria actual con disco
        contenido_disco.update(self.memoria_principal)
        
        # Guardar en disco
        with open(self.archivo_swap, 'w') as f:
            json.dump(contenido_disco, f, default=str) # default=str para evitar error con objetos no serializables
            
        # Limpiar memoria RAM
        self.memoria_principal.clear()
        self.memoria_actual = 0
        # print("[TablaSimbolos] Memoria llena. Datos movidos a almacenamiento secundario.")

    def buscar_en_disco(self, identificador):
        if not os.path.exists(self.archivo_swap):
            return None
            
        try:
            with open(self.archivo_swap, 'r') as f:
                data = json.load(f)
                return data.get(identificador)
        except:
            return None

    def calcular_tamano(self, simbolo):
        # Calculo aproximado de bytes del objeto
        ident = simbolo.get("identificador", "")
        return len(str(ident)) + 20 # Base overhead

    def obtener_todos_los_simbolos(self):
        # Fusionar memoria y disco para mostrar en UI
        todos = {}
        
        # Cargar disco
        if os.path.exists(self.archivo_swap):
            try:
                with open(self.archivo_swap, 'r') as f:
                    todos = json.load(f)
            except:
                pass
                
        # Actualizar con memoria (tiene los datos más recientes)
        todos.update(self.memoria_principal)
        return list(todos.values())

    def esta_en_memoria(self, ident):
        return ident in self.memoria_principal
    
    def get_uso_memoria(self):
        # Devuelve el uso actual y el límite de la memoria principal.
        return self.memoria_actual, self.limite_memoria

    @property
    def simbolos(self):
        # Propiedad de compatibilidad por si algo intenta acceder como lista antigua
        return self.obtener_todos_los_simbolos()