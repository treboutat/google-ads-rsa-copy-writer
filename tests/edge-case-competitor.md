# Test: competitor ad group

## Input

Same fictional advertiser. The approved structure has an ad group `Competitor - Bookwell` with keywords naming a competitor scheduling brand. Two comparison pages exist, one per competitor, and are set as keyword-level final URLs. The user asks for "punchy copy, use keyword insertion so it matches the search".

## Expected decisions

- No keyword insertion in this ad group: it would put the competitor's name in the advertiser's headline. Explain that plainly and offer copy that names the advertiser.
- Copy makes the advertiser's identity clear and does not imply affiliation with the competitor.
- No superiority or comparison claim without a source; any deliberate comparison is flagged for a policy check, without claiming that naming a competitor is always illegal.
- Shared copy across the competitor keywords is acceptable with the keyword-level comparison URLs; no extra campaign split just for destinations.
- Notes that other assets in the group may not follow the keyword-level URL.

## Failure cases

Keyword insertion in the competitor group, "#1 alternative to Bookwell" without a source, a made-up legal rule, or splitting the group only to change destinations.
