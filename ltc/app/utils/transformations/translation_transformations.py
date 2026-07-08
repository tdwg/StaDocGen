from pathlib import Path
import pandas as pd
import shutil
import globals
import glob
import yaml
from functools import reduce

# Script to transform the single source translation file into a separate file for each translation
# Columns are grouped by language tag suffix, then each group is copied to a separate file.
# Only languages specified in the translations.yml file will be generated
# Workflow
# latimer-translations.csv > ltc-<lang>-translations.csv > ltc-translations-termlist.csv
# process_terms.py > translation_transformations.py

namespace = 'ltc'
current_dir = Path().absolute()
root_dir = globals.get_project_root()
project_dir = str(root_dir) +'/'+namespace+'/app'
translations_src = str(project_dir)+'/data/sources/latimer-translations.csv'
translations_csv = str(project_dir)+'/data/output/latimer-translations.csv'

# Create copies
shutil.copy(translations_src, translations_csv)

# Read translations YAML file
translations_yml = str(root_dir)+'/'+namespace+'/app/utils/translations.yml'
yml_dict = []
for yf in glob.glob(translations_yml, recursive=True):
    with open(yf, 'r') as f:
        meta = yaml.load(f, Loader=yaml.FullLoader)


# -------------------------------------------------------


source_df = pd.read_csv(translations_csv, encoding="utf8", skip_blank_lines=True)
for k in meta['Languages']:

    # Get language tag and filter columns in source translation file
    lang = k['code']
    source_df.rename(columns={'term_localName': 'term_local_name'}, inplace=True)
    source_df.sort_values(by='term_local_name', axis='index', inplace=True, na_position='last')
    patterns = [lang+'$', 'term_local_name']
    combined_pattern = reduce(lambda x, y: f'{x}|{y}', patterns)
    lang_df = source_df.filter(regex=combined_pattern)

    # Eliminate duplicate records based on term_local_name, following the same
    # pattern as process_terms.py: usage notes are ignored and the first
    # occurrence of each term is kept
    duplicate_count = int(lang_df.duplicated(subset='term_local_name').sum())
    lang_df = lang_df.drop_duplicates(subset='term_local_name', keep='first')
    print(f'{lang}: {duplicate_count} duplicate translation records removed, {len(lang_df)} unique terms remain')

    translations_target = str(project_dir) + '/data/output/ltc-'+lang+'-translations.csv'

    lang_df.to_csv(translations_target, index=False, encoding='utf8')


# ------------------------------------------------------------
# Translations

path = current_dir.parent.parent
ltc_csv = str(path)+'/data/output/ltc-termlist.csv'
ltc_df = pd.read_csv(ltc_csv, encoding="utf8")

translations_yml = str(path)+'/utils/translations.yml'
yml_dict = []
for yf in glob.glob(translations_yml, recursive=True):
    with open(yf, 'r') as f:
        meta = yaml.load(f, Loader=yaml.FullLoader)

    for k in meta['Languages']:
        lang = k['code']
        translations_source = str(path) + '/data/output/ltc-' + lang + '-translations.csv'
        translations_target= str(path) + '/data/output/ltc-translations-termlist.csv'

        translations_df = pd.read_csv(translations_source, encoding='utf8')

        # Merge Termlist with Translation
        # Both sides are unique on term_local_name, so the merge is one-to-one
        lang_df = pd.merge(ltc_df, translations_df[['term_local_name','label_'+lang,'definition_'+lang,'usage_'+lang,'notes_'+lang]], on='term_local_name', how='left')

        # Save New Translation Termlist
        lang_df.to_csv( translations_target, index=False, encoding='utf8')