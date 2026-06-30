---
title: "Pipeline de Chamada de Variantes Germinativas WGS com Nextflow, FastAPI e GATK"
description: "Como construímos um pipeline genômico de produção orquestrado por Nextflow, gerenciado via FastAPI e visualizado com um dashboard TypeScript — tudo containerizado e integrado a um Data Lake Biomédico"
tags: [nextflow, gatk, bioinformatics, genomics, fastapi, python, docker]
published: false
---

## O Problema

O sequenciamento completo do genoma (WGS) é hoje peça central na pesquisa biomédica. No entanto, executar um pipeline de chamada de variantes germinativas seguindo as GATK Best Practices está longe de ser trivial — especialmente quando se exige reprodutibilidade e rastreabilidade.

Uma análise típica de WGS envolve:

1. **Controle de qualidade** dos FASTQs brutos
2. **Alinhamento** contra o genoma de referência (BWA-MEM)
3. **Pós-alinhamento** (MarkDuplicates, BQSR)
4. **Chamada de variantes** (HaplotypeCaller)
5. **Genotipagem conjunta e filtragem** (VQSR)
6. **Relatório de qualidade** (MultiQC)

Sem orquestração, cada etapa é executada manualmente ou com scripts ad hoc. Gerenciamento de containers, limpeza de arquivos intermediários, lógica de retry e proveniência de resultados viram um fardo que compromete a reprodutibilidade.

Foi para resolver isso que construímos o **Projeto 3 — Genomics Pipeline** da Plataforma Integrada de Bioinformática: um pipeline Nextflow associado a uma camada de orquestração FastAPI e um dashboard TypeScript.

---

## Arquitetura

```
                ┌──────────────┐
                │   Frontend   │  Vanilla TS + Vite + Plotly
                │  /genomics/  │
                └──────┬───────┘
                       │ HTTP
                ┌──────▼───────┐
                │  FastAPI API │  Gerenciamento de runs
                │  /api/genomics│  POST/GET runs, logs, cancel
                └──────┬───────┘
                       │ docker exec
                ┌──────▼───────┐
                │  Nextflow    │  BWA → GATK → Filter → MultiQC
                │  Worker      │  32G / 8 CPUs, Docker-in-Docker
                └──────────────┘
```

### Stack

| Camada | Tecnologia |
|--------|-----------|
| Motor de pipeline | Nextflow DSL2 |
| Alinhamento | BWA-MEM (biocontainers/bwa) |
| Pós-alinhamento | GATK4 MarkDuplicates + BQSR |
| Chamada de variantes | GATK4 HaplotypeCaller |
| Filtragem | GATK4 VQSR + VariantFiltration |
| QC | FastQC + MultiQC |
| API de orquestração | Python 3.12 / FastAPI async |
| Banco de dados | PostgreSQL 16 |
| Object storage | MinIO |
| Frontend | TypeScript + Vite 6 + Plotly |

---

## O Pipeline (Nextflow DSL2)

O pipeline é modular, com cada etapa em um módulo independente:

```
pipeline/
├── main.nf              → Entry point
├── conf/
│   ├── base.config      → Alocação de recursos
│   ├── docker.config    → Imagens dos containers
│   ├── grch38.config    → Caminhos da referência GRCh38
│   └── test.config      → Modo teste (chr22)
├── modules/             → fastqc, bwa_mem, markduplicates,
│                          baserecalibrator, haplotype_caller,
│                          genotype_gvcfs, variant_filtration, multiqc
└── subworkflows/        → align, variant_call, filter
```

O workflow principal executa 4 subworkflows em sequência:

```groovy
workflow {
    ALIGN(reads_ch, ref_bwa_idx, ref_fasta, ref_dict, ref_dbsnp, ref_indels)
    VARIANT_CALL(ALIGN.out.bqsr_bam, ref_fasta, ref_dict, ref_dbsnp)
    FILTER(VARIANT_CALL.out.raw_vcf, ..., ref_fasta, ref_dict, ref_dbsnp, ref_indels)
    MULTIQC(qc_files)
}
```

Decisões de design importantes:

- **Módulos DSL2** para cada ferramenta — é possível trocar ou estender etapas sem tocar no resto
- **Perfil Docker** — todas as ferramentas rodam via containers oficiais (`broadinstitute/gatk`, `biocontainers/bwa`)
- **Modo teste** — executa apenas no cromossomo 22, ideal para CI e desenvolvimento
- **Limpeza automática** — em caso de sucesso, o `workDir` é deletado para economizar disco

---

## A API REST

A camada FastAPI expõe endpoints para disparar e monitorar execuções:

```bash
# Criar e disparar um run
curl -X POST http://localhost:8002/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Amostra NA12878",
    "samplesheet_path": "/workspace/samplesheet.csv",
    "reference": "grch38"
  }'

# Listar runs (com filtro opcional de status)
curl http://localhost:8002/runs?status=running

# Obter detalhes
curl http://localhost:8002/runs/<uuid>

# Logs em tempo real
curl http://localhost:8002/runs/<uuid>/logs

# Relatório MultiQC
curl http://localhost:8002/runs/<uuid>/report

# Cancelar
curl -X POST http://localhost:8002/runs/<uuid>/cancel
```

