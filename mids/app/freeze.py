import json
import re

from flask import Flask, render_template, jsonify, Response
from flask_frozen import Freezer
from markupsafe import Markup
import sys
import markdown2
import pandas as pd
import yaml
from datetime import date
app = Flask(__name__, template_folder='templates')
freezer = Freezer(app)

app.config['TEMPLATES_AUTO_RELOAD'] = True  # pick up template edits without restarting the dev server
app.config['FREEZER_DESTINATION'] = 'build'
app.config['FREEZER_RELATIVE_URLS'] = True
#app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True

# Resolve differences in relative paths with routes.py file
relpath = ''

with open('meta.yml') as metadata:
    meta = yaml.safe_load(metadata)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html',
                           pageTitle='404 Error'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html',
                           pageTitle='500 Unknown Error'), 500

# A markdown image followed on the next line by its caption/attribution, e.g.
#   ![alt text](custom/images/x.jpg)
#   Caption. Image: [Title](commons-url) by Author, [License](license-url), via Wikimedia Commons.
# Image paths are relative to the static folder.
FIGURE_RE = re.compile(r'<p><img src="(?!https?:)([^"]+)" alt="([^"]*)"\s*/?>\s*(.*?)</p>', flags=re.S)

def render_figures(html, static_prefix):
    """Convert markdown image + caption paragraphs into figures. static_prefix is the page's relative path to static/."""
    return FIGURE_RE.sub(
        lambda m: ('<figure class="doc-figure"><img src="{0}{1}" alt="{2}" loading="lazy">'
                   '<figcaption>{3}</figcaption></figure>').format(static_prefix, m.group(1), m.group(2), m.group(3).strip()),
        html)

def highlight_section(html, heading_id):
    """Wrap the h2 section with the given id (up to the next h2) in a highlighted block."""
    return re.sub(r'(<h2 id="' + re.escape(heading_id) + r'">.*?)(?=<h2[ >]|\Z)',
                  r'<section class="review-highlight">\1</section>\n', html, count=1, flags=re.S)

def split_review_sections(html):
    """Split rendered public review markdown into title, figure, intro, and (heading, body) sections at each h3."""
    title = 'Public Review'
    h2 = re.search(r'<h2[^>]*>(.*?)</h2>', html, flags=re.S)
    if h2:
        title = h2.group(1).strip()
        html = html[:h2.start()] + html[h2.end():]
    # The first figure is shown beside the page content rather than inside the panel
    figure = ''
    fig = re.search(r'<figure class="doc-figure">.*?</figure>', html, flags=re.S)
    if fig:
        figure = fig.group(0)
        html = html[:fig.start()] + html[fig.end():]
    parts = re.split(r'<h3[^>]*>(.*?)</h3>', html, flags=re.S)
    intro = parts[0].strip()
    sections = [{'heading': Markup(parts[i].strip()), 'body': Markup(parts[i + 1].strip())}
                for i in range(1, len(parts), 2)]
    return {'title': Markup(title), 'figure': Markup(figure), 'intro': Markup(intro), 'sections': sections}

@app.route('/')
def home():
    today = date.today()
    lastModified = today.strftime("%Y-%m-%d")
    home_mdfile = str(relpath) + 'md/home-content.md'
    public_review_mdfile = str(relpath) + 'md/mids-public-review-landing-page.md'
    with open(home_mdfile, encoding="utf8") as f:
        marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])
    with open(public_review_mdfile, encoding="utf8") as f:
        marked_public_review_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks", "header-ids"])
    return render_template('home.html',
                           home_markdown=Markup(marked_text),
                           pageTitle='Home',
                           title=meta['title'],
                           acronym=meta['acronym'],
                           landingPage=meta['links']['landing_page'],
                           githubRepo=meta['links']['github_repository'],
                           slug='home',
                           lastModified=lastModified,
                           public_review=split_review_sections(render_figures(marked_public_review_text, 'static/'))
                           )

