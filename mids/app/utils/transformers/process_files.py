import sys
from pathlib import Path

# Make the repo-root globals.py importable however the script is run (mids/app/utils/transformers -> repo root)
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from globals import get_project_root
import pandas as pd
import shutil
from datetime import date
import os

# Process Source Files
# This script runs a sequence of batch processes enclosed in three functions that were previously separate files.
# The sequence is initiated by running the file, then each function is chained in the following sequence:
# process_source_mappings() -> transform_levels() -> transform_information_elements()
# Last Modified: 2026-01-08

# Globals
root = get_project_root()
currentPath = Path().absolute()
projectPath = currentPath.parent.parent.parent

today = date.today()
ts = today.strftime("%Y%m%d")
namespace = 'mids'

'''
	Process MIDS Mappings 
'''
def process_source_mappings():
	# Mapping source files are stored as *.tsv (tab-delimited). StaDocGen parses CSV when generating documentation. This script converts the source tsv to source csv.

	# SOURCE FILES
	# dwc_tsv = str(root) + '/mids/app/data/source/sssom_dwc_biology_mappings.sssom.tsv'
	dwc_biology_tsv = str(root) + '/mids/app/data/source/mids_dwc-a_biology_1.sssom.tsv'
	dwc_geology_tsv = str(root) + '/mids/app/data/source/mids_dwc-a_geology_1.sssom.tsv'
	dwc_paleo_tsv = str(root) + '/mids/app/data/source/mids_dwc-a_paleontology_1.sssom.tsv'
	abcd_biology_tsv = str(root) + '/mids/app/data/source/mids_abcd2_biology_1.sssom.tsv'

	# TARGET FILES
	dwc_biology_sssom = str(root) + '/mids/app/data/output/mids-dwc-biology-sssom.tsv'
	dwc_biology_unique = str(root) + '/mids/app/data/output/mids-dwc-biology-sssom-unique.tsv'
	dwc_geology_sssom = str(root) + '/mids/app/data/output/mids-dwc-geology-sssom.tsv'
	dwc_geology_unique = str(root) + '/mids/app/data/output/mids-dwc-geology-sssom-unique.tsv'
	dwc_paleo_sssom = str(root) + '/mids/app/data/output/mids-dwc-paleontology-sssom.tsv'
	dwc_paleo_unique = str(root) + '/mids/app/data/output/mids-dwc-paleontology-sssom-unique.tsv'
	abcd_biology_sssom = str(root) + '/mids/app/data/output/mids-abcd-biology-sssom.tsv'
	abcd_biology_unique = str(root) + '/mids/app/data/output/mids-abcd-biology-sssom-unique.tsv'

	# ------------------------------------------------------------
	# READ TSV FILES
	df_dwc_biology = pd.read_csv(dwc_biology_tsv, encoding='utf8',sep='\t')
	df_dwc_geology = pd.read_csv(dwc_geology_tsv, encoding='utf8',sep='\t')
	df_dwc_paleo = pd.read_csv(dwc_paleo_tsv, encoding='utf8',sep='\t')
	df_abcd_biology = pd.read_csv(abcd_biology_tsv, encoding="utf8",sep='\t')

	# ------------------------------------------------------------
	# Generate Unique Class-Property Pairs
	# DWC Biology
	df_dwc_biology_mapping = df_dwc_biology[['sssom:subject_category','sssom:subject_id']].drop_duplicates()
	df_dwc_biology_mapping.rename(columns={'sssom:subject_id': 'qualified_term',
	                    'sssom:subject_category': 'class_name'
	                   }, inplace=True)
	df_dwc_biology_mapping['term_local_name'] = df_dwc_biology_mapping['qualified_term'].str.replace('mids:', '')
	df_dwc_biology_mapping.to_csv(dwc_biology_unique, index=False, encoding='utf8',sep='\t')

	# DWC Geology
	df_dwc_geology_mapping = df_dwc_geology[['sssom:subject_category','sssom:subject_id']].drop_duplicates()
	df_dwc_geology_mapping.rename(columns={'sssom:subject_id': 'qualified_term',
	                    'sssom:subject_category': 'class_name'
	                   }, inplace=True)
	df_dwc_geology_mapping['term_local_name'] = df_dwc_geology_mapping['qualified_term'].str.replace('mids:', '')
	df_dwc_geology_mapping.to_csv(dwc_geology_unique, index=False, encoding='utf8',sep='\t')

	# DWC Paleontology
	df_dwc_paleo_mapping = df_dwc_paleo[['sssom:subject_category', 'sssom:subject_id']].drop_duplicates()
	df_dwc_paleo_mapping.rename(columns={'sssom:subject_id': 'qualified_term',
	                                       'sssom:subject_category': 'class_name'
	                                       }, inplace=True)
	df_dwc_paleo_mapping['term_local_name'] = df_dwc_paleo_mapping['qualified_term'].str.replace('mids:', '')
	df_dwc_paleo_mapping.to_csv(dwc_paleo_unique, index=False, encoding='utf8', sep='\t')


	# ABCD Biology
	df_abcd_biology = pd.read_csv(abcd_biology_tsv, encoding="utf8",sep='\t')
	# Generate Unique Class-Property Pairs for ABCD
	df_abcd_biology_mapping = df_abcd_biology[['sssom:subject_category','sssom:subject_id']].drop_duplicates()
	df_abcd_biology_mapping.rename(columns={'sssom:subject_id': 'qualified_term',
	                    'sssom:subject_category': 'class_name'
	                   }, inplace=True)
	df_abcd_biology_mapping['term_local_name'] = df_abcd_biology_mapping['qualified_term'].str.replace('mids:', '')
	df_abcd_biology_mapping.to_csv(abcd_biology_unique, index=False, encoding='utf8',sep='\t')

	# ------------------------------------------------------------
	# WRITE NEW MAPPINGS FILES
	# DWC BIOLOGY
	df_dwc_biology['object_source_version'] = 'http://rs.tdwg.org/dwc/terms'
	# Replace colon in column names with underscores - jinja2 template reserved character
	df_dwc_biology.columns = df_dwc_biology.columns.str.replace(':','_', regex=True)
	# Create persistent URLs
	df_dwc_biology['object_url'] = df_dwc_biology['sssom_object_id'].str.replace('dwc:','http://rs.tdwg.org/dwc/terms/')
	df_dwc_biology['subject_url'] = df_dwc_biology['sssom_subject_id'].str.replace('mids:','https://tdwg.github.io    /mids/information-elements#')
	df_dwc_biology['object_namespace'] = 'dwc'
	df_dwc_biology.to_csv(dwc_biology_sssom, index=False, encoding='utf8',sep='\t')

	# DWC GEOLOGY
	df_dwc_geology['object_source_version'] = 'http://rs.tdwg.org/dwc/terms'
	# Replace colon in column names with underscores - jinja2 template reserved character
	df_dwc_geology.columns = df_dwc_geology.columns.str.replace(':','_', regex=True)
	# Create persistent URLs
	df_dwc_geology['object_url'] = df_dwc_geology['sssom_object_id'].str.replace('dwc:','http://rs.tdwg.org/dwc/terms/')
	df_dwc_geology['subject_url'] = df_dwc_geology['sssom_subject_id'].str.replace('mids:','https://tdwg.github.io    /mids/information-elements#')
	df_dwc_geology['object_namespace'] = 'dwc'
	df_dwc_geology.to_csv(dwc_geology_sssom, index=False, encoding='utf8',sep='\t')

	# DWC PALEONTOLOGY
	df_dwc_paleo['object_source_version'] = 'http://rs.tdwg.org/dwc/terms'
	# Replace colon in column names with underscores - jinja2 template reserved character
	df_dwc_paleo.columns = df_dwc_paleo.columns.str.replace(':', '_', regex=True)
	# Create persistent URLs
	df_dwc_paleo['object_url'] = df_dwc_paleo['sssom_object_id'].str.replace('dwc:',
	                                                                             'http://rs.tdwg.org/dwc/terms/')
	df_dwc_paleo['subject_url'] = df_dwc_paleo['sssom_subject_id'].str.replace('mids:',
	                                                                               'https://tdwg.github.io    /mids/information-elements#')
	df_dwc_paleo['object_namespace'] = 'dwc'
	df_dwc_paleo.to_csv(dwc_paleo_sssom, index=False, encoding='utf8', sep='\t')


	# ABCD BIOLOGY
	df_abcd_biology['object_source_version'] = 'http://www.tdwg.org/schemas/abcd/2.06'
	# Replace colon in column names with underscores - jinja2 template reserved character
	df_abcd_biology.columns = df_abcd_biology.columns.str.replace(':','_', regex=True)
	# Create persistent URLs
	df_abcd_biology['object_url'] = df_abcd_biology['sssom_object_id'].str.replace('abcd:','http://rs.tdwg.org/abcd/terms/')
	df_abcd_biology['subject_url'] = df_abcd_biology['sssom_subject_id'].str.replace('mids:','https://tdwg.github.io    /mids/information-elements#')
	df_abcd_biology['object_namespace'] = 'abcd'
	df_abcd_biology.to_csv(abcd_biology_sssom, index=False, encoding='utf8',sep='\t')

	# Run next process
	transform_levels()
	return False

