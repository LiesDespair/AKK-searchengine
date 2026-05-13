"""
UTILITY: Text Transformation & Parsing
--------------------------------------
PURPOSE:
Provides the 'Text Transformation' logic required to turn raw HTML into
searchable tokens.

TECHNICAL SPECIFICATIONS:
- Tokenization: Alphanumeric sequences only ([a-zA-Z0-9]+).
- Stemming: Porter Stemmer (nltk) for improved recall.
- Importance Flagging: Identifies tokens within <title>, <h1>-<h3>, <b>,
  and <strong> tags.
- Postings Format: { token: [ (doc_id, tf, [positions], importance), ... ] }

NOTES:
- Silences MarkupResemblesLocatorWarning and XMLParsedAsHTMLWarning to
  handle the 'broken/missing HTML' in the UCI corpus.
"""

import re
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning, XMLParsedAsHTMLWarning
from nltk.stem import PorterStemmer
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

stemmer = PorterStemmer()
def process_content(html_content):
    soup = BeautifulSoup(html_content, 'lxml')

    #look for important stems
    important_tags = ['title', 'h1', 'h2', 'h3', 'b', 'strong']
    important_stems = set()
    for tag in soup.find_all(important_tags):
        for token in re.findall(r'[a-zA-Z0-9]+', tag.get_text().lower()):
            important_stems.add(stemmer.stem(token))

    #pass over entire document
    all_tokens = re.findall(r'[a-zA-Z0-9]+', soup.get_text().lower())

    #stem -> [term_freq, [positions in json], is_important]
    stem_stats = {}
    for idx, token in enumerate(all_tokens):
        stemmed = stemmer.stem(token)
        if stemmed not in stem_stats:
            is_important = 1 if stemmed in important_stems else 0
            stem_stats[stemmed] = [1, [idx], is_important]
        else:
            if stemmed in important_stems:
                stem_stats[stemmed][2] = 1  # Make important
            stem_stats[stemmed][0] += 1  # Increment TF
            stem_stats[stemmed][1].append(idx)  # Add position

    return stem_stats

