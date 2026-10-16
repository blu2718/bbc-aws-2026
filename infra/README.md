# infra/

Plantilla CloudFormation del MVP de Kimün (`plantilla.yaml`), stack `kimun-mvp` en us-east-1.

## Validar

cfn-lint está instalado fuera del repo, en un venv propio (no va en `requirements.txt`):

```fish
~/.local/share/kimun-tools/cfn-lint-venv/bin/cfn-lint infra/plantilla.yaml
aws cloudformation validate-template --template-body file://infra/plantilla.yaml --region us-east-1
```

Para reinstalarlo: `python3 -m venv ~/.local/share/kimun-tools/cfn-lint-venv` y `~/.local/share/kimun-tools/cfn-lint-venv/bin/pip install cfn-lint==1.57.2`.

## Crear el stack

Requiere `CAPABILITY_NAMED_IAM` porque el rol y el instance profile tienen nombre fijo.

```fish
aws cloudformation create-stack --stack-name kimun-mvp --template-body file://infra/plantilla.yaml --capabilities CAPABILITY_NAMED_IAM --region us-east-1
aws cloudformation wait stack-create-complete --stack-name kimun-mvp --region us-east-1
aws cloudformation describe-stacks --stack-name kimun-mvp --region us-east-1 --query 'Stacks[0].Outputs'
```

## Pendiente fuera de la plantilla

- El parámetro SecureString `/kimun/django-secret-key` no lo crea CloudFormation (`AWS::SSM::Parameter` no admite SecureString). La instancia solo puede leerlo.
- Ese parámetro lo crea `scripts/desplegar.sh` si no existe (ver "Desplegar la app").
- El `OriginReadTimeout` de CloudFront queda en 30 s: las vistas no llaman a Bedrock (lo hace el worker en segundo plano).
- Para borrar el stack, primero hay que vaciar el bucket (`aws s3 rm s3://kimun-mvp-<cuenta> --recursive`). Si no, el borrado queda en `DELETE_FAILED`.
- Los trabajos de Transcribe y los vocabularios deben llamarse `kimun-*`, y la salida de Transcribe debe ir a `transcripciones/` del bucket. Así lo exigen los permisos del rol.

## Desplegar la app

Requiere credenciales de AWS y el stack `kimun-mvp` creado. Desde la raíz del repo:

```fish
scripts/desplegar.sh [--recargar-demo] [--permitir-cambios]
```

1. Lee bucket, instancia y URL de los outputs del stack.
2. Crea `/kimun/django-secret-key` como SecureString solo si no existe. Nunca lo muestra ni lo sobrescribe.
3. `git archive` de HEAD a `s3://<bucket>/releases/kimun-<sha>-<fecha>.tar.gz`.
4. Por SSM (`send-command`), la instancia descarga el release, respalda la base con `infra/remoto/respaldar.sh` y ejecuta `infra/remoto/instalar.sh` del propio release: venv, `migrate`, `collectstatic`, `check --deploy`, `cargar_demo`, servicios y un health check local. El script muestra la salida.
5. `curl` a `<UrlCloudFront>/login/`.

- `--recargar-demo`: corre `cargar_demo` aunque ya haya cursos. Por defecto solo corre si la base no tiene ningún curso. No borra datos: actualiza los de demo.
- `--permitir-cambios`: empaqueta el árbol de trabajo (versionados y no ignorados) aunque haya cambios sin commit. Sin la opción, el script aborta si hay cambios.
- Variables: `KIMUN_STACK` (`kimun-mvp`), `KIMUN_REGION` (`us-east-1`), `KIMUN_PARAMETRO_SECRET` (`/kimun/django-secret-key`).
- `cargar_demo` imprime la contraseña de cada usuaria solo cuando la crea (no cambia las que ya existen). En el primer despliegue salen todas; en un `--recargar-demo` sobre una base anterior a la Task 12 salen las de `directora`, `educadora_b` y `educadora_c`, que son nuevas. Quedan en la salida del despliegue y en el historial de comandos de SSM.

## En la instancia

- Código: `/opt/kimun/releases/<release>` (se conservan los 5 más recientes) y el symlink `/opt/kimun/actual`.
- Entorno virtual: `/opt/kimun/venv` (Python 3.12, solo `requirements.txt`).
- Datos (usuario `kimun`): `/var/lib/kimun/db.sqlite3` (SQLite en WAL), `/var/lib/kimun/static`, `/var/lib/kimun/media`.
- Entorno: `/etc/kimun/kimun.env` (lo genera `instalar.sh`, sin secretos): `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_SECRET_KEY_PARAMETRO`, `DJANGO_DB_PATH`, `DJANGO_STATIC_ROOT`, `DJANGO_MEDIA_ROOT`, `DJANGO_SECURE_HSTS_SECONDS=3600`, `AWS_DEFAULT_REGION`, `BEDROCK_MODEL_ID` (`us.anthropic.claude-sonnet-5`), `BEDROCK_REGION`, `KIMUN_BUCKET`.
- El SECRET_KEY lo lee Django de Parameter Store con el rol de la instancia.

## Respaldos de la base

Cada despliegue, antes de `migrate`, sube un respaldo a `s3://<bucket>/respaldos/db-<fecha UTC>-antes-<release>.sqlite3.gz`. Usa `sqlite3.backup()` del Python del venv (copia en caliente, consistente con WAL) y verifica `integrity_check`. Si el respaldo falla, el despliegue se detiene. En el primer despliegue no hay base y se omite. La instancia solo puede escribir en `respaldos/`, no leer ni borrar.

Para restaurar: la instancia no puede leer `respaldos/`. Desde tu máquina, copia el respaldo a `releases/` (`aws s3 cp s3://<bucket>/respaldos/<archivo>.gz s3://<bucket>/releases/<archivo>.gz`) y luego, en la instancia:

```bash
aws s3 cp s3://<bucket>/releases/<archivo>.gz /tmp/ && gunzip /tmp/<archivo>.gz
sudo systemctl stop kimun-web kimun-worker kimun-propuestas
sudo install -o kimun -g kimun -m 0640 /tmp/<archivo> /var/lib/kimun/db.sqlite3
sudo rm -f /var/lib/kimun/db.sqlite3-wal /var/lib/kimun/db.sqlite3-shm
sudo systemctl start kimun-web kimun-worker kimun-propuestas
```

## Servicios y logs

Units en `infra/systemd/`. `instalar.sh` instala, habilita y reinicia los tres en cada despliegue; si alguno no queda activo, el despliegue falla y muestra las últimas 50 líneas de su `journalctl`.

- `kimun-web`: Gunicorn en el puerto 8000, 3 workers, timeout 60 s.
- `kimun-worker`: `manage.py procesar_capturas --intervalo 2`. Separa las notas en observaciones, lee las fotos y transcribe los audios (Bedrock y Transcribe). Es el único que llama a Bedrock por una captura: la página solo consulta el estado. Devuelve a la cola las capturas atascadas en procesando.
- `kimun-propuestas`: `manage.py procesar_propuestas --intervalo 5`. Genera las propuestas de nivel que pide la educadora o que se encolan al aceptar observaciones (Task 7, Bedrock).
- Sin SSH: entrar con `aws ssm start-session --target <InstanciaId> --region us-east-1` (o mandar comandos con `aws ssm send-command`).
- `systemctl status kimun-web kimun-worker kimun-propuestas`; logs con `journalctl -u <servicio> -f`.
