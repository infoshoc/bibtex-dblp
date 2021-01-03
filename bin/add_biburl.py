#!/usr/bin/env python
"""
Finds biburl for entries in bibliography
"""

import argparse
import itertools
import logging
import re

import bibtex_dblp.database
import bibtex_dblp.dblp_api


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]


def is_weird(word):
    return '{' in word or '}' in word


def is_not_weird(word):
    return not is_weird(word)


def extract_biburl(entry):
    if 'biburl' in entry.fields:
        biburl = entry.fields['biburl']
        logging.debug('Found biburl field %s', biburl)

        return biburl

    # TODO: use doi somehow

    pub_query_parts = list()

    for person in entry.persons.get('author'):
        pub_query_parts.extend(itertools.chain.from_iterable(map(camel_case_split, person.first_names)))
        pub_query_parts.extend(itertools.chain.from_iterable(map(camel_case_split, person.last_names)))

    for field in ('title', 'booktitle', 'year'):
        if field not in entry.fields:
            continue

        pub_query_parts.append(entry.fields[field])

        pub_query = ' '.join(pub_query_parts)
        logging.debug('Query "%s"', pub_query)
        pub_query = ' '.join(filter(is_not_weird, pub_query.split(' ')))
        # 4 possible publications are: Arxiv, Conference, Journal and spare
        max_search_results = 4
        search_results = bibtex_dblp.dblp_api.search_publication(pub_query, max_search_results=(max_search_results + 1))

        if search_results.total_matches == 0:
            logging.info('Not found publications matching query "%s"', pub_query)

            return None

        if search_results.total_matches > max_search_results:
            logging.info('Found too many (%d) publications matching "%s"', search_results.total_matches, pub_query)

            continue

        # Taking the most recent publication
        biburl = max(search_results.results, key=lambda result: result.publication.year).publication.url + '.bib'
        logging.info('Found %s', biburl)

        return biburl

    logging.warning('Not found publications matching query "%s"', ' '.join(pub_query_parts))


def add_biburl(bib):
    bib_present = 0
    bib_found = 0
    bib_not_found = 0

    for entry_str, entry in bib.entries.items():
        if 'biburl' in entry.fields:
            bib_present += 1

            continue

        biburl = extract_biburl(entry)

        if biburl is None:
            bib_not_found += 1
        else:
            bib_found += 1
            entry.fields['biburl'] = biburl

    return bib, bib_present, bib_found, bib_not_found


def main():
    parser = argparse.ArgumentParser(description='Convert DBLP entries to specific format (condensed, standard, crossref).')

    parser.add_argument('infile', help='Input bibtex file', type=str)
    parser.add_argument('--out', '-o', help='Output bibtex file. If no output file is given, the input file will be overwritten.', type=str, default=None)

    parser.add_argument('--verbose', '-v', help='print more output', action="store_true")
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG if args.verbose else logging.INFO)

    outfile = args.infile if args.out is None else args.out

    bib = bibtex_dblp.database.load_from_file(args.infile)
    bib, bib_present, bib_found, bib_not_found = add_biburl(bib)
    logging.info("Present biburl in {} entries (out of {}) from DBLP".format(bib_present, len(bib.entries)))
    logging.info("Updated {} entries (out of {}) from DBLP".format(bib_found, len(bib.entries)))
    logging.info("Not found {} entries (out of {}) from DBLP".format(bib_not_found, len(bib.entries)))
    bibtex_dblp.database.write_to_file(bib, outfile)
    logging.info("Written to {}".format(outfile))


if __name__ == "__main__":
    main()
