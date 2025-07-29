FROM alpine:3.18

# Installera nödvändiga paket
RUN apk add --no-cache \
    kamailio \
    kamailio-utils \
    netcat-openbsd \
    && rm -rf /var/cache/apk/*

# Skapa nödvändiga kataloger
RUN mkdir -p /var/log/kamailio /etc/kamailio

# Exponera portar
EXPOSE 5060/udp 5060/tcp 5061/tcp

# Kopiera konfigurationsfil
COPY k8s/configmap.yaml /tmp/
RUN grep -A 1000 "kamailio.cfg: |" /tmp/configmap.yaml | tail -n +2 > /etc/kamailio/kamailio.cfg

# Starta Kamailio
CMD ["kamailio", "-f", "/etc/kamailio/kamailio.cfg", "-DD", "-E"] 