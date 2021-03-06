#!/usr/bin/env python3
"""gtex_rnaseq_sabv.py

GTEx RNAseq Sex As Biological Variable (SABV) Analysis

Command-line version; see also Jupyter notebook gtex_rnaseq_sabv.ipynb

 - Author: Jeremy Yang
 - Based on R code by Oleg Ursu.
 - Required: Python3, Pandas 0.22+

Workflow (analysis):
 - READ: median TPMs, 1-row/gene+tissue+sex (from gtex_rnaseq_prep_app.py).
 - READ: sample TPMs, 1-row/gene+sample (from gtex_rnaseq_prep_app.py).
 - READ: gene IDs and names mapping file.

 - COMPUTE: TAU, TAU_F, TAU_M, tissue specificity index (Yanai et al., 2004)., by gene and gene+sex.
 - COMPUTE: Log fold-change, log of ratio (TPM_F/TPM_M).

 - COMPUTE: Wilcoxon rank sum test, F vs M, each gene+tissue.

 - OUTPUT: SABV metrics, TAU Log fold-change, 1-row/gene+tissue+sex.
 - OUTPUT: Wilcoxon rank Sum stats and pvals, 1-row/gene+tissue.

"""
#############################################################################
import sys,os,io,re,time,argparse
import numpy,scipy,scipy.stats
import pandas

#############################################################################
def ReadMedianTPMs(ifile, verbose):
  fin = open(ifile)
  print('=== GTEx Median-TPMs datafile: %s'%fin.name, file=sys.stdout)
  tpms = pandas.read_csv(fin, sep='\t')
  print("Median-TPMs dataset nrows: %d ; ncols: %d:"%(tpms.shape[0],tpms.shape[1]), file=sys.stdout)
  return tpms

#############################################################################
def ReadSampleTPMs(ifile, verbose):
  fin = open(ifile)
  print('=== GTEx Sample-TPMs datafile: %s'%fin.name, file=sys.stdout)
  tpms = pandas.read_csv(fin, sep='\t')
  print("Sample-TPMs dataset nrows: %d ; ncols: %d:"%(tpms.shape[0],tpms.shape[1]), file=sys.stdout)
  return tpms

#############################################################################
### Format: one line per tissue name, in preferred order.
#############################################################################
def ReadTissues(ifile, verbose):
  fin = open(ifile)
  print('=== GTEx Tissues datafile: %s'%fin.name, file=sys.stdout)
  tissues = pandas.read_csv(fin, sep=';', index_col=False, header=None, names=['name'])
  tissues = tissues.name.str.strip()
  if verbose: print("n_tissues: %d:"%(tissues.size), file=sys.stdout)
  if verbose: print("DEBUG: tissues:\n%s"%(str(tissues)), file=sys.stderr)
  return tissues

#############################################################################
def DescribeDf(df, verbose):
  buff = io.StringIO()
  df.info(buf=buff,verbose=bool(verbose>0),null_counts=bool(verbose>0))
  print(re.sub(re.compile('^', re.M), '\t', buff.getvalue()), file=sys.stdout)

#############################################################################
### Read gene symbols.
#############################################################################
def ReadGenes(ifile, verbose):
  print("=== ReadGenes:", file=sys.stdout)
  fin = open(ifile)
  print('Biomart ENSG2NCBI genes datafile: %s'%fin.name, file=sys.stdout)
  genes = pandas.read_csv(fin, sep='\t', usecols=[1,2,3], na_values=[''], dtype={2:str})
  print("Genes dataset nrows: %d ; ncols: %d:"%(genes.shape[0],genes.shape[1]), file=sys.stdout)
  genes.columns = ['ENSG','NCBI','HGNC']
  genes.dropna(inplace=True)
  return genes

#############################################################################
def TAUs(tpms, verbose):
  taus = tpms.groupby(['ENSG']).TPM.agg(TAU)
  taus = pandas.DataFrame(taus).rename(columns={'TPM':'TAU'})
  taus = taus.reset_index(drop=False)
  return taus

#############################################################################
def TAUs_SABV(tpms, verbose):
  taus_sex = tpms.groupby(['ENSG','SEX']).TPM.agg(TAU)
  taus_sex = pandas.DataFrame(taus_sex).rename(columns={'TPM':'TAU_BYSEX'})
  taus_sex = taus_sex.reset_index(drop=False)
  return taus_sex

