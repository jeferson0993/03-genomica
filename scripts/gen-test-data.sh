#!/usr/bin/env bash
# gen-test-data.sh
# Generate synthetic FASTQ for testing (chr22, wgsim)
set -euo pipefail

OUTDIR="${OUTDIR:-/workspace/fastq}"
REF_FASTA="${REF_FASTA:-/ref/grch38/GRCh38.fa}"
N_READS="${N_READS:-10000}"
READ_LEN="${READ_LEN:-150}"
SEED="${SEED:-42}"

mkdir -p "$OUTDIR"

echo "=== Generating synthetic FASTQ ==="
wgsim \
    -N "$N_READS" \
    -1 "$READ_LEN" \
    -2 "$READ_LEN" \
    -r 0.001 \
    -R 0.0 \
    -X 0.0 \
    -S "$SEED" \
    "$REF_FASTA" \
    "${OUTDIR}/SAMPLE_01_R1.fastq" \
    "${OUTDIR}/SAMPLE_01_R2.fastq"

gzip -f "${OUTDIR}/SAMPLE_01_R1.fastq"
gzip -f "${OUTDIR}/SAMPLE_01_R2.fastq"

echo "=== Generating samplesheet ==="
cat > /workspace/samplesheet.csv << EOF
sample,fastq_1,fastq_2
SAMPLE_01,${OUTDIR}/SAMPLE_01_R1.fastq.gz,${OUTDIR}/SAMPLE_01_R2.fastq.gz
EOF

echo "=== Test data generated ==="
echo "Output: ${OUTDIR}/"
ls -lh "${OUTDIR}/"
echo "Samplesheet: /workspace/samplesheet.csv"
