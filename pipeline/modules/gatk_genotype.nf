// ─── GATK GenotypeGVCFs Module ───
// Input:  Combined GVCF
// Output: Raw VCF with genotypes

process GATK_GENOTYPE {
    tag "cohort"

    input:
    path combined_gvcf
    path combined_gvcf_tbi
    path fasta
    path dict
    path dbsnp

    output:
    path("cohort.raw.vcf.gz"),        emit: vcf
    path("cohort.raw.vcf.gz.tbi"),    emit: tbi

    script:
    """
    gatk GenotypeGVCFs \
        --reference ${fasta} \
        --variant ${combined_gvcf} \
        --dbsnp ${dbsnp} \
        --output cohort.raw.vcf.gz
    """
}
