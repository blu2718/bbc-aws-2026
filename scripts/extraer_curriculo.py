#!/usr/bin/env python3
"""Extrae el currículo de Transición desde el Programa Pedagógico del MINEDUC.

Genera (o actualiza) datos/curriculo_transicion.json con, por núcleo:
sigla, nombre, trayectoria educativa (lo esperado al iniciar NT1 y cómo
continúa en Enseñanza Básica) y sus OA con las conductas observables de NT1
y NT2.

Usa `pdftotext -layout` página por página y parsea el texto. Los textos se
copian tal cual del PDF. Lo que no se puede extraer con seguridad queda
marcado con "REVISAR" (o con el prefijo "REVISAR: " delante del texto
extraído) para corregirlo a mano.

Uso:
    python3 scripts/extraer_curriculo.py LV PM CM
    python3 scripts/extraer_curriculo.py --todos

Si el JSON de salida ya existe, se reemplazan solo los núcleos pedidos y se
conservan los demás.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PDF_POR_DEFECTO = RAIZ / "contexto" / "programa-pedagogico-transicion-mineduc.pdf"
SALIDA_POR_DEFECTO = RAIZ / "datos" / "curriculo_transicion.json"

# Orden canónico y páginas (numeración impresa = numeración del PDF).
NUCLEOS = {
    "IA": ("Identidad y Autonomía", 26, 65),
    "CC": ("Convivencia y Ciudadanía", 66, 101),
    "CM": ("Corporalidad y Movimiento", 102, 129),
    "LV": ("Lenguaje Verbal", 134, 183),
    "LA": ("Lenguajes Artísticos", 184, 219),
    "EEN": ("Exploración del Entorno Natural", 224, 275),
    "CES": ("Comprensión del Entorno Sociocultural", 276, 321),
    "PM": ("Pensamiento Matemático", 322, 378),
}

REVISAR = "REVISAR"

# Marcadores de sección del documento.
# IA y EEN titulan la lista "Objetivos de Aprendizaje", sin "del Núcleo".
RE_OBJETIVOS = re.compile(r"^\s*Objetivos de Aprendizaje( del Núcleo)?\s*$")
M_TRAYECTORIA = "Trayectoria educativa"
M_PREVIOS = "¿QUÉ APRENDIZAJES PREVIOS"
M_CONTINUAN = "¿CÓMO CONTINÚAN"
# CES lo titula en mayúsculas.
RE_CONOCIMIENTOS = re.compile(r"^\s*Conocimientos disciplinarios\s*$", re.IGNORECASE)
M_ESPERA = "¿QUÉ SE ESPERA QUE APRENDAN?"
M_RECONOCER = "¿CÓMO SE PODRÍA RECONOCER EL LOGRO"
M_EXPERIENCIAS = "¿QUÉ EXPERIENCIAS"

RE_LABEL_OA = re.compile(r"^\s*OA\s+(\d+)\b\s*")
RE_LABEL_NT = re.compile(r"^\s*NT\s*([12])\b\s*")
RE_NOTA_PIE = re.compile(r"^\d{1,3}\s+\S")
# Llamada a nota al pie pegada a una palabra ("capaces de19:").
RE_LLAMADA_NOTA = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]\d{1,3}\b")
# Caracteres que no deberían aparecer en un texto limpio.
RE_RARO = re.compile("[\\[\\]{}<>|\\\\\ufffd\uf000-\uf8ff]")
RE_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜáéíóúüñÑ]+(?:-[A-Za-zÁÉÍÓÚÜáéíóúüñÑ]+)*")


def pagina(pdf, n):
    """Texto -layout de una página, sin encabezado ni notas al pie.

    Devuelve (líneas, números de las notas al pie de la página)."""
    salida = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(n), "-l", str(n), str(pdf), "-"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    lineas = salida.replace("\f", "").split("\n")
    # El encabezado es la primera línea no vacía y lleva el número de página.
    for i, linea in enumerate(lineas):
        if linea.strip():
            if re.search(rf"(^|\s){n}(\s|$)", linea):
                lineas = lineas[i + 1:]
            break
    # Notas al pie: bloque final que empieza en la columna 0 con un número.
    notas = set()
    for i, linea in enumerate(lineas):
        if RE_NOTA_PIE.match(linea):
            resto = [l for l in lineas[i:] if l.strip()]
            if all(RE_NOTA_PIE.match(l) or l.startswith(" ") for l in resto):
                notas = {int(l.split()[0]) for l in resto if RE_NOTA_PIE.match(l)}
                lineas = lineas[:i]
                break
    return lineas, notas


def vocabulario(pdf):
    """Palabras que aparecen en todo el PDF, para decidir guiones de corte."""
    texto = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    return {p.lower() for p in RE_PALABRA.findall(texto)}


class Extractor:
    def __init__(self, pdf):
        self.pdf = pdf
        self.vocab = vocabulario(pdf)
        self.revisar = []  # (ubicación, motivo)
        self.guiones = []  # (ubicación, unión aplicada)
        self.diferencias = []  # (ubicación, texto de la lista, texto de la progresión)
        self.notas = set()  # números de notas al pie del núcleo en curso
        self.llamadas = []  # (ubicación, llamada a nota al pie quitada)

    # -- utilidades de texto -------------------------------------------------

    def unir(self, lineas, donde):
        """Une líneas en un párrafo, resolviendo guiones de corte de línea.

        Devuelve (texto, dudas)."""
        dudas = []
        texto = ""
        for linea in (l.strip() for l in lineas):
            if not linea:
                continue
            if not texto:
                texto = linea
                continue
            m = re.search(r"([A-Za-zÁÉÍÓÚÜáéíóúüñÑ]+)-$", texto)
            if m and re.match(r"[a-záéíóúüñ]", linea):
                antes = m.group(1)
                despues = RE_PALABRA.match(linea).group(0).split("-")[0]
                junta = (antes + despues).lower()
                con_guion = f"{antes}-{despues}".lower()
                if junta in self.vocab:
                    texto = texto[:-1] + linea
                    self.guiones.append((donde, antes + despues))
                elif con_guion in self.vocab:
                    texto = texto + linea
                    self.guiones.append((donde, f"{antes}-{despues} (guion conservado)"))
                else:
                    texto = texto[:-1] + linea
                    self.guiones.append((donde, f"{antes + despues} (dudoso)"))
                    dudas.append(f"corte de línea dudoso: '{antes}-' + '{despues}'")
            else:
                texto += " " + linea
        texto = re.sub(r"\s{2,}", " ", texto).strip()
        texto = RE_LLAMADA_NOTA.sub(lambda m: self.quitar_llamada(m, donde), texto)
        if RE_LLAMADA_NOTA.search(texto):
            dudas.append(f"posible llamada a nota al pie: '{RE_LLAMADA_NOTA.search(texto).group(0)}'")
        if RE_RARO.search(texto):
            dudas.append(f"carácter extraño: '{RE_RARO.search(texto).group(0)}'")
        return texto, dudas

    def quitar_llamada(self, m, donde):
        """Quita una llamada a nota pegada a una palabra si la nota existe."""
        if int(m.group(0)[1:]) in self.notas:
            self.llamadas.append((donde, m.group(0)))
            return m.group(0)[0]
        return m.group(0)

    def marcar(self, texto, dudas, donde):
        if not texto:
            self.revisar.append((donde, "no se pudo extraer"))
            return REVISAR
        if dudas:
            self.revisar.append((donde, "; ".join(dudas)))
            return f"{REVISAR}: {texto}"
        return texto

    @staticmethod
    def bloques(lineas):
        """Separa líneas en bloques usando las líneas en blanco."""
        actual, todos = [], []
        for linea in lineas:
            if linea.strip():
                actual.append(linea)
            elif actual:
                todos.append(actual)
                actual = []
        if actual:
            todos.append(actual)
        return todos

    @staticmethod
    def buscar(lineas, marcador, desde=0):
        """Índice de la primera línea que contiene el marcador (texto o regex)."""
        for i in range(desde, len(lineas)):
            if marcador.search(lineas[i]) if isinstance(marcador, re.Pattern) else marcador in lineas[i]:
                return i
        return -1

    # -- secciones -----------------------------------------------------------

    def lista_oa(self, lineas, sigla):
        """OA de la sección 'Objetivos de Aprendizaje del Núcleo'."""
        ini = self.buscar(lineas, RE_OBJETIVOS)
        fin = self.buscar(lineas, M_TRAYECTORIA, ini)
        if ini < 0 or fin < 0:
            self.revisar.append((sigla, "no se encontró la lista de OA"))
            return {}
        oas = {}
        for bloque in self.bloques(lineas[ini + 1:fin]):
            numeros = [m.group(1) for m in map(RE_LABEL_OA.match, bloque) if m]
            if not numeros:
                if "Bases Curriculares" in bloque[0]:
                    continue  # párrafo introductorio
                self.revisar.append((sigla, f"texto sin OA en la lista: {' '.join(l.strip() for l in bloque)[:80]}"))
                continue
            if len(numeros) > 1:
                self.revisar.append((sigla, f"bloque con varios OA en la lista: {numeros}"))
            n = int(numeros[0])
            limpio = [RE_LABEL_OA.sub("", l) for l in bloque]
            oas[n] = self.unir(limpio, f"OA {n} {sigla} (texto)")
        return oas

    def esperado_inicio(self, lineas, sigla):
        ini = self.buscar(lineas, M_PREVIOS)
        fin = self.buscar(lineas, M_CONTINUAN, ini)
        donde = f"{sigla} esperado_inicio_nt1"
        if ini < 0 or fin < 0:
            return self.marcar("", [], donde)
        texto, dudas = self.unir(lineas[ini + 1:fin], donde)
        if not texto.startswith("Al iniciar Primer Nivel de Transición"):
            dudas.append("no empieza con 'Al iniciar Primer Nivel de Transición'")
        return self.marcar(texto, dudas, donde)

    def continuidad_basica(self, lineas, sigla):
        """Segunda parte de la trayectoria: cómo continúa en Enseñanza Básica."""
        ini = self.buscar(lineas, M_CONTINUAN)
        fin = self.buscar(lineas, RE_CONOCIMIENTOS, ini)
        donde = f"{sigla} continuidad_basica"
        if ini < 0 or fin < 0:
            return self.marcar("", [], donde)
        texto, dudas = self.unir(lineas[ini + 1:fin], donde)
        if not texto.startswith("Durante"):
            dudas.append("no empieza con 'Durante'")
        return self.marcar(texto, dudas, donde)

    def progresiones(self, lineas, sigla):
        """Por cada '¿QUÉ SE ESPERA QUE APRENDAN?': número, texto y conductas."""
        inicios = [i for i, l in enumerate(lineas) if M_ESPERA in l]
        resultado = []
        for k, ini in enumerate(inicios):
            fin_sec = inicios[k + 1] if k + 1 < len(inicios) else len(lineas)
            sec = lineas[ini:fin_sec]
            i_rec = self.buscar(sec, M_RECONOCER)
            i_exp = self.buscar(sec, M_EXPERIENCIAS, max(i_rec, 0))
            bloque_oa = sec[1:i_rec] if i_rec > 0 else []
            numeros = [m.group(1) for m in map(RE_LABEL_OA.match, bloque_oa) if m]
            n = int(numeros[0]) if len(numeros) == 1 else None
            donde = f"OA {n if n else '?'} {sigla}"
            texto, _ = self.unir([RE_LABEL_OA.sub("", l) for l in bloque_oa], donde)
            if i_rec < 0 or i_exp < 0:
                self.revisar.append((donde, "no se encontró la sección de conductas completa"))
                resultado.append((n, texto, None))
                continue
            resultado.append((n, texto, self.conductas(sec[i_rec + 1:i_exp], donde)))
        return resultado

    def conductas(self, lineas, donde):
        grupos = {"NT1": [], "NT2": []}
        nivel = None
        for bloque in self.bloques(lineas):
            etiquetas = [m.group(1) for m in map(RE_LABEL_NT.match, bloque) if m]
            if len(etiquetas) > 1:
                self.revisar.append((donde, f"bloque con varias etiquetas NT: {etiquetas}"))
            if etiquetas:
                nivel = f"NT{etiquetas[0]}"
            if nivel is None:
                self.revisar.append((donde, "conductas sin etiqueta NT 1 / NT 2"))
                continue
            for linea in bloque:
                linea = RE_LABEL_NT.sub("", linea).strip()
                if linea.startswith(">"):
                    grupos[nivel].append([linea[1:].strip()])
                elif grupos[nivel]:
                    grupos[nivel][-1].append(linea)
                else:
                    self.revisar.append((f"{donde} {nivel}", f"texto antes de la primera viñeta: {linea[:80]}"))
        salida = {}
        for nivel, items in grupos.items():
            salida[nivel] = []
            for j, item in enumerate(items, 1):
                d = f"{donde} {nivel} conducta {j}"
                texto, dudas = self.unir(item, d)
                salida[nivel].append(self.marcar(texto, dudas, d))
            if not salida[nivel]:
                self.revisar.append((f"{donde} {nivel}", "sin conductas"))
                salida[nivel] = [REVISAR]
        return salida

    # -- núcleo ----------------------------------------------------------------

    def nucleo(self, sigla):
        nombre, desde, hasta = NUCLEOS[sigla]
        lineas = []
        self.notas = set()
        for n in range(desde, hasta + 1):
            texto, notas = pagina(self.pdf, n)
            lineas += texto + ["", ""]
            self.notas |= notas
        primera = " ".join(l.strip() for l in pagina(self.pdf, desde)[0][:12])
        if "Núcleo de Aprendizaje" not in primera or nombre not in primera:
            self.revisar.append((sigla, f"la página {desde} no abre el núcleo {nombre}"))

        lista = self.lista_oa(lineas, sigla)
        progs = self.progresiones(lineas, sigla)
        por_numero = {}
        for n, texto_prog, conductas in progs:
            if n is None:
                self.revisar.append((sigla, f"progresión sin número de OA: {texto_prog[:80]}"))
                continue
            if n in por_numero:
                self.revisar.append((sigla, f"OA {n} aparece dos veces en las progresiones"))
            por_numero[n] = (texto_prog, conductas)

        oas = []
        for n in sorted(set(lista) | set(por_numero)):
            donde = f"OA {n} {sigla}"
            # El texto oficial es el de la lista del núcleo (igual a las Bases).
            if n in lista:
                texto = self.marcar(*lista[n], f"{donde} (texto)")
            else:
                texto = self.marcar("", [], f"{donde} (texto: falta en la lista de OA)")
            texto_prog, conductas = por_numero.get(n, ("", None))
            if n not in por_numero:
                self.revisar.append((donde, "falta su sección de progresión y conductas"))
            elif n in lista and _norm(texto_prog) != _norm(lista[n][0]):
                # Informativo: el PDF repite el OA con otra redacción.
                self.diferencias.append((donde, lista[n][0], texto_prog))
            if conductas is None:
                conductas = {"NT1": [REVISAR], "NT2": [REVISAR]}
            oas.append({
                "numero": n,
                "codigo": f"OA {n} {sigla}",
                "texto": texto,
                "conductas": conductas,
            })
        esperados = list(range(1, len(oas) + 1))
        if [o["numero"] for o in oas] != esperados:
            self.revisar.append((sigla, f"numeración de OA no correlativa: {[o['numero'] for o in oas]}"))

        return {
            "sigla": sigla,
            "nombre": nombre,
            "esperado_inicio_nt1": self.esperado_inicio(lineas, sigla),
            "continuidad_basica": self.continuidad_basica(lineas, sigla),
            "oas": oas,
        }


def _norm(texto):
    return re.sub(r"\W+", " ", texto).strip().lower()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("siglas", nargs="*", help=f"núcleos a extraer: {' '.join(NUCLEOS)}")
    parser.add_argument("--todos", action="store_true", help="extraer los 8 núcleos")
    parser.add_argument("--pdf", type=Path, default=PDF_POR_DEFECTO)
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO)
    args = parser.parse_args()

    siglas = list(NUCLEOS) if args.todos else [s.upper() for s in args.siglas]
    if not siglas:
        parser.error("indica al menos un núcleo o --todos")
    desconocidas = [s for s in siglas if s not in NUCLEOS]
    if desconocidas:
        parser.error(f"núcleos desconocidos: {desconocidas}")

    if args.salida.exists():
        datos = json.loads(args.salida.read_text(encoding="utf-8"))
    else:
        datos = {
            "nivel_educativo": "transicion",
            "fuente": "Programa Pedagógico de Transición, MINEDUC 2019",
            "provisorio": True,
            "nucleos": [],
        }

    ex = Extractor(args.pdf)
    nuevos = {s: ex.nucleo(s) for s in siglas}
    actuales = {n["sigla"]: n for n in datos["nucleos"]}
    actuales.update(nuevos)
    datos["nucleos"] = [actuales[s] for s in NUCLEOS if s in actuales]

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Escrito {args.salida.relative_to(RAIZ) if args.salida.is_relative_to(RAIZ) else args.salida}\n")
    print("Conteo por núcleo:")
    for s in siglas:
        n = nuevos[s]
        nt1 = sum(len(o["conductas"]["NT1"]) for o in n["oas"])
        nt2 = sum(len(o["conductas"]["NT2"]) for o in n["oas"])
        print(f"  {s}: {len(n['oas'])} OA, {nt1 + nt2} conductas (NT1 {nt1}, NT2 {nt2})")

    print(f"\nMarcado REVISAR ({len(ex.revisar)}):")
    for donde, motivo in ex.revisar:
        print(f"  - {donde}: {motivo}")

    if ex.diferencias:
        print(f"\nOA cuyo texto en la progresión difiere de la lista del núcleo ({len(ex.diferencias)}).")
        print("Se usó el de la lista del núcleo:")
        for donde, lista, prog in ex.diferencias:
            print(f"  - {donde}\n      lista:      {lista}\n      progresión: {prog}")

    if ex.llamadas:
        print(f"\nLlamadas a nota al pie quitadas ({len(ex.llamadas)}):")
        for donde, llamada in ex.llamadas:
            print(f"  - {donde}: '{llamada}'")

    dudosos = [g for g in ex.guiones if "dudoso" in g[1]]
    print(f"\nCortes de línea con guion resueltos: {len(ex.guiones)} ({len(dudosos)} dudosos, marcados REVISAR)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
