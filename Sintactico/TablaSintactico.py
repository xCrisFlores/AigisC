import json
import os
import tempfile
import atexit

class TablaSimbolos:
    def __init__(self, limite_memoria_bytes=100):
        self.simbolos = []  # Símbolos en memoria
        self.limite_memoria = limite_memoria_bytes
        self.memoria_actual = 0
        
        # Crear archivo temporal para almacenamiento auxiliar
        self.archivo_temp = tempfile.NamedTemporaryFile(
            mode='w+', 
            delete=False, 
            suffix='.json',
            prefix='tabla_simbolos_'
        )
        self.ruta_archivo = self.archivo_temp.name
        self.simbolos_en_archivo = 0
        
        # Inicializar archivo vacío
        self._limpiar_archivo()
        
        # Registrar limpieza al finalizar el programa
        atexit.register(self._cleanup)
        
        print(f"[TablaSimbolos] Inicializada con límite de {limite_memoria_bytes} bytes")
        print(f"[TablaSimbolos] Archivo temporal: {self.ruta_archivo}")

    def _limpiar_archivo(self):
        """Limpia el contenido del archivo temporal"""
        self.archivo_temp.seek(0)
        self.archivo_temp.truncate()
        json.dump([], self.archivo_temp)
        self.archivo_temp.flush()
        self.simbolos_en_archivo = 0

    def _cleanup(self):
        """Elimina el archivo temporal al finalizar"""
        try:
            self.archivo_temp.close()
            if os.path.exists(self.ruta_archivo):
                os.unlink(self.ruta_archivo)
                print(f"[TablaSimbolos] Archivo temporal eliminado: {self.ruta_archivo}")
        except Exception as e:
            print(f"[TablaSimbolos] Error al eliminar archivo temporal: {e}")

    def agregar(self, simbolo):
        """Agrega un símbolo a la tabla, moviéndolo a archivo si es necesario"""
        try:
            tamano = self.calcular_tamano(simbolo)
            
            # Si agregar este símbolo excede el límite, mover símbolos antiguos al archivo
            if self.memoria_actual + tamano > self.limite_memoria:
                self._mover_a_archivo()
            
            # Agregar símbolo a memoria
            self.simbolos.append(simbolo)
            self.memoria_actual += tamano
            
            # print(f"[TablaSimbolos] Símbolo agregado: {simbolo.get('identificador')} ({tamano} bytes)")
            # print(f"[TablaSimbolos] Memoria: {self.memoria_actual}/{self.limite_memoria} bytes")
            
        except Exception as e:
            print(f"[TablaSimbolos] Error al agregar símbolo: {e} -> {simbolo}")

    def _mover_a_archivo(self):
        """Mueve los símbolos más antiguos de memoria al archivo temporal"""
        if not self.simbolos:
            return
        
        # Calcular cuántos símbolos mover (mover la mitad de los símbolos actuales)
        cantidad_mover = max(1, len(self.simbolos) // 2)
        simbolos_a_mover = self.simbolos[:cantidad_mover]
        self.simbolos = self.simbolos[cantidad_mover:]
        
        # Leer símbolos existentes del archivo
        try:
            with open(self.ruta_archivo, 'r') as f:
                simbolos_archivo = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            simbolos_archivo = []
        
        # Agregar nuevos símbolos al archivo
        simbolos_archivo.extend(simbolos_a_mover)
        
        # Escribir de vuelta al archivo
        with open(self.ruta_archivo, 'w') as f:
            json.dump(simbolos_archivo, f, indent=2)
        
        # Actualizar contadores
        self.simbolos_en_archivo = len(simbolos_archivo)
        self.memoria_actual = sum(self.calcular_tamano(s) for s in self.simbolos)
        
        print(f"[TablaSimbolos] Movidos {cantidad_mover} símbolos al archivo")
        print(f"[TablaSimbolos] En memoria: {len(self.simbolos)} | En archivo: {self.simbolos_en_archivo}")

    def calcular_tamano(self, simbolo):
        """Calcula el tamaño aproximado de un símbolo en bytes"""
        ident = simbolo.get("identificador") if simbolo else None
        if not ident or not isinstance(ident, str):
            ident = "<anonimo>"
        
        # Tamaño base: identificador + overhead de otros campos
        tamano_base = len(ident) + 10
        
        # Agregar tamaño de tipo_dato si existe
        tipo_dato = simbolo.get("tipo_dato")
        if tipo_dato and isinstance(tipo_dato, str):
            tamano_base += len(tipo_dato)
        
        return tamano_base

    def verificar_memoria(self):
        """Verifica si se ha excedido el límite de memoria"""
        if self.memoria_actual > self.limite_memoria:
            print(f"[TablaSimbolos] ⚠️  Límite de memoria excedido: {self.memoria_actual}/{self.limite_memoria} bytes")
            return False
        return True

    def listar(self):
        """Retorna todos los símbolos (memoria + archivo)"""
        simbolos_totales = list(self.simbolos)
        
        # Agregar símbolos del archivo si existen
        if self.simbolos_en_archivo > 0:
            try:
                with open(self.ruta_archivo, 'r') as f:
                    simbolos_archivo = json.load(f)
                    simbolos_totales = simbolos_archivo + simbolos_totales
            except Exception as e:
                print(f"[TablaSimbolos] Error al leer archivo: {e}")
        
        return simbolos_totales

    def buscar(self, identificador):
        """Busca un símbolo por identificador en memoria y archivo"""
        # Buscar en memoria primero
        for simbolo in self.simbolos:
            if simbolo.get("identificador") == identificador:
                return simbolo
        
        # Buscar en archivo si no está en memoria
        if self.simbolos_en_archivo > 0:
            try:
                with open(self.ruta_archivo, 'r') as f:
                    simbolos_archivo = json.load(f)
                    for simbolo in simbolos_archivo:
                        if simbolo.get("identificador") == identificador:
                            return simbolo
            except Exception as e:
                print(f"[TablaSimbolos] Error al buscar en archivo: {e}")
        
        return None

    def obtener_estadisticas(self):
        """Retorna estadísticas de uso de memoria"""
        return {
            "memoria_usada": self.memoria_actual,
            "limite_memoria": self.limite_memoria,
            "porcentaje_uso": (self.memoria_actual / self.limite_memoria * 100) if self.limite_memoria > 0 else 0,
            "simbolos_en_memoria": len(self.simbolos),
            "simbolos_en_archivo": self.simbolos_en_archivo,
            "total_simbolos": len(self.simbolos) + self.simbolos_en_archivo,
            "archivo_temporal": self.ruta_archivo
        }

    def imprimir_estadisticas(self):
        """Imprime estadísticas de uso de memoria"""
        stats = self.obtener_estadisticas()
        print("\n" + "="*60)
        print("ESTADÍSTICAS DE TABLA DE SÍMBOLOS")
        print("="*60)
        print(f"Memoria usada:        {stats['memoria_usada']}/{stats['limite_memoria']} bytes ({stats['porcentaje_uso']:.1f}%)")
        print(f"Símbolos en memoria:  {stats['simbolos_en_memoria']}")
        print(f"Símbolos en archivo:  {stats['simbolos_en_archivo']}")
        print(f"Total de símbolos:    {stats['total_simbolos']}")
        print(f"Archivo temporal:     {stats['archivo_temporal']}")
        print("="*60 + "\n")

    def __del__(self):
        """Limpieza al destruir el objeto"""
        self._cleanup()


