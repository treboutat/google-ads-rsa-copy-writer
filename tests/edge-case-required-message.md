# Test: required qualifier, disclaimer asset and Final URL expansion

## Input

Fictional lender. Every ad must show "Loans from $10,000. Subject to credit approval." The user's draft pins that line to Description 1. The campaign also has an approved text disclaimer asset, and Final URL expansion is on. A second RSA in the same ad group says "Instant approval, no credit check."

## Expected decisions

- Identify that the approved disclaimer replaces pinned Description 1, so the pin alone does not protect the qualifier; resolve both messages (for example move the qualifier into the disclaimer text or a supported position) and never delete the disclaimer to make room.
- Note that Google's pin-retaining setup turns off Final URL expansion and URL inclusions; flag the conflict rather than switching off unrelated features.
- Flag "Instant approval, no credit check" as incompatible with the required qualifier and as an unsupported claim; revise it.
- Do not offer H3 or D2 as always-visible positions.
- When the fix lives in the disclaimer asset, hand it to the asset and compliance owner, keep the pin as a fallback and hold activation of the affected ads.
- Keep plain product descriptions the business states (online application, fixed payments) instead of stripping them as unsupported; write toward a full set from buyer needs, uses and objections.
- Keep useful pins even if Ad Strength drops.

## Failure cases

Declaring the setup complete from a preview, removing the qualifier to raise Ad Strength, or claiming pins always raise CPC.
