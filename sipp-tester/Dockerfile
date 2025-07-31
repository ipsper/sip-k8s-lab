FROM ubuntu:22.04

# Installera nödvändiga paket inklusive SIPp
RUN apt-get update && apt-get install -y \
    netcat \
    curl \
    wget \
    build-essential \
    cmake \
    libncurses5-dev \
    libpcap-dev \
    libssl-dev \
    libsctp-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installera SIPp från källa
RUN cd /tmp && \
    git clone https://github.com/SIPp/sipp.git && \
    cd sipp && \
    cmake . -DUSE_SSL=1 -DUSE_SCTP=1 && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/sipp

# Skapa arbetskatalog
WORKDIR /app

# Kopiera test-script
COPY test-scripts/ /app/test-scripts/
COPY sipp-scenarios/ /app/sipp-scenarios/

# Gör script körbara
RUN chmod +x /app/test-scripts/*.sh

# Exponera portar för SIPp
EXPOSE 5060/udp 5060/tcp

# Default command
CMD ["/app/test-scripts/run-tests.sh"]