@app.route('/information-elements/')
def information_elements():
    info_elements_mdfile = str(relpath) + 'md/information-elements-header.md'
    disciplines_section_header_mdfile = str(relpath) + 'md/disciplines-section-header.md'
    information_elements_section_header_mdfile = str(relpath) + 'md/information-elements-section-header.md'
    mids_levels_section_header_mdfile = str(relpath) + 'md/mids-levels-section-header.md'


    with open(info_elements_mdfile, encoding="utf8") as f:
        info_elements_marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])
    with open(disciplines_section_header_mdfile, encoding="utf8") as f:
        disciplines_header_marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])
    with open(information_elements_section_header_mdfile, encoding="utf8") as f:
        info_elements_section_header_marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])
    with open(mids_levels_section_header_mdfile, encoding="utf8") as f:
        mids_levels_section_header_marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])

    # Read Disciplines
    discipline_terms_tsv = str(relpath) + 'data/output/discipline_terms.tsv'
    discipline_terms_df = pd.read_csv(discipline_terms_tsv, sep='\t', lineterminator='\n', encoding='utf-8')
    discipline_terms_df = discipline_terms_df.replace(r'\n', ' ', regex=True)

    # Read Information Elements from Master List (see transformation scripts)
    information_elements_tsv = str(relpath) + 'data/output/master-list.tsv'
    information_elements_df = pd.read_csv(information_elements_tsv, sep='\t', lineterminator='\n', encoding='utf-8')
    information_elements_df = information_elements_df.replace(r'\n', ' ', regex=True)
    information_elements_df['anchor_name'] = information_elements_df['term_local_name'].str.lower()
    information_elements_df = information_elements_df.sort_values(by=['term_local_name'])

    # Read MIDS Levels
    levels_tsv = str(relpath) + 'data/output/levels.tsv'
    levels_df = pd.read_csv(levels_tsv, sep='\t', lineterminator='\n', encoding='utf-8')
    levels = levels_df.sort_values(by=['term_local_name'])
    levels_df['level'] = levels_df['term_local_name'].map(lambda x: x.lstrip('+-').rstrip('MIDS'))

    # Read Examples convert rows to comma-separated string from list
    examples_tsv = str(relpath) + 'data/output/examples.tsv'
    examples_df = pd.read_csv(examples_tsv, sep='\t', lineterminator='\r', encoding='utf-8')
    examples_df = examples_df.replace('\n', '', regex=True)
    df2 = examples_df.groupby('term_local_name')['example'].apply(list).reset_index(name="examples_list")
    df2['examples_list'] = df2['examples_list'].apply(lambda x: "|".join(map(str, x)))

    # Merge Examples with Information Elements
    merged_df = pd.merge(information_elements_df, df2[['term_local_name', 'examples_list']], on="term_local_name",
                         how="left")
    merged_df.rename(columns={'examples_list_y': 'examples_list'}, inplace=True)

    # Schemas
    schemas_tsv = str(relpath) + 'data/output/schemas.tsv'
    schemas_df = pd.read_csv(schemas_tsv, sep='\t', lineterminator='\n', encoding='utf-8')
    schemas = schemas_df.sort_values(by=['level', 'informationElement'])

    # Schemas by Level
    schemas_grpdict = schemas_df.groupby('level')[
        ['discipline','informationElement','identifier']].apply(
             lambda g: list(map(tuple, g.values.tolist()))).to_dict()
    schemas_by_level = []
    for i in schemas_grpdict:
        schemas_by_level.append({
            'level': i,
            'schemasList': schemas_grpdict[i]
    })

    #sizes_df = schemas_df.groupby(['discipline','level']).size().to_frame('count')
    #max_counts = sizes_df.groupby('level').max()

    return render_template('information-elements.html',
                        headerMarkdown=Markup(info_elements_marked_text),
                        disciplinesSectionHeaderMarkdown=Markup(disciplines_header_marked_text),
                        infoElementsSectionHeaderMarkdown=Markup(info_elements_section_header_marked_text),
                        midsLevelsSectionHeaderMarkdown=Markup(mids_levels_section_header_marked_text),
                        pageTitle='Information Elements',
                        title=meta['title'],
                        acronym=meta['acronym'],
                        landingPage=meta['links']['landing_page'],
                        githubRepo=meta['links']['github_repository'],
                        slug='information-elements',
                        levels=levels,
                        informationElements=merged_df,
                        examples=examples_df,
                        disciplinesTerms=discipline_terms_df,
                        schemas=schemas,
                        schemasByLevel=schemas_by_level
                        )

@app.route('/mappings/')
def mappings():
    mappings_mdfile = str(relpath) + 'md/mappings-header.md'
    with open(mappings_mdfile, encoding="utf8") as f:
        marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])

    sssom_mdfile = str(relpath) + 'md/sssom-reference.md'
    with open(sssom_mdfile, encoding="utf8") as f:
        sssom_marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])

    mappings_tsv = str(relpath) + 'data/output/mappings.tsv'
    mappings_df_csv = pd.read_csv(mappings_tsv, sep='\t', lineterminator='\r', encoding='utf-8', skipinitialspace=True)

    mappings_df_csv = mappings_df_csv.fillna('')
    mappings_df_csv['anchor_name'] = mappings_df_csv['term_local_name'].str.lower()
    mappings_df = mappings_df_csv.sort_values(by=['sssom_subject_category','sssom_subject_id','sssom_object_category','sssom_object_id'])

    unique_mappings_df = mappings_df.drop_duplicates(subset=['sssom_subject_category','sssom_subject_id','sssom_object_category','sssom_object_id'])

    return render_template('mappings.html',
                           headerMarkdown=Markup(marked_text),
                           sssomReference=Markup(sssom_marked_text),
                           pageTitle='MIDS Mappings',
                           title=meta['title'],
                           acronym=meta['acronym'],
                           landingPage=meta['links']['landing_page'],
                           githubRepo=meta['links']['github_repository'],
                           slug='mappings',
                           mappings=unique_mappings_df,
                           )

