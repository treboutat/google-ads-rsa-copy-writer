"""Validate Google Ads responsive search ad (RSA) fields, pins and ad counts.

    python3 validate_rsa.py rsa_upload.csv
    python3 validate_rsa.py rsa_upload.csv --existing current_ads.csv --counts
    python3 validate_rsa.py rsa_edits.csv --edits

    from validate_rsa import validate, display_len
    problems, notes = validate(headlines, descriptions, path1, path2,
                               headline_pins=[...], description_pins=[...])

Problems break the upload and make the command exit 1. Notes need a human
decision (a pin that needs a stated reason, an ad group over the enabled-RSA
limit, a dynamic token to check by hand) and never change the exit code.

Checks:
- 3-15 headlines up to 30 characters; 2-4 descriptions up to 90; paths up to 15.
  Double-width characters count twice, as Google counts them. Keyword insertion
  ({KeyWord:Fallback}) is measured on its fallback text. Other dynamic tokens
  ({LOCATION(City)}, {CUSTOMIZER...}, {COUNTDOWN...}) are noted for a manual check.
- No blank or case-insensitive duplicate assets; Path 2 needs Path 1.
- Pins: headline positions 1-3, description positions 1-2, no position on a blank
  asset, and Headline 1, Headline 2 and Description 1 can always be filled.
  Dual pinning of H1 and H2, and pins at H3 or D2 (positions that do not always
  show), are noted so the review records why.
- Upload rows: Paused "Responsive search ad" rows with a campaign, ad group and
  an http(s) final URL. With --edits (in-place edits to existing ads, which keep
  their current status) the Paused rule is skipped; every other check applies.
- With --counts: every asset's display length, for the review file.
- With --existing: enabled RSAs already in each ad group plus the new rows,
  against Google's limit of three enabled RSAs per ad group.

Malformed CSV, duplicate or empty column names, unrecognized asset columns,
missing required columns and rows wider or narrower than the header are input
errors (exit 2).
"""
import re
import unicodedata

_DKI = re.compile(r'\{keyword:([^}]*)\}', re.I)
_OTHER = re.compile(r'\{(?!keyword:)[^}]*\}', re.I)
_ASSET = re.compile(r'^(headline|description|path)\b', re.I)
HEADLINES = [f'Headline {n}' for n in range(1, 16)]
DESCRIPTIONS = [f'Description {n}' for n in range(1, 5)]
ASSET_COLUMNS = (set(HEADLINES) | {f'{h} position' for h in HEADLINES}
                 | set(DESCRIPTIONS) | {f'{d} position' for d in DESCRIPTIONS}
                 | {'Path 1', 'Path 2'})
REQUIRED_COLUMNS = ['Campaign', 'Ad group', 'Ad type', 'Headline 1', 'Headline 2', 'Headline 3',
                    'Description 1', 'Description 2', 'Final URL', 'Status']
MAX_ENABLED_RSAS = 3


def display_len(text):
    text = _DKI.sub(lambda m: m.group(1), str(text))
    return sum(2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1 for ch in text)


def _blank(x):
    return x is None or x != x or not str(x).strip()  # x != x: NaN from an empty sheet cell


def _pin(value, allowed, label, problems):
    """Return the pinned position as an int, None when unpinned."""
    if _blank(value):
        return None
    raw = str(value).strip().upper().lstrip('HD')
    try:
        pos = int(float(raw))
    except ValueError:
        problems.append(f'{label} position {value!r} is not a number')
        return None
    if pos not in allowed:
        problems.append(f'{label} position {pos} (allowed: {", ".join(map(str, allowed))})')
        return None
    return pos


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
    problems += [f'headline >30: {h} ({display_len(h)})' for h in hs if display_len(h) > 30]
    problems += [f'description >90: {d} ({display_len(d)})' for d in ds if display_len(d) > 90]
    problems += [f'path >15: {p} ({display_len(p)})' for p in (p1, p2) if display_len(p) > 15]
    if p2 and not p1:
        problems.append('Path 2 without Path 1')
    problems += [f'empty keyword-insertion fallback: {x}' for x in hs + ds
                 if any(not m.group(1).strip() for m in _DKI.finditer(x))]
    notes += [f'dynamic token needs a manual length and rendering check: {x}'
              for x in hs + ds if _OTHER.search(x)]

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


