from pathlib import Path
import pandas as pd
import shutil

namespace = 'ltc'
current_dir = Path().absolute()
path = current_dir.parent.parent

# 1.  Create copy of source csv
sssom_src = str(path)+'/data/sources/ltc_sssom_mapping.csv'
sssom_csv = str(path)+'/data/output/ltc-sssom.csv'
shutil.copy(sssom_src, sssom_csv)

sssom_df = pd.read_csv(sssom_csv, encoding='utf8')
sssom_df = sssom_df.rename(columns={'term_uri': 'term_iri'})
# Create Term Column with Machine-readable version of the term
# and the Term URI Column
sssom_df = sssom_df.assign(
    term_local_name=sssom_df['subject_id']
        .str.replace('http://rs.tdwg.org/ltc/terms/', '')
        .str.replace('http://purl.org/dc/terms/', '')
        .str.replace('http://rs.tdwg.org/dwc/terms/', '')
        .str.replace('https://schema.org/', '')
        .str.replace('http://rs.tdwg.org/chrono/terms/', ''),
    term_iri=sssom_df['subject_id'])

# Classes are excluded from the documentation outputs; drop mappings whose
# subject is a class along with the class (subject_category) column
class_count = int((sssom_df['subject_type'] == 'rdfs class').sum())
sssom_df = sssom_df[sssom_df['subject_type'] != 'rdfs class']
sssom_df = sssom_df.drop(columns=['subject_category'])
print(f'{class_count} class mapping records removed')

# Eliminate duplicate mappings: the same term/predicate/object mapping can be
# recorded once per organizing class; the first occurrence is kept
duplicate_count = int(sssom_df.duplicated(subset=['term_local_name', 'predicate_id', 'object_id']).sum())
sssom_df = sssom_df.drop_duplicates(subset=['term_local_name', 'predicate_id', 'object_id'], keep='first')
print(f'{duplicate_count} duplicate mapping records removed, {len(sssom_df)} unique mappings remain')

sssom_df.to_csv(sssom_csv, index=False, encoding='utf8')