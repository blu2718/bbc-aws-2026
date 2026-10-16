"""Rúbricas provisorias.

Son una hipótesis del equipo que hay que validar con Integra (PLAN.md, "Mapeo
provisorio de niveles"); se reemplazan cuando entreguen su rúbrica.

- Transición: los textos salen de la tabla de
  `contexto/hallazgos-programa-pedagogico-transicion.md` ("Cómo lo usamos",
  punto 2) y calzan con las metas por defecto 1, 3, 5 y 7.
- Sala cuna y nivel medio: no hay conductas NT1/NT2 ni trayectoria; el mapeo
  combina cuántos OA del núcleo muestra el niño (los de las Bases Curriculares
  de su nivel) y con cuánta autonomía, con la misma escala de apoyo.

Los mapeos están pensados para 8 niveles. Si la rúbrica pasa a tener más, los
niveles sin texto aquí quedan sin descriptor hasta rehacer el mapeo.
"""

TRANSICION = "transicion"

# (nivel, año de las conductas o None, criterio)
MAPEO_PROVISORIO = [
    (1, None, "Muestra lo esperado al iniciar NT1."),
    (2, "NT1", "Muestra algunas conductas de NT1, con ayuda."),
    (3, "NT1", "Muestra varias conductas de NT1, algunas de forma autónoma."),
    (4, "NT1", "Muestra las conductas de NT1 de forma autónoma."),
    (5, "NT2", "Muestra algunas conductas de NT2, con ayuda."),
    (6, "NT2", "Muestra varias conductas de NT2, algunas de forma autónoma."),
    (7, "NT2", "Muestra la mayoría de las conductas de NT2 de forma autónoma."),
    (8, "NT2", "Muestra las conductas de NT2 de forma autónoma (lo esperado al egresar)."),
]

# Sala cuna y nivel medio: (nivel, criterio) sobre los OA del núcleo en su nivel educativo.
MAPEO_PROVISORIO_OA = [
    (1, "Se inicia en los aprendizajes de los OA del núcleo: los muestra ocasionalmente y con ayuda."),
    (2, "Muestra algunas conductas de los OA del núcleo, con ayuda."),
    (3, "Muestra varias conductas de los OA del núcleo, con ayuda."),
    (4, "Muestra varias conductas de los OA del núcleo, algunas de forma autónoma."),
    (5, "Muestra la mayoría de las conductas de los OA del núcleo, con ayuda ocasional."),
    (6, "Muestra la mayoría de las conductas de los OA del núcleo de forma autónoma."),
    (7, "Muestra las conductas de todos los OA del núcleo, la mayoría de forma autónoma."),
    (8, "Muestra las conductas de todos los OA del núcleo de forma autónoma (lo esperado al terminar el nivel)."),
]

NIVELES_PROVISORIOS = len(MAPEO_PROVISORIO)


def nombre_provisorio(nivel):
    """Nombre de un nivel de la rúbrica provisoria. Los de Integra traen el suyo ("Desarrollando")."""
    return f"Nivel {nivel}"


def descriptores_provisorios(nucleo, cantidad_niveles=NIVELES_PROVISORIOS, nivel_educativo=TRANSICION):
    """Devuelve [(nivel, descripción)] para un núcleo, hasta cantidad_niveles."""
    if nivel_educativo != TRANSICION:
        return [
            (nivel, f"{texto} Núcleo: {nucleo.nombre}.")
            for nivel, texto in MAPEO_PROVISORIO_OA if nivel <= cantidad_niveles
        ]
    resultado = []
    for nivel, _anio, texto in MAPEO_PROVISORIO:
        if nivel > cantidad_niveles:
            break
        descripcion = f"{texto} Núcleo: {nucleo.nombre}."
        if nivel == 1 and nucleo.esperado_inicio_nt1:
            descripcion = f"{texto} {nucleo.esperado_inicio_nt1}"
        resultado.append((nivel, descripcion))
    return resultado
