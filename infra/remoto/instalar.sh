#!/usr/bin/env bash
# Instala un release de Kimün en la EC2 de kimun-mvp. Corre como root vía SSM
# (lo llama scripts/desplegar.sh después de descargar y descomprimir el
# release). Idempotente: se puede repetir con el mismo release o con otro.
#
# Uso:
#   instalar.sh --release-dir /opt/kimun/releases/<release> --dominio <d...cloudfront.net> \
#               --bucket <bucket> --region <region> --parametro </kimun/...> [--recargar-demo]
set -euo pipefail

RELEASES=/opt/kimun/releases
ACTUAL=/opt/kimun/actual
VENV=/opt/kimun/venv
ENV_FILE=/etc/kimun/kimun.env
DATOS=/var/lib/kimun
CONSERVAR=5
# Modelo de Bedrock explícito en el entorno, para no depender del valor por
# defecto del código (registro/ia/bedrock.py).
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-5

error() {
    echo "ERROR: $*" >&2
    exit 1
}

RELEASE_DIR=""
DOMINIO=""
BUCKET=""
REGION=""
PARAMETRO=""
RECARGAR_DEMO=0

while [ $# -gt 0 ]; do
    case "$1" in
        --release-dir) RELEASE_DIR="${2:-}"; shift 2 || error "falta el valor de --release-dir" ;;
        --dominio) DOMINIO="${2:-}"; shift 2 || error "falta el valor de --dominio" ;;
        --bucket) BUCKET="${2:-}"; shift 2 || error "falta el valor de --bucket" ;;
        --region) REGION="${2:-}"; shift 2 || error "falta el valor de --region" ;;
        --parametro) PARAMETRO="${2:-}"; shift 2 || error "falta el valor de --parametro" ;;
        --recargar-demo) RECARGAR_DEMO=1; shift ;;
        *) error "argumento desconocido: $1" ;;
    esac
done

# Validación antes de tocar nada. Los valores terminan en el EnvironmentFile
# y en comandos, así que solo se aceptan formatos conocidos.
[[ "$RELEASE_DIR" =~ ^/opt/kimun/releases/kimun-[0-9a-f]{7,40}(-cambios)?-[0-9]{14}$ ]] \
    || error "--release-dir inválido: '$RELEASE_DIR'"
[[ "$DOMINIO" =~ ^[a-z0-9.-]+\.cloudfront\.net$ ]] || error "--dominio inválido: '$DOMINIO'"
[[ "$BUCKET" =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]] || error "--bucket inválido: '$BUCKET'"
[[ "$REGION" =~ ^[a-z]{2}(-[a-z]+)+-[0-9]+$ ]] || error "--region inválida: '$REGION'"
[[ "$PARAMETRO" =~ ^/[A-Za-z0-9_./-]+$ ]] || error "--parametro inválido: '$PARAMETRO'"
[ "$(id -u)" -eq 0 ] || error "hay que correrlo como root"
[ -f "$RELEASE_DIR/kimun/manage.py" ] || error "no está $RELEASE_DIR/kimun/manage.py"

# manage.py como usuario kimun, con el entorno de producción y el código del
# release nuevo (el symlink se cambia recién cuando todo esto funcionó).
manage() {
    runuser -u kimun -- /bin/bash -c \
        'set -a; . /etc/kimun/kimun.env; set +a; cd "$1/kimun"; shift; exec /opt/kimun/venv/bin/python manage.py "$@"' \
        _ "$RELEASE_DIR" "$@"
}

echo "==> Release: $RELEASE_DIR"

echo "==> Python 3.12"
rpm -q python3.12 python3.12-pip >/dev/null 2>&1 || dnf install -y -q python3.12 python3.12-pip

echo "==> Usuario kimun y directorios"
id -u kimun >/dev/null 2>&1 || useradd --system --home-dir /opt/kimun --shell /sbin/nologin kimun
install -d -m 0755 /opt/kimun "$RELEASES" /etc/kimun
install -d -o kimun -g kimun -m 0750 "$DATOS" "$DATOS/static" "$DATOS/media"

echo "==> Entorno virtual $VENV"
[ -x "$VENV/bin/python" ] || /usr/bin/python3.12 -m venv "$VENV"
"$VENV/bin/pip" install -q --disable-pip-version-check -r "$RELEASE_DIR/kimun/requirements.txt"

