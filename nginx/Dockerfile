FROM nginxproxy/nginx-proxy:1.11.6
# HTTP/2 is off until nginx-proxy ships nginx >= 1.31.9 (nginx2root).
# ENABLE_HTTP2=false drops `http2 on;` from the vhosts, but the template still forces it on its fallback
# server, which then serves h2c on port 80 for any unknown Host. The sed removes that line; the grep
# fails the build if the template changes (1.11.6 keeps two conditional `http2 on;` per vhost).
ENV ENABLE_HTTP2=false
RUN sed -i '/server_name _; # This is just an invalid value/,/http2 on;/{/^    http2 on;$/d}' /app/nginx.tmpl \
    && grep -c 'http2 on;' /app/nginx.tmpl | grep -qx 2
