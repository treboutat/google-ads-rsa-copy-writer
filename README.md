# Google Ads RSA Copy Writer

A Claude skill that writes Google Ads responsive search ads. Give it your offer, keyword themes and landing pages and get back two RSAs per ad group, normally with 15 headlines and four descriptions each, every claim traced to a source, pins only where a message must always show, and a Google Ads Editor upload file with everything paused.

It writes copy for the buyer you want, not for an Ad Strength grade. It never changes the account.

## Who it's for
Anyone writing or refreshing Search ads: a new campaign that needs copy, ad groups stuck on one thin RSA, or ads full of claims nobody can source. It works for a brand-new account and for a refresh of ads that already run.

## Install

**As a Claude Code skill:**
```bash
mkdir -p ~/.claude/skills/google-ads-rsa-copy-writer
cp SKILL.md ~/.claude/skills/google-ads-rsa-copy-writer/SKILL.md
cp -r references scripts ~/.claude/skills/google-ads-rsa-copy-writer/
```
Then say "write RSAs for these ad groups" and share the context below. The validator needs only Python 3.

**In Claude.ai:** zip this folder and upload it as a custom skill in Claude's skills settings, or add `SKILL.md` and `references/method-rules.md` to a project.

**As a plain SOP:** read `SKILL.md` and `references/method-rules.md`. They are a complete procedure even if you never run them through Claude.

## What you provide
1. The campaigns and ad groups with their keyword themes (search terms that triggered the ads help even more).
2. The offer: what you sell, to whom, the price or starting price, where you deliver, and what you don't do.
3. Proof you can source: reviews, certifications, guarantees, customer counts.
4. Messages every searcher must see: disclosures, legal lines, real qualifiers like a price floor.
5. The landing page for each ad group.
6. For a refresh: an export of current ads with text, pins, status and URLs.

It works with partial context, writes what it can, and lists what it couldn't support.

## What you get
- **Review file:** a Summary per ad group (what changes, each RSA's angle, claims left out and why, required messages and how they're protected, open dependencies), an RSA Copy tab with every asset, its character count, pin and source, and a QA tab with the checks actually run.
- **`rsa_upload.csv`:** new RSAs only, Paused, in Google Ads Editor's column layout, checked by `scripts/validate_rsa.py`. Edits to existing ads are listed for an in-place change so the ad keeps its ID and history.

## How it writes
- A full set of useful assets is the normal standard: 15 headlines and four descriptions, or a stated reason for fewer. No padding, no invented proof.
- No quotas: no fixed headline-type split, no required keyword insertion, no short-headline count.
- Unpinned by default; pins only for a named required message, with Google's settings that can override a pin (Final URL expansion, campaign text disclaimers) checked first.
- No keyword insertion in competitor or trademark ad groups, no implied affiliation, and "near you" only where you actually serve.
- Success is judged on customer cost, quality and volume after your conversion lag. Ad Strength is a hint about omissions, not a performance score.

## Files
- `SKILL.md`: the workflow
- `references/method-rules.md`: the judgment rules, with links to Google's documentation
- `references/output-spec.md`: the review file and the Editor upload layout
- `scripts/validate_rsa.py`: character limits (including double-width characters and keyword-insertion fallbacks), duplicates, paths, pin positions and fill, upload-row checks, and the three-enabled-RSAs limit against your current ads (`--existing`). `--counts` prints every asset's length; `--edits` checks in-place edits to existing ads
- `tests/`: a worked example and edge cases (competitor ad group, required qualifier with a disclaimer asset, refreshing a working ad), plus unit tests for the validator (`python3 -m unittest discover -s tests/scripts`)

## Related skills
- [Google Ads Gap Analysis](https://github.com/treboutat/google-ads-gap-analysis): find search terms worth adding as keywords, then use this skill to write their ads.
- [Google Ads Search Term Scorer](https://github.com/treboutat/google-ads-search-term-scorer) and [Google Ads Account Audit](https://github.com/treboutat/google-ads-account-audit).

---
From [TNT Growth](https://tntgrowth.com/skills?utm_source=github&utm_campaign=treboutat). Use it, fork it, adapt it to your account.
