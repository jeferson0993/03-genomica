FROM openjdk:17-slim

LABEL description="Nextflow worker for Genomics Pipeline (Projeto 3) — slimmado"

RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    curl \
    ca-certificates \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://get.nextflow.io | bash \
    && mv nextflow /usr/local/bin/ \
    && chmod +x /usr/local/bin/nextflow

ENV NXF_OPTS="-Xms512m -Xmx4g"
ENV JAVA_OPTS="-Xms512m -Xmx4g"

WORKDIR /workspace

ENTRYPOINT ["/bin/bash"]
