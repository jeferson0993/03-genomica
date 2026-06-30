// ─── R Report Module ───
// Input:  Filtered VCF, bcftools stats, GTF annotation
// Output: HTML report + summary CSV + plots

process R_REPORT {
    tag "r-report-${vcf_base}"

    publishDir "${params.outdir}/r-report", mode: 'copy'

    input:
    tuple val(vcf_base), path(vcf), path(vcf_tbi), path(stats), path(gtf)

    output:
    path("report.html"),         emit: report_html
    path("vcf_summary.csv"),     emit: summary_csv
    path("*.png"),               emit: plots,   optional: true
    path("vcf_summary.log"),     emit: logfile, optional: true

    script:
    def gtf_arg = gtf ? "--gtf ${gtf}" : ""
    def stats_arg = stats ? "--stats ${stats}" : ""
    """
    Rscript ${projectDir}/scripts/r/vcf_summary.R \
        --vcf ${vcf} \
        ${gtf_arg} \
        ${stats_arg} \
        --outdir .

    R -e "rmarkdown::render('${projectDir}/scripts/r/report.Rmd', \
        params = list(vcf = '${vcf}', stats = '${stats}'), \
        output_file = 'report.html')"
    """
}
