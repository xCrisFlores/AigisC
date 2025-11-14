class TablaSimbolos:
    def __init__(self, limite_memoria_bytes=100):
        self.simbolos = []
        self.limite_memoria = limite_memoria_bytes
        self.memoria_actual = 0

    def agregar(self, simbolo):
        try:
            tamano = self.calcular_tamano(simbolo)
            self.simbolos.append(simbolo)
            self.memoria_actual += tamano
            self.verificar_memoria()
        except Exception as e:
            print(f"[TablaSimbolos] Error al agregar símbolo: {e} -> {simbolo}")

    def calcular_tamano(self, simbolo):
        ident = simbolo.get("identificador") if simbolo else None
        if not ident or not isinstance(ident, str):
            ident = "<anonimo>"
        return len(ident) + 10

    def verificar_memoria(self):
        if self.memoria_actual > self.limite_memoria:
            print("[TablaSimbolos] Advertencia: límite de memoria excedido.")

    def listar(self):
        return self.simbolos
