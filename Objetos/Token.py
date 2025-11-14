class Token:
    def __init__(self, tipo: str, valor: str, linea: int, columna: int):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna
        self.valido = tipo not in ("NumeroInvalido", "TokenNoReconocido")

    def print_token(self):
        return f"N.Linea: {self.linea} Col: {self.columna} Token: {self.tipo} Valor: {self.valor} Descripcion: {'VALIDO' if self.valido else 'NO VALIDO'}"