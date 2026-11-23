#!/usr/bin/env bash
# Checks that HTTP/2 is off on both ports of the nginx-proxy image (nginx2root).
# Builds the image, runs it in front of a dummy backend with a self-signed certificate, then probes it.
# Usage: nginx/test_http2.sh (needs docker and openssl; uses port 8443, override with PORT=...)
set -euo pipefail

cd "$(dirname "$0")"

NAME=rnb-osm-nginx-test
HOST=osm.test
PORT=${PORT:-8443}
CERTS_DIR=$(mktemp -d)
FAILURES=0

cleanup() {
    docker rm -f "$NAME-proxy" "$NAME-backend" >/dev/null 2>&1 || true
    docker network rm "$NAME" >/dev/null 2>&1 || true
    rm -rf "$CERTS_DIR"
}
trap cleanup EXIT

docker build --quiet --tag "$NAME" . >/dev/null

# nginx-proxy only serves HTTPS for a host with a certificate.
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=$HOST" \
    -keyout "$CERTS_DIR/$HOST.key" -out "$CERTS_DIR/$HOST.crt" 2>/dev/null
# With a default certificate, the fallback server completes TLS for clients without SNI.
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=default" \
    -keyout "$CERTS_DIR/default.key" -out "$CERTS_DIR/default.crt" 2>/dev/null

docker network create "$NAME" >/dev/null
docker run --detach --name "$NAME-backend" --network "$NAME" \
    --env VIRTUAL_HOST="$HOST" --env VIRTUAL_PORT=80 traefik/whoami:v1.10 >/dev/null
docker run --detach --name "$NAME-proxy" --network "$NAME" --publish "$PORT:443" \
    --volume "$CERTS_DIR:/etc/nginx/certs:ro" \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro "$NAME" >/dev/null

# check <label> <output> <grep -E pattern>
check() {
    if echo "$2" | grep -qE "$3"; then
        echo "ok    $1"
    else
        echo "FAIL  $1 (got: $2)"
        FAILURES=$((FAILURES + 1))
    fi
}

https() {
    curl --silent --insecure --output /dev/null --resolve "$HOST:$PORT:127.0.0.1" "$@" || true
}

# Wait for nginx-proxy to generate its config and route the host.
for _ in $(seq 30); do
    [ "$(https --write-out '%{http_code}' "https://$HOST:$PORT/")" = 200 ] && break
    sleep 1
done

check "HTTPS: vhost is proxied" "$(https --write-out '%{http_code}' "https://$HOST:$PORT/")" '^200$'
# Each check expects an exact value, so a failed handshake or a curl without HTTP/2 fails instead of passing.
check "HTTPS, curl --http2: answers in HTTP/1.1" \
    "$(https --http2 --write-out '%{http_version}' "https://$HOST:$PORT/")" '^1\.1$'
# Over TLS, ALPN must pick http/1.1, with SNI and without (what scanners hitting the IP send).
alpn() {
    echo | openssl s_client -connect "127.0.0.1:$PORT" -alpn h2,http/1.1 "$@" 2>/dev/null || true
}
check "HTTPS with SNI: ALPN picks http/1.1" "$(alpn -servername "$HOST" | grep '^ALPN')" '^ALPN protocol: http/1\.1$'
check "HTTPS without SNI: ALPN picks http/1.1" "$(alpn -noservername | grep '^ALPN')" '^ALPN protocol: http/1\.1$'
# On port 80, an h2c prior-knowledge request must get no HTTP/2 answer, neither for the vhost nor for the
# fallback server (unknown Host): nginx either answers the preface in HTTP/1.1 (curl exit 16, nginx 1.31.3)
# or closes the connection without a reply (curl exit 52). Without the fix, curl gets `2 0`.
# The proxy's curl is used because the host's may lack HTTP/2.
for host in "$HOST" unknown.test; do
    h2c=$(docker exec "$NAME-proxy" curl --silent --http2-prior-knowledge --output /dev/null --max-time 5 \
        --write-out '%{http_version} %{exitcode}' --header "Host: $host" http://localhost/ || true)
    check "port 80, Host $host: no h2c" "$h2c" '^0 (16|52)$'
done

if [ "$FAILURES" -gt 0 ]; then
    echo "$FAILURES check(s) failed"
    exit 1
fi
echo "All checks passed"