echo "==> $ENV_FILE (sin secretos: el SECRET_KEY se lee de Parameter Store)"
tmp_env=$(mktemp /etc/kimun/.kimun.env.XXXXXX)
cat > "$tmp_env" <<EOF
# Generado por infra/remoto/instalar.sh. No editar a mano.
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=$DOMINIO,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://$DOMINIO
DJANGO_SECRET_KEY_PARAMETRO=$PARAMETRO
DJANGO_DB_PATH=$DATOS/db.sqlite3
DJANGO_STATIC_ROOT=$DATOS/static
DJANGO_MEDIA_ROOT=$DATOS/media
DJANGO_SECURE_HSTS_SECONDS=3600
AWS_DEFAULT_REGION=$REGION
BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID
BEDROCK_REGION=$REGION
KIMUN_BUCKET=$BUCKET
EOF
chown root:kimun "$tmp_env"
chmod 0640 "$tmp_env"
mv -f "$tmp_env" "$ENV_FILE"

echo "==> migrate"
manage migrate --noinput
echo "==> collectstatic"
manage collectstatic --noinput
echo "==> check --deploy"
manage check --deploy --fail-level ERROR

echo "==> cargar_demo"
cursos=$(manage shell --no-imports -c "from registro.models import Curso; print(Curso.objects.count())" | tail -n 1)
[[ "$cursos" =~ ^[0-9]+$ ]] || error "no se pudo contar los cursos (salida: '$cursos')"
if [ "$RECARGAR_DEMO" -eq 1 ] || [ "$cursos" -eq 0 ]; then
    echo "Corriendo cargar_demo (las contraseñas solo se muestran al crear cada usuaria)."
    manage cargar_demo
else
    echo "Base con $cursos curso(s): se omite cargar_demo (usar --recargar-demo para forzarlo)."
fi

echo "==> Release activo: $ACTUAL -> $RELEASE_DIR"
ln -sfn "$RELEASE_DIR" "$ACTUAL.nuevo"
mv -T "$ACTUAL.nuevo" "$ACTUAL"

echo "==> Servicios systemd"
# kimun-web (Gunicorn), kimun-worker (procesar_capturas: separa notas, lee fotos
# y transcribe audios) y kimun-propuestas (procesar_propuestas: propuestas de nivel).
SERVICIOS=(kimun-web kimun-worker kimun-propuestas)
for servicio in "${SERVICIOS[@]}"; do
    install -m 0644 "$RELEASE_DIR/infra/systemd/$servicio.service" /etc/systemd/system/
done
systemctl daemon-reload
for servicio in "${SERVICIOS[@]}"; do
    systemctl enable "$servicio"
    systemctl restart "$servicio"
done
# Unos segundos para que un servicio que se cae al partir no pase como activo
# (con Restart=always quedaría en "activating" esperando el reinicio).
sleep 5
for servicio in "${SERVICIOS[@]}"; do
    if ! systemctl is-active --quiet "$servicio"; then
        echo "$servicio no quedó activo ($(systemctl is-active "$servicio" || true))." >&2
        journalctl -u "$servicio" -n 50 --no-pager >&2 || true
        exit 1
    fi
    echo "$servicio: activo"
done

echo "==> Health check local"
codigo=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 \
    --retry 30 --retry-connrefused --retry-delay 1 \
    -H "Host: $DOMINIO" -H 'CloudFront-Forwarded-Proto: https' \
    http://127.0.0.1:8000/login/) || true
if [ "$codigo" != "200" ]; then
    echo "GET /login/ respondió '$codigo' (se esperaba 200)." >&2
    journalctl -u kimun-web -n 50 --no-pager >&2 || true
    exit 1
fi
echo "GET http://127.0.0.1:8000/login/ -> $codigo"

echo "==> Limpieza de releases (se conservan los $CONSERVAR más recientes y el activo)"
activo=$(readlink -f "$ACTUAL")
find "$RELEASES" -mindepth 1 -maxdepth 1 -type d -name '.descarga.*' -exec rm -rf {} +
find "$RELEASES" -mindepth 1 -maxdepth 1 -type d -name 'kimun-*' -printf '%T@ %p\n' \
    | sort -rn | tail -n +$((CONSERVAR + 1)) | cut -d' ' -f2- \
    | while read -r viejo; do
        if [ "$viejo" != "$activo" ]; then
            echo "Borrando $viejo"
            rm -rf -- "$viejo"
        fi
    done

echo "==> Resumen"
echo "Release activo: $activo"
for servicio in "${SERVICIOS[@]}"; do
    echo "$servicio: $(systemctl is-active "$servicio" || true)"
done
echo "SQLite journal_mode: $(manage shell --no-imports -c "from django.db import connection; c = connection.cursor(); c.execute('PRAGMA journal_mode'); print(c.fetchone()[0])" | tail -n 1)"
