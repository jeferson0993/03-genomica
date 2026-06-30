# Plano de Implementação — Projeto 3: Genomics Pipeline

## Visão Geral

Pipeline de chamada de variantes germinativas WGS seguindo GATK Best Practices.
Entrada: FASTQ → Saída: VCF filtrado + relatório MultiQC.
Orquestrado via Nextflow, com API FastAPI para disparo e monitoramento.

Integra-se à infraestrutura compartilhada do monorepo:
- **Data Lake** (Projeto 2): lê FASTQs do bucket `raw`, escreve resultados em `processed`/`curated` e registra saídas no catálogo.
- **PostgreSQL e MinIO**: serviços compartilhados definidos no `docker-compose.yml` raiz.
- **Gateway Nginx**: rota `/api/genomics/` para acesso externo.

---

## Escopo

| Item | Incluído |
|---|---|
| Pipeline Nextflow | Alinhamento BWA → GATK HaplotypeCaller → VCF filtrado |
| Controle de qualidade | FastQC + MultiQC obrigatório antes de qualquer análise |
| API REST | Disparar runs, consultar status, baixar relatórios |
| Containerização | Imagens oficiais (Broad GATK, biocontainers) via docker.config do Nextflow |
| Referência genômica | GRCh38 (hg38) — download automatizado + índices BWA/GATK |
| Execução | Worker separado executa Nextflow; API apenas orquestra via subprocess |

---

## Stack

| Área | Tecnologia |
|---|---|
| Workflow | Nextflow + módulos próprios (inspirado em nf-core/sarek) |
| Alinhamento | BWA-MEM (`biocontainers/bwa`) |
| Pós-alinhamento | GATK4 MarkDuplicates, BQSR (`broadinstitute/gatk`) |
| Chamada variantes | GATK4 HaplotypeCaller (GVCF) |
| Joint genotyping | GATK4 CombineGVCFs + GenotypeGVCFs |
| Filtragem | GATK4 VQSR / VariantFiltration |
| Relatórios | FastQC, MultiQC |
| Container | Imagens oficiais via `docker.config` do Nextflow |
| Orquestração | Python, FastAPI, SQLAlchemy async |
| Gerenciador | uv (API Python) |
| Lint / type | ruff, mypy |

---

## Estrutura de Diretórios

```
03-genomica/
├── docker-compose.yml          # usa network externa bioinfo-platform-net
├── .env.example
├── pyproject.toml              # API Python
│
├── app/                        # FastAPI (achatado, sem subdiretório api/)
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── run.py              # PipelineRun ORM
│   │   └── reference.py        # ReferenceGenome ORM
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── run.py
│   │   └── reference.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── runs.py
│   │   └── references.py
│   └── services/
│       ├── __init__.py
│       ├── pipeline_service.py # Dispara Nextflow no worker via subprocess
│       ├── minio_service.py    # Upload/download MinIO (Data Lake)
│       ├── datalake_service.py # Registra resultados no catálogo do Data Lake
│       └── monitor_service.py  # Poll nextflow logs / trace
│
├── pipeline/                   # Nextflow pipeline
│   ├── main.nf
│   ├── nextflow.config
│   ├── modules/
│   │   ├── fastqc.nf
│   │   ├── bwa_align.nf
│   │   ├── gatk_dedup.nf
│   │   ├── gatk_bqsr.nf
│   │   ├── gatk_haplotypecaller.nf
│   │   ├── gatk_combine.nf
│   │   ├── gatk_genotype.nf
│   │   └── gatk_vqsr.nf
│   ├── subworkflows/
│   │   ├── align.nf
│   │   ├── variant_call.nf
│   │   └── filter.nf
│   ├── conf/
│   │   ├── base.config         # CPU/mem allocations
│   │   ├── docker.config       # Container images (oficiais)
│   │   └── grch38.config       # Reference paths (volume montado)
│   ├── bin/
│   │   └── custom scripts
│   └── assets/
│       └── samplesheet.csv
│
├── containers/                 # (opcional) apenas se necessário customizar
│
├── scripts/
│   ├── download-ref-grch38.sh  # Baixa FASTA + índices + known sites
│   └── gen-test-data.sh        # Gera FASTQ sintético (chr22 via wgsim)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   └── test_services/
│
└── docs/
    └── README.md
```

---

## Pipeline (estágios)

