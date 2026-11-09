"""Validate Google Ads responsive search ad (RSA) fields, pins and ad counts.

    python3 validate_rsa.py rsa_upload.csv
    python3 validate_rsa.py rsa_upload.csv --existing current_ads.csv --counts
    python3 validate_rsa.py rsa_edits_review.csv --edits

    from validate_rsa import validate, display_len
    problems, notes = validate(headlines, descriptions, path1, path2,
                               headline_pins=[...], description_pins=[...])

Problems break the upload and make the command exit 1. Notes need a human
decision (a pin that needs a stated reason, an ad group over the enabled-RSA
limit, a dynamic token to check by hand, punctuation that policy often rejects)
and never change the exit code.

Checks:
- 3-15 headlines up to 30 characters; 2-4 descriptions up to 90; paths up to 15.
  Double-width characters count twice, as Google counts them. Dynamic text is
  measured on what it can render: keyword insertion ({KeyWord:Fallback}) and ad
  customizers ({CUSTOMIZER.Name:Default}) on their default text, IF functions
  ({=IF(device=mobile,Text):Default}) on their longest combination. Anything else
  in braces (countdowns, location insertion, customizers without a default,
  business data, IF functions this parser can't read) is left out of the count
  and noted for a manual check.
- No blank or case-insensitive duplicate assets; Path 2 needs Path 1.
- Pins: position values are 1, 2 or 3 for headlines and 1 or 2 for descriptions
  (a spreadsheet's 1.0 is read as 1); no position on a blank asset; Headline 1, Headline 2 and
  Description 1 can always be filled. Dual pinning of H1 and H2, and pins at H3
  or D2 (positions that don't always show), are noted so the review records why.
- Upload rows: Paused "Responsive search ad" rows with a campaign, ad group and
  an http(s) final URL and no Ad ID. With --edits (a review file of in-place edits
  to existing ads, not an import file) every row needs a unique Ad ID, the Paused
  rule is skipped and Removed ads are rejected.
- With --counts: every asset's display length, for the review file.
- With --existing: enabled RSAs already in each ad group plus the new rows,
  against Google's limit of three enabled RSAs per ad group. Reads Google Ads UI
  and Editor exports: UTF-8 or UTF-16, comma or tab separated, title rows above
  the header, any header capitalization.

Column names are matched without regard to case ("Ad Group" or "Ad group").
Malformed CSV, duplicate or empty column names, unrecognized asset columns,
missing required columns and rows wider or narrower than the header are input
errors (exit 2).
"""
import csv
import io
import re
import unicodedata

_DKI = re.compile(r'\{keyword:([^}]*)\}', re.I)
_CUSTOMIZER = re.compile(r'\{customizer\.[^:}]*:([^}]*)\}', re.I)
_IF = re.compile(r'\{=IF\([^,()]*,([^)]*)\):([^}]*)\}', re.I)
_TOKEN = re.compile(r'\{[^}]*\}')
_ASSET = re.compile(r'^(headline|description|path)\b', re.I)
HEADLINES = [f'Headline {n}' for n in range(1, 16)]
DESCRIPTIONS = [f'Description {n}' for n in range(1, 5)]
ASSET_COLUMNS = (HEADLINES + [f'{h} position' for h in HEADLINES]
                 + DESCRIPTIONS + [f'{d} position' for d in DESCRIPTIONS] + ['Path 1', 'Path 2'])
KNOWN_COLUMNS = ASSET_COLUMNS + ['Campaign', 'Ad Group', 'Ad type', 'Status', 'Ad ID', 'Final URL',
                                 'Final mobile URL', 'Tracking template', 'Final URL suffix']
REQUIRED_COLUMNS = ['Campaign', 'Ad Group', 'Ad type', 'Headline 1', 'Headline 2', 'Headline 3',
                    'Description 1', 'Description 2', 'Final URL', 'Status']
MAX_ENABLED_RSAS = 3


def _width(text):
    return sum(2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1 for ch in text)


def measure(text):
    """Return (length, unmeasured_tokens) for one asset as it can render."""
    import itertools
    text = str(text)
    ifs = list(_IF.finditer(text))[:6]
    variants = []
    for choice in itertools.product((1, 2), repeat=len(ifs)):
        v, last = [], 0
        for m, k in zip(ifs, choice):
            v += [text[last:m.start()], m.group(k)]
            last = m.end()
        variants.append(''.join(v) + text[last:])
    lengths, unmeasured = [], []
    for v in variants:
        v = _DKI.sub(lambda m: m.group(1), v)
        v = _CUSTOMIZER.sub(lambda m: m.group(1), v)
        unmeasured += _TOKEN.findall(v)
        lengths.append(_width(_TOKEN.sub('', v)))
    return max(lengths), sorted(set(unmeasured))