#############################################################################
#def SABV_TAU(rnaseq, verbose):
#  print("=== SABV_TAU:", file=sys.stdout)
#  print("DEBUG: SABV_TAU IN: nrows = %d, cols: %s"%(rnaseq.shape[0],str(rnaseq.columns.tolist())), file=sys.stderr)
#
#  ### Compute TAU by gene:
#  rnaseq_nosex_tau = rnaseq.groupby(['ENSG']).TPM.agg(TAU)
#  rnaseq_nosex_tau = pandas.DataFrame(rnaseq_nosex_tau).rename(columns={'TPM':'TAU'})
#  rnaseq_nosex_tau['SEX'] = 'ALL'
#
#  ### Compute TAU by gene+sex:
#  rnaseq_tau_f = rnaseq.loc[rnaseq['SEX']=='female'].groupby(['ENSG']).TPM.agg(TAU)
#  rnaseq_tau_f = pandas.DataFrame(rnaseq_tau_f).rename(columns={'TPM':'TAU'})
#  rnaseq_tau_f = rnaseq_tau_f.reset_index(drop=False)
#  rnaseq_tau_f['SEX'] = 'female'
#  print("DEBUG: rnaseq_tau_f.columns = %s"%(str(rnaseq_tau_f.columns)), file=sys.stderr)
#
#  rnaseq_tau_m = rnaseq.loc[rnaseq['SEX']=='male'].groupby(['ENSG']).TPM.agg(TAU)
#  rnaseq_tau_m = pandas.DataFrame(rnaseq_tau_m).rename(columns={'TPM':'TAU'})
#  rnaseq_tau_m = rnaseq_tau_m.reset_index(drop=False)
#  rnaseq_tau_m['SEX'] = 'male'
#  print("DEBUG: rnaseq_tau_m.columns = %s"%(str(rnaseq_tau_m.columns)), file=sys.stderr)
#
#  rnaseq_tau = pandas.concat([rnaseq_nosex_tau, rnaseq_tau_f, rnaseq_tau_m])
#
#  print("DEBUG: SABV_TAU OUT: nrows = %d, cols: %s"%(rnaseq_tau.shape[0],str(rnaseq_tau.columns.tolist())), file=sys.stderr)
#  return rnaseq_tau


#############################################################################
#def SABV_GTRanks(rnaseq, verbose):
#  print("=== SABV_GTRanks:", file=sys.stdout)
#  print("DEBUG: SABV_GTRanks IN: nrows = %d, cols: %s"%(rnaseq.shape[0],str(rnaseq.columns.tolist())), file=sys.stderr)
#  print("=== Assign gene-tissue rank (quantile) among tissues (F):", file=sys.stdout)
#  t0 = time.time()
#  rnaseq_ranks_f = GTRanks(rnaseq[['ENSG','SMTSD','TPM_F']].copy(), 'TPM_F')
#  print("GTRanks (F) elapsed: %ds"%(time.time()-t0), file=sys.stderr)
#  rnaseq_ranks_f['LEVEL_F'] = rnaseq_ranks_f.TPM_F_RANK.apply(lambda x: 'Not detected' if x==0 else 'Low' if x<.25 else 'Medium' if x<.75 else 'High')
#  print("=== Assign gene-tissue rank (quantile) among tissues (M):", file=sys.stdout)
#  t0 = time.time()
#  rnaseq_ranks_m = GTRanks(rnaseq[['ENSG','SMTSD','TPM_M']].copy(), 'TPM_M')
#  print("GTRanks (M) Elapsed: %ds"%(time.time()-t0), file=sys.stderr)
#  rnaseq_ranks_m['LEVEL_M'] = rnaseq_ranks_m.TPM_M_RANK.apply(lambda x: 'Not detected' if x==0 else 'Low' if x<.25 else 'Medium' if x<.75 else 'High')
#  rnaseq = pandas.merge(rnaseq_ranks_f, rnaseq_ranks_m, on=['ENSG','SMTSD'], how='inner')
#  print("DEBUG: SABV_GTRanks OUT: nrows = %d, cols: %s"%(rnaseq.shape[0],str(rnaseq.columns.tolist())), file=sys.stderr)
#  return rnaseq