'''
	Transform MIDS Levels
	Input: /source/levels.tsv
	Output: /output/levels.tsv
'''
def transform_levels():
	# Source Files Path
	sourceFile = str(projectPath) + '/app/data/source/levels.tsv'

	# Timestamped output path
	# Create timestamped folder for working files (works in progress)
	targetPath = str(projectPath) + '/app/data/output'
	targetFile = str(targetPath) + '/levels.tsv'

	# Create timestamped folder if it doesn't exist
	if not os.path.isdir(targetPath):
	    os.mkdir(targetPath)

	# -------------------------------------------------------
	# Create copies
	# term_src > sourceFile
	# term_csv > targetFile
	shutil.copy(sourceFile, targetFile)
	# -------------------------------------------------------
	# Process
	# ltc_df > target_df
	# Read
	df = pd.read_csv(targetFile, encoding="utf8",sep='\t')

	df['level'] = df['term_local_name'].str.replace('MIDS','')
	df['pref_label'] = 'MIDS Level ' + df['level']
	# RDF Type
	df['rdf_type'] = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#Class'

	# Qualified Term
	df['term_ns_name'] = 'mids:' + df['term_local_name']
	df['namespace'] = 'mids:'

	df.rename(columns={'notes': 'usage'
	                   }, inplace=True)
	# Resave timestamped
	df.to_csv(targetFile, index=False, encoding='utf8',sep='\t')

	print('Levels transformed successfully.')
	# Transform Information Elements Next
	transform_information_elements()
	return False

