# Latimer Core Transformation Scripts
Sequence of csv transformations for the purposes of generating documentation from source csv files

## Sequence
Scripts must be run in a specific order to produce production files
copy_source_files.py >
sssom_transformations.py > process_terms.py > translation_transformations.py

### SKOS and SSSOM Mappings  
Transforms both mapping files  
Script:skos_transformations.py  

| Mapping Type | Type   | Path                                     |
| ------------ |--------| ---------------------------------------- |
| SKOS         | Source | ltc-source/mapping/ltc_skos_mapping.csv  |
| SKOS         | Target | ltc-docs/ltc-skos.csv                    |
| SSSOM        | Source | ltc-source/mapping/ltc_sssom_mapping.csv |
| SSSOM        | Target | ltc-docs/ltc-sssom.csv                   |


### Terms
Script: process_terms.py
Eliminates duplicate term records based on term_localName (usage notes are ignored; the first
occurrence of each term is kept), then runs the terms transformations merged in from the
former terms_transformations.py.


