class ErrorSemantico:
    """Sistema de detección y reporte de errores semánticos"""
    
    def __init__(self):
        self.errores_tipo = []
        self.errores_declaracion = []
        self.errores_inicializacion = []
        self.errores_funcion = []
        self.advertencias = []
    
    def agregar_error(self, categoria, mensaje, contexto=None):
        """Agrega un error semántico"""
        error_completo = f"[{categoria.upper()}] {mensaje}"
        if contexto:
            error_completo += f" (contexto: {contexto})"
        
        if categoria == "tipo":
            self.errores_tipo.append(error_completo)
        elif categoria == "declaración":
            self.errores_declaracion.append(error_completo)
        elif categoria == "inicialización":
            self.errores_inicializacion.append(error_completo)
        elif categoria == "función":
            self.errores_funcion.append(error_completo)
    
    def agregar_advertencia(self, mensaje, contexto=None):
        """Agrega una advertencia"""
        adv_completa = f"[ADVERTENCIA] {mensaje}"
        if contexto:
            adv_completa += f" (contexto: {contexto})"
        self.advertencias.append(adv_completa)
    
    def obtener_errores(self):
        """Retorna todos los errores"""
        return (self.errores_tipo + self.errores_declaracion + 
                self.errores_inicializacion + self.errores_funcion)
    
    def obtener_advertencias(self):
        """Retorna todas las advertencias"""
        return self.advertencias
    
    def tiene_errores(self):
        """Verifica si hay errores"""
        return len(self.obtener_errores()) > 0
    
    def obtener_reporte_detallado(self):
        """Genera un reporte detallado por categorías"""
        reporte = []
        
        if self.errores_tipo:
            reporte.append("\nERRORES DE TIPO:")
            reporte.extend([f"-{e}" for e in self.errores_tipo])
        
        if self.errores_declaracion:
            reporte.append("\nERRORES DE DECLARACIÓN:")
            reporte.extend([f"-{e}" for e in self.errores_declaracion])
        
        if self.errores_inicializacion:
            reporte.append("\nERRORES DE INICIALIZACIÓN:")
            reporte.extend([f"-{e}" for e in self.errores_inicializacion])
        
        if self.errores_funcion:
            reporte.append("\nERRORES DE FUNCIÓN:")
            reporte.extend([f"-{e}" for e in self.errores_funcion])
        
        if self.advertencias:
            reporte.append("\nADVERTENCIAS:")
            reporte.extend([f"-{a}" for a in self.advertencias])
        
        return "\n".join(reporte) if reporte else "Sin errores ni advertencias"
