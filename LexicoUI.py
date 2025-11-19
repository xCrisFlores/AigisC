from Lexico.Lexico import Lexico
from Sintactico.Sintactico import Sintactico
from tkinter import scrolledtext
import tkinter as tk

class LexicalAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador Léxico y Sintáctico")
        self.root.geometry("1200x700")
        
        self.lexico = Lexico()

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

        # --- Monitor de Memoria (CAMBIO 1) ---
        self.memory_label = tk.Label(self.root, text="Uso de Memoria: 0 / 100 bytes", 
                                      font=('Arial', 9, 'italic'))
        self.memory_label.pack(pady=2)

        # --- Botón Compilar ---
        self.compile_btn = tk.Button(self.root, text="Compilar", command=self.compile_code, 
                                   background="#32b4f0", font=('Arial', 10, 'bold'))
        self.compile_btn.pack(padx=10, pady=10)
        
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
        self.error_display.delete("1.0", tk.END)
        self.symbol_display.delete("1.0", tk.END)

        code = self.code_editor.get("1.0", tk.END)
        tokens = self.lexico.tokenize(code)
        
        parser = Sintactico(tokens)
        ast = parser.analisis_sintactico()

        # --- ACTUALIZAR MONITOR DE MEMORIA (CAMBIO 2) ---
        uso_actual, limite = parser.tabla.get_uso_memoria()
        self.memory_label.config(text=f"Uso de Memoria: {uso_actual} / {limite} bytes")
        # --- Fin de la actualización ---

        # Mostrar errores con indicador visual
        if parser.errores:
            lines = code.split('\n')
            for err in parser.errores:
                self.error_display.insert(tk.END, f"{err}\n")
                
                try:
                    parts = err.split(',')
                    linea_str = parts[0].split(' ')[-1] 
                    col_str = parts[1].split(':')[0].split(' ')[-1]
                    
                    l = int(linea_str)
                    c = int(col_str)
                    
                    if 0 <= l-1 < len(lines):
                        linea_codigo = lines[l-1]
                        indicador = " " * (c - 1) + "^"
                        self.error_display.insert(tk.END, f"    {linea_codigo}\n")
                        self.error_display.insert(tk.END, f"    {indicador}\n\n")
                except:
                    pass
        else:
            self.error_display.config(fg="green")
            self.error_display.insert(tk.END, "Análisis sintáctico completado con éxito.\n")
            self.error_display.config(fg="red")

        # Mostrar tabla de símbolos
        self.symbol_display.insert(tk.END, f"{'ID':<15}{'Cat':<12}{'Tipo':<10}{'Ámbito':<10}{'Loc':<8}\n")
        self.symbol_display.insert(tk.END, "-" * 60 + "\n")

        todos_simbolos = parser.tabla.obtener_todos_los_simbolos()
        
        for simbolo in todos_simbolos:
            ident = str(simbolo.get("identificador", "-"))
            cat = str(simbolo.get("categoria", "-"))
            tipo = str(simbolo.get("tipo_dato", "-"))
            ambito = str(simbolo.get("ambito", "-"))
            ubicacion = "MEM" if parser.tabla.esta_en_memoria(ident) else "DISK"

            self.symbol_display.insert(
                tk.END,
                f"{ident:<15}{cat:<12}{tipo:<10}{ambito:<10}{ubicacion:<8}\n"
            )

        self.symbol_display.insert(tk.END, "\n\nÁrbol Sintáctico (Resumen):\n")
        self.symbol_display.insert(tk.END, str(ast))

if __name__ == "__main__":
    root = tk.Tk()
    app = LexicalAnalyzerGUI(root)
    root.mainloop()