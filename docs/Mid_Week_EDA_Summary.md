# Mid-Week EDA Summary

Consolidated view of findings across all 5 tracks, after both the initial exploratory pass and a deeper follow-up pass on every track. Full detail, decisions, and open questions for each track live in `Track_A` through `Track_E_Findings_Report.md` — this is the condensed version for a quick group read.

**Status note:** this summary reflects a full two-pass exploration across all five tracks. Every notebook has been run end-to-end and verified error-free; every surprising number has been cross-checked against an independent baseline before being reported. Once the team has worked through their own tracks directly, revisit this document and fold in anything new.

**Update since this summary was written:** `analysis_master.csv` (the full cross-track join) has since been built and independently verified — every headline number below (delay/review-score buckets, the March 2018 spike/dip, the 646-order review gap) reproduces exactly from the merged file, confirming none of these findings were an artifact of a single track's isolated processing. See `data_dictionary.md` §7 for the finalized schema. The project has since moved from an analysis phase into an explanatory-visualization phase — this document's numbers remain the reference set of "what to visualize," but chart-building itself is now the active work, not further analysis.

---

## The central story, now cross-validated across independently-built tracks

**Delivery delay predicts review score — and the mechanism is now understood, not just correlated:**

| Delay bucket | Mean review score |
|---|---|
| 5+ days early | 4.32 |
| On-time/early | 4.20 |
| 1–3 days late | 3.77 |
| 4–7 days late | 2.32 |
| 8+ days late | 1.73 |

Digging one level deeper: **transport time (carrier-side) is a stronger predictor of an individual order's review score than processing time (seller-side)** — 0.82-point spread vs. 0.43-point spread across quintiles, and the single strongest correlate overall (−0.299, edging out total delay itself at −0.267). But at the **seller** level, processing time is the stronger signal for *which sellers* are reliably good (−0.449 vs. −0.296) — the two findings answer different questions and both belong in the final report.

**Independent cross-track validation:** Track A (built first, in isolation) found an unexplained late-rate spike in **March 2018 (20.7%, vs. ~5% typical)**. Track D (built later, also testing independently) found March 2018 has the **lowest review score of any regular month (3.75)**. Two separately-built tracks landing on the same real-world event is strong evidence this is a genuine signal, not a data artifact — even though the underlying cause of March 2018's operational trouble is still unexplained.

---

## Track A — Payments & Order Funnel
- Order funnel is clean (97% delivered); delivery estimates are heavily padded (median ~12 days early, only 8.1% actually late).
- **Growth vs. quality, not flat:** volume grew steadily through 2017–2018, but late rate spiked at real points — **Nov 2017 (13.8%, plausibly Black Friday)** and **March 2018 (20.7%, still unexplained)**. Strong candidate anchor chart for the final presentation.
- Boleto payments take ~29 hours to approve (vs. under 1 hour for cards) — a real but well-explained difference (inherent to the payment method).
- Voucher orders cancel at 5-6x other types; narrowed to "different customer profile" over "redemption failure" (lower order value, no geographic pattern), but not fully resolved.
- Payment type, installments, and split-payment status all ruled out as lateness predictors.

## Track B — Products & Categories
- 74 categories, long-tailed; needs top-N or small-multiples for any chart.
- Physical size genuinely drives freight cost (weight/volume correlate with freight at ~0.6); photo count doesn't relate to price (ruled out).
- Category-level cancellation varies modestly (0.19%–0.80% among top categories).
- **Three categories are declining despite overall marketplace growth**: `market_place` (−15.8%), `toys` (−5.1%), `consoles_games` (−4.1%) — a real "growth isn't reaching everywhere" signal.
- Freight burden is heavily concentrated: `home_comfort_2` and `flowers` carry freight at 44–54% of item price.

## Track C — Sellers & Delivery Logistics
- Geolocation deduplicated (1M → 19,011 zip-level rows); small-sample seller trap identified and flagged (`low_confidence`, 42% of sellers).
- Seller size doesn't predict lateness (confirmed twice — bucketed and continuous).
- **A teammate's contributed extension had 3 real structural bugs** (repeated variable names silently overwriting each other), fully rewritten and fixed — now produces working same-state/cross-state, distance, and seller×route analysis.
- Cross-state delivery nearly doubles both delivery time (15.1 vs. 7.9 days) and late rate (8.96% vs. 5.86%) versus same-state.
- Specific seller×destination-state routes identified with severe problems (one at 62.5% late, 35-day average delivery).
- Top 10% of sellers handle 68.4% of all orders — marketplace performance is concentrated in a small group.

## Track D — Customers & Reviews
- Review scores are bimodal (57.8% five-star, 11.5% one-star).
- **The review-gap selection bias is now resolved, not just flagged**: two independent checks rule out "not enough time yet" — the 646 missing reviews are genuine non-response, concentrated where satisfaction was worst.
- Only 3.1% of customers ever place a second order; repeat customers had a measurably better first-order delivery experience (6.4% vs. 7.9% late).
- Freight burden does **not** meaningfully hurt satisfaction on its own (nearly flat across freight-ratio quintiles) — an important nuance against Track B's freight-burden finding.
- **Having a comment is a strong dissatisfaction signal** (3.70 vs. 4.38 average score) — a cheap proxy worth surfacing directly, discovered in this pass.
- Full driver ranking built: transport time > total delay > processing time > everything else (category, distance, freight ratio all secondary).

## Track E — Marketing Funnel + Integration
- Overall conversion: 10.5%; `email`/`social` channels underperform despite decent volume.
- Two-sided overlap finding confirmed: only 12.3% of active sellers have funnel records, only 45.1% of "won" deals become active sellers — funnel data stays a standalone story.
- **Conversion efficiency improved dramatically as volume grew** (under 1% → 13-14%) — the opposite pattern from Track A's operational dips, a genuine and useful contrast for the final narrative.
- Declared signup attributes (`lead_type`, `business_type`) genuinely predict real future seller performance — a closing-the-loop finding.
- The uninterpreted `lead_behaviour_profile` tag correlates with real outcomes despite its meaning being unknown.

---

## Data quality and process patterns worth the whole team knowing
- **Never open a raw CSV in Excel** — still rule #1.
- Several real bugs were found in the deeper analysis passes — not data problems, but code problems (variable name collisions silently overwriting data, missing environment setup, column-collision merges). All caught by actually running each notebook end-to-end before trusting it, not just reading the code.
- Several surprising numbers during the deeper passes turned out to be our own scripting mistakes (a scaling error inflating a percentage, incomplete variable loading) — caught only by cross-checking against an already-known baseline number. Worth treating any surprising result as "verify before reporting," not "report because it's interesting."
- The same "which level are you counting at" lesson from the original pass (products vs. order-items vs. orders) kept reappearing in new forms throughout the deeper passes — worth keeping as a standing mental checklist.

## What's next
1. Each track owner reviews their own track's two-pass findings report and notebook.
2. ~~Build `analysis_master.csv`~~ — ✅ **Done and verified** (see `data_dictionary.md` §7).
3. **Move from exploratory to explanatory chart-building — this is now the main open gap**, prioritized using Track D's driver-ranking findings and the course's Week 4/5/8 encoding/heuristics frameworks. See `Roadmap_and_Visualization_Plan.md` for the full chart list and rationale.
4. Build the interactive dashboard (Streamlit).
5. Begin drafting the final synthesis (where to invest, where to intervene) and the technical report — the analytical groundwork is complete; what remains is visualization, synthesis, and communication.
