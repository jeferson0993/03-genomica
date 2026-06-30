// ─── GATK VQSR Module ───
// Input:  Raw VCF + known sites for training
// Output: Filtered VCF

process GATK_VQSR {
    tag "cohort"

    input:
    path raw_vcf
    path raw_vcf_tbi
    path fasta
    path dict
    path dbsnp
    path known_indels

    output:
    path("cohort.filtered.vcf.gz"), emit: vcf
    path("cohort.filtered.vcf.gz.tbi"), emit: tbi

    script:
    """
    gatk VariantRecalibrator \
        --input ${raw_vcf} \
        --output cohort.recal \
        --tranches-file cohort.tranches \
        --reference ${fasta} \
        --resource:dbsnp,known=false,training=true,truth=true,prior=15.0 ${dbsnp} \
        --resource:mills,known=false,training=true,truth=true,prior=12.0 ${known_indels} \
        --an QD --an MQ --an MQRankSum --an ReadPosRankSum --an FS --an SOR \
        --mode SNP

    gatk ApplyVQSR \
        --input ${raw_vcf} \
        --output cohort.filtered.vcf.gz \
        --reference ${fasta} \
        --recal-file cohort.recal \
        --tranches-file cohort.tranches \
        --mode SNP \
        --truth-sensitivity-filter-level 99.7
    """
}
