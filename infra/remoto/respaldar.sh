#!/usr/bin/env bash
# Respalda la base SQLite de Kimün en s3://<bucket>/respaldos/. Corre como root
# vía SSM; scripts/desplegar.sh lo llama antes de instalar un release, así que
# el respaldo refleja la base antes de migrate y cargar_demo.
#
# Usa la API de respaldo en caliente de SQLite (sqlite3.backup() del Python del
# venv, equivalente a `.backup` del CLI): copia consistente aunque kimun-web
# esté escribiendo (WAL). Si todavía no hay base (primer despliegue), no hace nada.
#
# Uso:
#   respaldar.sh --bucket <bucket> --region <region> [--etiqueta <texto>]
set -euo pipefail

DB=/var/lib/kimun/db.sqlite3
PYTHON=/opt/kimun/venv/bin/python

error() {
    echo "ERROR: $*" >&2
    exit 1
}

BUCKET=""
REGION=""
ETIQUETA="manual"
while [ $# -gt 0 ]; do
    case "$1" in
        --bucket) BUCKET="${2:-}"; shift 2 || error "falta el valor de --bucket" ;;
        --region) REGION="${2:-}"; shift 2 || error "falta el valor de --region" ;;
        --etiqueta) ETIQUETA="${2:-}"; shift 2 || error "falta el valor de --etiqueta" ;;
        *) error "argumento desconocido: $1" ;;
    esac
done

[[ "$BUCKET" =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]] || error "--bucket inválido: '$BUCKET'"
[[ "$REGION" =~ ^[a-z]{2}(-[a-z]+)+-[0-9]+$ ]] || error "--region inválida: '$REGION'"
[[ "$ETIQUETA" =~ ^[A-Za-z0-9._-]{1,100}$ ]] || error "--etiqueta inválida: '$ETIQUETA'"
[ "$(id -u)" -eq 0 ] || error "hay que correrlo como root"

echo "==> Respaldo de $DB"
if [ ! -f "$DB" ]; then
    echo "No existe $DB (primer despliegue): no hay nada que respaldar."
    exit 0
fi
[ -x "$PYTHON" ] || error "no está $PYTHON para hacer el respaldo"

umask 077
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fecha=$(date -u +%Y%m%d%H%M%S)
archivo="db-$fecha-$ETIQUETA.sqlite3"

"$PYTHON" - "$DB" "$tmp/$archivo" <<'EOF'
import sqlite3
import sys

origen, destino = sys.argv[1], sys.argv[2]
src = sqlite3.connect(origen, timeout=20)
dst = sqlite3.connect(destino)
with dst:
    src.backup(dst)
src.close()
# El respaldo es un archivo autónomo (sin -wal): se deja en modo DELETE.
dst.execute("PRAGMA journal_mode=DELETE")
resultado = dst.execute("PRAGMA integrity_check").fetchone()[0]
dst.close()
if resultado != "ok":
    sys.exit(f"integrity_check del respaldo: {resultado}")
print("integrity_check: ok")
EOF

gzip -9 "$tmp/$archivo"
clave="respaldos/$archivo.gz"
aws s3 cp --only-show-errors --region "$REGION" "$tmp/$archivo.gz" "s3://$BUCKET/$clave"
echo "Respaldo subido: s3://$BUCKET/$clave ($(stat -c %s "$tmp/$archivo.gz") bytes)"
