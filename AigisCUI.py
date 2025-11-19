from Lexico.Lexico import Lexico
from Semantico.Semantico import ejecutar_analisis_semantico
from Sintactico.Sintactico import Sintactico
from tkinter import scrolledtext
import tkinter as tk

class AigisCUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador Léxico y Sintáctico")
        self.root.geometry("1200x700")
        
        self.lexico = Lexico()
        self.codigo_original = ""  # Guardará el código antes de optimizar
        self.ast_optimizado = None
        self.optimizado = False  # Estado del botón optimizar/revertir

        # --- Frame Superior ---
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel Izquierdo (Editor)
        left_frame = tk.Frame(top_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) 
        
        tk.Label(left_frame, text="Editor de Código:").pack(anchor="w")
        
        editor_frame = tk.Frame(left_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        self.line_numbers = tk.Text(editor_frame, width=4, padx=3, takefocus=0, 
                                     border=0, background='#f0f0f0', state='disabled', wrap='none')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        self.code_editor = scrolledtext.ScrolledText(editor_frame, height=20, width=50)
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.code_editor.bind('<KeyRelease>', self.update_line_numbers)
        self.code_editor.bind('<MouseWheel>', self.on_scroll)
        self.code_editor.vbar.config(command=self.sync_scroll)
        
        self.update_line_numbers()

        # Panel Derecho (Tabla de Símbolos)
        right_frame = tk.Frame(top_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="Tabla de Símbolos (Memoria + Archivo):").pack(anchor="w")
        self.symbol_display = scrolledtext.ScrolledText(right_frame, height=20, width=50)
        self.symbol_display.pack(fill=tk.BOTH, expand=True)

        # --- Monitor de Memoria ---
        self.memory_label = tk.Label(self.root, text="Uso de Memoria: 0 / 100 bytes", 
                                      font=('Arial', 9, 'italic'))
        self.memory_label.pack(pady=2)

        # --- Frame para botones ---
        button_frame = tk.Frame(self.root)
        button_frame.pack(padx=10, pady=10)

        # Botón Compilar
        self.compile_btn = tk.Button(button_frame, text="Compilar", command=self.compile_code, 
                                   background="#32b4f0", font=('Arial', 10, 'bold'))
        self.compile_btn.pack(side=tk.LEFT, padx=5)

        # Botón Optimizar / Revertir
        self.optimize_btn = tk.Button(button_frame, text="Optimizar", command=self.toggle_optimize,
                                      background="#f0a832", font=('Arial', 10, 'bold'))
        self.optimize_btn.pack(side=tk.LEFT, padx=5)

        # --- Área de Errores ---
        tk.Label(root, text="Errores Detectados:").pack(anchor="w", padx=5)
        self.error_display = scrolledtext.ScrolledText(root, height=8, fg="red", bg="#fff0f0")
        self.error_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def sync_scroll(self, *args):
        self.on_scroll(*args)
        self.code_editor.yview(*args)

    def on_scroll(self, *args):
        self.line_numbers.yview_moveto(self.code_editor.yview()[0])
        
    def update_line_numbers(self, event=None):
        line_count = self.code_editor.get('1.0', 'end-1c').count('\n') + 1
        line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        self.line_numbers.insert('1.0', line_numbers_text)
        self.line_numbers.config(state='disabled')
        self.on_scroll()

    def compile_code(self):
        """Compila el código completo: léxico, sintáctico y semántico"""
        self.error_display.delete("1.0", tk.END)
        self.symbol_display.delete("1.0", tk.END)

        code = self.code_editor.get("1.0", tk.END)

        try:
           
            tokens = self.lexico.tokenize(code)
            parser = Sintactico(tokens)
            ast = parser.analisis_sintactico()

            if parser.errores:
                self.error_display.insert(tk.END, f"{len(parser.errores)} errores sintácticos:\n", 'error')
                for err in parser.errores[:10]:
                    self.error_display.insert(tk.END, f"-{err}\n", 'error')
            else:
                self.error_display.insert(tk.END, "Análisis sintáctico exitoso\n\n", 'success')

            
            errores_semanticos, ast_optimizado, tabla_semantica = ejecutar_analisis_semantico(
                ast, 
                parser.tabla,
                optimizar=True
            )

            self.ast_optimizado = ast_optimizado

            if errores_semanticos:
                self.error_display.insert(tk.END, f"{len(errores_semanticos)} errores semánticos:\n", 'error')
                for err in errores_semanticos[:15]:
                    self.error_display.insert(tk.END, f"-{err}\n", 'error')
                if len(errores_semanticos) > 15:
                    self.error_display.insert(tk.END, f"  ... y {len(errores_semanticos) - 15} más\n", 'error')
            

            self.error_display.insert(tk.END, f"{"COMPILACIÓN COMPLETADA CON ERRORES" if errores_semanticos else "COMPILACIÓN COMPLETADA"}\n", 'error' if errores_semanticos else 'success')

            self.error_display.tag_config('success', foreground='green')
            self.error_display.tag_config('error', foreground='red')

      
            self.mostrar_tabla_semantica(tabla_semantica, parser.tabla)

        except Exception as e:
            self.error_display.insert(tk.END, f"\nERROR CRÍTICO: {str(e)}\n", 'error')
            import traceback
            self.error_display.insert(tk.END, traceback.format_exc(), 'error')

    def mostrar_tabla_semantica(self, tabla_semantica, tabla_sintactico):
        """Muestra la tabla de símbolos semántica"""
        self.symbol_display.insert(tk.END, "TABLA DE SÍMBOLOS\n", 'header')
        self.symbol_display.insert(tk.END, "-" * 90 + "\n")
        
        # Encabezado
        self.symbol_display.insert(
            tk.END,
            f"{'Identificador':<20}{'Tipo':<15}{'Categoría':<15}{'Ámbito':<20}{'Inicializado':<15}{'Refs':<8}\n"
        )
        self.symbol_display.insert(tk.END, "-" * 90 + "\n")

        # Símbolos
        for clave, simbolo in tabla_semantica.simbolos.items():
            ident = str(simbolo.get("identificador", "-"))[:18]
            tipo = str(simbolo.get("tipo", "-"))[:13]
            cat = str(simbolo.get("categoria", "-"))[:13]
            ambito = str(simbolo.get("ambito", "-"))[:18]
            inicializado = "✓" if simbolo.get("inicializado", False) else "✗"
            refs = str(simbolo.get("referencias", 0))

            self.symbol_display.insert(
                tk.END,
                f"{ident:<20}{tipo:<15}{cat:<15}{ambito:<20}{inicializado:<15}{refs:<8}\n"
            )

    def toggle_optimize(self):
            """Optimizar o revertir el código en el editor"""
            if not self.ast_optimizado:
                return  # No hay AST compilado

            if not self.optimizado:
                # Optimizar: generar código optimizado y reemplazar
                from Semantico.Optimizador import OptimizadorCodigo
                optimizador = OptimizadorCodigo()
                codigo_opt = optimizador.generar_codigo(self.ast_optimizado)  # Método que devuelva string
                self.code_editor.delete("1.0", tk.END)
                self.code_editor.insert("1.0", codigo_opt)
                self.optimize_btn.config(text="Revertir")
                self.optimizado = True
            else:
                # Revertir al código original
                self.code_editor.delete("1.0", tk.END)
                self.code_editor.insert("1.0", self.codigo_original)
                self.optimize_btn.config(text="Optimizar")
                self.optimizado = False

if __name__ == "__main__":
    root = tk.Tk()
    app = AigisCUI(root)
    root.mainloop()