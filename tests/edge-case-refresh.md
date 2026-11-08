# Test: refresh an account with a working ad

## Input

Fictional plumbing company serving three named counties from one office. Existing ad group has two enabled RSAs: RSA 1 has 9 headlines and 2 descriptions and produces booked jobs at an acceptable cost; RSA 2 has 15 headlines, "Excellent" Ad Strength, and a higher cost per booked job. RSA 1 uses `{LOCATION(City)}` in a headline and says "Plumbers Near You". The user asks to "fix the ad strength on RSA 1 and add a third ad".

## Expected decisions

- Keep RSA 1 working: propose an in-place edit that adds truthful headlines and descriptions toward 15 and 4, not a replacement, and say the edit keeps its ad ID and history.
- Flag location insertion and "near you": acceptable only for the three counties actually served; city insertion can name towns outside the area.
- Do not treat RSA 2's Excellent grade as evidence it is better; the cost per booked job says otherwise.
- Count enabled RSAs: two existing plus one new is three, at the limit; say so.
- Judge the result on booked jobs after the conversion lag, not Ad Strength.

## Failure cases

Pausing RSA 1 for its grade, adding assets only to raise Ad Strength, or calling the two RSAs a controlled test.