@app.route('/resources/')
def resources():
    content_mdfile = str(relpath) + 'md/resources-content.md'
    with open(content_mdfile, encoding="utf8") as f:
        marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])

    with open(str(relpath) + 'md/tools.yml') as tools_yml:
        tools_meta = yaml.safe_load(tools_yml)

    with open(str(relpath) + 'md/glossary.yml') as glossary_yml:
        glossary_meta = yaml.safe_load(glossary_yml)

    return render_template('resources.html',
                           content_markdown=Markup(marked_text),
                           tools_metadata=tools_meta,
                           glossary_metadata=glossary_meta,
                           pageTitle='Resources',
                           title=meta['title'],
                           acronym=meta['acronym'],
                           landingPage=meta['links']['landing_page'],
                           githubRepo=meta['links']['github_repository'],
                           slug='resources')
@app.route('/about/')
def about():
    about_mdfile = str(relpath) + 'md/about-content.md'
    with open(about_mdfile, encoding="utf8") as f:
        marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks"])

    return render_template('about.html',
        about_markdown=Markup(marked_text),
        pageTitle='About MIDS',
        title=meta['title'],
        acronym=meta['acronym'],
        landingPage=meta['links']['landing_page'],
        githubRepo=meta['links']['github_repository'],
        slug='about')


@app.route('/public-review/')
def public_review():
    lastModified = date.today().strftime("%Y-%m-%d")
    public_review_mdfile = str(relpath) + 'md/mids-public-review-participation-detailed.md'
    with open(public_review_mdfile, encoding="utf8") as f:
        marked_text = markdown2.markdown(f.read(), extras=["tables", "fenced-code-blocks", "header-ids"])
    marked_text = render_figures(marked_text, '../static/')
    marked_text = highlight_section(marked_text, 'what-is-under-review')
    # Build the sidebar table of contents from the h2 headings
    toc = [{'id': m.group(1), 'label': Markup(m.group(2).strip())}
           for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', marked_text, flags=re.S)]

    return render_template('public-review.html',
                           public_review_detailed_markdown=Markup(marked_text),
                           toc=toc,
                           tdwg_process_links=meta['tdwg_process_links'],
                           pageTitle='Public Review',
                           title=meta['title'],
                           acronym=meta['acronym'],
                           landingPage=meta['links']['landing_page'],
                           githubRepo=meta['links']['github_repository'],
                           slug='public-review',
                           lastModified=lastModified)

#API Requests for Table Filters
@app.route('/api/data.json')
def get_data():
    """Return all data as JSON"""
    output_json = str(relpath) + 'api/data.json'
    mappings_tsv = str(relpath) + 'data/output/mappings.tsv'
    mappings_df = pd.read_csv(mappings_tsv, sep='\t', lineterminator='\r', encoding='utf-8', skipinitialspace=True, index_col=0)
    df_cleaned = mappings_df.dropna(how='all')
    json_string = df_cleaned.to_json(orient="records")
    with open(output_json, 'w') as outfile:
        outfile.write(json_string)
    return Response(json_string, mimetype='application/json')

@app.route('/api/filters.json')
def get_filters():
    """Return unique values for each filterable column"""
    mappings_tsv = str(relpath) + 'data/output/mappings.tsv'
    mappings_df = pd.read_csv(mappings_tsv, sep='\t', lineterminator='\r', encoding='utf-8', skipinitialspace=True, index_col=0)
    mappings_df = mappings_df.fillna('')
    df_cleaned = mappings_df.dropna(how='all')
    # Get Unique attribute values from Columns to create filters
    unique_levels = df_cleaned['sssom_subject_category'].unique()
    unique_infoElements = df_cleaned['sssom_subject_id'].unique()
    unique_disciplines = df_cleaned['discipline'].unique()
    # Create lists from unique value sets
    levels = list(filter(None, unique_levels.tolist()))
    infoElements = list(filter(None, unique_infoElements.tolist()))
    disciplines = list(filter(None, unique_disciplines.tolist()))

    return jsonify({
        'levels': levels,
        'infoElements': infoElements,
        'disciplines': disciplines
    })





if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(port=8001)