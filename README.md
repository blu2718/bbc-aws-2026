# bbc-aws-2026
Hackathon Breaking Barriers 2026 · Desafío 1 Fundación Integra. El plan está en `PLAN.md`.

La app web (Django) vive en `kimün/`. Los datos compartidos (`datos/`) y los scripts (`scripts/`) quedan en la raíz.

## Desarrollo local

Requiere Python 3.12. Todos los comandos se corren dentro de `kimün/`.

```powershell
cd kimün
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # en Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py cargar_demo          # muestra las contraseñas de "educadora" y "asistente" la primera vez
python manage.py runserver
```

Si Windows bloquea `Activate.ps1` ("la ejecución de scripts está deshabilitada"), ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o usa `.\.venv\Scripts\python.exe` en lugar de `python`.

Abrir http://127.0.0.1:8000 y entrar como `educadora` (revisa y valida) o `asistente` (solo registra). Para el panel de administración, crear un usuario con `python manage.py createsuperuser` y entrar en `/admin/`. Ahí se cambia la cantidad de niveles de la rúbrica (Rúbricas) y se asigna la directora de un jardín.

`cargar_demo` se puede correr varias veces sin duplicar datos. Para fijar la contraseña, define `DEMO_PASSWORD` antes de correrlo y usa `--cambiar-password` si la usuaria ya existe.

Tests: `pytest` (dentro de `kimün/`). Variables de entorno: ver `kimün/.env.example`.

## Estructura

| Ruta | Contenido |
|---|---|
| `kimün/config/` | Configuración de Django (todo lo variable se lee del entorno) |
| `kimün/registro/models.py` | Todas las entidades del plan, con sus restricciones |
| `kimün/registro/curriculo.py`, `kimün/registro/rubrica.py` | Carga del currículo de Transición y rúbrica provisoria 8×8 |
| `kimün/registro/permisos.py` | `cursos_de(usuario)` para ver, `cursos_donde_registra` para capturar y `cursos_que_valida` para revisar y validar: filtro obligatorio en toda vista con datos de un curso |
| `kimün/registro/management/commands/cargar_demo.py` | Currículo, semestres y curso de demo con 15 niños ficticios |
| `kimün/templates/`, `kimün/registro/templates/` | Plantillas base, login y tabla del curso |
| `kimün/static/vendor/` | Pico.css y HTMX con versión fija (sin CDN) |
| `datos/` | `curriculo_transicion.json` (85 OA, trayectoria por núcleo) y `demo_curso.json` |
| `scripts/extraer_curriculo.py` | Regenera el currículo desde el PDF: `python -X utf8 scripts/extraer_curriculo.py --todos` (requiere `pdftotext` de Poppler; en Windows, `winget install oschwartz10612.Poppler`) |

La cantidad de niveles (hoy 8) se define en la rúbrica de cada nivel educativo, no en el código: nunca usar un 8 fijo. Para el máximo, usar `Rubrica.nivel_maximo(nivel_educativo)`.

Al agregar campos a los modelos, crear la migración en la misma rama (`python manage.py makemigrations`) para evitar choques entre ramas.