'''
	Process Information Elements
'''
def transform_information_elements():

	# Paths
	current_path = Path().absolute()
	project_path = current_path.parent.parent.parent
	# Source Files Path
	source_file = str(project_path) + '/app/data/source/information_elements.tsv'
	schemas_file = str(project_path) + '/app/data/source/schemas.tsv'
	examples_source = str(project_path) + '/app/data/source/examples.tsv'
	disciplines_terms = str(project_path) + '/app/data/source/discipline_terms.tsv'

	# Timestamped output path
	# Create timestamped folder for working files (works in progress)
	target_path = str(project_path) + '/app/data/output'
	target_file = str(target_path) + '/information-elements.tsv'
	target_schema_file = str(target_path) + '/schemas.tsv'
	examples_target = str(target_path) + '/examples.tsv'
	target_disciplines_terms = str(target_path) + '/disciplines_terms.tsv'

	# Create folder if it doesn't exist
	if not os.path.isdir(target_path):
	    os.mkdir(target_path)

	# -------------------------------------------------------
	# Create copies
	# term_src > source_file
	# term_csv > target_file
	shutil.copy(source_file, target_file)
	shutil.copy(examples_source, examples_target)
	shutil.copy(schemas_file, target_schema_file)
	shutil.copy(disciplines_terms, target_disciplines_terms)

	# -------------------------------------------------------
	# Process
	# mids_df > target_df
	# Read
	df = pd.read_csv(target_file, encoding="utf8",sep='\t')

	# Renamez
	df.rename(columns={'informationElement_localName': 'term_local_name',
	                    'term_added': 'term_created'
	                   }, inplace=True)
	# RDF Type
	df['rdf_type'] = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#Property'

	# Qualified Term
	df['term_ns_name'] = 'mids:' + df['term_local_name']

	# Process Examples ------------------------------------------- */
	df_examples = pd.read_csv(examples_target, encoding="utf8",sep='\t')
	df_examples.rename(columns={'informationElement_localName': 'term_local_name'}, inplace=True)
	df_examples.to_csv(examples_target, encoding="utf8",sep='\t',index=False)

	examples_df = pd.read_csv(examples_target, sep='\t', lineterminator='\r', encoding='utf-8')
	examples_df = examples_df.replace('\n',' ', regex=True)

	df2 = examples_df.groupby('term_local_name')['example'].apply(list).reset_index(name="examples_list")
	df2 = df2[df2['examples_list'].notna()]
	df_final = pd.merge(df, df2, how="left", on=["term_local_name"])

	df_final.to_csv(target_file, encoding="utf8",sep='\t',index=False)

	print('Information Elements processed successfully.')
	return False


# First process MIDS mappings
process_source_mappings()

