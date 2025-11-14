from Lexico.Lexico import Lexico
from Sintactico.Sintactico import Sintactico
from tkinter import scrolledtext
import tkinter as tk

class LexicalAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador Léxico")
        self.root.geometry("1200x600")
        
        #Instancia del analizador léxico
        self.lexico = Lexico()

        # Frame superior para editor y tabla en columnas
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = tk.Frame(top_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        left_frame.columnconfigure(0, weight=1)
        
        tk.Label(left_frame, text="Editor de Código:").pack()
        
        # Frame para números de línea y editor
        editor_frame = tk.Frame(left_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # Números de línea
        self.line_numbers = tk.Text(editor_frame, width=4, padx=3, takefocus=0, 
                                     border=0, background='#f0f0f0', state='disabled', wrap='none')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Editor de código
        self.code_editor = scrolledtext.ScrolledText(editor_frame, height=15, width=40)
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.code_editor.config(yscrollcommand=self.on_scroll)
        
        # Inicializar números de línea
        self.update_line_numbers()

        right_frame = tk.Frame(top_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        right_frame.columnconfigure(0, weight=8)
        
        tk.Label(right_frame, text="Tabla de Símbolos:").pack()
        self.symbol_display = scrolledtext.ScrolledText(right_frame, height=15)
        self.symbol_display.pack(fill=tk.BOTH, expand=True)


        self.compile_btn = tk.Button(root, text="Compilar", command=self.compile_code, background="#32b4f0", font=('Arial', 10, 'bold'),)
        self.compile_btn.pack(padx=20, pady=20)
        

        # Área de errores
        tk.Label(root, text="Errores Léxicos:").pack()
        self.error_display = scrolledtext.ScrolledText(root, height=7, fg="red")
        self.error_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_scroll(self, *args):
        """Sincroniza el scroll de números de línea con el editor"""
        self.line_numbers.yview_moveto(args[0])
        
    def update_line_numbers(self, event=None):
        """Actualiza los números de línea"""
        line_count = self.code_editor.get('1.0', 'end-1c').count('\n') + 1
        line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        self.line_numbers.insert('1.0', line_numbers_text)
        self.line_numbers.config(state='disabled')

    def compile_code(self):
    
        self.error_display.delete("1.0", tk.END)
        self.symbol_display.delete("1.0", tk.END)

        code = self.code_editor.get("1.0", tk.END)

        # Tokenizar usando la clase Lexico
        tokens = self.lexico.tokenize(code)

       
        parser = Sintactico(tokens)
        ast = parser.analisis_sintactico()

        if parser.errores:
            for err in parser.errores:
                self.error_display.insert(tk.END, err + "\n")
        else:
            self.error_display.insert(tk.END, "Análisis sintáctico completado con éxito.\n")

        # Mostrar tabla de símbolos
        self.symbol_display.insert(
            tk.END,
            f"{'Identificador':<15}{'Categoría':<15}{'Tipo Dato':<12}{'Ámbito':<10}{'Línea':<8}{'Estado':<12}\n"
        )
        self.symbol_display.insert(tk.END, "-" * 80 + "\n")

        for simbolo in parser.tabla.simbolos:
            ident = simbolo.get("identificador") or "-"
            cat = simbolo.get("categoria") or "-"
            tipo = simbolo.get("tipo_dato") or "-"
            ambito = simbolo.get("ambito") or "-"
            linea = simbolo.get("linea") or "-"
            estado = simbolo.get("estado") or "-"

            self.symbol_display.insert(
                tk.END,
                f"{ident:<15}{cat:<15}{tipo:<12}{ambito:<10}{linea:<8}{estado:<12}\n"
            )



        self.symbol_display.insert(tk.END, "\n\nÁrbol Sintáctico (Resumen):\n")
        self.symbol_display.insert(tk.END, str(ast))


if __name__ == "__main__":
    root = tk.Tk()
    app = LexicalAnalyzerGUI(root)
    root.mainloop()