import re
import unittest

from bin.add_address import extract_address_from_booktitle, conference_year_short_name_pattern


class ExtractAddressFromBookTitle(unittest.TestCase):
    def test_conference_year_short_name_pattern(self):
        self.assertIsNotNone(re.match(
            conference_year_short_name_pattern,
            '{SODA} 2012',
        ))

    def test_conference_year_short_name_pattern_2(self):
        self.assertIsNotNone(re.match(
            conference_year_short_name_pattern,
            "STOC'13",
        ))

    def test_last(self):
        self.assertEqual(extract_address_from_booktitle(
            '19th International Conference on Principles of Distributed Systems, '
            '{OPODIS} 2015, '
            'December 14-17, '
            '2015, '
            'Rennes, France'
        )[0], 'Rennes, France')

    def test_before_last(self):
        self.assertEqual(extract_address_from_booktitle(
            'Proceedings of the Twenty-Third Annual {ACM-SIAM} Symposium on Discrete Algorithms, '
            '{SODA} 2012, '
            'Kyoto, Japan, '
            'January 17-19, '
            '2012'
        )[0], 'Kyoto, Japan')

    def test_comma_in_name(self):
        self.assertEqual(extract_address_from_booktitle(
            'Automata, Languages, and Programming - 39th International Colloquium, '
            '{ICALP} 2012, '
            'Warwick, UK, '
            'July 9-13, '
            '2012, '
            'Proceedings, '
            'Part {II}'
        )[0], 'Warwick, UK')

    def test_short_year_in_short_conference_name(self):
        self.assertEqual(extract_address_from_booktitle(
            "Theory of Computing Conference, "
            "STOC'13, "
            "Palo Alto, CA, USA, "
            "June 1-4, "
            "2013"
        )[0], 'Palo Alto, CA, USA')

    def test_short_first(self):
        self.assertEqual(extract_address_from_booktitle(
            "{PODC} '20: "
            "{ACM} Symposium on Principles of Distributed Computing, "
            "Virtual Event, Italy, "
            "August 3-7, 2020"
        )[0], 'Virtual Event, Italy')


if __name__ == '__main__':
    unittest.main()
