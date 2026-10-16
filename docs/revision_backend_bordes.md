# Revisión del proyecto y casos borde — 15 de octubre de 2026

## Alcance

Revisión del código Django, rutas y plantillas, formularios, permisos, procesamiento
de capturas, propuestas de nivel y configuración de despliegue. Pruebas locales
con base de datos de test y sustitutos de Bedrock/Transcribe; sin llamadas reales
a AWS, despliegues ni cambios a la base de datos local existente.

## Pendientes prioritarios

1. **P1 — Texto y fotos pueden agotar el tiempo de la petición web.**
   `registro/views_registro.py:procesar` llama a `procesar_si_pendiente`, que ejecuta
   la lectura y separación dentro de la petición. El cliente Bedrock tiene
   `read_timeout=60` y un presupuesto de reintentos de 90 segundos; una foto puede
   requerir dos invocaciones. `infra/README.md` documenta un tiempo de espera de
   origen de 30 segundos y `kimun-web.service` configura Gunicorn con 60 segundos.
   Ambos archivos afirman que las vistas no llaman a Bedrock, lo que contradice
   el código actual. Una respuesta lenta puede dejar la pantalla esperando o
   interrumpir el procesamiento. Hacer que la vista consulte el estado y que
   `procesar_capturas` procese también texto/fotos, como ya ocurre con audio.
   Este cambio de arquitectura queda pendiente; no se midió latencia en AWS.

2. **P1 — La base local está desactualizada.**
   `manage.py showmigrations --plan` muestra `registro.0001` y `0002` aplicadas,
   pero `0003` a `0008` pendientes. Faltan cambios de esquema usados por las
   capturas, perfiles y propuestas actuales. Las migraciones existen en el repo:
   tras respaldar la base, ejecutar `python manage.py migrate` desde `kimun/`.
   No se modificó esa base durante esta revisión. Las pruebas crean su propia
   base con todas las migraciones, por lo que un test aprobado no resuelve este
   pendiente del entorno local.

3. **P1 — No se puede validar la conexión AWS real desde esta sesión.**
   La cadena local de boto3 no encontró credenciales ni perfiles configurados
   (se deshabilitó la consulta de metadatos EC2 para este diagnóstico), y
   `KIMUN_BUCKET` no está definido. Bedrock necesita credenciales con permiso de
   invocación; audio necesita además bucket y permisos S3/Transcribe.
   Esto describe el entorno accesible de esta sesión, no el estado de EC2.
   Pendiente comprobar con el entorno del despliegue: credenciales vigentes,
   acceso al modelo, bucket y funcionamiento de ambos workers.

## Conexiones implementadas

| Flujo | Evidencia en el código | Dependencia operativa |
|---|---|---|
| Registro y revisión | Formularios → vistas → Captura/Observacion → aceptación y ficha | Migraciones aplicadas |
| Texto y foto | `procesamiento.py` → `lectura.py` → cliente Bedrock | Acceso a Bedrock; revisar el tiempo de espera HTTP |
| Audio | Worker → ClienteTranscribe → S3 → separación Bedrock | `KIMUN_BUCKET`, credenciales y `procesar_capturas` activo |
| Propuestas de nivel | Solicitud/aceptación → `propuestas.py` → `procesar_propuestas` | Worker de propuestas activo y acceso a Bedrock |
| Despliegue | `instalar.sh` instala/reinicia web, capturas y propuestas | Verificar estado real en EC2 |

Se verificaron las 31 rutas nombradas referenciadas literalmente desde las
plantillas: todas están definidas. No se encontró un botón principal sin ruta
de backend en esta comprobación. No sustituye una prueba visual del navegador.

En desarrollo, `runserver` por sí solo no inicia los workers. Abrir terminales
adicionales dentro de `kimun/`, con el mismo entorno y credenciales:

```powershell
.\.venv\Scripts\python.exe manage.py procesar_capturas
.\.venv\Scripts\python.exe manage.py procesar_propuestas
```

Los comandos son procesos separados y permanecen ejecutándose. Django no carga
automáticamente un archivo `.env`; las variables deben estar en el entorno.

## Fallos reproducidos y corregidos

Se agregaron 21 casos en `registro/tests/test_bordes_integracion.py`. Antes de
los cambios: **12 fallaban y 9 pasaban**. Los fallos representaban cinco problemas:

- El texto adjunto a una foto/audio y el contexto agregado posteriormente no
  llegaban a la separación. Ahora se combinan con la transcripción al leer,
  conservando el texto extraído por separado y sin duplicarlo al reintentar.
- Un POST completamente vacío dejaba el formulario sin validar y respondía 200.
  Ahora muestra la validación y responde 400.
- Las fechas `0001-01-01` y `0001-01-15` producían un error 500 al calcular la
  quincena anterior. Ahora se omite la navegación anterior en el límite mínimo.
- Un objeto de captura desactualizado podía devolver a pendiente un trabajo
  recién tomado por otro worker. Ahora la actualización también exige que
  coincidan la fecha de actualización y el número de intentos leídos.
- El worker aceptaba `NaN` e infinito como intervalo. Ahora los rechaza antes
  de procesar trabajos.

También se comprueban los límites de 4.000/4.001 caracteres, foto y audio
simultáneos, fecha bisiesta, fecha futura, fecha inexistente y valores negativos
o cero para el intervalo.

Se usa un hasher rápido únicamente dentro de la suite de tests para las cuentas
ficticias; la configuración de contraseñas de la aplicación no cambia.

## Validación

- Pruebas focalizadas de los nuevos casos, capturas, fotos, audio y registro:
  **108 aprobadas**.
- `manage.py check`: sin problemas.
- `manage.py makemigrations --check --dry-run`: sin cambios pendientes de generar.
- `python -m pip check`: sin dependencias incompatibles declaradas.
- `git diff --check`: sin errores de espacios.
- Suite completa: **950 aprobadas en 82,77 segundos**, incluidos los 21 casos
  nuevos. Comando ejecutado desde `kimun/`:

  ```powershell
  .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --durations=10 --tb=short --basetemp=C:/Users/cahc2/.codex/visualizations/2026/10/16/01a14278-f495-7c22-860d-1138f73a4ee9/pytest-final
  ```

La primera ejecución encontró un error de permisos al crear carpetas temporales
en Windows. Se usó `--basetemp` dentro de una carpeta permitida; no era un fallo
de lógica de la aplicación. Las ejecuciones de pytest se hicieron de una en una.
