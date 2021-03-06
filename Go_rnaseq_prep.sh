#!/bin/sh
#
SRCDATADIR="/home/data/GTEx/data"
DATADIR="data"
#
cwd=$(pwd)
#
if [ $(hostname -s) = "chiltepin" ]; then
	rnaseqfile="$SRCDATADIR/GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_tpm.gct.gz"
else
	rnaseqfile="$SRCDATADIR/GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_tpm_demo.gct.gz"
	# rnaseqfile="$SRCDATADIR/GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_tpm_demo_10pct.gct.gz"
fi
#
#
$cwd/python/gtex_rnaseq_prep_app.py \
	--i_tissue $DATADIR/tissue_order.csv \
	--i_subject $SRCDATADIR/GTEx_v7_Annotations_SubjectPhenotypesDS.txt \
	--i_sample $SRCDATADIR/GTEx_v7_Annotations_SampleAttributesDS.txt \
	--i_gene $DATADIR/gtex_gene_xref.tsv \
	--i_rnaseq $rnaseqfile \
	--o_sample $DATADIR/gtex_rnaseq_prep_sample.tsv \
	--o_median $DATADIR/gtex_rnaseq_prep_median.tsv \
	--o_profiles $DATADIR/gtex_rnaseq_prep_profiles.tsv \
	--o_tissue $DATADIR/gtex_rnaseq_prep_tissues.tsv \
	-v
#
#
