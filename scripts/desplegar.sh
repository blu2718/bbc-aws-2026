#!/usr/bin/env bash
# Despliega Kimün en la EC2 del stack kimun-mvp. Se corre desde la máquina del
# desarrollador, con credenciales de AWS:
#
#   scripts/desplegar.sh [--recargar-demo] [--permitir-cambios]
#
# 1. Lee bucket, instancia y URL de los outputs del stack (nada escrito a mano).
# 2. Crea el SECRET_KEY en Parameter Store como SecureString solo si no existe
#    (nunca lo muestra ni lo sobrescribe).
# 3. Empaqueta el código (git archive de HEAD) y lo sube a s3://<bucket>/releases/.
# 4. Por SSM, la instancia descarga el release y ejecuta infra/remoto/instalar.sh
#    del propio release (venv, migrate, collectstatic, cargar_demo, servicios).
# 5. Prueba <UrlCloudFront>/login/ con curl.
#
# Variables (con valor por defecto): KIMUN_STACK=kimun-mvp, KIMUN_REGION=us-east-1,
# KIMUN_PARAMETRO_SECRET=/kimun/django-secret-key.
set -euo pipefail

STACK="${KIMUN_STACK:-kimun-mvp}"
REGION="${KIMUN_REGION:-us-east-1}"
PARAMETRO="${KIMUN_PARAMETRO_SECRET:-/kimun/django-secret-key}"
PLAZO_SEGUNDOS=1800

uso() {
    cat <<'EOF'
Uso: scripts/desplegar.sh [--recargar-demo] [--permitir-cambios] [-h|--help]

  --recargar-demo     Corre cargar_demo aunque la base ya tenga cursos (no borra
                      datos; actualiza los de demo). Por defecto solo corre si
                      no hay ningún curso.
  --permitir-cambios  Despliega el árbol de trabajo aunque tenga cambios sin
                      commit (archivos versionados y no ignorados).
  -h, --help          Muestra esta ayuda.

Variables: KIMUN_STACK (kimun-mvp), KIMUN_REGION (us-east-1),
KIMUN_PARAMETRO_SECRET (/kimun/django-secret-key).
EOF
}

error() {
    echo "ERROR: $*" >&2
    exit 1
}

RECARGAR_DEMO=0
PERMITIR_CAMBIOS=0
while [ $# -gt 0 ]; do
    case "$1" in
        --recargar-demo) RECARGAR_DEMO=1 ;;
        --permitir-cambios) PERMITIR_CAMBIOS=1 ;;
        -h | --help) uso; exit 0 ;;
        *) uso >&2; error "opción desconocida: $1" ;;
    esac
    shift
done

for comando in aws git python3 curl tar; do
    command -v "$comando" >/dev/null 2>&1 || error "falta el comando $comando"
done
[[ "$REGION" =~ ^[a-z]{2}(-[a-z]+)+-[0-9]+$ ]] || error "KIMUN_REGION inválida: '$REGION'"
[[ "$PARAMETRO" =~ ^/[A-Za-z0-9_./-]+$ ]] || error "KIMUN_PARAMETRO_SECRET inválido: '$PARAMETRO'"

cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# --- 1. Outputs del stack ----------------------------------------------------
output_del_stack() {
    local valor
    valor=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" --output text)
    [ -n "$valor" ] && [ "$valor" != "None" ] || error "el stack $STACK no tiene el output $1"
    printf '%s' "$valor"
}

echo "==> Outputs del stack $STACK ($REGION)"
BUCKET=$(output_del_stack NombreBucket)
INSTANCIA=$(output_del_stack InstanciaId)
URL=$(output_del_stack UrlCloudFront)
DOMINIO=$(output_del_stack DominioCloudFront)
[[ "$BUCKET" =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]] || error "bucket inválido: '$BUCKET'"
[[ "$INSTANCIA" =~ ^i-[0-9a-f]+$ ]] || error "instancia inválida: '$INSTANCIA'"
[[ "$DOMINIO" =~ ^[a-z0-9.-]+\.cloudfront\.net$ ]] || error "dominio inválido: '$DOMINIO'"
[ "$URL" = "https://$DOMINIO" ] || error "UrlCloudFront ($URL) no coincide con el dominio ($DOMINIO)"
echo "Bucket: $BUCKET | Instancia: $INSTANCIA | URL: $URL"

# --- 2. SECRET_KEY en Parameter Store ----------------------------------------
echo "==> SECRET_KEY ($PARAMETRO)"
if tipo=$(aws ssm get-parameter --name "$PARAMETRO" --region "$REGION" \
    --query Parameter.Type --output text 2>"$tmp/ssm.err"); then
    [ "$tipo" = "SecureString" ] || error "$PARAMETRO existe pero es $tipo, no SecureString"
    echo "Ya existe (SecureString): no se toca."
elif grep -q ParameterNotFound "$tmp/ssm.err"; then
    # La clave se genera en un archivo 0600 dentro de $tmp (0700, se borra al
    # salir): no aparece en la línea de comandos ni en la salida. El CLI v2 no
    # acepta --cli-input-json desde un pipe. Sin --overwrite: si alguien la
    # creó entretanto, falla.
    (umask 077 && python3 -c 'import json, secrets, sys; print(json.dumps({"Name": sys.argv[1], "Type": "SecureString", "Value": secrets.token_urlsafe(50), "Description": "SECRET_KEY de Django (kimun-mvp)"}))' "$PARAMETRO" >"$tmp/secreto.json")
    aws ssm put-parameter --cli-input-json "file://$tmp/secreto.json" --region "$REGION" \
        --query Version --output text >/dev/null
    rm -f "$tmp/secreto.json"
    echo "Creado como SecureString (el valor no se muestra)."