#############################################################################
#def WilcoxonSignedRank(rnaseq, rnaseq_ranks, verbose):
#  print("=== WilcoxonSignedRank:", file=sys.stdout)
#  print("DEBUG: WilcoxonSignedRank IN: nrows = %d, cols: %s"%(rnaseq.shape[0],str(rnaseq.columns.tolist())), file=sys.stderr)
#  ### For each gene, compute sex difference via Wilcoxon signed-rank test,
#  ### with Wilcox treatment, discarding all zero-differences.
#  results = pandas.DataFrame({'ENSG':rnaseq.ENSG.drop_duplicates().sort_values(), 'WilcoxonSignedRank_stat':None, 'WilcoxonSignedRank_pval':None}).reset_index(drop=True)
#  for i in range(results.shape[0]):
#    tpm_f_this = rnaseq_ranks.TPM_F_RANK[rnaseq_ranks.ENSG==results.ENSG[i]]
#    tpm_m_this = rnaseq_ranks.TPM_M_RANK[rnaseq_ranks.ENSG==results.ENSG[i]]
#    ### What is best minimum size??
#    if tpm_f_this[tpm_f_this>0].size<8 or tpm_m_this[tpm_m_this>0].size<8:
#      continue
#    try:
#      stat, pval = scipy.stats.wilcoxon(x=tpm_f_this, y=tpm_m_this, zero_method='wilcox')
#    except Exception as e:
#      print("Exception [i=%d; ensg=%s]: %s"%(i+1,results.ENSG[i],str(e)), file=sys.stderr)
#      print("DEBUG: tpm_f_this=%s; tpm_m_this=%s"%(str(tpm_f_this),str(tpm_m_this)), file=sys.stderr)
#      continue
#    results.WilcoxonSignedRank_stat.iloc[i] = stat
#    results.WilcoxonSignedRank_pval.iloc[i] = pval 
#  rnaseq = pandas.merge(rnaseq, results, on=['ENSG'])
#  print("DEBUG: WilcoxonSignedRank OUT: nrows = %d, cols: %s"%(rnaseq.shape[0],str(rnaseq.columns.tolist())), file=sys.stderr)
#  return rnaseq

#############################################################################
def WilcoxonRankSum(tpms, verbose):
  wrs = tpms[['SMTSD', 'ENSG']].copy().drop_duplicates().sort_values(by=['SMTSD', 'ENSG'])
  wrs.reset_index(drop=True, inplace=True)
  wrs['stat'] = pandas.Series(dtype=float)
  wrs['pval'] = pandas.Series(dtype=float)

  for smtsd in wrs.SMTSD.unique():
    tpms_this = tpms[tpms.SMTSD==smtsd]
    for ensg in tpms_this.ENSG.unique():
      vals_f = tpms_this.TPM[(tpms_this.ENSG==ensg) & (tpms_this.SEX=="female")]
      vals_m = tpms_this.TPM[(tpms_this.ENSG==ensg) &(tpms_this.SEX=="male")]
      stat, pval = scipy.stats.ranksums(x=vals_f, y=vals_m)
      #stat, pval = scipy.stats.mannwhitneyu(x=vals_f.rank(), y=vals_m.rank(), use_continuity=True, alternative="two-sided")
      wrs.stat.loc[(wrs.SMTSD==smtsd) & (wrs.ENSG==ensg)] = stat
      wrs.pval.loc[(wrs.SMTSD==smtsd) & (wrs.ENSG==ensg)] = pval
  return wrs

#############################################################################
def SABV_LogFoldChange(tpms, verbose):
  lfc = pandas.merge(
	tpms[tpms.SEX=='female'][['ENSG', 'SMTSD','TPM']].rename(columns={'TPM':'TPM_F'}),
	tpms[tpms.SEX=='male'][['ENSG', 'SMTSD','TPM']].rename(columns={'TPM':'TPM_M'}),
	on=['ENSG', 'SMTSD'], how='inner')
  lfc['log2foldchange'] = ((lfc.TPM_F+1) / (lfc.TPM_M+1)).apply(numpy.log2)
  #lfc['log2foldchange_abs'] = lfc.log2foldchange.apply(numpy.abs)
  return lfc

