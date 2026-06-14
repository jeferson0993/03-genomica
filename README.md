# Genomics Pipeline

Pipeline de chamada de variantes germinativas WGS seguindo GATK Best Practices.
Orquestrado via Nextflow, com API FastAPI para disparo e monitoramento.

Entrada: FASTQ → Saída: VCF filtrado + MultiQC.

Integra-se à infraestrutura compartilhada do monorepo:
- **Data Lake** (Projeto 2): lê FASTQs do bucket `raw`, escreve resultados em `processed`/`curated` e registra saídas no catálogo.
- **PostgreSQL e MinIO**: serviços compartilhados no `docker-compose.yml` raiz.
- **Gateway Nginx**: rota `/api/genomics/`.

## Arquitetura

```
┌──────────┐     ┌──────────────────┐     ┌──────────────────┐
│  FastAPI │────▶│  Worker Nextflow │────▶│  PostgreSQL      │
│  (runs,  │     │  (container sep.)│     │  (shared, Proj2) │
│  monitor)│     │                  │     └──────────────────┘
└────┬─────┘     └────────┬─────────┘
     │                     │
     │            ┌────────▼───────────┐
     └───────────▶│  MinIO (Data Lake) │
                  │  raw/ → processed/ │
                  │  → curated/        │
                  └────────┬───────────┘
                           │
                  ┌────────▼───────────┐
                  │  Catálogo Data Lake│
                  │  (registro dataset)│
                  └────────────────────┘
```

## Pipeline (8 estágios)

```
samplesheet.csv (sample,fastq_1,fastq_2)
         │
         ▼
┌──────────────────────────┐
│  1. FastQC + MultiQC     │  ← obrigatório
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  2. BWA-MEM alignment    │  bwa mem → samtools sort/index
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  3. GATK MarkDuplicates  │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  4. BQSR                 │  BaseRecalibrator + ApplyBQSR
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  5. GATK HaplotypeCaller │  GVCF mode por amostra
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  6. CombineGVCFs +       │  joint genotyping (cohort)
│     GenotypeGVCFs        │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  7. VQSR / Hard Filter   │  VCF filtrado
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  8. VCF + Stats + Report │  bcftools stats + MultiQC
└──────────────────────────┘
```

## Estrutura do Projeto

```
03-genomica/
├── docker-compose.yml          # network externa bioinfo-platform-net
├── .env.example
├── pyproject.toml              # API Python
├── app/                        # FastAPI (achatado)
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/                 # PipelineRun, ReferenceGenome
│   ├── schemas/
│   ├── api/                    # runs, references
│   └── services/               # pipeline_service, minio_service,
│                               # datalake_service, monitor_service
├── pipeline/                   # Nextflow
│   ├── main.nf
│   ├── modules/                # fastqc, bwa_align, gatk_dedup, ...
│   ├── subworkflows/           # align, variant_call, filter
│   └── conf/                   # base.config, docker.config, grch38.config
├── scripts/
│   ├── download-ref-grch38.sh  # FASTA + índices BWA + known sites GATK
│   └── gen-test-data.sh        # FASTQ sintético (chr22, wgsim)
├── tests/
└── docs/
```

## Pré-requisitos

- Docker + Docker Compose
- Infraestrutura compartilhada rodando (`docker compose up -d` na raiz)
- Java 17+ (para Nextflow, dentro do container worker)

## Setup

```bash
# 1. Configure variáveis de ambiente
cp .env.example .env

# 2. Baixe a referência genômica GRCh38 + índices
docker compose run --rm ref-dl

# 3. Suba os serviços
docker compose up -d

# 4. Verifique o healthcheck (via gateway)
curl https://bioinfo.run.place/api/genomics/health
```

### Teste rápido (chr22)

```bash
# Gera FASTQ sintético do cromossomo 22
bash scripts/gen-test-data.sh

# Dispara pipeline de teste
curl -X POST https://bioinfo.run.place/api/genomics/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-chr22",
    "samplesheet": "raw://genomics/samplesheets/test-chr22.csv",
    "reference": "grch38"
  }'
```

## API — Endpoints

| Método | Caminho | Descrição |
|--------|---------|----------|
| `POST` | `/runs` | Disparar pipeline |
| `GET` | `/runs` | Listar execuções |
| `GET` | `/runs/{id}` | Detalhes + status |
| `GET` | `/runs/{id}/report` | Download MultiQC |
| `GET` | `/runs/{id}/logs` | Logs Nextflow |
| `POST` | `/runs/{id}/cancel` | Cancelar execução |
| `GET` | `/references` | Listar genomas |
| `POST` | `/references` | Registrar referência |
| `GET` | `/health` | Healthcheck |

## Modelo de Dados

### PipelineRun

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID (PK) | Identificador único |
| status | enum | pending → queued → running → completed / failed |
| samplesheet_path | str | Caminho no MinIO (bucket raw) |
| reference | str | Nome da referência |
| params | JSONB | Parâmetros do Nextflow |
| output_dir | str | Diretório de saída (`processed/runs/{id}/`) |
| report_path | str? | Caminho do MultiQC |
| nextflow_run_id | str | ID interno do Nextflow |
| started_at / completed_at | timestamptz | Timeline |
| datalake_dataset_id | str? | ID no catálogo do Data Lake |
| error_message | text? | Erro se falhou |

### ReferenceGenome

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID (PK) | Identificador único |
| name | str | grch38, grch37 |
| species | str | Homo sapiens |
| fasta_path | str | Caminho no volume (`/ref/{name}/`) |
| bwa_index_prefix | str | Prefixo índices BWA |
| dbsnp_path | str | dbSNP para BQSR |
| known_indels_path | str | Mills + 1000G indels |
| gtf_path | str | GTF de genes |
| minio_prefix | str | Prefixo no MinIO (`refs/grch38/`) |

## Convenções

- FastQC + MultiQC obrigatório antes de qualquer análise
- Imagens oficiais via `docker.config` do Nextflow (Broad GATK, biocontainers)
- Outputs nunca sobrescritos — cada run gera diretório novo
- Dados brutos lidos do Data Lake (MinIO bucket `raw`), nunca alterados
- Resultados em `processed/runs/{id}/`, VCF final em `curated/genomics/{run_id}/`
- Resultados registrados no catálogo do Data Lake (rastreabilidade)
- Seed aleatório fixo (`42`) para reprodutibilidade
- Código em inglês, documentação em português brasileiro

## Testes

```bash
uv run pytest tests/ -v
```

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Workflow | Nextflow + módulos próprios |
| Alinhamento | BWA-MEM + samtools |
| Pós-alinhamento | GATK4 MarkDuplicates, BQSR |
| Chamada variantes | GATK4 HaplotypeCaller (GVCF) |
| Joint genotyping | GATK4 CombineGVCFs + GenotypeGVCFs |
| Filtragem | GATK4 VQSR / VariantFiltration |
| QC | FastQC, MultiQC |
| API | Python 3.12+ / FastAPI |
| ORM | SQLAlchemy 2.0 async |
| Storage | MinIO (Data Lake, Projeto 2) |
| Database | PostgreSQL 16 (compartilhado) |
| Container | Docker + imagens oficiais |
| Lint / type | ruff, mypy |
# 03-genomica