```
samplesheet.csv (sample,fastq_1,fastq_2)
         │
         ▼
┌──────────────────────────┐
│  1. FastQC + MultiQC     │  ← sempre obrigatório
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  2. BWA-MEM alignment    │  bwa mem → samtools sort/index
│     (BAM por amostra)     │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  3. GATK MarkDuplicates   │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  4. BQSR                  │  BaseRecalibrator + ApplyBQSR
│     (Base Quality Score   │
│      Recalibration)       │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  5. GATK HaplotypeCaller  │  GVCF mode por amostra
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  6. CombineGVCFs +        │  cohort-level
│     GenotypeGVCFs         │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  7. VQSR / Hard Filtering │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  8. VCF + Stats + Report  │  bcftools stats + MultiQC
└──────────────────────────┘
```

---

## Modelo de Dados

### PipelineRun

| Campo | Tipo | Descrição |
|---|---|---|
| id | UUID (PK) | Identificador único |
| name | str | Nome da execução |
| status | enum(pending, queued, running, completed, failed, cancelled) | Estado |
| samplesheet_path | str | Caminho da samplesheet no MinIO |
| reference | str | Nome da referência (ex: grch38) |
| params | JSONB | Parâmetros extras do Nextflow |
| nextflow_run_id | str | ID interno do Nextflow |
| output_dir | str | Diretório de saída no MinIO (`processed/runs/{id}/`) |
| report_path | str? | Caminho do MultiQC report |
| started_at | timestamptz | Início |
| completed_at | timestamptz? | Término |
| duration_seconds | int? | Duração total |
| error_message | text? | Erro se falhou |
| datalake_dataset_id | str? | ID do dataset registrado no catálogo do Data Lake (Projeto 2) |

### ReferenceGenome

| Campo | Tipo | Descrição |
|---|---|---|
| id | UUID (PK) | Identificador único |
| name | str | grch38, grch37, etc. |
| species | str | Homo sapiens |
| fasta_path | str | Caminho **no volume compartilhado** (`/ref/{name}/GRCh38.fa`) |
| bwa_index_prefix | str | Prefixo dos índices BWA (`/ref/{name}/bwa/hg38`) |
| dbsnp_path | str | dbSNP vcf para BQSR |
| known_indels_path | str | Mills + 1000G indels |
| gtf_path | str | GTF de genes |
| minio_prefix | str | Prefixo no MinIO onde a referência está armazenada (`refs/grch38/`) |
| is_default | bool | Usado como referência padrão |
| created_at | timestamptz | Data de registro |

---

## Endpoints da API

| Método | Caminho | Descrição |
|---|---|---|
| `POST` | `/runs` | Disparar pipeline (body: samplesheet, reference, name, params) |
| `GET` | `/runs` | Listar execuções (`?status=&limit=&offset=`) |
| `GET` | `/runs/{id}` | Detalhes + status atual |
| `GET` | `/runs/{id}/report` | Download do MultiQC report |
| `GET` | `/runs/{id}/logs` | Logs do Nextflow |
| `POST` | `/runs/{id}/cancel` | Cancelar execução |
| `GET` | `/references` | Listar genomas de referência disponíveis |
| `POST` | `/references` | Registrar nova referência |
| `GET` | `/health` | Healthcheck |

---

## Fluxo de uma Execução

```
1. POST /runs { samplesheet: "raw://samplesheets/cohort_01.csv", reference: "grch38", name: "cohort_01" }
2. Cria PipelineRun(status=pending) no PostgreSQL
3. Obtém samplesheet do MinIO (bucket raw)
4. Dispara worker: docker compose exec worker nextflow run pipeline/main.nf -params-file params.json
5. PipelineRun.status = running
6. MonitorService poll logs/trace do Nextflow via Docker
7. Ao finalizar:
   - Sucesso: status = completed, copia resultados para MinIO (processed/curated)
   - Registra dataset de saída no catálogo do Data Lake (POST /catalog)
   - Falha:   status = failed, registra error_message
8. Resultados em: processed/runs/{id}/  +  catalogados no Data Lake
```

---

## Docker Compose

```yaml
services:
  api:              # FastAPI, porta 8000, depende de postgres+minio (shared)
  worker:           # Nextflow runtime, imagem pipeline-omics, volume refs
  ref-dl:           # one-shot: download GRCh38 + índices BWA e known sites GATK

networks:
  default:
    external: true
    name: bioinfo-platform-net
```

Usa a **infraestrutura compartilhada** da raiz: postgres, minio, gateway.
Não duplica serviços — segue o padrão de Projetos 01 e 02.

### Worker

O worker é um container separado (não o api) que:
- Contém Java 17+ e Nextflow
- Monta volume `/ref/` com genomas de referência (read-only)
- Monta volume `/workspace` para execução dos pipelines
- Executa `nextflow run` via comando disparado pela API (docker exec)
- Usa `docker.config` com imagens oficiais para cada ferramenta