#############################################################################
### Compute tissue specificity index (Yanai et al., 2004).
### $ \tau = \frac{\sum_{i=0}^N (1 - x_i)}{N - 1} $
### * N = number of tissues
### * x = expression profile component normalized by the maximal component value
###
### Validate with example vector from paper.  Should be 0.95.
### print('%.2f'%TAU([0,8,0,0,0,2,0,2,0,0,0,0]), file=sys.stdout)
#############################################################################
def TAU(X):
  N = len(X)
  xmax = max(X)
  if xmax==0: return(0.0)
  tau = 0.0
  for x in X:
    tau += (1 - x/xmax)
  tau /= (N - 1)
  return(tau)

#############################################################################
### Assign gene-tissue rank (quantile) among tissues.
### Ranks, for given gene, tissue expression from gene-tissue TPMs.
#############################################################################
#def GTRanks(rnaseq, tpm_col):
#  tpm_rank = pandas.Series(dtype="float", index=range(rnaseq.shape[0]))
#  for i in rnaseq.index:
#    ensg = rnaseq.ENSG[i]
#    val_this = rnaseq[tpm_col][i]
#    vals_ensg = rnaseq[tpm_col][rnaseq.ENSG==ensg]
#    vals_ensg = vals_ensg.sort_values().reset_index(drop=True)
#    j = vals_ensg[vals_ensg == val_this].index[0]
#    tpm_rank.iloc[i] = j/vals_ensg.size 
#  rnaseq[tpm_col+'_RANK'] = tpm_rank
#  return(rnaseq)

#############################################################################
if __name__=='__main__':
  parser = argparse.ArgumentParser(description='GTEx RNAseq Exfiles/SABV preprocessor')
  parser.add_argument("--i",dest="ifile",help="input median TPM, 1-row/gene+tissue+sex (TSV)")
  parser.add_argument("--i_sample",dest="ifile_sample",help="input sample TPM, 1-row/gene+sample (TSV)")
  parser.add_argument("--i_tissue",dest="ifile_tissue",help="input (ordered) tissue file")
  parser.add_argument("--o",dest="ofile",help="output (TSV)")
  parser.add_argument("--decimals",type=int,default=3,help="output decimal places")
  parser.add_argument("-v","--verbose",action="count")
  args = parser.parse_args()

  PROG=os.path.basename(sys.argv[0])
  t0 = time.time()

  if args.verbose:
    print('Python: %s\nPandas: %s'%(sys.version,pandas.__version__), file=sys.stdout)

  if args.ifile_tissue:
    tissues = ReadTissues(args.ifile_tissue, args.verbose)
  else:
    tissues = None

  if not args.ifile:
    parser.error('Input TPM file required.')

  tpms = ReadMedianTPMs(args.ifile, args.verbose)

  if args.verbose:
    #DescribeTPMs(tpms)
    print("SABV TPM median unique counts: genes: %d"%(tpms.ENSG.nunique()), file=sys.stdout)

  print('=== SABV analysis:', file=sys.stdout)
  print('=== Compute TAU (tissue specificity, Yanai et al., 2004):', file=sys.stdout)
  taus = TAUs(tpms, args.verbose)
  taus_sex = TAUs_SABV(tpms, args.verbose)
  tpms = pandas.merge(tpms, taus, on=['ENSG'], how='left')
  tpms = pandas.merge(tpms, taus_sex, on=['ENSG','SEX'], how='left')

  print("=== Compute Log fold-change, log of ratio (F/M):", file=sys.stdout)
  ### (One row per gene+tissue, cols for M and F TPM.)
  lfc = SABV_LogFoldChange(tpms, args.verbose)
  tpms = pandas.merge(tpms, lfc, on=['ENSG','SMTSD'], how='left')

  if not args.ifile_sample:
    print("NOTE: sample TPM input needed for Wilcoxon rank-sum test (skipping).", file=sys.stdout)
  else:
    sampletpms = ReadSampleTPMs(args.ifile_sample, args.verbose)
    wrs = WilcoxonRankSum(sampletpms, args.verbose)
    wrs = wrs.rename(columns={'stat':'WilcoxonRankSum_stat', 'pval':'WilcoxonRankSum_pval'})
    tpms = pandas.merge(tpms, wrs, on=['ENSG','SMTSD'], how='left')

  if args.ofile:
    print("=== Output SABV file: %s"%args.ofile, file=sys.stdout)
    tpms.round(args.decimals).to_csv(args.ofile, sep='\t', index=False)

  print("%s Elapsed: %ds"%(PROG,(time.time()-t0)), file=sys.stderr)
