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

    def test_dynamic_text_measured_as_rendered(self):
        self.assertEqual(v.display_len('{CUSTOMIZER.Price:From $500} Plans'), len('From $500 Plans'))
        self.assertEqual(v.display_len('{=IF(device=mobile,Call Now):Visit Our Site}'), len('Visit Our Site'))
        self.assertEqual(v.display_len('{=IF(device=mobile,Call Us From Your Phone):Visit}'),
                         len('Call Us From Your Phone'))
        problems, notes = v.validate(
            H15[:12] + ['Sale Ends {COUNTDOWN(2026/12/01 00:00:00,5)}', '{LOCATION(City)} Plumbers',
                        '{CUSTOMIZER.Price:From $500} Plans'], D4)
        self.assertEqual(problems, [])
        self.assertEqual(sum('excludes' in n for n in notes), 2)
        problems, _ = v.validate(H15[:14] + ['{CUSTOMIZER.Price:Plans From $500 For Every Team Size}'], D4)
        self.assertTrue(any('headline >30' in p for p in problems))

    def test_two_if_functions_and_empty_customizer(self):
        two = '{=IF(device=mobile,AAAAAAAAAAAAAAA):B} {=IF(device=mobile,C):DDDDDDDDDDDDDDD}'
        self.assertEqual(v.display_len(two), 31)
        problems, _ = v.validate(H15[:14] + [two], D4)
        self.assertTrue(any('headline >30' in p for p in problems))
        problems, _ = v.validate(H15[:14] + ['{CUSTOMIZER.Price:} Plans'], D4)
        self.assertTrue(any('empty customizer default' in p for p in problems))

    def test_punctuation_notes(self):
        _, notes = v.validate(H15, D4[:3] + ['Wait... Now?! Limited spots.'])
        self.assertTrue(any('repeated punctuation' in n for n in notes))
        _, notes = v.validate(H15, D4[:3] + ['More to come... soon.'])
        self.assertFalse(any('repeated punctuation' in n for n in notes))
        problems, notes = v.validate(H15[:14] + ['Book Today!'], D4[:3] + ['Call now!! Limited spots.'])
        self.assertEqual(problems, [])
        self.assertTrue(any('exclamation mark in a headline' in n for n in notes))
        self.assertTrue(any('repeated punctuation' in n for n in notes))


