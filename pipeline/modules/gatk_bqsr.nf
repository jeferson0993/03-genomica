// ─── GATK BQSR Module ───
// Input:  Dedup BAM + known sites VCFs
// Output: Recalibrated BAM + recalibration table

process GATK_BQSR {
    tag "${sample}"

    input:
    tuple val(sample), path(bam), path(bai)
    path fasta
    path dict
    path dbsnp
    path known_indels

    output:
    tuple val(sample), path("${sample}.bqsr.bam"),  emit: bam
    path("${sample}.bqsr.bam.bai"),                  emit: bai
    path("${sample}.recal.table"),                   emit: table

    script:
    """
    gatk BaseRecalibrator \
        --input ${bam} \
        --output ${sample}.recal.table \
        --reference ${fasta} \
        --known-sites ${dbsnp} \
        --known-sites ${known_indels}

    gatk ApplyBQSR \
        --input ${bam} \
        --output ${sample}.bqsr.bam \
        --reference ${fasta} \
        --bqsr-recal-file ${sample}.recal.table

    samtools index ${sample}.bqsr.bam
    mv ${sample}.bqsr.bam.bai ${sample}.bqsr.bam.bai
    """
}
