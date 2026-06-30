---
title: "Building a WGS Germline Variant Calling Pipeline with Nextflow, FastAPI, and GATK"
description: "How we built a production-grade genomics pipeline orchestrated by Nextflow, managed via FastAPI, and visualized with a TypeScript frontend — all containerized and integrated with a biomedical Data Lake"
tags: [nextflow, gatk, bioinformatics, genomics, fastapi, python, docker]
published: false
---

## The Problem

Whole-genome sequencing (WGS) has become a cornerstone of biomedical research. However, running a proper germline variant calling pipeline is far from trivial — especially when reproducibility and traceability are required.

A typical WGS analysis involves:

1. **Quality control** of raw FASTQ files
2. **Alignment** against a reference genome (BWA-MEM)
3. **Post-alignment processing** (MarkDuplicates, BQSR)
4. **Variant calling** (HaplotypeCaller)
5. **Joint genotyping and filtering** (VQSR)
6. **QC reports** (MultiQC)

Without pipeline orchestration, each step is often run manually or glued together with ad hoc scripts. Container management, intermediate file cleanup, retry logic, and result provenance become ad-hoc burdens that compromise reproducibility.

We built the **Genomics Pipeline** as Project 3 of the Integrated Bioinformatics Platform — a Nextflow-based pipeline paired with a FastAPI orchestration layer and a TypeScript dashboard, all running on shared Docker infrastructure.

---

## Architecture

```
                ┌──────────────┐
                │   Frontend   │  Vanilla TS + Vite + Plotly
                │  /genomics/  │
                └──────┬───────┘
                       │ HTTP
                ┌──────▼───────┐
                │  FastAPI API │  Runs management, references
                │  /api/genomics│  POST/GET runs, logs, cancel
                └──────┬───────┘
                       │ docker exec
                ┌──────▼───────┐
                │  Nextflow    │  BWA → GATK → Filter → MultiQC
                │  Worker      │  32G / 8 CPUs, Docker-in-Docker
                └──────────────┘
```

### Components

| Layer | Technology |
|-------|-----------|
| Pipeline engine | Nextflow DSL2 |
| Alignment | BWA-MEM (biocontainers/bwa) |
| Post-alignment | GATK4 MarkDuplicates + BQSR (broadinstitute/gatk) |
| Variant calling | GATK4 HaplotypeCaller |
| Filtering | GATK4 VQSR + VariantFiltration |
| QC | FastQC + MultiQC |
| Orchestration API | Python 3.12 / FastAPI (async) |
| Database | PostgreSQL 16 (via shared infra) |
| Object storage | MinIO (via shared infra) |
| Frontend | Vanilla TypeScript + Vite 6 + Plotly |
| Containerization | Docker |

---

## Pipeline Design (Nextflow)

The pipeline is written in Nextflow DSL2 with a modular structure:

```
pipeline/
├── main.nf              → Entry point
├── nextflow.config      → Global params + profiles
├── conf/
│   ├── base.config      → Resource allocations
│   ├── docker.config    → Container images
│   ├── grch38.config    → GRCh38 reference paths
│   └── test.config      → Test mode (chr22 only)
├── modules/
│   ├── fastqc.nf
│   ├── bwa_mem.nf
│   ├── markduplicates.nf
│   ├── baserecalibrator.nf
│   ├── haplotype_caller.nf
│   ├── genotype_gvcfs.nf
│   ├── variant_filtration.nf
│   └── multiqc.nf
└── subworkflows/
    ├── align.nf         → Stages 1-4
    ├── variant_call.nf  → Stages 5-6
    └── filter.nf        → Stage 7
```

The main workflow has 4 subworkflows executed in sequence:

```groovy
workflow {
    ALIGN(reads_ch, ref_bwa_idx, ref_fasta, ref_dict, ref_dbsnp, ref_indels)
    VARIANT_CALL(ALIGN.out.bqsr_bam, ref_fasta, ref_dict, ref_dbsnp)
    FILTER(VARIANT_CALL.out.raw_vcf, VARIANT_CALL.out.raw_vcf_tbi,
           ref_fasta, ref_dict, ref_dbsnp, ref_indels)
    MULTIQC(qc_files)
}
```

Key design decisions:

- **DSL2 modules** for each tool — swap or extend individual steps without touching the rest
- **Docker profiles** — all tools run via official containers (`broadinstitute/gatk`, `biocontainers/bwa`, etc.)
- **GRCh38 config** — reference indices (fasta, dict, BWA index, dbsnp, known indels) are pre-downloaded into a shared Docker volume
- **Test mode** — runs on chr22 only, for CI and development
- **Output cleanup** — on success, the `workDir` is automatically deleted to save disk

---

## API: Run Management

The FastAPI layer provides REST endpoints to dispatch and monitor pipeline runs:

### Create a run

```bash
curl -X POST http://localhost:8002/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sample NA12878",
    "samplesheet_path": "/workspace/samplesheet.csv",
    "reference": "grch38",
    "params": {"test_mode": true}
  }'
```

Returns a `PipelineRun` with status `pending`. The API then:

1. Checks concurrency limit (configurable via `MAX_CONCURRENT_RUNS`)
2. Writes a JSON params file with the run-specific configuration
3. Calls `docker exec` in the worker container to launch `nextflow run main.nf -params-file ...`
4. Stores the Nextflow PID and updates status to `queued`

### Monitor progress

```bash
# List runs (with optional status filter)
curl http://localhost:8002/runs?status=running

# Get run details
curl http://localhost:8002/runs/<uuid>

# Stream logs
curl http://localhost:8002/runs/<uuid>/logs

# Download MultiQC report
curl http://localhost:8002/runs/<uuid>/report

# Cancel a run
curl -X POST http://localhost:8002/runs/<uuid>/cancel
```