### Modelo de dados

```python
class PipelineRun(Base):
    id: Mapped[uuid.UUID]
    name: Mapped[str]
    status: Mapped[PipelineStatus]  # pending → queued → running → completed/failed
    samplesheet_path: Mapped[str]
    reference: Mapped[str]
    nextflow_run_id: Mapped[str | None]
    output_dir: Mapped[str | None]
    report_path: Mapped[str | None]
    datalake_dataset_id: Mapped[str | None]  # Link para o Data Lake
```

### Controle de concorrência

Para evitar exaustão de recursos, a API rejeita novos runs quando o limite é atingido:

```python
if active_count >= settings.max_concurrent_runs:
    raise HTTPException(status_code=429, detail="Limite de execuções simultâneas atingido")
```

---

## Frontend

O dashboard (Vanilla TypeScript + Vite 6 + Plotly) é uma SPA com:

- **Lista de runs** — tabela com badges de status, duração, referência
- **Detalhe do run** — streaming de logs em tempo real, links para download do VCF
- **Visualizador MultiQC** — dashboard de qualidade embutido
- **Gerenciador de referências** — upload e listagem de genomas de referência

---

## Reprodutibilidade

Diversas decisões garantem que os resultados sejam reproduzíveis:

1. **Seed fixa** — `params.seed = 42` propagado para o GATK
2. **Dados de entrada imutáveis** — FASTQs vindos do Data Lake (bucket `raw` com object-lock)
3. **Containers versionados** — todas as imagens com tags explícitas, sem `latest`
4. **Publicação de resultados** — VCF final e relatório MultiQC salvos em diretório específico do run
5. **Integração com Data Lake** — ao finalizar, resultados são registrados no catálogo com proveniência completa
6. **Limpeza de intermediários** — arquivos temporários deletados em caso de sucesso

---

## Infraestrutura

O pipeline executa em um **worker dedicado** com Docker-in-Docker:

```yaml
worker:
  build: worker/Dockerfile  # nfcore/base + Java + Python
  volumes:
    - ref_data:/ref                # Genoma de referência (~60 GB)
    - workspace:/workspace         # Arquivos do run
    - /var/run/docker.sock:/var/run/docker.sock
  environment:
    NXF_OPTS: -Xms512m -Xmx4g
  deploy:
    resources:
      limits:
        memory: 32G
        cpus: '8'
```

O volume `ref_data` é populado por um serviço one-shot:

```bash
docker compose run --rm ref-dl
```

---

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/runs` | Criar e disparar um novo run |
| `GET` | `/runs` | Listar runs (filtro opcional `?status=`) |
| `GET` | `/runs/{id}` | Detalhes do run |
| `GET` | `/runs/{id}/logs` | Logs do pipeline |
| `GET` | `/runs/{id}/report` | Caminho do relatório MultiQC |
| `POST` | `/runs/{id}/cancel` | Cancelar execução |
| `POST` | `/references` | Registrar genoma de referência |
| `GET` | `/references` | Listar referências disponíveis |
| `GET` | `/health` | Health check (PostgreSQL + MinIO) |

---

## Lições Aprendidas

1. **Nextflow + Docker é poderoso, mas consome memória.** O worker precisa de pelo menos 4 GB de RAM só para a JVM. Configuramos `NXF_OPTS` e `JAVA_OPTS` de forma conservadora.

2. **Docker-in-Docker é a forma mais simples de rodar containers Nextflow** dentro de um ambiente containerizado. Montar `/var/run/docker.sock` evita forwarding complexo de sockets.

3. **O download do genoma de referência é o maior ponto de atrito.** Os índices do GRCh38 têm ~60 GB. Criamos um serviço separado (`ref-dl`) em vez de inflar a imagem do worker.

4. **Limites de concorrência são essenciais** — um único HaplotypeCaller pode consumir 8+ cores e 16 GB+ de RAM. Sem o throttle na API, os runs causariam OOM no host.

5. **Integração VCF → Data Lake** — cada run concluído registra um `datalake_dataset_id` para análises downstream (descoberta de biomarcadores, redes biológicas).

6. **Frontend importa para adoção.** Pesquisadores não querem SSH no servidor para rodar `nextflow run`. O dashboard com logs em tempo real torna o pipeline acessível.

---

## Repositório

Este é o Projeto 3 do monorepo da Plataforma Integrada de Bioinformática (16 projetos). O código completo está em:

```
03-genomica/
├── app/              → FastAPI backend
├── pipeline/         → Nextflow DSL2
├── frontend/         → TypeScript SPA
├── worker/           → Dockerfile do worker
├── scripts/          → Utilitários de download
└── docker-compose.yml
```

---

Se você está construindo um pipeline genômico ou precisa de um workflow de chamada de variantes em nível de produção orquestrado via REST, espero que este projeto sirva de referência. A combinação **Nextflow + FastAPI + Docker** é portável o suficiente para um servidor de laboratório e escalável para um cluster multi-nó.

Comentários e perguntas são bem-vindos!
