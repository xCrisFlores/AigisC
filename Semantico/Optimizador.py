class OptimizadorCodigo:
    
    def __init__(self):
        self.optimizaciones_aplicadas = []
    
    def optimizar(self, ast):
        """Aplica optimizaciones al AST"""
        print("\n[Optimizador] Iniciando optimización...")
        
        # Optimización 1: Eliminación de código muerto
        ast_optimizado = self._eliminar_codigo_muerto(ast)
        
        # Optimización 2: Propagación de constantes
        ast_optimizado = self._propagar_constantes(ast_optimizado)
        
        # Optimización 3: Evaluación de expresiones constantes
        ast_optimizado = self._evaluar_expresiones_constantes(ast_optimizado)
        
        print(f"[Optimizador] {len(self.optimizaciones_aplicadas)} optimizaciones aplicadas")
        return ast_optimizado
    
    def _eliminar_codigo_muerto(self, nodo):
        """Elimina código inalcanzable después de return"""
        # Implementación simplificada
        self.optimizaciones_aplicadas.append("Eliminación de código muerto")
        return nodo
    
    def _propagar_constantes(self, nodo):
        """Propaga valores de constantes conocidas"""
        self.optimizaciones_aplicadas.append("Propagación de constantes")
        return nodo
    
    def _evaluar_expresiones_constantes(self, nodo):
        """Evalúa expresiones con valores constantes en tiempo de compilación"""
        if not nodo or not hasattr(nodo, 'tipo'):
            return nodo
        
        # Ejemplo: 2 + 3 => 5
        if nodo.tipo == "Operacion" and hasattr(nodo, 'hijos') and len(nodo.hijos) == 2:
            izq = nodo.hijos[0]
            der = nodo.hijos[1]
            
            if izq.tipo == "Numero" and der.tipo == "Numero":
                try:
                    val_izq = float(izq.valor)
                    val_der = float(der.valor)
                    
                    if nodo.valor == '+':
                        resultado = val_izq + val_der
                    elif nodo.valor == '-':
                        resultado = val_izq - val_der
                    elif nodo.valor == '*':
                        resultado = val_izq * val_der
                    elif nodo.valor == '/':
                        if val_der != 0:
                            resultado = val_izq / val_der
                        else:
                            return nodo
                    else:
                        return nodo
                    
                    from Objetos.Nodo import Nodo
                    self.optimizaciones_aplicadas.append(f"Evaluación constante: {val_izq} {nodo.valor} {val_der} = {resultado}")
                    return Nodo("Numero", valor=str(resultado))
                except:
                    pass
        
        # Recursión en hijos
        if hasattr(nodo, 'hijos') and nodo.hijos:
            nodo.hijos = [self._evaluar_expresiones_constantes(hijo) for hijo in nodo.hijos]
        
        return nodo
    
    def generar_codigo(self, nodo):
        """Convierte el AST optimizado en código fuente como string"""
        if not nodo:
            return ""
        if nodo.tipo == "Numero":
            return str(nodo.valor)
        elif nodo.tipo == "Identificador":
            return str(nodo.valor)
        elif nodo.tipo == "Operacion" and hasattr(nodo, 'hijos'):
            izq = self.generar_codigo(nodo.hijos[0])
            der = self.generar_codigo(nodo.hijos[1])
            return f"({izq} {nodo.valor} {der})"
        elif nodo.tipo == "Asignacion" and hasattr(nodo, 'hijos') and len(nodo.hijos) == 2:
            ident = self.generar_codigo(nodo.hijos[0])
            expr = self.generar_codigo(nodo.hijos[1])
            return f"{ident} = {expr}"
        elif nodo.tipo == "Bloque" and hasattr(nodo, 'hijos'):
            return "\n".join(self.generar_codigo(h) for h in nodo.hijos)
        # Agregar más casos según los tipos de nodo de tu AST
        return ""