def display_len(text):
    return measure(text)[0]


def _blank(x):
    return x is None or x != x or not str(x).strip()  # x != x: NaN from an empty sheet cell


def _pin(value, allowed, label, problems):
    """Return the pinned position as an int, None when unpinned."""
    if _blank(value):
        return None
    shown = raw = str(value).strip()
    if re.fullmatch(r'[1-9]\.0+', raw):  # spreadsheets write 1 as 1.0
        raw = raw.split('.')[0]
    if raw not in {str(p) for p in allowed}:
        problems.append(f'{label} position {shown!r} (use {", ".join(map(str, allowed))} or leave blank)')
        return None
    return int(raw)


def _check_pins(kind, texts, pins, allowed, required, problems):
    pinned = {}
    unpinned = 0
    for i, (text, value) in enumerate(zip(texts, pins), start=1):
        label = f'{kind} {i}'
        if _blank(text):
            if not _blank(value):
                problems.append(f'{label} has a position but no text')
            continue
        pos = _pin(value, allowed, label, problems)
        if pos is None:
            unpinned += 1
        else:
            pinned.setdefault(pos, []).append(i)
    if not pinned:
        return pinned
    empty = [p for p in required if p not in pinned]
    if unpinned < len(empty):
        names = ', '.join(f'{kind[0]}{p}' for p in empty)
        problems.append(f'not enough unpinned {kind.lower()}s to fill {names} '
                        f'({unpinned} unpinned for {len(empty)} position(s))')
    return pinned


def validate(H, D, p1='', p2='', headline_pins=None, description_pins=None):
    """Return (problems, notes) for one RSA.

    H and D keep their slot order so pins line up; blank slots are allowed and skipped.
    """
    problems, notes = [], []
    headline_pins = list(headline_pins or [None] * len(H))
    description_pins = list(description_pins or [None] * len(D))
    headline_pins += [None] * (len(H) - len(headline_pins))
    description_pins += [None] * (len(D) - len(description_pins))

    h_pins = _check_pins('Headline', H, headline_pins, (1, 2, 3), (1, 2), problems)
    d_pins = _check_pins('Description', D, description_pins, (1, 2), (1,), problems)

    hs = [str(h) for h in H if not _blank(h)]
    ds = [str(d) for d in D if not _blank(d)]
    p1, p2 = ('' if _blank(p) else str(p) for p in (p1, p2))
    if not 3 <= len(hs) <= 15:
        problems.append(f'{len(hs)} headlines (3-15)')
    if not 2 <= len(ds) <= 4:
        problems.append(f'{len(ds)} descriptions (2-4)')
    if len({h.strip().lower() for h in hs}) != len(hs):
        problems.append('duplicate headline')
    if len({d.strip().lower() for d in ds}) != len(ds):
        problems.append('duplicate description')
    for kind, items, limit in (('headline', hs, 30), ('description', ds, 90),
                               ('path', [p for p in (p1, p2) if p], 15)):
        for x in items:
            n, unmeasured = measure(x)
            if n > limit:
                problems.append(f'{kind} >{limit}: {x} ({n})')
            if unmeasured:
                notes.append(f'{kind} length {n} excludes {" ".join(unmeasured)}; '
                             f'check the rendered text by hand: {x}')
    if p2 and not p1:
        problems.append('Path 2 without Path 1')
    problems += [f'empty keyword-insertion fallback: {x}' for x in hs + ds
                 if any(not m.group(1).strip() for m in _DKI.finditer(x))]
    problems += [f'empty customizer default text: {x}' for x in hs + ds
                 if any(not m.group(1).strip() for m in _CUSTOMIZER.finditer(x))]
    notes += [f'exclamation mark in a headline (Google\'s punctuation policy commonly '
              f'disapproves these): {h}' for h in hs if '!' in h]
    notes += [f'repeated punctuation (often disapproved): {x}' for x in hs + ds
              if re.search(r'[!?]{2,}|,{2,}|(?<!\.)\.\.(?!\.)|\.{4,}', x)]

    if 1 in h_pins and 2 in h_pins:
        notes.append('Headline 1 and Headline 2 both pinned: unpinned headlines can only serve at '
                     'H3, which does not always show; record why both pins are needed')
    if 3 in h_pins:
        notes.append('pin at H3: Headline 3 does not always show, so it cannot carry required text')
    if 2 in d_pins:
        notes.append('pin at D2: Description 2 does not always show, so it cannot carry required text')
    if h_pins or d_pins:
        notes.append('pinned: ' + ', '.join(
            [f'H{p} <- headline {"/".join(map(str, s))}' for p, s in sorted(h_pins.items())]
            + [f'D{p} <- description {"/".join(map(str, s))}' for p, s in sorted(d_pins.items())])
            + '; name the message each pin protects')
    return problems, notes