else
    cat "$tmp/ssm.err" >&2
    error "no se pudo consultar $PARAMETRO"
fi

# --- 3. Paquete del release --------------------------------------------------
echo "==> Paquete"
sha=$(git rev-parse --short HEAD)
fecha=$(date -u +%Y%m%d%H%M%S)
if [ -n "$(git status --porcelain)" ]; then
    if [ "$PERMITIR_CAMBIOS" -ne 1 ]; then
        git status --short >&2
        error "hay cambios sin commit. Haz commit o usa --permitir-cambios."
    fi
    RELEASE="kimun-$sha-cambios-$fecha"
    echo "Empaquetando el árbol de trabajo con cambios sin commit (--permitir-cambios)."
    git ls-files -z --cached --others --exclude-standard \
        | tar --null --ignore-failed-read --owner=0 --group=0 --numeric-owner \
            -czf "$tmp/$RELEASE.tar.gz" -T -
else
    RELEASE="kimun-$sha-$fecha"
    git archive --format=tar.gz -o "$tmp/$RELEASE.tar.gz" HEAD
fi
CLAVE="releases/$RELEASE.tar.gz"
aws s3 cp --only-show-errors "$tmp/$RELEASE.tar.gz" "s3://$BUCKET/$CLAVE" --region "$REGION"
echo "Subido s3://$BUCKET/$CLAVE"

# --- 4. Instalación por SSM --------------------------------------------------
# El send-command solo lleva este bootstrap corto; la lógica vive versionada en
# infra/remoto/instalar.sh, dentro del release. Todos los valores interpolados
# ya se validaron arriba.
DIR="/opt/kimun/releases/$RELEASE"
instalar=(bash "$DIR/infra/remoto/instalar.sh" --release-dir "$DIR" --dominio "$DOMINIO"
    --bucket "$BUCKET" --region "$REGION" --parametro "$PARAMETRO")
[ "$RECARGAR_DEMO" -eq 1 ] && instalar+=(--recargar-demo)
comandos=(
    "set -eu"
    "install -d -m 0755 /opt/kimun/releases"
    "d=\$(mktemp -d /opt/kimun/releases/.descarga.XXXXXX)"
    "aws s3 cp --only-show-errors --region $REGION s3://$BUCKET/$CLAVE \"\$d/release.tar.gz\""
    "mkdir -m 0755 \"\$d/codigo\""
    "tar -xzf \"\$d/release.tar.gz\" -C \"\$d/codigo\" --no-same-owner"
    "rm -rf $DIR"
    "mv \"\$d/codigo\" $DIR"
    "rm -rf \"\$d\""
    "${instalar[*]}"
)
parametros=$(python3 -c 'import json, sys; print(json.dumps({"commands": sys.argv[1:], "executionTimeout": ["1800"]}))' "${comandos[@]}")

echo "==> SSM send-command a $INSTANCIA"
COMANDO_ID=$(aws ssm send-command --instance-ids "$INSTANCIA" --document-name AWS-RunShellScript \
    --comment "kimun desplegar $RELEASE" --timeout-seconds 120 --parameters "$parametros" \
    --region "$REGION" --query Command.CommandId --output text)
echo "CommandId: $COMANDO_ID (esperando hasta $((PLAZO_SEGUNDOS / 60)) min)"

limite=$((SECONDS + PLAZO_SEGUNDOS))
estado=""
while :; do
    if estado=$(aws ssm get-command-invocation --command-id "$COMANDO_ID" --instance-id "$INSTANCIA" \
        --region "$REGION" --query Status --output text 2>"$tmp/inv.err"); then
        case "$estado" in
            Pending | InProgress | Delayed | Cancelling) ;;
            *) break ;;
        esac
    elif ! grep -q InvocationDoesNotExist "$tmp/inv.err"; then
        cat "$tmp/inv.err" >&2
        error "no se pudo consultar el comando $COMANDO_ID"
    fi
    [ "$SECONDS" -lt "$limite" ] || error "el comando $COMANDO_ID no terminó en $PLAZO_SEGUNDOS s"
    sleep 5
done

echo "==> Salida de la instancia (SSM la corta en unos 24 000 caracteres)"
aws ssm get-command-invocation --command-id "$COMANDO_ID" --instance-id "$INSTANCIA" \
    --region "$REGION" --query StandardOutputContent --output text
errores=$(aws ssm get-command-invocation --command-id "$COMANDO_ID" --instance-id "$INSTANCIA" \
    --region "$REGION" --query StandardErrorContent --output text)
if [ -n "$errores" ] && [ "$errores" != "None" ]; then
    echo "--- stderr ---"
    printf '%s\n' "$errores"
fi
[ "$estado" = "Success" ] || error "el despliegue terminó con estado $estado"

# --- 5. Prueba por CloudFront ------------------------------------------------
echo "==> GET $URL/login/"
codigo=$(curl -sS --max-time 30 -D "$tmp/cabeceras" -o "$tmp/cuerpo" -w '%{http_code}' "$URL/login/") || true
head -n 1 "$tmp/cabeceras" 2>/dev/null || true
grep -o '<title>[^<]*</title>' "$tmp/cuerpo" 2>/dev/null || true
[ "$codigo" = "200" ] || error "$URL/login/ respondió '$codigo' (se esperaba 200)"
echo "Listo: $URL (usuaria de prueba: educadora; la contraseña aparece en la salida del primer despliegue)."