### Data model

```python
class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID]          # Primary key
    name: Mapped[str]              # Human-readable name
    status: Mapped[PipelineStatus] # pending → queued → running → completed/failed
    samplesheet_path: Mapped[str]  # CSV with sample,fastq_1,fastq_2
    reference: Mapped[str]         # grch38
    params: Mapped[dict | None]    # Arbitrary JSON overrides
    nextflow_run_id: Mapped[str | None]
    output_dir: Mapped[str | None]
    report_path: Mapped[str | None]
    datalake_dataset_id: Mapped[str | None]  # Link to Data Lake
```

### Concurrency limiter

To prevent resource exhaustion, the API rejects new runs when `max_concurrent_runs` is reached:

```python
if active_count >= settings.max_concurrent_runs:
    raise HTTPException(
        status_code=429,
        detail=f"Limit of {settings.max_concurrent_runs} concurrent runs reached"
    )
```

---

## Frontend: Runs Dashboard

The frontend (Vanilla TypeScript + Vite 6 + Plotly) is a single-page application with:

- **Runs list** — table with status badges, duration, reference
- **Run detail** — real-time log streaming, VCF download links
- **MultiQC report viewer** — embedded QC dashboard
- **Reference manager** — upload and list reference genomes

Built with a `VITE_API_URL` proxy and `BASE_PATH=/genomics/` for the nginx gateway.

```bash
cd frontend && npm run dev   # dev server
npm run build                # tsc + vite build
```

---

## Reproducibility Features

Several design decisions ensure reproducibility:

1. **Fixed seed** — `params.seed = 42` in `nextflow.config`, propagated to GATK's `--java-options`
2. **Immutable input data** — FASTQs come from the shared Data Lake (MinIO bucket `raw`, object-lock protected)
3. **Container pinning** — all tools use Docker images with explicit tags, no `latest`
4. **Result publication** — final VCF and MultiQC report are published to a run-specific output directory
5. **Data Lake integration** — after completion, results are registered in the Data Lake catalog with full provenance
6. **WorkDir cleanup** — intermediate files are deleted on success, keeping only the final artifacts

---

## Testing

The project has tests for both the API and the pipeline:

```bash
uv run pytest tests/ -v
```

Test coverage includes:
- API endpoint validation (pytest + httpx + respx)
- Database operations with SQLAlchemy async sessions
- Pipeline service dispatch and cancellation
- Reference genome CRUD operations

---

## Infrastructure

The pipeline runs on a dedicated **worker container** with Docker-in-Docker access:

```yaml
worker:
  build:
    context: .
    dockerfile: worker/Dockerfile  # nfcore/base + Java + Python
  volumes:
    - ref_data:/ref                # Shared reference genome volume
    - workspace:/workspace         # Run-specific files
    - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
  environment:
    NXF_OPTS: -Xms512m -Xmx4g
    JAVA_OPTS: -Xms512m -Xmx4g
  deploy:
    resources:
      limits:
        memory: 32G
        cpus: '8'
```

The `ref_data` volume is populated by a one-shot `ref-dl` service that downloads GRCh38 (fasta, BWA index, GATK known sites) and can be triggered with:

```bash
docker compose run --rm ref-dl
```

---

## API Endpoints Summary

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/runs` | Create and dispatch a new run |
| `GET` | `/runs` | List runs (optional `?status=` filter) |
| `GET` | `/runs/{id}` | Run details and status |
| `GET` | `/runs/{id}/logs` | Stream pipeline logs |
| `GET` | `/runs/{id}/report` | MultiQC report path |
| `POST` | `/runs/{id}/cancel` | Cancel a running pipeline |
| `POST` | `/references` | Register a reference genome |
| `GET` | `/references` | List available references |
| `GET` | `/health` | PostgreSQL + MinIO health check |

---

## Lessons Learned

1. **Nextflow + Docker is powerful but memory-intensive.** The worker needs at least 4G of RAM just for the JVM. We set `NXF_OPTS` and `JAVA_OPTS` conservatively.

2. **Docker-in-Docker is the simplest way to run Nextflow containers** from within a containerized environment. Mounting `/var/run/docker.sock` avoids complex socket forwarding.

3. **Reference genome download is the biggest friction point.** GRCh38 indices are ~60 GB. We made it a separate one-shot service (`ref-dl`) instead of bloating the worker image.

4. **Concurrency limits are essential** — a single `HaplotypeCaller` job can consume 8+ cores and 16G+ RAM. Without the API-level throttle, runs would OOM the host.

5. **VCF to Data Lake integration** — each completed run registers a `datalake_dataset_id` for downstream analysis (biomarker discovery, network analysis).

6. **Frontend matters for adoption.** Researchers don't want to SSH into a server to run `nextflow run`. The TypeScript dashboard with real-time logging makes the pipeline accessible.

---

## Repository

This is Project 3 of the Integrated Bioinformatics Platform monorepo (16 projects). The full code is at:

```
03-genomica/
├── app/              → FastAPI backend
├── pipeline/         → Nextflow pipeline (DSL2)
├── frontend/         → TypeScript SPA
├── worker/           → Dockerfile for Nextflow worker
├── scripts/          → Reference download utilities
└── docker-compose.yml
```

---

If you're building a genomics pipeline or need a production-grade variant calling workflow orchestrated via REST, I hope this project serves as a reference. The **Nextflow + FastAPI + Docker** stack is portable enough for a single lab server and scalable enough for a multi-node cluster.

Comments and questions are welcome!
