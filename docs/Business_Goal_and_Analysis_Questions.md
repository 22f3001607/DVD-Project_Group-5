# Business Goal & Analysis Questions

**Verification note:** all "✅ Answered" statuses below have since been cross-checked directly against the built and verified `analysis_master.csv` (not just against each track's individual output) — every headline figure quoted reproduces exactly. No status changes were needed; the analysis-question list stands as-is. The remaining open item is Q9 (final synthesis), which is now a visualization/writing task — see `Roadmap_and_Visualization_Plan.md`.

## The business goal, in our own words

Olist's marketplace connects thousands of small and medium sellers across Brazil to customers, handling everything from listing to payment to logistics. Leadership's single goal is **growth that doesn't come at the cost of customer experience** — but every lever they can pull trades one against the other: onboard sellers aggressively and volume rises, but delivery reliability and review quality can slip; enforce quality strictly and satisfaction improves, but the catalogue shrinks and growth stalls.

Our job is to trace the **full order journey** — placement, payment, seller handling, freight, delivery, and the review the customer leaves at the end — and turn it into a clear, visual answer to two linked questions: **what actually drives a customer from a happy order to a one-star review, and where in the marketplace is risk quietly building up?** The end product should let leadership see, concretely, where to invest and where to intervene — without guessing.

## Analysis questions — now with status, after two full passes of analysis

Each track has now gone through an initial pass and a deeper follow-up pass (see each track's findings report for full detail). Status shown below reflects where things actually stand, not just what we planned to ask.

1. **What does the order journey look like end to end, and where does friction show up before delivery even begins?** *(Track A)*
   **✅ Answered.** The funnel itself is clean (97% delivered). The more interesting finding: order volume grew steadily through 2017–2018, but delivery quality did *not* grow steadily alongside it — real spikes in late-delivery rate in Nov 2017 (13.8%, plausibly Black Friday) and March 2018 (20.7%, cause still unexplained).

2. **Do payment method or installment plans carry any real risk signal?** *(Track A)*
   **✅ Mostly ruled out, one thread still open.** Payment type and installments don't predict lateness. Voucher orders do cancel at ~5-6x the rate of other types — narrowed down (lower average order value, no geographic pattern) but not fully explained.

3. **Which product categories carry disproportionate satisfaction risk or represent a growth opportunity?** *(Track B)*
   **✅ Answered.** Category-level cancellation and freight-burden both vary meaningfully. Three categories (`market_place`, `toys`, `consoles_games`) are actually *declining* despite the marketplace's overall growth — a real "growth isn't reaching everywhere" signal.

4. **Which seller behaviors and regions predict reliable vs. unreliable delivery, and how confident can we be given small seller sample sizes?** *(Track C)*
   **✅ Answered, with an important nuance.** Seller size doesn't predict lateness. Cross-state and long-distance deliveries are real risk factors. A small-sample `low_confidence` flag (42% of sellers) is now built into the data. New: specific seller×destination-state routes were identified with severe reliability problems (one route at 62.5% late).

5. **Does delivery performance predict review score, and how strongly?** *(Track D — the project's central hypothesis)*
   **✅ Answered, decisively, with a specific mechanism identified.** Yes — review score declines almost monotonically as delay worsens. Digging deeper: **transport time (carrier-side) matters more to satisfaction than processing time (seller-side)** at the order level, though the reverse holds when looking at which *sellers* are reliably good (processing time better separates good sellers from bad ones on average). This is now the clearest, best-supported finding in the whole project.

6. **Is the population of unreviewed orders systematically different from reviewed ones?** *(Track D)*
   **✅ Resolved, not just documented.** Yes — confirmed as genuine non-response (not a data-collection timing artifact, ruled out via two independent checks) concentrated where satisfaction was worst. Any "average satisfaction" figure needs this caveat stated with confidence now, not as an open question.

7. **Does a customer's delivery experience relate to whether they come back for a second order?** *(Track D)*
   **✅ Answered.** Customers who became repeat buyers had a measurably better first-order delivery experience (6.4% late vs. 7.9% for one-time customers) — real, modest, supporting evidence for "better delivery → more repeat business."

8. **How efficient is seller acquisition, and does the acquisition channel say anything about performing sellers?** *(Track E)*
   **✅ Answered, and became a notable counter-narrative.** Conversion efficiency actually *improved* dramatically as lead volume grew (under 1% to 13-14%) — the opposite pattern from Track A's operational dips. Separately: declared seller attributes at signup (`lead_type`, `business_type`) do predict real future performance — a genuine closing-the-loop finding.

9. **Pulling it together: where should leadership invest, and where should they intervene?**
   **⏳ Still the job of the final report/presentation, not yet written.** All the ingredients now exist: transport-time investment (Q5), specific bad routes and reliable-seller profiles (Q4, Q8), category risk (Q3), and a real growth-vs-quality tension with evidence on both sides (Q1 vs. Q8) to build the presentation's central argument around.

## New questions that emerged from the deeper passes (not in the original list)

- Should Olist prioritize carrier/transport-network improvements over pushing sellers to process orders faster, given transport time's stronger relationship to review score?
- Could declared signup information (`lead_type`, `business_type`) support an early-warning flag for new sellers, before enough real order history exists to assess them directly?
- What explains the March 2018 operational dip specifically? Unresolved from the data alone — worth asking the team if anyone has outside context.
