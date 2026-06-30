// ─── Filter Subworkflow ───
// Runs: VQSR + bcftools stats + MultiQC

include { GATK_VQSR } from '../modules/gatk_vqsr'
include { BCFTOOLS_STATS } from '../modules/bcftools_stats'

workflow FILTER {
    take:
    raw_vcf         // path: raw VCF
    raw_vcf_tbi     // path: raw VCF index
    ref_fasta       // path: reference FASTA
    ref_dict        // path: reference dict
    ref_dbsnp       // path: dbSNP
    ref_known_indels // path: known indels

    main:
    GATK_VQSR(raw_vcf, raw_vcf_tbi, ref_fasta, ref_dict, ref_dbsnp, ref_known_indels)
    BCFTOOLS_STATS(GATK_VQSR.out.vcf)

    emit:
    filtered_vcf = GATK_VQSR.out.vcf
    vcf_stats = BCFTOOLS_STATS.out.stats
}