class PinTest(unittest.TestCase):
    def test_valid_pins_and_alternatives_share_a_position(self):
        pins = ['1', '1'] + [''] * 13
        problems, notes = v.validate(H15, D4, headline_pins=pins, description_pins=['1', '', '', ''])
        self.assertEqual(problems, [])
        self.assertTrue(any('H1 <- headline 1/2' in n and 'D1 <- description 1' in n for n in notes))

    def test_bad_position_values(self):
        for bad in ('4', 'H1', 'D1', 'HD2', '1.7', 'inf', '01', '+1', '4.0'):
            problems, _ = v.validate(H15, D4, headline_pins=[bad] + [''] * 14)
            self.assertEqual(problems, [f"Headline 1 position {bad!r} (use 1, 2, 3 or leave blank)"], bad)
        self.assertEqual(v.validate(H15, D4, headline_pins=['1.0'] + [''] * 14)[0], [])
        problems, _ = v.validate(H15, D4, description_pins=['', '3', '', ''])
        self.assertIn("Description 2 position '3' (use 1, 2 or leave blank)", problems)

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

    def test_edits_require_ad_id(self):
        write_csv([upload_row(Status='Enabled')], self.path('e.csv'))
        self.assertEqual(run([self.path('e.csv'), '--edits'])[0], 2)
        write_csv([upload_row(Status='Enabled', **{'Ad ID': ''})], self.path('b.csv'))
        code, out = run([self.path('b.csv'), '--edits'])
        self.assertEqual(code, 1)
        self.assertIn('blank Ad ID', out)

    def test_real_ui_export_utf16_tabs_title_rows(self):
        write_csv([upload_row(), upload_row(**{'Headline 1': 'Different Opening'})], self.path('u.csv'))
        text = ('Ad report\nOctober 1, 2026 - October 31, 2026\n'
                'Campaign\tAd Group\tAd type\tAd status\tStatus\n'
                'Search - Scheduling\tScheduling Software\tResponsive search ad\tEnabled\tApproved\n'
                'Search - Scheduling\tScheduling Software\tResponsive search ad\tEnabled\tApproved\n'
                'Total: Account\t\t\t\t\n')
        with open(self.path('e.csv'), 'w', encoding='utf-16') as fh:
            fh.write(text)
        code, out = run([self.path('u.csv'), '--existing', self.path('e.csv')])
        self.assertEqual(code, 0, out)
        self.assertIn('2 enabled + 2 new = 4 RSAs', out)

    def test_existing_without_serving_state_is_an_error(self):
        write_csv([upload_row()], self.path('u.csv'))
        write_csv([{'Campaign': 'Search - Scheduling', 'Ad Group': 'Scheduling Software',
                    'Ad type': 'Responsive search ad', 'Status': 'Yes'}], self.path('e.csv'))
        self.assertEqual(run([self.path('u.csv'), '--existing', self.path('e.csv')])[0], 2)

    def test_single_status_column_counts_serving_states(self):
        write_csv([upload_row()], self.path('u.csv'))
        rows = [{'Campaign': 'Search - Scheduling', 'Ad Group': 'Scheduling Software',
                 'Ad type': 'Responsive search ad', 'Status': s}
                for s in ('Eligible', 'Approved (limited)', 'Campaign paused', 'Paused', 'Removed')]
        rows.append({'Campaign': 'Search - Scheduling', 'Ad Group': 'Scheduling Software',
                     'Ad type': 'Expanded text ad', 'Status': 'Eligible'})
        write_csv(rows, self.path('e.csv'))
        code, out = run([self.path('u.csv'), '--existing', self.path('e.csv')])
        self.assertIn('3 enabled + 1 new = 4 RSAs', out)

    def test_existing_with_no_rsas_counts_zero(self):
        write_csv([upload_row()], self.path('u.csv'))
        write_csv([{'Campaign': 'Search - Scheduling', 'Ad Group': 'Scheduling Software',
                    'Ad type': 'Expanded text ad', 'Status': 'Eligible'}], self.path('e.csv'))
        code, out = run([self.path('u.csv'), '--existing', self.path('e.csv')])
        self.assertEqual(code, 0, out)

    def test_export_encodings_title_rows_and_narrow_totals(self):
        write_csv([upload_row(), upload_row(**{'Headline 1': 'Different Opening'})], self.path('u.csv'))
        body = ('Campaign and ad group report, Ad group level\n'
                'Campaign,Ad Group,Ad type,Status\n'
                'Search - Scheduling,Scheduling Software,Responsive search ad,Enabled\n'
                'Search - Scheduling,Scheduling Software,Responsive search ad,Enabled\n'
                'Total: Account,\n')
        for name, data in (('le.csv', body.encode('utf-16-le')), ('cp.csv', body.replace('Report', 'Café').encode('cp1252'))):
            with open(self.path(name), 'wb') as fh:
                fh.write(data)
            code, out = run([self.path('u.csv'), '--existing', self.path(name)])
            self.assertIn('2 enabled + 2 new = 4 RSAs', out, name)

    def test_edits_rules(self):
        rows = [upload_row(Status='Enabled', **{'Ad ID': '111'}),
                upload_row(Status='Removed', **{'Ad ID': '111'}),
                upload_row(Status='Enabled', **{'Ad ID': 'existing RSA 1 (ID needed)'})]
        write_csv(rows, self.path('e.csv'))
        code, out = run([self.path('e.csv'), '--edits'])
        self.assertEqual(code, 1)
        self.assertIn('a removed ad cannot be edited', out)
        self.assertIn('Ad ID 111 repeats row 2', out)
        self.assertIn('is a label, not an ID', out)

    def test_ad_id_in_upload_is_a_problem(self):
        write_csv([upload_row(**{'Ad ID': '123'})], self.path('u.csv'))
        code, out = run([self.path('u.csv')])
        self.assertEqual(code, 1)
        self.assertIn('new ads have no ID', out)

    def test_edits_keep_status_and_counts_print(self):
        write_csv([upload_row(Status='Enabled', **{'Ad ID': '123456'})], self.path('e.csv'))
        code, out = run([self.path('e.csv'), '--edits', '--counts'])
        self.assertEqual(code, 0, out)
        self.assertIn('count Headline 1: 17 | Headline Number 1', out)
        self.assertNotIn('enabled-RSA limit not checked', out)
        write_csv([upload_row(Status='Enabled', **{'Headline 2': 'x' * 31, 'Ad ID': '1'})], self.path('f.csv'))
        self.assertEqual(run([self.path('f.csv'), '--edits'])[0], 1)

    def test_pins_flow_through_cli(self):
        write_csv([upload_row(**{'Headline 1 position': '1', 'Headline 2 position': '2'})], self.path('u.csv'))
        code, out = run([self.path('u.csv')])
        self.assertEqual(code, 0, out)
        self.assertIn('both pinned', out)


if __name__ == '__main__':
    unittest.main()
