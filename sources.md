# Sources & basis

This skill is the public version of TNT Growth's internal RSA copy workflow, aligned with our approved Google Ads method (release `2026-10-14.1`, written by Adam Treboutat). Notes on its claims so they're defensible.

## A full set is the working standard, not a platform rule
Google requires 3 to 15 headlines and 2 to 4 descriptions. The skill aims for 15 and 4 because a full set of distinct, truthful assets gives the system more useful combinations and forces the writer through capabilities, proof, objections and qualifiers. It is an operating standard: fewer is fine with a stated reason, and padding is never fine.

## Ad Strength is not the goal
Google says Ad Strength is not an input to Ad Rank or Quality Score. In Adam Treboutat's published analysis of 3,900 Google ads across 65 accounts, Ad Strength had essentially no correlation with within-account CPA rank (r = 0.002) ([the study](https://www.linkedin.com/feed/update/urn:li:activity:7490761101337350144/)). That is an observational result from those accounts, not proof that Ad Strength never matters, so the skill reads its suggestions as hints about omissions.

## Pins are a tradeoff
Pinning restricts combinations. The skill pins only for a named message that must always show and treats that as a deliberate tradeoff, not as proof of higher or lower cost. Interactions with Final URL expansion, URL inclusions and campaign text disclaimer assets follow Google's documentation as of October 2026.

## Claims need sources
Any number, price, guarantee, comparison or superlative needs a source. A claim that appears in a brief without one is left out and listed, following Google's unreliable-claims policy and basic honesty with buyers.

## Platform facts
Character limits, double-width counting, pinning behavior, asset flexibility, keyword insertion, the three-enabled-RSA limit and reporting changes link to Google's documentation and were checked in October 2026. The upload column names were checked against the field names in Google Ads Editor 14.12 (November 2026); Google doesn't publish an Editor column reference for RSA pins, and the pin values (`1`, `2`, `3`) weren't confirmed against an Editor export, so `references/output-spec.md` says how to check before a large import. Google changes the platform often; re-verify before a decision depends on one. The validator encodes the limits as of these dates.

## What this skill deliberately does not claim
- No client names or client results. Worked examples and test fixtures are fictional.
- No CTR, conversion-rate or CPA improvement projection.
- No claim that two RSAs in one ad group are a controlled test.
- Recommendations aren't account changes. It makes none.