---

## Integração com Data Lake (Projeto 2)

| Etapa | Bucket MinIO | Descrição |
|---|---|---|
| Leitura FASTQs | `raw` | Dados brutos imutáveis, ingeridos pelo Projeto 1 |
| Samplesheets | `raw/genomics/samplesheets/` | CSV com amostras |
| BAMs intermediários | `processed/runs/{id}/` | BAM sorted/dedup/BQSR |
| GVCFs | `processed/runs/{id}/` | GVCF por amostra |
| VCF final | `curated/genomics/{run_id}/` | VCF filtrado + índices |
| MultiQC | `curated/genomics/{run_id}/qc/` | Relatório HTML |

Ao finalizar uma execução, a API chama o endpoint `POST /catalog` do Data Lake para registrar os datasets gerados, criando rastreabilidade completa.

---

## Gateway Nginx

A rota `/api/genomics/` será adicionada ao `nginx.conf.template`:

```nginx
location /api/genomics/ {
    proxy_pass http://03-genomica-api-1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 30s;
    proxy_read_timeout 120s;
}
```

---

## Fases de Implementação

### Fase 1 — Fundação (dias 1-2)

- `app/` — FastAPI scaffold achatado (sem subdiretório `api/`): `main.py`, `config.py`, `database.py`, models (PipelineRun, ReferenceGenome)
- `pipeline/` — `main.nf` vazio, `nextflow.config`, `conf/base.config`, `conf/docker.config` (com imagens oficiais: `broadinstitute/gatk`, `biocontainers/bwa`, `staphb/fastqc`, `multiqc/multiqc`)
- `docker-compose.yml` — apenas `api`, `worker`, `ref-dl`; rede externa `bioinfo-platform-net`; sem postgres/minio próprios
- Script `download-ref-grch38.sh` — FASTA + BWA index + GATK known sites; aceita `--chr22-only` para teste rápido
- Script `gen-test-data.sh` — gera FASTQ sintético (chr22, wgsim) para validação
- `.env.example`
- Atualizar `gateway/nginx.conf.template` com rota `/api/genomics/`

### Fase 2 — Pipeline Nextflow (dias 3-6)

- Módulo FastQC (FASTQ → reports HTML)
- Módulo BWA-MEM (bwa mem + samtools sort/index)
- Módulo GATK MarkDuplicates
- Módulo GATK BQSR (BaseRecalibrator + ApplyBQSR)
- Módulo GATK HaplotypeCaller (GVCF)
- Módulo CombineGVCFs + GenotypeGVCFs
- Módulo VQSR / Hard Filter
- Módulo MultiQC final
- `conf/grch38.config` com paths da referência (volume `/ref/`)
- Teste com dados sintéticos via `gen-test-data.sh` (FASTQ chr22, cobertura 1x)

### Fase 3 — API + Orquestração + Data Lake (dias 7-9)

- `services/pipeline_service.py` — dispara `nextflow run` via `docker compose exec worker`
- `services/monitor_service.py` — poll trace + log parsing
- `services/minio_service.py` — upload/download MinIO (buckets do Data Lake)
- `services/datalake_service.py` — registra resultados no catálogo do Data Lake (`POST /catalog`)
- `api/runs.py` — CRUD + cancel
- `api/references.py` — listar/registrar genomas
- Tratamento de erros: falha do Nextflow → status=failed + error_message
- Testes com dados sintéticos via API (POST /runs, GET /runs)

### Fase 4 — Qualidade (dias 10-11)

- Ruff + mypy passando
- Testes unitários (mock Nextflow)
- Teste de integração com FASTQ sintético (pipeline completo em chr22)
- `README.md` com setup, parâmetros, arquitetura
- Revisão final

---

## Convenções

- **Código**: identificadores em inglês
- **Documentação**: português brasileiro
- **QC obrigatório**: FastQC + MultiQC antes de qualquer análise (manual seção 3)
- **Versionamento**: registrar referência genômica e versão de cada ferramenta
- **Container**: imagens oficiais via `docker.config` do Nextflow
- **Imutabilidade**: outputs nunca sobrescritos; cada run gera diretório novo
- **Dados brutos**: lidos do Data Lake (MinIO bucket `raw`), nunca alterados
- **Resultados**: escritos em `processed/runs/{id}/` no Data Lake, VCF final em `curated/genomics/{run_id}/`
- **Catálogo**: resultados registrados via API do Data Lake para rastreabilidade
- **Reprodutibilidade**: seed aleatório fixo, parâmetros documentados em JSONB
