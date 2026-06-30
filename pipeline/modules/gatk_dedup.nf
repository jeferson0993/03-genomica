// ─── GATK MarkDuplicates Module ───
// Input:  Sorted BAM
// Output: Dedup BAM + metrics

process GATK_MARKDUPLICATES {
    tag "${sample}"

    input:
    tuple val(sample), path(bam), path(bai)

    output:
    tuple val(sample), path("${sample}.dedup.bam"),  emit: bam
    path("${sample}.dedup.bam.bai"),                  emit: bai
    path("${sample}.dedup.metrics"),                  emit: metrics

    script:
    """
    gatk MarkDuplicates \
        --INPUT ${bam} \
        --OUTPUT ${sample}.dedup.bam \
        --METRICS_FILE ${sample}.dedup.metrics \
        --CREATE_INDEX true \
        --VALIDATION_STRINGENCY SILENT \
        --OPTICAL_DUPLICATE_PIXEL_DISTANCE 2500

    mv ${sample}.dedup.bai ${sample}.dedup.bam.bai
    """
}
