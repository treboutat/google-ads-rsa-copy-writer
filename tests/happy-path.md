# Test: complete RSA build for a new ad group

## Input

Fictional scheduling software for clinics, "Slotwise". Campaign `Search - Scheduling`, ad group `Clinic Scheduling Software`, keywords around clinic scheduling software, patient booking software and appointment scheduling for clinics. Plans start at $500/month, confirmed on the pricing page. Real capabilities: online booking, automated reminders by text and email, waitlist fill, EHR integrations with two named systems. Proof with sources: 4.7 rating from 310 reviews on a public review site, HIPAA-compliant hosting confirmed on the security page. An old brief also claims a "92% response rate" with no source. Final URL `https://slotwise.example/clinics`; the page offers a free 14-day trial and a demo booking. No existing ads.

## Expected output

- Two RSAs with different angles (for example price and plan fit versus no-shows and proof), each with 15 distinct truthful headlines and four descriptions, or a stated reason for fewer.
- The 92% claim left out and listed in the Summary with the evidence that would allow it.
- "Free" only in a form that carries the 14-day condition, or kept off assets where the condition could disappear.
- The $500 price floor used as a deliberate qualifier; a pin is acceptable if the business wants every searcher to see it, with the reason recorded.
- Review file (Summary, RSA Copy, QA) and `rsa_upload.csv` with both rows Paused, validated by `scripts/validate_rsa.py`.

## Validation

- [ ] Field limits, duplicates and pins checked by the script; any notes carried into QA.
- [ ] No 4/8/3 split, no required keyword insertion or location insertion, no short-headline quota, no blanket no-pin or always-pin rule.
- [ ] Every permitted combination stays accurate: no two CTAs fighting, no price next to an unqualified "Free".
- [ ] Ad Strength is not used as the reason for any choice.
- [ ] CTAs match the page (trial and demo both exist), and CTAs across the two RSAs still make sense when their assets combine.
- [ ] Plain feature descriptions from the business's brief are cited as such, not stripped; only objective claims without a source are left out.
