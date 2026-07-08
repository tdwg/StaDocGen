from pathlib import Path
import pandas as pd

# Process LtC Terms
# Reads the source terms directly, deduplicates on term_localName, filters out
# class records, then runs the terms transformation sequence (merged in from
# the former terms_transformations.py). Sources are never copied verbatim to
# the output directory, so classes never appear there.
# Run from this directory: python process_terms.py
# Sequence: sssom_transformations.py > process_terms.py > translation_transformations.py
# Last Modified: 2026-07-08

namespace = 'ltc'
current_dir = Path().absolute()
path = current_dir.parent.parent

term_src = str(path)+'/data/sources/ltc_terms_source.csv'
term_csv = str(path)+'/data/output/ltc-termlist.csv'

ns_src = str(path)+'/data/sources/ltc_namespaces.csv'
ns_csv = str(path)+'/data/output/ltc-namespaces.csv'

dt_src = str(path)+'/data/sources/ltc_datatypes.csv'
dt_csv = str(path)+'/data/output/ltc-datatypes.csv'

# -------------------------------------------------------
# Terms
ltc_df = pd.read_csv(term_src, encoding="utf8")

# Eliminate duplicate records
# The same term_localName can appear once per organizing class, with rows
# differing only in usage notes and tdwgutility_organizedInClass. Usage notes
# are ignored; the first occurrence of each term_localName is kept.
duplicate_count = int(ltc_df.duplicated(subset='term_localName').sum())
ltc_df = ltc_df.drop_duplicates(subset='term_localName', keep='first')
print(f'{duplicate_count} duplicate term records removed, {len(ltc_df)} unique terms remain')

# Classes are excluded from the documentation outputs; keep property terms only
class_count = int((ltc_df['rdf_type'] != 'http://www.w3.org/1999/02/22-rdf-syntax-ns#Property').sum())
ltc_df = ltc_df[ltc_df['rdf_type'] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#Property']
print(f'{class_count} class records removed, {len(ltc_df)} property terms remain')

# Rename Columns
ltc_df = ltc_df.rename(columns={'term_localName': 'term_local_name',
                                'tdwgutility_required': 'is_required',
                                'tdwgutility_repeatable': 'is_repeatable'})

# Terms are class-independent after deduplication; drop the organizing class
ltc_df = ltc_df.drop(columns=['tdwgutility_organizedInClass'])
# Fix boolean values
ltc_df = ltc_df.replace({'is_required': {'Yes': 'True', 'No': 'False'},
                         'is_repeatable': {'Yes': 'True', 'No': 'False'}})
# Save
ltc_df.to_csv(term_csv, index=False, encoding='utf8')

# ------------------------------------------------------------
# Namespaces
ns_df = pd.read_csv(ns_src, encoding="utf8")
# Rename namespaces columns
ns_df = ns_df.rename(columns={'curie': 'namespace', 'value': 'namespace_iri'})
# Add colon to namespace for merger with terms csv
ns_df = ns_df.assign(namespace=ns_df['namespace'].astype(str) + ':')

if 'ltc:' not in ns_df.values:
    ltc_row = {"namespace": "ltc:", "namespace_iri": "http://rs.tdwg.org/ltc/terms/"}
    ns_df = pd.concat([ns_df, pd.DataFrame([ltc_row])], ignore_index=True)
ns_df.to_csv(ns_csv, index=False, encoding='utf8')

# Merge Terms and Namespaces
ns_df = pd.read_csv(ns_csv, encoding="utf8")
ltc_df = pd.read_csv(term_csv, encoding="utf8")

ltc_df = pd.merge(ltc_df, ns_df[['namespace', 'namespace_iri']], on='namespace', how='inner')

# Create Term IRI
ltc_df = ltc_df.assign(
    term_iri=ltc_df['namespace_iri'].astype(str) + ltc_df['term_local_name'],
    term_ns_name=ltc_df['namespace'].astype(str) + ltc_df['term_local_name'],
    term_version_iri='http://rs.tdwg.org/ltc/terms/' + ltc_df['term_local_name'] + '-' + ltc_df['term_modified'])

ltc_df = ltc_df.sort_values(by='term_local_name', axis='index', na_position='last')

# Data cleanup
ltc_df = ltc_df.assign(examples=ltc_df['examples'].str.replace('"', ''),
                       definition=ltc_df['definition'].str.replace('"', ''),
                       usage=ltc_df['usage'].str.replace('"', ''),
                       notes=ltc_df['notes'].str.replace('"', ''))

# Resave terms file
ltc_df.to_csv(term_csv, index=False, encoding='utf8')

# ------------------------------------------------------------
# Datatypes
dt_df = pd.read_csv(dt_src, encoding='utf8')
dt_df = dt_df.rename(columns={'term_localName': 'term_local_name'})
# Datatypes are class-independent: they repeat per organizing class but are
# identical per term, so drop the class column and deduplicate on
# term_local_name to keep the terms merge one-to-one
dt_df = dt_df.drop(columns=['tdwgutility_organizedInClass'])
dt_df = dt_df.drop_duplicates(subset='term_local_name', keep='first')

# Datatypes for excluded (class) terms are not copied to the output
dt_df = dt_df[dt_df['term_local_name'].isin(ltc_df['term_local_name'])]

# Save datatypes file
dt_df.to_csv(dt_csv, index=False, encoding='utf8')

# ------------------------------------------------------------
# Merge Terms and Datatypes
ltc_df = pd.merge(ltc_df, dt_df[['term_local_name', 'datatype']], on='term_local_name', how='left')
# Resave
ltc_df.to_csv(term_csv, index=False, encoding='utf8')
