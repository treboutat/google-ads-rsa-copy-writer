---
name: google-ads-rsa-copy-writer
description: "Write or refresh Google Ads responsive search ads (RSAs): full sets of truthful headlines and descriptions built from the real offer, buyer and landing page, deliberate pins only for required messages, character-validated fields and a paused Google Ads Editor upload file. Use for Google Ads ad copy, RSA builds, new headlines and descriptions, ad copy refreshes and RSA reviews. Read-only: it never changes the account. Not for keyword structure, negative keywords, sitelinks or other assets, bidding or full account audits."
metadata:
  author: TNT Growth
  version: "1.0.0"
  method-release: "2026-10-14.1"
---

# Google Ads RSA Copy Writer

Write the actual ads: two meaningfully different RSAs per ad group, each normally with 15 headlines and four descriptions, every objective claim traced to a source, pins only where a named message must always show, and a clean upload file with everything paused. Nothing is changed in the account. The deliverable is reviewable copy and an Editor-ready CSV.

## 0. Load the method

This file is the workflow. [references/method-rules.md](references/method-rules.md) holds the judgment rules (TNT Growth's Google Ads RSA method, release 2026-10-14.1); read it in full before drafting. [references/output-spec.md](references/output-spec.md) defines the review file and the upload file. If a reference is missing, say so in the Summary and do not claim it was applied.

Route neighbouring requests elsewhere:

- Which keywords or ad groups to build: keyword research and campaign structure come first. This skill writes copy for the structure you have.
- Sitelinks, callouts and other assets: a separate asset build. This skill only checks how campaign assets (especially text disclaimers) interact with the RSA.
- "Why did performance drop?", bidding and budgets, or a full audit: out of scope. Flag a copy-related cause if you see one and keep going.

## 1. Get the business context

Collect what changes the copy, in one message, and keep working on anything you can already write:

- **Scope.** The campaigns and ad groups, with their keyword themes. Search terms that actually triggered the ads help more than the keyword list alone.
- **The offer.** What is sold, to whom, at what price or starting price, where it is delivered, and what the business does not do.
- **Proof.** Facts you can cite: reviews, certifications, years in business, customer counts, guarantees. Each needs a source (a page, a document, an account fact). Ask for the source when a brief states a number without one.
- **Required messages.** Disclosures, legal or brand requirements, and qualifiers the business wants every searcher to see (a price floor, a minimum, an eligibility rule).
- **Landing pages.** The final URL for each ad group. Read the page if you can open it; the CTA has to match what the page offers.
- **Existing ads.** For a refresh: current RSAs with text, pins, status and final URLs (an Editor or UI export is fine), plus anything known to work. For a new build: say so.
- **Brand and competitor rules.** Brand spellings, words to avoid, and whether competitor keywords are in scope.

If no outcome data is available, write the copy anyway and say the judgment of which ad works waits for mature results.

## 2. Read the current state (refresh only)

For each ad group in scope, list the enabled and relevant paused RSAs, their pins, statuses and destinations, and any keyword-level or mobile URL overrides. Note account or campaign settings that can change what serves: Final URL expansion, URL inclusions, campaign text disclaimer assets and automatically created assets. Mark anything you cannot see as unknown rather than assuming it is off.

Diagnose concrete problems: unclear offer, unsupported claims, wrong buyer, missing qualifiers, repetition, combinations that contradict each other, a CTA that does not match the page. Keep working ads. Ad Strength is a hint about omissions, not a reason to replace an ad that is producing customers at an acceptable cost.

Decide per ad group whether to create, edit, keep or pause each RSA. Pause an ad when its core claim is false or unsupportable and most assets would change; otherwise prefer an in-place edit, which keeps the ad's ID and history. An edited existing ad counts as one of the two RSAs. If a live ad is missing a required message or makes a false claim, say so at the top of the Summary as something to act on now, not after the refresh. Count enabled RSAs: the limit is three per ad group.

## 3. Define the buying decision per ad group

Before writing, state in a line or two: the buyer's need, the offer, why it fits, what makes it credible, the qualifier (if any) and the next step. Ad groups whose searchers want different things get different messages; ad groups that serve the same need can share copy.

Pick two angles per ad group when the offer supports real variation, for example "price and plan fit" versus "outcome and proof". Do not invent a second landing page or a near-duplicate ad to reach two.

## 4. Write the assets

For each RSA, write 15 headlines (up to 30 characters) and four descriptions (up to 90), plus optional display paths (up to 15 each). Work through capabilities, outcomes, proof, qualifiers, objection answers and CTAs until the set is complete. Use fewer only for a stated reason; never pad with repetition or invented proof.

Rules that most often go wrong:

- Every asset must make sense alone and next to any other asset. Read the risky pairs: two CTAs, a price and "Free", a qualifier and a claim that contradicts it.
- An objective claim (number, rating, price, guarantee, speed or outcome promise, comparison, superlative) without a source stays out, even if it was in the brief. List it in the Summary with the evidence that would let it in. Plain descriptions of what the business offers can come from its own brief or site; cite that and keep writing. Specific terms the business states about its own offer (prices, loan or plan limits, terms, delivery times) can be used with the brief cited, but the ad must match the landing page, so confirming them on the page is a launch check. Results, ratings and comparisons need underlying evidence.
- Thin facts mean more angles, not fewer headlines: buyer problem, who it is for, use cases, objections, the qualifier, and each call to action the page supports.
- Assets from different RSAs in the same ad group can combine, so check CTAs and claims across the RSAs, not just within one.
- No quotas: no fixed headline-type split, no short-headline count, no required keyword insertion, no location insertion, no first-word rule.
- No keyword insertion in competitor or trademark ad groups. Never auto-insert a competitor's name, and never imply affiliation. In an ad group covering several competitors, keep competitor names out of the copy.
- "Near you" and location insertion only where the service is actually delivered locally.
- Keep the brand's real spelling and acronyms; avoid gimmicky capitalization.

## 5. Pin only what must always show

Leave everything unpinned when every combination is accurate. Pin when a named message must always appear: a required disclosure, a brand requirement or a truthful qualifier. Write the message each pin protects. Several alternatives can share a pinned position if every one carries the required message. Do not rely on H3 or D2 for required text, and treat pinning both H1 and H2 as an exception with a reason.

Before relying on a pin, check two settings: Final URL expansion and URL inclusions (Google's pin-retaining setup turns these off), and campaign text disclaimer assets (an approved disclaimer replaces pinned Description 1). If either applies, resolve both messages; never drop a required disclosure to make room for a qualifier.

## 6. Validate

Build `rsa_upload.csv` in the layout in [references/output-spec.md](references/output-spec.md) and run the validator from wherever this skill is installed:

```bash
python3 <skill-folder>/scripts/validate_rsa.py rsa_upload.csv --existing current_ads.csv --counts
```

- `--existing` takes an export of current ads (Campaign, Ad group, Ad type, Status). If the user pasted their ads instead, write that minimal CSV from what they gave. Omit it for a brand-new ad group and state the count (0 existing) in QA.
- `--counts` prints every asset's display length; use those numbers in the RSA Copy tab.
- Edits to existing ads don't go in the upload file. Put them in a second file in the same layout with their current status and run it with `--edits` so field and pin checks still apply.

Fix every PROBLEM line. Carry every note into the QA tab with the decision taken. The script needs only Python 3; no packages.

If you cannot run code, count characters per the rules (spaces and punctuation count, double-width characters count twice, keyword insertion counts its fallback) and say in the QA tab that the counts were checked by hand.

Then review what a script cannot: claims against sources, every risky combination, CTA against page, the other RSAs in the ad group (their assets can be borrowed), and the settings from step 5.

## 7. Deliver

Give the review file (Summary, RSA Copy, QA; markdown is fine in chat or Claude Code) and the clean upload file, as specified in [references/output-spec.md](references/output-spec.md). New ads are Paused. Edits to existing ads are listed for an in-place change so the ad ID and history stay.

End the Summary with how to judge the result: let the new ads run, then compare customer cost, quality and volume after the conversion lag, not Ad Strength or CTR alone. Two RSAs in one ad group are not a controlled test; use a Google Ads experiment if a causal answer matters.

Never claim the ads are live, approved or better performing. The skill writes and checks copy; launching and judging it are separate steps.
