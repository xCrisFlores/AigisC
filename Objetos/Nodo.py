import json

class Nodo:
    def __init__(self, tipo, valor=None, hijos=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos or []

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self):
        return {
            "tipo": self.tipo,
            "valor": self.valor,
            "hijos": [h.to_dict() for h in self.hijos]
        }