def _decode(raw):
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    head = raw[:400]
    if head and head.count(b'\x00') > len(head) // 4:  # UTF-16 without a byte-order mark
        return raw.decode('utf-16-le' if head[1:2] == b'\x00' else 'utf-16-be')
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return raw.decode('cp1252')  # Excel's default on Windows


def _read_csv(path, error, find_header=False):
    """Read a CSV into (fields, rows) with canonical column names where known."""
    try:
        with open(path, 'rb') as fh:
            text = _decode(fh.read())
    except (OSError, UnicodeError) as exc:
        error(f'{path}: {exc}')
    lines = text.splitlines()
    start = 0
    if find_header:  # UI exports put a report title and date range above the header
        for i, line in enumerate(lines):
            cells = {c.strip().strip('"').casefold() for c in re.split(r'[\t,]', line)}
            if 'campaign' in cells and 'ad group' in cells:
                start = i
                break
    body = '\n'.join(lines[start:])
    delimiter = '\t' if lines[start:] and lines[start].count('\t') > lines[start].count(',') else ','
    canonical = {c.casefold(): c for c in KNOWN_COLUMNS}
    try:
        reader = csv.DictReader(io.StringIO(body), delimiter=delimiter, strict=True)
        fields = [f.strip() for f in (reader.fieldnames or [])]
        fields = [canonical.get(f.casefold(), f) for f in fields]
        if (not fields or any(not f for f in fields)
                or len({f.casefold() for f in fields}) != len(fields)):
            error(f'{path}: expected nonempty, unique column names')
        reader.fieldnames = fields
        rows = list(reader)
    except csv.Error as exc:
        error(f'{path}: {exc}')
    if find_header:  # report footers ("Total: Account") can be narrower than the header
        rows = [r for r in rows if not str(r.get(fields[0]) or '').strip().casefold().startswith('total')]
    # An unquoted comma shifts every later asset; never validate a shifted row.
    for i, r in enumerate(rows, start=start + 2):
        if None in r or any(v is None for v in r.values()):
            error(f'{path} row {i} does not match the header width; quote fields that contain commas')
    return fields, rows


def _key(r):
    return (r['Campaign'].strip().casefold(), r['Ad Group'].strip().casefold())


# Serving or policy states of an enabled ad. Ads whose campaign or ad group is
# paused still count toward the per-ad-group limit.
_ENABLED = ('enabled', 'active', 'eligible', 'approved', 'under review', 'disapproved',
            'limited', 'campaign paused', 'ad group paused', 'not eligible')
_KNOWN_STATES = _ENABLED + ('paused', 'removed', 'disabled')


