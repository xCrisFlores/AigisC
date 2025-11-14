import re
from typing import List
from Objetos.Token import Token

class Lexico:
    def __init__(self):
        #Regex de nuestras reglas
        self.token_regex = [
            ("ComentarioMultilinea", r"///.*?///"),
            ("ComentarioUnilinea", r"//[^\n]*"),
            ("Reservada", r"\b(if|else|for|while|return|const|readonly|global|local|shared|try|catch|throw|model|template|extends|override|import|from|in|is not|is|not|and|or|AND|OR|NOT|void|int|float|char|bool|string|mapInt|mapString|function|true|false|print|input|println|readLine|readInt|readFloat|write|writeLine)\b"),
            #("NumeroInvalido", r"[+-]?(?:\d+\.)+\d*\.?\d*|\.[+-]?\d+\.+\d*"), #esta regex falla
            ("Numero", r"[+-]?(?:\d+\.\d+|\d+\.|\.\d+|\d+)\b"),
            ("Cadena", r'"([^"\\]|\\.)*"'),
            ("AsignacionCompuesta", r"(\+=|-=|\*=|/=)"),
            ("Relacional", r"(==|!=|<=|>=|<|>)"),
            ("Incrementador", r"(\+\+|--|//|\*\*)"), 
            ("Asignacion", r"="),
            ("Aritmetico", r"[+\-*/%]"),
            ("Logico", r"(&&|\|\||!)"),
            ("LlaveIzq", r"\{"),
            ("LlaveDer", r"\}"),
            ("ParentIzq", r"\("),
            ("ParentDer", r"\)"),
            ("CorcheteIzq", r"\["),
            ("CorcheteDer", r"\]"),
            ("DosPuntos", r":"),  
            ("Coma", r","),
            ("PuntoComa", r";"),
            ("Punto", r"\."),
            ("Identificador", r"[a-zA-Z_][a-zA-Z0-9_]*"),
            ("Espacio", r"[ \t]+"),
            ("SaltoLinea", r"\n"),
            ("TokenNoReconocido", r"[^\s]+"),
        ]

        self.regex_completa = re.compile(
            "|".join(f"(?P<{name}>{pattern})" for name, pattern in self.token_regex),
            re.DOTALL
        )

    def tokenize(self, code: str) -> List[Token]: 
        tokens = []
        linea = 1
        pos_inicio = 0

        for match in self.regex_completa.finditer(code):
            tipo = match.lastgroup
            valor = match.group(tipo)

            if tipo in ("Espacio", "ComentarioUnilinea", "ComentarioMultilinea"):
                continue

            if tipo == "SaltoLinea":
                linea += 1
                pos_inicio = match.end()
                continue

            columna = match.start() - pos_inicio + 1
            token = Token(tipo, valor, linea, columna)
            tokens.append(token)

        return tokens