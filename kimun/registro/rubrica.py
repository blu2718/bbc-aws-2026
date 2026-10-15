"""Rúbrica provisoria de Transición.

Es una hipótesis del equipo que hay que validar con Integra (PLAN.md, "Mapeo
provisorio de niveles"); se reemplaza cuando entreguen su rúbrica. Los textos
salen de la tabla de `contexto/hallazgos-programa-pedagogico-transicion.md`
("Cómo lo usamos", punto 2) y calzan con las metas por defecto 1, 3, 5 y 7.

El mapeo está pensado para 8 niveles. Si la rúbrica pasa a tener más, los
niveles sin texto aquí quedan sin descriptor hasta rehacer el mapeo.
"""

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

NIVELES_PROVISORIOS = len(MAPEO_PROVISORIO)


def descriptores_provisorios(nucleo, cantidad_niveles=NIVELES_PROVISORIOS):
    """Devuelve [(nivel, descripción)] para un núcleo de Transición, hasta cantidad_niveles."""
    resultado = []
    for nivel, _anio, texto in MAPEO_PROVISORIO:
        if nivel > cantidad_niveles:
            break
        descripcion = f"{texto} Núcleo: {nucleo.nombre}."
        if nivel == 1 and nucleo.esperado_inicio_nt1:
            descripcion = f"{texto} {nucleo.esperado_inicio_nt1}"
        resultado.append((nivel, descripcion))
    return resultado
