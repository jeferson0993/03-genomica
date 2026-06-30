#!/usr/bin/env Rscript

library(optparse)
library(VariantAnnotation)
library(GenomicRanges)
library(rtracklayer)
library(ggplot2)
library(dplyr)
library(tidyr)

option_list <- list(
  make_option("--vcf", type = "character", help = "Path to filtered VCF.gz"),
  make_option("--gtf", type = "character", default = NULL, help = "Path to GTF annotation"),
  make_option("--stats", type = "character", default = NULL, help = "Path to bcftools stats"),
  make_option("--outdir", type = "character", default = ".", help = "Output directory")
)
opt <- parse_args(OptionParser(option_list = option_list))

dir.create(opt$outdir, showWarnings = FALSE, recursive = TRUE)

vcf <- readVcf(opt$vcf, param = ScanVcfParam(
  info = c("QD", "FS", "MQ", "MQRankSum", "ReadPosRankSum", "SOR"),
  geno = c("GT", "DP", "GQ")
))

# ─── Basic variant stats ───
n_variants <- nrow(vcf)
n_snps <- sum(grepl("^SNP", info(vcf)$VCF))
n_indels <- sum(grepl("^INDEL", info(vcf)$VCF))
n_multiallelic <- sum(altSizes(vcf) > 1)

# Ti/Tv ratio
is_transition <- function(ref, alt) {
  ref <- as.character(ref)
  alt <- as.character(alt)
  (ref == "A" & alt == "G") | (ref == "G" & alt == "A") |
  (ref == "C" & alt == "T") | (ref == "T" & alt == "C")
}
ref_chars <- as.character(ref(vcf))
alt_chars <- as.character(unlist(alt(vcf)))
n_ti <- sum(is_transition(ref_chars, alt_chars), na.rm = TRUE)
n_tv <- n_variants - n_ti
titv_ratio <- round(n_ti / max(n_tv, 1), 2)

# ─── Depth distribution ───
dp <- unlist(geno(vcf)$DP)
dp_df <- data.frame(depth = dp[is.finite(dp)])

if (nrow(dp_df) > 0) {
  p_depth <- ggplot(dp_df, aes(x = depth)) +
    geom_histogram(bins = 50, fill = "#2563eb", alpha = 0.8) +
    scale_x_log10() +
    labs(title = "Depth Distribution", x = "Depth (log10)", y = "Count") +
    theme_minimal()
  ggsave(file.path(opt$outdir, "depth_dist.png"), p_depth, width = 8, height = 5)
}

# ─── QUAL distribution ───
qual_df <- data.frame(qual = fixed(vcf)$QUAL)
qual_df <- qual_df[is.finite(qual_df$qual), , drop = FALSE]

if (nrow(qual_df) > 0) {
  p_qual <- ggplot(qual_df, aes(x = qual)) +
    geom_histogram(bins = 50, fill = "#059669", alpha = 0.8) +
    scale_x_log10() +
    labs(title = "QUAL Score Distribution", x = "QUAL (log10)", y = "Count") +
    theme_minimal()
  ggsave(file.path(opt$outdir, "qual_dist.png"), p_qual, width = 8, height = 5)
}

# ─── Variants per chromosome ───
seqnames_df <- as.data.frame(table(as.character(seqnames(vcf))))
colnames(seqnames_df) <- c("chromosome", "count")
seqnames_df <- seqnames_df[order(seqnames_df$count, decreasing = TRUE), ]

if (nrow(seqnames_df) > 0) {
  p_chrom <- ggplot(head(seqnames_df, 24), aes(x = reorder(chromosome, -count), y = count)) +
    geom_bar(stat = "identity", fill = "#7c3aed", alpha = 0.8) +
    labs(title = "Variants per Chromosome", x = "Chromosome", y = "Count") +
    theme_minimal() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))
  ggsave(file.path(opt$outdir, "chrom_dist.png"), p_chrom, width = 10, height = 5)
}

# ─── Annotation overlap ───
annotation_summary <- data.frame(category = character(), count = integer(), stringsAsFactors = FALSE)
if (!is.null(opt$gtf) && file.exists(opt$gtf)) {
  gtf <- import(opt$gtf)
  genes <- gtf[gtf$type == "gene"]
  exons <- gtf[gtf$type == "exon"]

  ov_genes <- countOverlaps(vcf, genes)
  ov_exons <- countOverlaps(vcf, exons)

  annotation_summary <- rbind(
    annotation_summary,
    data.frame(category = "intergenic", count = sum(ov_genes == 0)),
    data.frame(category = "genic", count = sum(ov_genes > 0)),
    data.frame(category = "exonic", count = sum(ov_exons > 0))
  )
}

# ─── Write summary CSV ───
summary <- data.frame(
  metric = c(
    "total_variants", "snps", "indels", "multiallelic",
    "ti_tv_ratio", "median_qual", "mean_depth"
  ),
  value = c(
    n_variants, n_snps, n_indels, n_multiallelic,
    titv_ratio,
    round(median(qual_df$qual, na.rm = TRUE), 1),
    round(mean(dp, na.rm = TRUE), 1)
  )
)

write.csv(summary, file.path(opt$outdir, "vcf_summary.csv"), row.names = FALSE)

if (nrow(annotation_summary) > 0) {
  write.csv(annotation_summary, file.path(opt$outdir, "annotation_summary.csv"), row.names = FALSE)
}

writeLines(c(
  sprintf("Total variants: %d", n_variants),
  sprintf("SNPs: %d", n_snps),
  sprintf("INDELs: %d", n_indels),
  sprintf("Ti/Tv ratio: %s", titv_ratio),
  sprintf("Median QUAL: %.1f", median(qual_df$qual, na.rm = TRUE)),
  if (!is.null(opt$gtf)) sprintf("Genes overlapped: %d", sum(ov_genes > 0)) else "",
  sprintf("Output: %s", opt$outdir)
), file.path(opt$outdir, "vcf_summary.log"))

cat("vcf_summary.R completed successfully\n")
