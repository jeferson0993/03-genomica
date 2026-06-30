#!/usr/bin/env bash
# download-ref-grch38.sh
# Download GRCh38 reference genome + BWA indexes + GATK known sites
# Usage: bash download-ref-grch38.sh [--chr22-only]
set -euo pipefail

REF_DIR="${REF_DIR:-/ref/grch38}"
CHR22_ONLY=false

if [[ "${1:-}" == "--chr22-only" ]]; then
    CHR22_ONLY=true
    echo "Downloading only chr22 for testing"
fi

mkdir -p "${REF_DIR}/bwa" "${REF_DIR}/known-sites" "${REF_DIR}/annotation"

echo "=== Downloading GRCh38 FASTA ==="
if [ "$CHR22_ONLY" = true ]; then
    wget -q -O "${REF_DIR}/GRCh38.fa.gz" \
        "https://hgdownload.cse.ucsc.edu/goldenPath/hg38/chromosomes/chr22.fa.gz"
else
    wget -q -O "${REF_DIR}/GRCh38.fa.gz" \
        "ftp://ftp.ensembl.org/pub/release-113/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz"
fi

gunzip -f "${REF_DIR}/GRCh38.fa.gz"

# Create .dict file
samtools dict "${REF_DIR}/GRCh38.fa" -o "${REF_DIR}/GRCh38.dict" 2>/dev/null || \
    echo "Warning: samtools dict failed, create manually"

echo "=== Indexing with BWA ==="
bwa index -p "${REF_DIR}/bwa/hg38" "${REF_DIR}/GRCh38.fa"

echo "=== Indexing with samtools FASTA ==="
samtools faidx "${REF_DIR}/GRCh38.fa"

if [ "$CHR22_ONLY" = false ]; then
    echo "=== Downloading known sites ==="
    # dbSNP
    wget -q -O "${REF_DIR}/known-sites/dbsnp_151.vcf.gz" \
        "https://ftp.ncbi.nih.gov/snp/organisms/human_9606_b151_GRCh38p7/VCF/00-common_all.vcf.gz"
    wget -q -O "${REF_DIR}/known-sites/dbsnp_151.vcf.gz.tbi" \
        "https://ftp.ncbi.nih.gov/snp/organisms/human_9606_b151_GRCh38p7/VCF/00-common_all.vcf.gz.tbi"

    # Mills & 1000G gold standard indels
    wget -q -O "${REF_DIR}/known-sites/Mills_and_1000G_gold_standard.indels.hg38.vcf.gz" \
        "https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Mills_and_1000G_gold_standard.indels.hg38.vcf.gz"
    wget -q -O "${REF_DIR}/known-sites/Mills_and_1000G_gold_standard.indels.hg38.vcf.gz.tbi" \
        "https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Mills_and_1000G_gold_standard.indels.hg38.vcf.gz.tbi"

    # 1000G phase1 SNPs
    wget -q -O "${REF_DIR}/known-sites/1000G_phase1.snps.high_confidence.hg38.vcf.gz" \
        "https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/1000G_phase1.snps.high_confidence.hg38.vcf.gz"
    wget -q -O "${REF_DIR}/known-sites/1000G_phase1.snps.high_confidence.hg38.vcf.gz.tbi" \
        "https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/1000G_phase1.snps.high_confidence.hg38.vcf.gz.tbi"

    echo "=== Downloading GTF annotation ==="
    wget -q -O "${REF_DIR}/annotation/gencode.v44.annotation.gtf.gz" \
        "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/gencode.v44.annotation.gtf.gz"
    gunzip -f "${REF_DIR}/annotation/gencode.v44.annotation.gtf.gz"
fi

echo "=== Download complete ==="
echo "Reference: ${REF_DIR}"
ls -lh "${REF_DIR}/"
