#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# generate-certs.sh
# Generates a self-signed TLS certificate for local / development Docker use.
# For production, replace these files with real certificates from Let's Encrypt
# or your organisation's CA.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")/.." && pwd)/certs"
CERT_FILE="$CERT_DIR/server.crt"
KEY_FILE="$CERT_DIR/server.key"

mkdir -p "$CERT_DIR"

if [[ -f "$CERT_FILE" && -f "$KEY_FILE" ]]; then
    echo "Certificates already exist at $CERT_DIR — skipping generation."
    echo "Delete them and re-run this script to regenerate."
    exit 0
fi

echo "Generating self-signed certificate in $CERT_DIR ..."

openssl req -x509 \
    -newkey rsa:4096 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -days 365 \
    -nodes \
    -subj "/C=EG/ST=Cairo/L=Cairo/O=BioIntellect/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo "Done."
echo "  Certificate : $CERT_FILE"
echo "  Private key : $KEY_FILE"
echo ""
echo "NOTE: This is a self-signed certificate — browsers will show a security"
echo "      warning. Accept the exception for local development."
echo "      For production, replace with a real certificate."