def _existing_enabled(path, error):
    fields, rows = _read_csv(path, error, find_header=True)
    lower = {f.casefold(): f for f in fields}
    # Prefer the serving state over a policy "Status" (Approved, Disapproved) when both exist.
    status = next((lower[c] for c in ('ad status', 'ad state', 'status') if c in lower), None)
    missing = [c for c in ('Campaign', 'Ad Group') if c not in fields] + ([] if status else ['Status'])
    if missing:
        error(f'{path}: missing {", ".join(missing)}')
    ad_type = lower.get('ad type')
    counts, recognized, rsas = {}, 0, 0
    for r in rows:
        if not r['Campaign'].strip():
            continue
        if ad_type and 'responsive search' not in r[ad_type].casefold():
            continue
        rsas += 1
        state = r[status].strip().casefold()
        recognized += state.startswith(_KNOWN_STATES)
        if state.startswith(_ENABLED):
            counts[_key(r)] = counts.get(_key(r), 0) + 1
    if rsas and not recognized:
        error(f'{path}: column {status!r} has no Enabled/Paused/Removed values, so enabled ads '
              'cannot be counted; export the ad status column')
    return counts


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='Validate RSA rows in a Google Ads Editor CSV.')
    ap.add_argument('csv_file')
    ap.add_argument('--existing', help='export of current ads (Campaign, Ad Group, Status, '
                                       'optional Ad type) to check the enabled-RSA limit')
    ap.add_argument('--edits', action='store_true',
                    help='review file of in-place edits to existing ads: requires Ad ID, '
                         'skips the new-ad Paused rule')
    ap.add_argument('--counts', action='store_true', help="print every asset's display length")
    a = ap.parse_args(argv)
    fields, rows = _read_csv(a.csv_file, ap.error)
    unknown = [f for f in fields if _ASSET.match(f) and f not in ASSET_COLUMNS]
    if unknown:
        ap.error(f'unrecognized asset columns: {", ".join(unknown)}; use Headline 1-15, '
                 'Description 1-4, their "position" columns, Path 1 and Path 2')
    if not rows:
        ap.error('no RSA rows found')
    missing = [f for f in REQUIRED_COLUMNS + (['Ad ID'] if a.edits else []) if f not in fields]
    if missing:
        ap.error(f'missing required columns: {", ".join(missing)}')
    existing = _existing_enabled(a.existing, ap.error) if a.existing else None

    bad = 0
    new_per_group = {}
    seen_ids = {}
    for i, r in enumerate(rows, start=2):
        H = [r.get(h) for h in HEADLINES]
        D = [r.get(d) for d in DESCRIPTIONS]
        HP = [r.get(f'{h} position') for h in HEADLINES]
        DP = [r.get(f'{d} position') for d in DESCRIPTIONS]
        problems, notes = validate(H, D, r.get('Path 1', ''), r.get('Path 2', ''), HP, DP)
        required = ['Campaign', 'Ad Group', 'Final URL'] + (['Ad ID'] if a.edits else [])
        problems += [f'blank {f}' for f in required if not r[f].strip()]
        url = r['Final URL'].strip()
        if url and not re.match(r'https?://', url, re.I):
            problems.append(f'final URL {url!r} must start with http:// or https://')
        if r['Ad type'].strip().casefold() != 'responsive search ad':
            problems.append(f"ad type {r['Ad type']!r} (expected Responsive search ad)")
        ad_id = (r.get('Ad ID') or '').strip()
        if a.edits:
            if r['Status'].strip().casefold() == 'removed':
                problems.append('status Removed: a removed ad cannot be edited')
            if ad_id and ad_id in seen_ids:
                problems.append(f'Ad ID {ad_id} repeats row {seen_ids[ad_id]}')
            seen_ids.setdefault(ad_id, i)
            if ad_id and not ad_id.isdigit():
                notes.append(f'Ad ID {ad_id!r} is a label, not an ID; get the real ID before applying')
        else:
            if ad_id:
                problems.append('Ad ID filled in an upload row: new ads have no ID; '
                                'put edits in the review file and run --edits')
            if r['Status'].strip().casefold() != 'paused':
                problems.append(f"status {r['Status']!r} (new RSAs upload Paused)")
            new_per_group[_key(r)] = new_per_group.get(_key(r), 0) + 1
        where = f"row {i} ({r.get('Campaign', '')} / {r.get('Ad Group', '')})"
        if a.counts:
            for f in HEADLINES + DESCRIPTIONS + ['Path 1', 'Path 2']:
                if not _blank(r.get(f)):
                    print(f'{where}: count {f}: {display_len(r[f])} | {r[f]}')
        for p in problems:
            print(f'{where}: PROBLEM {p}')
        for n in notes:
            print(f'{where}: note {n}')
        bad += bool(problems)

    for (camp, group), new in sorted(new_per_group.items()):
        if existing is not None:
            have = existing.get((camp, group), 0)
            if have + new > MAX_ENABLED_RSAS:
                print(f'{camp} / {group}: note {have} enabled + {new} new = {have + new} RSAs; '
                      f'only {MAX_ENABLED_RSAS} can be enabled, so decide which to pause or edit')
        elif new > MAX_ENABLED_RSAS:
            print(f'{camp} / {group}: note {new} new RSAs; only {MAX_ENABLED_RSAS} can be enabled')
    if existing is None and not a.edits:
        print('enabled-RSA limit not checked against current ads (pass --existing to check)')
    print(f'{len(rows)} RSAs checked, {bad} with problems')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
