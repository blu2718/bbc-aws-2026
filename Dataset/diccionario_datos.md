# Diccionario de datos E-1

> Datos y ruta completamente sintéticos para uso pedagógico; no constituyen un instrumento clínico validado.

Todos los CSV están en UTF-8, usan coma, encabezado y LF. Las fechas usan `AAAA-MM-DD`; cadena vacía solo está permitida en `nota_breve`. El orden es por PK, salvo observaciones (`id_nino`, fecha, ID) y la tabla puente (PK compuesta).

| Archivo | Columna | Tipo / valores | Nulo | Clave y significado |
|---|---|---|---|---|
| `jardines.csv` | `id_jardin` | cadena `JAR-0001` | No | PK ficticia. |
|  | `nombre_fantasia` | cadena | No | Nombre único y explícitamente sintético. |
|  | `comuna` | cadena | No | Contexto geográfico real. |
|  | `region` | cadena | No | Región compatible con la comuna. |
|  | `numero_salas` | entero 1–12 | No | Salas sintéticas del jardín. |
|  | `numero_educadoras` | entero ≥1 | No | Coincide con el personal relacionado. |
| `educadoras.csv` | `id_educadora` | cadena `EDU-0001` | No | PK ficticia. |
|  | `id_jardin` | cadena | No | FK a `jardines.id_jardin`. |
|  | `rol` | `educadora_parvulos`, `tecnico_parvulos` | No | Rol pedagógico sintético. |
|  | `anios_experiencia` | entero 0–35 | No | Experiencia sintética. |
| `ninos.csv` | `id_nino` | cadena `NINO-00001` | No | PK ficticia; no es nombre ni RUT. |
|  | `fecha_nacimiento` | fecha | No | Base para calcular edad. |
|  | `sexo_registrado` | `f`, `m`, `x`, `no_informado` | No | Categoría sintética explícita. |
|  | `id_jardin` | cadena | No | FK a `jardines.id_jardin`. |
|  | `sala_grupo` | cadena | No | Sala existente dentro del jardín. |
|  | `fecha_ingreso` | fecha | No | Anterior o igual a la primera observación. |
| `ruta_niveles.csv` | `nivel` | entero 1–9 | No | PK y orden de la ruta. |
|  | `nombre_nivel` | cadena | No | Nombre aprobado del nivel. |
|  | `edad_min_meses` | entero 0–36 | No | Inicio orientativo. |
|  | `edad_max_meses` | entero 0–36 | No | Fin orientativo. |
|  | `dominios` | cadena delimitada por `|` | No | Cinco dominios en orden canónico. |
|  | `descripcion` | cadena | No | Síntesis integradora. |
| `manifestaciones.csv` | `id_manifestacion` | cadena `MAN-LNN-DD-NN` | No | PK ficticia. |
|  | `nivel` | entero 1–9 | No | FK a `ruta_niveles.nivel`. |
|  | `dominio` | cinco valores del catálogo | No | Dominio principal. |
|  | `texto_observable` | cadena | No | Evidencia positiva observable. |
| `observaciones.csv` | `id_observacion` | cadena `OBS-0000001` | No | PK ficticia. |
|  | `id_nino` | cadena | No | FK a `ninos.id_nino`. |
|  | `id_educadora` | cadena | No | FK a `educadoras.id_educadora`. |
|  | `fecha_observacion` | fecha | No | Dentro de 2025-01-01 a 2026-10-13. |
|  | `formato_captura` | `video`, `audio`, `texto`, `foto` | No | Metadato; no hay archivos multimedia. |
|  | `nivel_estimado` | entero 1–9 | No | Estimación pedagógica sintética. |
|  | `nota_breve` | cadena, máximo 280 | Sí | Vacío = no se añadió nota opcional. |
| `observacion_manifestaciones.csv` | `id_observacion` | cadena | No | PK compuesta; FK a observaciones. |
|  | `id_manifestacion` | cadena | No | PK compuesta; FK a manifestaciones. |

`consolidado.json` es una vista anidada equivalente: contiene versión, fecha de referencia, naturaleza, ruta con manifestaciones y jardines con personal, niños/as y observaciones. Convierte la nota vacía a `null` y añade `edad_meses_observacion` como valor derivado.

La edad en meses completos se calcula como `12*(año_obs-año_nac)+(mes_obs-mes_nac)-1[día_obs<día_nac]`. Cada observación se vincula con una a cinco manifestaciones únicas de su nivel exacto. Una manifestación no vinculada significa únicamente que no quedó registrada.

## Referencias de la síntesis

- [OMS — Motor development milestones](https://www.who.int/tools/child-growth-standards/standards/motor-development-milestones)
- [CDC — Developmental Milestones](https://www.cdc.gov/act-early/milestones/index.html)
- [UNICEF — Developmental milestones](https://www.unicef.org/parenting/child-development/your-babys-developmental-milestones)
- [MINEDUC Chile — Bases Curriculares de Educación Parvularia](https://parvularia.mineduc.cl/wp-content/uploads/2019/09/Bases_Curriculares_Ed_Parvularia_2018-1.pdf)
