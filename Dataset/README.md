# Dataset sintético E-1 — Ruta de Trayectoria de Aprendizaje

> **Uso pedagógico:** todos los registros son ficticios. La ruta de nueve niveles es una síntesis para una hackathon; no es un instrumento clínico, diagnóstico, de tamizaje ni una evaluación validada.

## Contenido público

`datos_publicos/` contiene siete CSV relacionales y `consolidado.json`. `diccionario_datos.md`, `ejemplos_trayectorias.md` y `distribucion_y_validacion.md` explican la estructura y los resultados.

## Reproducción y validación

El entorno oficial de reproducción es Python 3.12.15 y solo usa la biblioteca estándar. Los hashes publicados se produjeron con esa versión exacta. La generación usa el valor fijo `20261013` y la fecha de referencia `2026-10-13`.

```zsh
python3.12 generador.py --output-root "$PWD" --zip-root "$(dirname "$PWD")"
python3.12 validador.py --output-root "$PWD" --zip-root "$(dirname "$PWD")"
```

La salida usa UTF-8, LF, orden canónico y ZIP sin compresión con fecha fija `1980-01-01`, permisos `0644` y entradas lexicográficas. Una segunda corrida limpia debe producir archivos idénticos bit a bit.

## Ausencias

Sesenta niños/as tienen una o dos observaciones debido a ingreso reciente; los otros 440 tienen entre cuatro y nueve. Una nota vacía significa que no se añadió nota opcional. La ausencia de observación, formato o manifestación solo significa que no quedó registrada en esa instancia.

## Distribución segura

Entregue a participantes únicamente `dataset_e1_publico.zip`. `dataset_e1_validacion_interna.zip` es material reservado de la organización y **NO SE DEBE DISTRIBUIR A PARTICIPANTES**.
