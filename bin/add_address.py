#!/usr/bin/env python
"""
Infering address for inproceedings entries in bibliography to silent ACM-Reference-Format
"""

import argparse
import logging
import re

import bibtex_dblp.database
import bibtex_dblp.dblp_api

day_pattern = r'[1-9][0-9]?'
year_pattern = r'[1-9][0-9]{3}'
year_short_pattern = r'[0-9]{2}'
month_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
any_pattern = '.+?'

conference_full_name_pattern = any_pattern
conference_short_name_pattern = '(?:\{[A-Z]+\})|(?:[A-Z]+)'
date_range_pattern = f'(?:{month_pattern} {day_pattern}-{day_pattern})|(?:{month_pattern} {day_pattern} - {month_pattern} {day_pattern})'
conference_year_short_name_pattern = f"^(?:{conference_short_name_pattern})(?:(?: {year_pattern})|(?: ?'{year_short_pattern}))$"
short_first_pattern = f'^(?:{conference_year_short_name_pattern[1:-1]}): (?:{conference_full_name_pattern}), (.*), {date_range_pattern}, {year_pattern}$'


def extract_address_from_booktitle(booktitle):
    candidates = booktitle.split(', ')

    booktitle_parts = list()
    conference_short_name = None
    city = None
    district = None
    contry = None

    for pattern in [short_first_pattern]:
        match = re.match(pattern, booktitle)
        if match is not None:
            address = match.group(1)
            booktitle = booktitle.replace(address + ', ', '')

            return address, booktitle


    for candidate in candidates:
        if conference_short_name is None:
            booktitle_parts.append(candidate)

            if re.match(conference_year_short_name_pattern, candidate):
                conference_short_name = candidate

            continue

        if re.match(date_range_pattern, candidate):
            logging.debug('%s is month and day', candidate)
            booktitle_parts.append(candidate)
        elif re.match(year_pattern, candidate):
            logging.debug('%s is a year', candidate)
            booktitle_parts.append(candidate)
        elif city is None:
            logging.debug('%s is a city', candidate)
            city = candidate
        elif contry is None:
            logging.debug('%s is a contry', candidate)
            contry = candidate
        elif candidate in ('USA', ):
            logging.debug('%s is a contry, and %s was district', candidate, contry)
            district = contry
            contry = candidate
        else:
            booktitle_parts.append(candidate)

    address = [city]

    if district is not None:
        address.append(district)

    if contry is not None:
        address.append(contry)

    if None in address:
        logging.warning('Unable to parse %s', booktitle)
        return None, None

    address = ', '.join(address)

    if re.match(date_range_pattern, address):
        logging.warning('Unable to parse %s', booktitle)
        return None, None

    booktitle = ', '.join(booktitle_parts)

    logging.info('Address detected %s', address)

    return address, booktitle


def extract_address(entry):
    if 'booktitle' in entry.fields:
        return extract_address_from_booktitle(entry.fields['booktitle'])
    else:
        return None, None


def add_address(bib):
    bib_present = 0
    bib_found = 0
    bib_not_found = 0

    for entry_str, entry in bib.entries.items():
        if entry.original_type not in ('inproceedings', ):
            continue

        if 'address' in entry.fields and len(entry.fields['address'].strip()) > 0:
            bib_present += 1

            continue

        address, booktitle = extract_address(entry)

        if address is None:
            bib_not_found += 1
        else:
            bib_found += 1
            entry.fields['address'] = address
            entry.fields['booktitle'] = booktitle

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
    bib, bib_present, bib_found, bib_not_found = add_address(bib)
    logging.info("Present address in {} entries (out of {}) from DBLP".format(bib_present, len(bib.entries)))
    logging.info("Updated {} entries (out of {}) from DBLP".format(bib_found, len(bib.entries)))
    logging.info("Not found {} entries (out of {}) from DBLP".format(bib_not_found, len(bib.entries)))
    bibtex_dblp.database.write_to_file(bib, outfile)
    logging.info("Written to {}".format(outfile))


if __name__ == "__main__":
    main()
