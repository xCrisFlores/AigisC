from collections import defaultdict


class TablaSemantica:
    """Tabla de símbolos extendida con información semántica"""
    
    def __init__(self):
        self.simbolos = {}
        self.ambitos = defaultdict(dict)
    
    def agregar(self, identificador, info):
        """Agrega un símbolo con su información semántica completa"""
        clave = f"{info['ambito']}.{identificador}"
        self.simbolos[clave] = info
        self.ambitos[info['ambito']][identificador] = info
    
    def buscar(self, identificador, ambito):
        """Busca un símbolo en un ámbito específico"""
        clave = f"{ambito}.{identificador}"
        return self.simbolos.get(clave)
    
    def buscar_en_ambitos(self, identificador, pila_ambitos):
        """Busca un símbolo en la pila de ámbitos (del más interno al más externo)"""
        for i in range(len(pila_ambitos), 0, -1):
            ambito = ".".join(pila_ambitos[:i])
            simbolo = self.buscar(identificador, ambito)
            if simbolo:
                return simbolo
        return None
    
    def existe_en_ambito(self, identificador, ambito):
        """Verifica si un identificador existe en un ámbito específico"""
        return identificador in self.ambitos[ambito]
    
    def obtener_simbolos_ambito(self, ambito):
        """Retorna todos los símbolos de un ámbito"""
        return self.ambitos.get(ambito, {})
