#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

// ─── Included configurations ───
includeConfig "${projectDir}/conf/base.config"
includeConfig "${projectDir}/conf/docker.config"

// ─── Parameters ───
params.samplesheet = "assets/samplesheet.csv"
params.reference = "grch38"
params.outdir = "./results"
params.run_id = "local"

// Modo teste (chr22, baixa cobertura)
params.test_mode = false

// Formato de saída: false = BAM (default), true = CRAM (2x compressão)
params.cram = false

// ─── Profile-selective configs ───
if (params.test_mode) {
    includeConfig "${projectDir}/conf/test.config"
}

if (params.reference == "grch38") {
    includeConfig "${projectDir}/conf/grch38.config"
}

// ─── Included subworkflows ───
include { ALIGN } from './subworkflows/align'
include { VARIANT_CALL } from './subworkflows/variant_call'
include { FILTER } from './subworkflows/filter'
include { MULTIQC } from './modules/multiqc'
include { R_REPORT } from './modules/r_report'

// ─── Read samplesheet ───
Channel.fromPath(params.samplesheet)
    | splitCsv(header: true, sep: ",")
    | map { row ->
        [row.sample, file(row.fastq_1, checkIfExists: true), file(row.fastq_2, checkIfExists: true)]
    }
    | set { reads_ch }

// ─── Reference files (from config) ───
ref_fasta   = file(params.ref_fasta)
ref_dict    = file(params.ref_dict)
ref_bwa_idx = file(params.ref_bwa_index)
ref_dbsnp   = file(params.ref_dbsnp)
ref_indels  = file(params.ref_known_indels)
ref_gtf     = file(params.ref_gtf)

// ─── Pipeline workflow ───
workflow {
    // Stage 1-4: Alignment + BQSR
    ALIGN(
        reads_ch,
        ref_bwa_idx,
        ref_fasta, ref_dict, ref_dbsnp, ref_indels
    )

    // Stage 5-6: Variant calling
    VARIANT_CALL(
        ALIGN.out.bqsr_bam,
        ref_fasta, ref_dict, ref_dbsnp
    )

    // Stage 7: Filtering
    FILTER(
        VARIANT_CALL.out.raw_vcf,
        VARIANT_CALL.out.raw_vcf_tbi,
        ref_fasta, ref_dict, ref_dbsnp, ref_indels
    )

    // Stage 8: MultiQC report
    qc_files = ALIGN.out.fastqc_html.mix(
        ALIGN.out.dedup_metrics,
        FILTER.out.vcf_stats
    ).collect()

    MULTIQC(qc_files)

    // Stage 9: R report (VCF summary + annotation + HTML)
    r_report_ch = FILTER.out.filtered_vcf
        .combine(FILTER.out.vcf_stats)
        .map { vcf, stats ->
            def base = vcf.name - ~/\.(vcf\.gz|vcf)$/
            [base, vcf, file("${vcf}.tbi"), stats, ref_gtf]
        }

    R_REPORT(r_report_ch)

    // ─── Outputs ───
    FILTER.out.filtered_vcf | view { "Filtered VCF: ${it}" }
    MULTIQC.out.report | view { "MultiQC report: ${it}" }
    R_REPORT.out.report_html | view { "R report: ${it}" }
}

// ─── Output publication + cleanup ───
workflow.onComplete {
    def outdir = file(params.outdir, type: 'dir')

    FILTER.out.filtered_vcf | each { vcf ->
        copyFile(vcf, "${outdir}/cohort.filtered.vcf.gz")
        copyFile(vcf + ".tbi", "${outdir}/cohort.filtered.vcf.gz.tbi")
    }

    MULTIQC.out.report | each { report ->
        copyFile(report, "${outdir}/multiqc_report.html")
    }

    BCFTOOLS_STATS.out.stats | each { stats ->
        copyFile(stats, "${outdir}/cohort.vcf.stats")
    }

    R_REPORT.out.report_html | each { report ->
        copyFile(report, "${outdir}/r_report.html")
    }

    // Cleanup workDir on success
    if (workflow.success) {
        file(workflow.workDir).deleteDir()
        log.info "Work directory cleaned: ${workflow.workDir}"
    }
}
