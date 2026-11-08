# Output layout

Two outputs: a review file people read and annotate, and a clean upload file Google Ads Editor can import. Reviewer notes never go in the upload file.

In a chat without file tools, show the review as tables and give the upload file as a CSV code block. With file tools, write the review as `rsa_review.md`, `rsa_review.xlsx` or one CSV per tab (whichever the user prefers; markdown is the default), plus `rsa_upload.csv`.

## Review file

### Summary tab

One short block per ad group:

- What changes: new RSAs, edits to existing ads, ads kept as they are.
- The buyer and the angle of each RSA, in one line each.
- Claims left out for lack of support, and what evidence would let them in.
- Required messages and how each is protected (pin, disclaimer asset, or none needed).
- Open dependencies that block launch, with the person or fact that resolves them.
- The review question for after launch and when to judge it (after the conversion lag).

### RSA Copy tab

One row per asset, so counts and notes stay readable.

| Column | Content |
|---|---|
| Campaign | Exact campaign name (or ID) |
| Ad group | Exact ad-group name (or ID) |
| RSA | `RSA A`, `RSA B` for new ads; the Ad ID for an existing ad |
| Action | `Create`, `Edit`, `Keep` or `Pause` |
| Proposed status | `Paused` for new ads; current status for edits and keeps |
| Angle | The buying reason this RSA leads with |
| Field | `Headline 1` to `Headline 15`, `Description 1` to `Description 4`, `Path 1`, `Path 2` |
| Text | The asset text exactly as it will upload; for a removed asset, the old text with `Remove` in Notes |
| Characters | Display length (double-width characters count twice; keyword insertion counted on its fallback) |
| Pin | Blank, or the position (`H1`, `H2`, `H3`, `D1`, `D2`) |
| Pin reason | The named message the pin protects; blank when unpinned |
| Claim source | URL, document or account fact behind an objective claim; `Business brief` or the page for plain descriptions of the offer |
| Final URL | Ad final URL |
| Notes | Mobile or keyword-level URLs, tracking, dynamic settings, reviewer comments |

### QA tab

One row per check actually run, with the result and what it covered:

- Field limits and duplicates: output of `scripts/validate_rsa.py`.
- Pins: every required position can fill; dual pins and H3/D2 pins have a stated reason.
- Claims: every number, price, guarantee, comparison and superlative has a source; unsupported ones are listed as removed.
- Combinations: no permitted pairing contradicts itself, repeats a CTA, drops a required qualifier or mixes audiences. Name the risky pairs you checked.
- Destinations: CTA matches the page; keyword-level and mobile URLs noted; other RSAs in the group checked because their assets can be borrowed.
- Ad count: existing enabled RSAs plus new ones per ad group, against the limit of three enabled.
- Settings that can override the copy: Final URL expansion, URL inclusions, campaign text disclaimers, automatically created assets. Mark each as checked, not applicable, or unknown.

Ad Strength, keyword-insertion count and short-headline count are not pass/fail rows.

## Upload file (`rsa_upload.csv`)

New RSAs only, one row per ad, every row `Paused`. Apply edits to an existing ad in place (UI, Editor or API) so its ad ID and history stay; list them in the review file instead.

Columns, in this order (leave unused asset and position cells blank):

```
Campaign, Ad group, Ad type, Status,
Headline 1 … Headline 15,
Headline 1 position … Headline 15 position,
Description 1 … Description 4,
Description 1 position … Description 4 position,
Path 1, Path 2, Final URL, Mobile final URL, Tracking template, Final URL suffix
```

- `Ad type` is `Responsive search ad`.
- Position cells hold `1`, `2` or `3` for headlines and `1` or `2` for descriptions; blank means unpinned.
- Quote any field containing a comma.
- Column names follow Google Ads Editor's RSA columns as of October 2026. Before a large import, export one existing RSA from Editor and compare headers; if Editor has renamed a column, rename it here and in `scripts/validate_rsa.py` together.

Run `python3 <skill-folder>/scripts/validate_rsa.py rsa_upload.csv --counts` before handing the file over. Add `--existing current_ads.csv` (an export of current ads with Campaign, Ad group, Ad type and Status, or a minimal CSV written from ads the user pasted) to check the three-enabled limit per ad group.

Edits to existing ads go in a separate file (`rsa_edits.csv`) in the same layout plus an `Ad ID` column, with the full new asset set, current status and existing final URL. List removed assets in the review file. Run it with `--edits`, which applies the field and pin checks but not the new-ad rules (Paused status).
