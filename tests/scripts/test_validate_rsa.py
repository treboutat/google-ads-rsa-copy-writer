"""Unit tests for scripts/validate_rsa.py.

    python3 -m unittest discover -s tests/scripts
"""
import contextlib
import csv
import importlib
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
v = importlib.import_module('validate_rsa')

H15 = [f'Headline Number {n}' for n in range(1, 16)]
D4 = [f'Description number {n} with detail.' for n in range(1, 5)]


def upload_row(**over):
    row = {'Campaign': 'Search - Scheduling', 'Ad group': 'Scheduling Software',
           'Ad type': 'Responsive search ad', 'Status': 'Paused',
           'Final URL': 'https://example.com/scheduling', 'Path 1': 'scheduling', 'Path 2': ''}
    for i, h in enumerate(H15, 1):
        row[f'Headline {i}'] = h
        row[f'Headline {i} position'] = ''
    for i, d in enumerate(D4, 1):
        row[f'Description {i}'] = d
        row[f'Description {i} position'] = ''
    row.update(over)
    return row


def write_csv(rows, path, fields=None):
    fields = fields or list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def run(args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            code = v.main(args)
        except SystemExit as exc:  # argparse input errors
            code = exc.code
    return code, out.getvalue()


class FieldTest(unittest.TestCase):
    def test_clean_full_set(self):
        self.assertEqual(v.validate(H15, D4), ([], []))

    def test_limits_and_wide_characters(self):
        self.assertEqual(v.display_len('価格'), 4)
        self.assertEqual(v.display_len('{KeyWord:Scheduling App} Today'), len('Scheduling App Today'))
        problems, _ = v.validate(H15[:2] + ['x' * 31], D4[:1] + ['y' * 91], 'p' * 16)
        joined = ' | '.join(problems)
        self.assertIn('headline >30', joined)
        self.assertIn('description >90', joined)
        self.assertIn('path >15', joined)

    def test_counts_blanks_and_duplicates(self):
        problems, _ = v.validate(['Acme Pricing', 'acme pricing', '  '], ['One.', ''])
        self.assertIn('2 headlines (3-15)', problems)
        self.assertIn('1 descriptions (2-4)', problems)
        self.assertIn('duplicate headline', problems)
        self.assertEqual(v.validate(H15 + ['Sixteenth Headline'], D4)[0], ['16 headlines (3-15)'])

    def test_path2_needs_path1_and_dki_fallback(self):
        problems, _ = v.validate(H15[:14] + ['{KeyWord:}'], D4, '', 'demo')
        self.assertIn('Path 2 without Path 1', problems)
        self.assertTrue(any('empty keyword-insertion fallback' in p for p in problems))

    def test_other_dynamic_tokens_are_notes_not_problems(self):
        problems, notes = v.validate(H15[:14] + ['{LOCATION(City)} Plumbers'], D4)
        self.assertEqual(problems, [])
        self.assertTrue(any('manual length' in n for n in notes))


class PinTest(unittest.TestCase):
    def test_valid_pins_and_alternatives_share_a_position(self):
        pins = ['1', '1'] + [''] * 13
        problems, notes = v.validate(H15, D4, headline_pins=pins, description_pins=['1', '', '', ''])
        self.assertEqual(problems, [])
        self.assertTrue(any('H1 <- headline 1/2' in n and 'D1 <- description 1' in n for n in notes))

    def test_bad_position_values(self):
        problems, _ = v.validate(H15, D4, headline_pins=['4'] + [''] * 14,
                                 description_pins=['', 'H3', '', ''])
        self.assertIn('Headline 1 position 4 (allowed: 1, 2, 3)', problems)
        self.assertIn('Description 2 position 3 (allowed: 1, 2)', problems)

    def test_position_on_blank_asset(self):
        problems, _ = v.validate(H15[:14] + [''], D4, headline_pins=[''] * 14 + ['2'])
        self.assertIn('Headline 15 has a position but no text', problems)

    def test_required_positions_must_fill(self):
        # Every headline pinned to H1 leaves nothing for H2.
        problems, _ = v.validate(H15[:3], D4[:2], headline_pins=['1', '1', '1'])
        self.assertTrue(any('fill H2' in p for p in problems))
        # Both descriptions pinned to D2 leave nothing for D1.
        problems, _ = v.validate(H15, D4[:2], description_pins=['2', '2'])
        self.assertTrue(any('fill D1' in p for p in problems))

    def test_dual_pin_and_unreliable_positions_are_noted(self):
        _, notes = v.validate(H15, D4, headline_pins=['1', '2', '3'] + [''] * 12,
                              description_pins=['', '2', '', ''])
        text = ' | '.join(notes)
        self.assertIn('Headline 1 and Headline 2 both pinned', text)
        self.assertIn('pin at H3', text)
        self.assertIn('pin at D2', text)

    def test_letter_prefixed_positions_accepted(self):
        problems, _ = v.validate(H15, D4, headline_pins=['H1'] + [''] * 14, description_pins=['D1', '', '', ''])
        self.assertEqual(problems, [])


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def test_clean_file_passes(self):
        write_csv([upload_row()], self.path('u.csv'))
        code, out = run([self.path('u.csv')])
        self.assertEqual(code, 0, out)
        self.assertIn('1 RSAs checked, 0 with problems', out)
        self.assertIn('enabled-RSA limit not checked', out)

    def test_row_level_problems(self):
        write_csv([upload_row(Status='Enabled', **{'Final URL': 'example.com', 'Ad type': 'Expanded text ad'})],
                  self.path('u.csv'))
        code, out = run([self.path('u.csv')])
        self.assertEqual(code, 1)
        self.assertIn("status 'Enabled'", out)
        self.assertIn('must start with http', out)
        self.assertIn('expected Responsive search ad', out)

    def test_existing_limit_is_a_note(self):
        write_csv([upload_row(), upload_row(**{'Headline 1': 'Different Opening'})], self.path('u.csv'))
        existing = [{'Campaign': 'search - scheduling', 'Ad group': 'Scheduling Software',
                     'Ad type': 'Responsive search ad', 'Status': 'Enabled'},
                    {'Campaign': 'Search - Scheduling', 'Ad group': 'Scheduling Software',
                     'Ad type': 'Responsive search ad', 'Status': 'Enabled'},
                    {'Campaign': 'Search - Scheduling', 'Ad group': 'Scheduling Software',
                     'Ad type': 'Responsive search ad', 'Status': 'Paused'},
                    {'Campaign': 'Search - Scheduling', 'Ad group': 'Scheduling Software',
                     'Ad type': 'Call ad', 'Status': 'Enabled'}]
        write_csv(existing, self.path('e.csv'))
        code, out = run([self.path('u.csv'), '--existing', self.path('e.csv')])
        self.assertEqual(code, 0, out)
        self.assertIn('2 enabled + 2 new = 4 RSAs', out)

    def test_shifted_row_is_an_input_error(self):
        row = upload_row()
        write_csv([row], self.path('u.csv'))
        with open(self.path('u.csv'), 'a', encoding='utf-8') as fh:
            fh.write(','.join(['x'] * (len(row) + 1)) + '\n')
        code, out = run([self.path('u.csv')])
        self.assertEqual(code, 2)

    def test_unknown_asset_column_and_missing_required(self):
        write_csv([dict(upload_row(), **{'Headline 16': 'Too Many'})], self.path('u.csv'))
        self.assertEqual(run([self.path('u.csv')])[0], 2)
        row = upload_row()
        del row['Final URL']
        write_csv([row], self.path('m.csv'))
        self.assertEqual(run([self.path('m.csv')])[0], 2)

    def test_edits_keep_status_and_counts_print(self):
        write_csv([upload_row(Status='Enabled')], self.path('e.csv'))
        code, out = run([self.path('e.csv'), '--edits', '--counts'])
        self.assertEqual(code, 0, out)
        self.assertIn('count Headline 1: 17 | Headline Number 1', out)
        self.assertNotIn('enabled-RSA limit not checked', out)
        write_csv([upload_row(Status='Enabled', **{'Headline 2': 'x' * 31})], self.path('f.csv'))
        self.assertEqual(run([self.path('f.csv'), '--edits'])[0], 1)

    def test_pins_flow_through_cli(self):
        write_csv([upload_row(**{'Headline 1 position': '1', 'Headline 2 position': '2'})], self.path('u.csv'))
        code, out = run([self.path('u.csv')])
        self.assertEqual(code, 0, out)
        self.assertIn('both pinned', out)


if __name__ == '__main__':
    unittest.main()
