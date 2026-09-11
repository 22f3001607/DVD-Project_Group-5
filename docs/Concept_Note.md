# Concept Note — A Visual Study of E-Commerce Orders, Delivery & Customer Satisfaction

## The project, briefly
We're studying Olist's Brazilian marketplace dataset (99,441 orders, Sept 2016–Oct 2018) plus a companion Marketing Funnel dataset, to identify what drives customer satisfaction and where the marketplace is at risk. Full business goal and analysis questions (now with resolution status per question) are in `Business_Goal_and_Analysis_Questions.md`.

## Dataset overview
11 CSV files across two groups: E-commerce core (9 files) and Marketing Funnel (2 files), joined on `order_id`, `customer_id`/`customer_unique_id`, `seller_id`, `product_id`, and zip-code prefixes.

## Team structure and approach
Split into 5 tracks along the order journey, one owner each (A–E). **Each track has gone through two passes:** an initial cleaning/exploration pass producing a shared master file, and a deeper follow-up pass that digs further into each track's own data, with Track D bringing all four other tracks' outputs together against review score, and **Track E completing the final cross-track join.**

**Shared data layer — now including the final integration file:**

| File | Track | Rows | Notes |
|---|---|---|---|
| `orders_master.csv` | A | 99,441 | Spine table; gained 2 columns in the deeper pass |
| `order_products_summary.csv`, `category_lookup.csv` | B | 98,666 / 74 | Order-level and category-level; gained 2 columns |
| `geolocation_agg.csv`, `sellers_master.csv` | C | 19,011 / 3,095 | Original pass |
| `sellers_master_enhanced.csv`, `order_logistics_master.csv` | C | 3,095 / 100,010 | Richer seller metrics and order-level logistics detail (processing vs. transport time, distance, delay bands) |
| `customers_master.csv`, `reviews_clean.csv` | D | 99,441 / 98,673 | Original pass |
| `funnel_summary.csv` | E | 11 | Standalone — confirmed a third time not to merge with the rest |
| **`analysis_master.csv`** | **E** | **99,441 × 69 cols** | **✅ Built and verified.** The full cross-track order-level join — spine + products + reviews + customers + logistics + enhanced seller metrics. All summary numbers (review distribution, late rate, review-gap count) reproduce every track's reported findings exactly. |

Full schemas and known gaps for every file, including the finalized `analysis_master.csv` schema, are in `data_dictionary.md`.

**Tools:** Python/pandas, Jupyter/Colab notebooks per track, matplotlib/seaborn for exploratory charts, Streamlit (leaning choice) for the dashboard, GitHub, shared Google Sheet for tracking.

## Initial observations, updated after the deeper analysis pass

The single most important addition from the deeper pass: **the project has a clear, mechanistic, cross-validated central story**, not just a correlation — and it's now backed by a single verified analytical table rather than five separate track outputs.

- **The central finding, sharpened:** delivery delay predicts review score — and specifically, **transport time (carrier-side) matters more than processing time (seller-side)** at the order level, though processing time better distinguishes *which sellers* are reliably good. This gives leadership a concrete lever, not just a correlation.
- **Independent cross-track validation:** Track A found an unexplained late-rate spike in March 2018 (20.7%, vs. ~5% typical). Track D, built completely separately, found March 2018 also has the lowest review score of any regular month (3.75). Two independently-built tracks landing on the same real-world event is strong evidence the finding is genuine, not a data artifact — even though *why* March 2018 was bad remains unexplained.
- **A genuine growth-vs-quality tension, now with evidence on both sides:** Track A found delivery quality did not hold steady as order volume grew (real spikes at points). Track E found the *opposite* pattern on the acquisition side — conversion efficiency actually improved substantially as lead volume grew. This tension, with concrete numbers on each side, is strong material for the final presentation's core argument.
- **The review-gap selection bias is resolved, not just flagged.** Two independent checks (review-request timing, and whether missing reviews cluster near the data's extraction cutoff) rule out "not enough time yet" as an explanation — the missing reviews are genuine non-response, concentrated where satisfaction was worst.
- **Several small-sample traps identified and handled with flags, not just caveats in prose:** `sellers_master`'s `low_confidence` flag (42% of sellers), funnel data's declared-catalog-size (confirmed unusable), several business-segment splits in Track E.
- **Two genuine closing-the-loop findings:** repeat customers had measurably better first-order delivery experiences (Track D), and declared seller attributes at signup predict real future performance (Track E) — both turn descriptive findings into forward-looking, actionable signals.
- **Freight burden, while real (Track B: some categories carry freight at ~50% of price), does not meaningfully hurt satisfaction on its own (Track D)** — an important nuance so the final report doesn't overstate freight as a satisfaction risk when it's really more of a margin/cost question.
- **One nuance surfaced during the `analysis_master.csv` build/verification:** the file carries two different "order value/freight" pairs (`total_price`/`total_freight`, order-summed, vs. `order_item_value`/`freight_value`, primary-item-only) that diverge on ~1.3% of orders with multiple items. See `data_dictionary.md` §7 for which to use where — worth the whole team knowing before building charts off this file.

## Data quality themes, reinforced across both passes
- **Never open a raw CSV in Excel** — still the most important standing rule.
- Several real bugs were found and fixed during the deeper passes — not data bugs, but analysis bugs (variable name collisions causing silent data loss or overwriting, missing environment setup, column-name collisions on merge). All were caught by testing before writing up findings, not assumed correct. Worth the team treating "run it end-to-end before trusting the output" as a standing practice, not a one-off check.
- Several apparent "surprising" numbers during the deeper passes turned out to be scripting mistakes on our own end (a scaling error, a mis-set correlation test) — caught by cross-checking against already-known baseline numbers before reporting them as findings. Worth continuing this habit as more analysis gets built.
- The `analysis_master.csv` build itself followed the same discipline: verified against every track's already-reported numbers before being treated as trustworthy for chart-building.

## Next steps
1. ~~Build `analysis_master.csv`~~ — ✅ **Done and verified.**
2. **Shift from exploratory analysis to explanatory chart-building — the current gap.** All analytical groundwork is complete; almost no actual visualizations exist yet. Prioritize using Track D's driver-ranking findings (transport time and total delay first; distance/category/freight ratio as secondary segmentation cuts) and apply Week 4/5/8 course frameworks (data type → channel matching, Cleveland-McGill accuracy ranking, Tufte's heuristics) to each chart's design.
3. Begin dashboard build (Streamlit).
4. Write the final synthesis (analysis question #9) and the technical report — the analytical groundwork exists; this is now a writing/visualization/narrative task, not an analysis gap.