def _read_csv(path, error):
    import csv
    try:
        with open(path, newline='', encoding='utf-8-sig') as fh:
            reader = csv.DictReader(fh, strict=True)
            fields = [f.strip() for f in (reader.fieldnames or [])]
            if (not fields or any(not f for f in fields)
                    or len({f.casefold() for f in fields}) != len(fields)):
                error(f'{path}: expected nonempty, unique CSV column names')
            reader.fieldnames = fields
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        error(f'{path}: {exc}')
    # An unquoted comma shifts every later asset; never validate a shifted row.
    for i, r in enumerate(rows, start=2):
        if None in r or any(v is None for v in r.values()):
            error(f'{path} row {i} does not match the header width; quote fields that contain commas')
    return fields, rows


def _key(r):
    return (r['Campaign'].strip().casefold(), r['Ad group'].strip().casefold())


def _existing_enabled(path, error):
    fields, rows = _read_csv(path, error)
    status = next((f for f in ('Status', 'Ad status', 'Ad state') if f in fields), None)
    missing = [f for f in ('Campaign', 'Ad group') if f not in fields] + ([] if status else ['Status'])
    if missing:
        error(f'{path}: missing {", ".join(missing)}')
    counts = {}
    for r in rows:
        if 'Ad type' in fields and 'responsive search' not in r['Ad type'].casefold():
            continue
        if r[status].strip().casefold() in ('enabled', 'active', 'eligible'):
            counts[_key(r)] = counts.get(_key(r), 0) + 1
    return counts


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='Validate RSA rows in a Google Ads Editor CSV.')
    ap.add_argument('csv_file')
    ap.add_argument('--existing', help='export of current ads (Campaign, Ad group, Status, '
                                       'optional Ad type) to check the enabled-RSA limit')
    ap.add_argument('--edits', action='store_true',
                    help='rows are in-place edits to existing ads: skip the new-ad Paused rule')
    ap.add_argument('--counts', action='store_true', help="print every asset's display length")
    a = ap.parse_args(argv)
    fields, rows = _read_csv(a.csv_file, ap.error)
    unknown = [f for f in fields if _ASSET.match(f) and f not in ASSET_COLUMNS]
    if unknown:
        ap.error(f'unrecognized asset columns: {", ".join(unknown)}; use Headline 1-15, '
                 'Description 1-4, their "position" columns, Path 1 and Path 2')
    if not rows:
        ap.error('no RSA rows found')
    missing = [f for f in REQUIRED_COLUMNS if f not in fields]
    if missing:
        ap.error(f'not an importable RSA upload: missing {", ".join(missing)}')
    existing = _existing_enabled(a.existing, ap.error) if a.existing else None

    bad = 0
    new_per_group = {}
    for i, r in enumerate(rows, start=2):
        H = [r.get(h) for h in HEADLINES]
        D = [r.get(d) for d in DESCRIPTIONS]
        HP = [r.get(f'{h} position') for h in HEADLINES]
        DP = [r.get(f'{d} position') for d in DESCRIPTIONS]
        problems, notes = validate(H, D, r.get('Path 1', ''), r.get('Path 2', ''), HP, DP)
        problems += [f'blank {f}' for f in ('Campaign', 'Ad group', 'Final URL') if not r[f].strip()]
        url = r['Final URL'].strip()
        if url and not re.match(r'https?://', url, re.I):
            problems.append(f'final URL {url!r} must start with http:// or https://')
        if r['Ad type'].strip().casefold() != 'responsive search ad':
            problems.append(f"ad type {r['Ad type']!r} (expected Responsive search ad)")
        if not a.edits and r['Status'].strip().casefold() != 'paused':
            problems.append(f"status {r['Status']!r} (new RSAs upload Paused)")
        if not a.edits:
            new_per_group[_key(r)] = new_per_group.get(_key(r), 0) + 1
        where = f"row {i} ({r.get('Campaign', '')} / {r.get('Ad group', '')})"
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
