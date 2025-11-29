import copy
import operator

class OptimizadorCodigo:
    def __init__(self):
        pass

    def optimizar(self, ast, tabla_semantica=None):
        """Aplica varias pasadas de optimización y devuelve el AST optimizado (no muta el original).

        `tabla_semantica` es opcional y se usa para optimizaciones globales (eliminar funciones/vars no referenciadas).
        """
        if not ast:
            return ast
        ast = copy.deepcopy(ast)
        # Pasadas locales
        ast = self._const_fold(ast)
        ast = self._algebraic_simplify(ast)
        ast = self._propagacion_constantes_por_bloque(ast)
        ast = self._cse_simple(ast)
        ast = self._eliminar_codigo_muerto_simple(ast)
        # Optimización de bucles
        ast = self._desenrollar_bucles_pequenos(ast)
        ast = self._extract_invariants(ast)
        ast = self._fusionar_for_consecutivos(ast)
        # Optimización global (usa tabla semántica si se dispone)
        if tabla_semantica is not None:
            ast = self._eliminar_codigo_muerto_global(ast, tabla_semantica)
        return ast

    # -------------------------
    # PASADAS SENCILLAS
    # -------------------------
    def _traverse(self, nodo, fn_parent=None):
        """Recorrido simple: aplica función que puede reemplazar nodo"""
        nueva = fn_parent(nodo) if fn_parent else None
        if nueva is not None:
            nodo = nueva
        if hasattr(nodo, 'hijos') and nodo.hijos:
            nuevos = []
            for h in nodo.hijos:
                nuevos.append(self._traverse(h, fn_parent))
            nodo.hijos = nuevos
        return nodo

    def _const_fold(self, ast):
        """Plegado de constantes: evalúa operaciones con literales numéricos"""
        def fold(n):
            try:
                if getattr(n, "tipo", None) in ("Operacion",):
                    if hasattr(n, 'hijos') and len(n.hijos) >= 2:
                        a = n.hijos[0]
                        b = n.hijos[1]
                        if getattr(a, "tipo", None) == "Numero" and getattr(b, "tipo", None) == "Numero":
                            val_a = float(a.valor) if '.' in str(a.valor) else int(a.valor)
                            val_b = float(b.valor) if '.' in str(b.valor) else int(b.valor)
                            op = n.valor
                            ops = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv, '%': operator.mod}
                            if op in ops:
                                try:
                                    res = ops[op](val_a, val_b)
                                except Exception:
                                    return None
                                # crear nodo Numero
                                new = copy.deepcopy(n)
                                new.tipo = "Numero"
                                new.valor = str(int(res)) if isinstance(res, int) or (isinstance(res, float) and res.is_integer()) else str(res)
                                new.hijos = []
                                return new
                # If boolean literal operations handled similarly?
            except Exception:
                return None
            return None

        return self._traverse(ast, fold)

    def _algebraic_simplify(self, ast):
        """Reglas simples: x+0 -> x, x*1 -> x, x*0 -> 0"""
        def simp(n):
            try:
                if getattr(n, "tipo", None) == "Operacion" and hasattr(n, 'hijos') and len(n.hijos) >= 2:
                    a, b = n.hijos[0], n.hijos[1]
                    op = n.valor
                    # x + 0 or 0 + x
                    if op == '+' and (getattr(b, "tipo", None) == "Numero" and str(b.valor) in ("0", "0.0")):
                        return a
                    if op == '+' and (getattr(a, "tipo", None) == "Numero" and str(a.valor) in ("0", "0.0")):
                        return b
                    # x * 1 or 1 * x
                    if op == '*' and (getattr(b, "tipo", None) == "Numero" and str(b.valor) in ("1", "1.0")):
                        return a
                    if op == '*' and (getattr(a, "tipo", None) == "Numero" and str(a.valor) in ("1", "1.0")):
                        return b
                    # x * 0 -> 0
                    if op == '*' and ((getattr(a, "tipo", None) == "Numero" and str(a.valor) in ("0","0.0")) or (getattr(b, "tipo", None) == "Numero" and str(b.valor) in ("0","0.0"))):
                        new = copy.deepcopy(n)
                        new.tipo = "Numero"
                        new.valor = "0"
                        new.hijos = []
                        return new
            except Exception:
                return None
            return None
        return self._traverse(ast, simp)

    def _propagacion_constantes_por_bloque(self, ast):
        """Propagación de constantes simple: en un bloque secuencial, reemplaza usos posteriores de variables asignadas con literal."""
        def process_block(n):
            if not hasattr(n, "hijos") or not n.hijos:
                return None
            consts = {}
            nuevos = []
            for hijo in n.hijos:
                # Detectar asignaciones sencillas: Asignacion o DeclaracionVariable cuyos hijos son Numero
                if getattr(hijo, "tipo", None) in ("Asignacion", "DeclaracionVariable") and hasattr(hijo, "hijos") and hijo.hijos:
                    rhs = hijo.hijos[0]
                    if getattr(rhs, "tipo", None) == "Numero":
                        # extraer identificador
                        if hasattr(hijo, "valor") and hijo.valor:
                            nombre = hijo.valor.split()[0] if isinstance(hijo.valor, str) else None
                            if nombre:
                                consts[nombre] = copy.deepcopy(rhs)
                                nuevos.append(hijo)
                                continue
                # Reemplazar identificadores por constante si está en consts
                def replace_ids(x):
                    if getattr(x, "tipo", None) == "Identificador" and getattr(x, "valor", None) in consts:
                        return copy.deepcopy(consts[x.valor])
                    return None
                nuevos.append(self._traverse(hijo, replace_ids))
            n.hijos = nuevos
            return n

        return self._traverse(ast, lambda x: process_block(x) if getattr(x,"tipo",None) in ("Programa","FuncionDeclarada","Modelo") else None)

    def _eliminar_codigo_muerto_simple(self, ast):
        """Quita instrucciones irrelevantes: bloques if con condición constante false, instrucciones después de return en función."""
        def clean(n):
            # If con condicion numerica
            if getattr(n, "tipo", None) == "If" and hasattr(n, "hijos") and len(n.hijos) >= 1:
                cond = n.hijos[0]
                if getattr(cond, "tipo", None) == "Numero":
                    val = float(cond.valor) if '.' in str(cond.valor) else int(cond.valor)
                    if val == 0:
                        return None  # eliminar if
                    else:
                        # reemplazar if por cuerpo (los hijos posteriores)
                        new_seq = copy.deepcopy(n)
                        # los hijos desde 1 en adelante se convierten en secuencia (Programa)
                        seq = new_seq
                        seq.tipo = "Programa"
                        seq.hijos = new_seq.hijos[1:]
                        return seq
            # Return: truncar siguientes siblings se hace en process_block (handled below)
            return None

        ast = self._traverse(ast, clean)

        # eliminar instrucciones después de Return en cuerpos de función
        def truncate_after_return(n):
            if getattr(n, "tipo", None) == "FuncionDeclarada" and hasattr(n, "hijos"):
                nuevos = []
                saw_return = False
                for h in n.hijos:
                    if saw_return:
                        # omitir
                        continue
                    nuevos.append(h)
                    if getattr(h, "tipo", None) == "Return":
                        saw_return = True
                n.hijos = nuevos
                return n
            return None
        return self._traverse(ast, truncate_after_return)

    def _desenrollar_bucles_pequenos(self, ast):
        """Desenrollado simple de ForRango si los límites son constantes y el número de iteraciones <= 4."""
        def unroll(n):
            if getattr(n, "tipo", None) == "ForRango" and hasattr(n, "hijos"):
                # se espera que n.valor contenga nombre_var o similar; hijos[0]=start, hijos[1]=end, hijos[2]=body
                try:
                    start_node = n.hijos[0]
                    end_node = n.hijos[1]
                    body = n.hijos[2] if len(n.hijos) > 2 else None
                    if getattr(start_node, "tipo", None) == "Numero" and getattr(end_node, "tipo", None) == "Numero" and body:
                        s = int(float(start_node.valor))
                        e = int(float(end_node.valor))
                        count = max(0, e - s)
                        if count <= 4:
                            seq = copy.deepcopy(n)
                            seq.tipo = "Programa"
                            seq.hijos = []
                            loop_var = getattr(n, "valor", "i")
                            for v in range(s, e):
                                # deep-copy body and replace Identificador equal to loop_var with Numero v
                                body_copy = copy.deepcopy(body)
                                def repl(x):
                                    if getattr(x, "tipo", None) == "Identificador" and getattr(x, "valor", None) == loop_var:
                                        new = copy.deepcopy(x)
                                        new.tipo = "Numero"
                                        new.valor = str(v)
                                        new.hijos = []
                                        return new
                                    return None
                                seq.hijos.append(self._traverse(body_copy, repl))
                            return seq
                except Exception:
                    return None
            return None
        return self._traverse(ast, unroll)

    def _hash_subtree(self, nodo):
        """Genera una tupla hashable representando la estructura del subárbol."""
        if nodo is None:
            return None
        childs = []
        if hasattr(nodo, 'hijos') and nodo.hijos:
            for h in nodo.hijos:
                childs.append(self._hash_subtree(h))
        return (getattr(nodo, 'tipo', None), getattr(nodo, 'valor', None), tuple(childs))

    def _cse_simple(self, ast):
        """Eliminación de subexpresiones comunes (CSE) simple: reemplaza subárboles idénticos por la primera ocurrencia."""
        seen = {}

        def cse(n):
            try:
                key = self._hash_subtree(n)
                if key is None:
                    return None
                if key in seen:
                    # Reemplazar por la primera ocurrencia (evita duplicación de trabajo)
                    return seen[key]
                else:
                    seen[key] = n
            except Exception:
                return None
            return None

        return self._traverse(ast, cse)

    def _extract_invariants(self, ast):
        """Extracción básica de invariantes en bucles: mueve instrucciones independientes de la variable de iteración fuera del bucle ForRango."""
        def extract(n):
            if getattr(n, 'tipo', None) == 'ForRango' and hasattr(n, 'hijos'):
                loop_var = getattr(n, 'valor', None)
                body = n.hijos[2] if len(n.hijos) > 2 else None
                if not body or not hasattr(body, 'hijos'):
                    return None
                movable = []
                remaining = []
                for stmt in body.hijos:
                    # recopilar identificadores usados en stmt
                    ids = set()
                    def collect_ids(x):
                        if getattr(x, 'tipo', None) == 'Identificador' and getattr(x, 'valor', None):
                            ids.add(x.valor)
                        return None
                    self._traverse(stmt, collect_ids)
                    # si loop_var no aparece en ids, podemos moverlo
                    if loop_var is None or loop_var not in ids:
                        movable.append(stmt)
                    else:
                        remaining.append(stmt)
                if movable:
                    # crear secuencia que primero ejecuta movables y luego el for con el cuerpo reducido
                    seq = copy.deepcopy(n)
                    seq.tipo = 'Programa'
                    seq.hijos = []
                    # agregar movables
                    for m in movable:
                        seq.hijos.append(copy.deepcopy(m))
                    # crear nuevo for con remaining
                    new_for = copy.deepcopy(n)
                    if hasattr(new_for, 'hijos') and len(new_for.hijos) > 2:
                        new_body = copy.deepcopy(new_for.hijos[2])
                        new_body.hijos = remaining
                        new_for.hijos[2] = new_body
                    seq.hijos.append(new_for)
                    return seq
            return None

        return self._traverse(ast, extract)

    def _eliminar_codigo_muerto_global(self, ast, tabla_semantica):
        """Elimina funciones y variables globales no referenciadas usando la tabla semántica."""
        def clean(n):
            if getattr(n, 'tipo', None) in ('Programa', 'Modelo') and hasattr(n, 'hijos'):
                nuevos = []
                for h in n.hijos:
                    # eliminar funciones no referenciadas
                    if getattr(h, 'tipo', None) == 'FuncionDeclarada':
                        nombre = getattr(h, 'valor', None)
                        simbolo = tabla_semantica.simbolos.get(nombre)
                        if simbolo and simbolo.get('categoria') in ('función','funcion') and simbolo.get('referencias', 0) == 0:
                            # omitir esta función
                            continue
                    nuevos.append(h)
                n.hijos = nuevos
                return n
            return None

        return self._traverse(ast, lambda x: clean(x) if getattr(x,'tipo',None) in ('Programa','Modelo') else None)

    def _fusionar_for_consecutivos(self, ast):
        """Fusiona bucles ForRango consecutivos con mismo rango y misma variable en un solo bucle concatenando cuerpos."""
        def fuse(n):
            if getattr(n, "tipo", None) in ("Programa", "FuncionDeclarada", "Modelo") and hasattr(n, "hijos"):
                nuevos = []
                i = 0
                while i < len(n.hijos):
                    a = n.hijos[i]
                    if i+1 < len(n.hijos):
                        b = n.hijos[i+1]
                        if getattr(a,"tipo",None)=="ForRango" and getattr(b,"tipo",None)=="ForRango":
                            try:
                                a_start = a.hijos[0]; a_end = a.hijos[1]; b_start = b.hijos[0]; b_end = b.hijos[1]
                                if getattr(a_start,"tipo",None)=="Numero" and getattr(b_start,"tipo",None)=="Numero" and str(a_start.valor)==str(b_start.valor) and str(a_end.valor)==str(b_end.valor) and getattr(a,"valor",None)==getattr(b,"valor",None):
                                    # fusionar
                                    fused = copy.deepcopy(a)
                                    # concatenar cuerpos
                                    body_a = a.hijos[2] if len(a.hijos)>2 else None
                                    body_b = b.hijos[2] if len(b.hijos)>2 else None
                                    fused_body = copy.deepcopy(body_a) if body_a else None
                                    if fused_body and body_b:
                                        if not hasattr(fused_body, "hijos") or fused_body.hijos is None:
                                            fused_body.hijos = []
                                        fused_body.hijos = fused_body.hijos + (copy.deepcopy(body_b.hijos) if hasattr(body_b,'hijos') else [copy.deepcopy(body_b)])
                                    fused.hijos[2] = fused_body
                                    nuevos.append(fused)
                                    i += 2
                                    continue
                            except Exception:
                                pass
                    nuevos.append(a)
                    i += 1
                n.hijos = nuevos
                return n
            return None
        return self._traverse(ast, fuse)

    def generar_codigo(self, nodo, indent=0):
        """Genera una representación textual simple del AST (para mostrar en la UI)."""
        if nodo is None:
            return ""
        pad = "    " * indent
        t = getattr(nodo, "tipo", "")
        v = getattr(nodo, "valor", "")
        out = ""
        if t == "Programa":
            for h in getattr(nodo, "hijos", []) or []:
                out += self.generar_codigo(h, indent) + "\n"
            return out
        if t == "DeclaracionVariable":
            tipo = None
            if hasattr(nodo, "hijos"):
                for h in nodo.hijos:
                    if getattr(h,"tipo",None) == "Tipo":
                        tipo = h.valor
            val = ""
            if hasattr(nodo, "hijos") and nodo.hijos:
                for h in nodo.hijos:
                    if getattr(h,"tipo",None) != "Tipo":
                        val = " = " + self.generar_codigo(h, 0).strip()
            return f"{pad}{tipo or 'var'} {v}{val};"
        if t in ("FuncionDeclarada",):
            header = f"{pad}{v}("
            # params
            params = []
            for h in getattr(nodo, "hijos", []) or []:
                if getattr(h,"tipo",None) == "Params":
                    for p in getattr(h,"hijos",[]) or []:
                        params.append(f"{p.tipo} {p.valor}")
            header += ", ".join(params) + ") {"
            body = ""
            for h in getattr(nodo, "hijos", []) or []:
                if getattr(h,"tipo",None) not in ("Params","TipoRetorno"):
                    body += "\n" + self.generar_codigo(h, indent+1)
            return header + (body + "\n" + pad + "}")
        if t == "Asignacion":
            val = ""
            if hasattr(nodo, "hijos") and nodo.hijos:
                val = self.generar_codigo(nodo.hijos[0], 0).strip()
            return f"{pad}{v.split()[0]} {v.split()[1] if len(str(v).split())>1 else '='} {val};"
        if t == "Operacion" or t == "OperacionRelacional" or t == "OperacionLogica":
            if hasattr(nodo,"hijos") and len(nodo.hijos) >= 2:
                a = self.generar_codigo(nodo.hijos[0],0).strip()
                b = self.generar_codigo(nodo.hijos[1],0).strip()
                return f"({a} {v} {b})"
            return v
        if t == "Numero":
            return str(v)
        if t == "Cadena":
            return f"\"{v}\""
        if t == "Identificador":
            return str(v)
        if t == "If":
            cond = self.generar_codigo(nodo.hijos[0],0) if hasattr(nodo,'hijos') and nodo.hijos else ""
            body = ""
            for h in getattr(nodo, "hijos", [])[1:]:
                body += "\n" + self.generar_codigo(h, indent+1)
            return f"{pad}if ({cond}) {{{body}\n{pad}}}"
        if t in ("ForRango","ForIter"):
            var = getattr(nodo, "valor", "i")
            start = self.generar_codigo(nodo.hijos[0],0) if getattr(nodo,'hijos',None) and len(nodo.hijos)>0 else "0"
            end = self.generar_codigo(nodo.hijos[1],0) if getattr(nodo,'hijos',None) and len(nodo.hijos)>1 else "0"
            body = ""
            if len(getattr(nodo,"hijos",[]))>2:
                body += "\n" + self.generar_codigo(nodo.hijos[2], indent+1)
            return f"{pad}for {var} in {start}{end} {{{body}\n{pad}}}"
        if t == "Return":
            val = self.generar_codigo(nodo.hijos[0],0) if hasattr(nodo,'hijos') and nodo.hijos else ""
            return f"{pad}return {val};"
        return f""