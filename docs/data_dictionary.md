# Data Dictionary — Processed Files (FINAL — updated after analysis_master.csv build)

Covers every shared output file produced across Tracks A–E, including each track's deeper follow-up pass, **and now the final `analysis_master.csv` cross-track join, which has been built and verified against this dictionary.** See each track's `Track_[X]_Findings_Report.md` for the reasoning behind each decision noted here.

**What changed in this update:** Section 7 (`analysis_master.csv`) is no longer "planned" — it exists, is verified (99,441 rows × 69 columns, one row per `order_id`, all summary numbers cross-checked against every track's reported findings and matched exactly), and its actual schema is documented below instead of the original join plan. One naming/semantics nuance was caught during verification and is flagged prominently (see §7.1) since it's an easy mistake to make when charting.

---

## 1. orders_master.csv (Track A)
One row per `order_id` (99,441 rows, 21 columns — grew by 2 in the deeper pass).

| Column | Type | Description |
|---|---|---|
| `order_id` | string | Primary key |
| `customer_id` | string | FK → `customers_master.csv` |
| `order_status` | string | `delivered` (96,478), `shipped` (1,107), `canceled` (625), `unavailable` (609), `invoiced` (314), `processing` (301), `created` (5), `approved` (2) |
| `purchase_ts` / `approved_ts` / `carrier_ts` / `delivered_ts` / `estimated_delivery_ts` | datetime | Parsed with plain `pd.to_datetime()` against confirmed ISO raw format |
| `approval_hours` | float | purchase → approval, hours |
| `carrier_handoff_days` | float | approval → carrier pickup, days |
| `delivery_days` | float | purchase → delivered, days |
| `delivery_delay_days` | float | delivered − estimated (**positive = late**) |
| `is_delivered`, `is_canceled`, `is_late` | bool | |
| `total_payment_value` | float | Summed across all payment rows |
| `payment_type_primary` | string | `credit_card` (74,975), `boleto` (19,784), `voucher` (3,151), `debit_card` (1,527), `not_defined` (3) |
| `max_installments` | int | |
| `n_payment_rows` | int | |
| `purchase_month` | string | `YYYY-MM` |
| `is_split_payment` | bool | `n_payment_rows > 1` |

**Known gaps:** 1 order has no payment record. ~1.4% of delivered orders show carrier timestamp before approval (mostly mild logging quirks; 1 genuine chronological-impossibility order isolated: `7c48bb55e8e4f7e56d412e9653db37bc`).

---

## 2. order_products_summary.csv (Track B)
One row per `order_id` (98,666 rows, 8 columns).

| Column | Type | Description |
|---|---|---|
| `order_id` | string | FK |
| `primary_category` | string | English category of the **highest-priced item** in the order |
| `n_items` | int | Item count |
| `n_distinct_categories` | int | Categories spanned |
| `total_price` | float | **Summed** item price across the whole order |
| `total_freight` | float | **Summed** shipping cost across the whole order |
| `is_canceled` | bool | Merged from `orders_master.csv` |
| `purchase_month` | string | Merged from `orders_master.csv` |

**Known gaps:** 775 orders have no items (mostly `unavailable`/`canceled` — 603 + 164, plus a small residual). `primary_category` can be `"unknown"` (610 products have no category → 1,603 order_items rows → 1,415 orders).

## category_lookup.csv (Track B)
One row per category (74 rows). `product_category_name_english`, `n_items_sold`, `n_orders`, `avg_price`, `median_price`, `avg_freight`. Unchanged.

---

## 3. geolocation_agg.csv (Track C)
One row per `zip_code_prefix` (19,011 rows). `lat`/`lng` = median coords, `city`/`state` = mode. ~3.6% of prefixes have >5km coordinate spread (documented limitation, not corrected).

## sellers_master.csv (Track C)
One row per `seller_id` (3,095 rows, 10 columns) — original pass. Superseded by `sellers_master_enhanced.csv` below for new work.

## sellers_master_enhanced.csv (Track C)
One row per `seller_id` (3,095 rows, 22 columns). Strict superset — verified identical on overlapping columns.

| Column | Type | Description |
|---|---|---|
| `seller_id`, `seller_city`, `seller_state`, `lat`, `lng`, `low_confidence` | — | `low_confidence = n_orders < 5`, 1,301/3,095 sellers (42%) |
| `size_bucket` | string | `1-4` / `5-20` / `21-100` / `100+` |
| `n_orders` | int | |
| `avg_processing_days`, `median_processing_days` | float | Purchase → carrier handoff |
| `avg_transport_days`, `median_transport_days` | float | Carrier handoff → delivered |
| `avg_delivery_days`, `median_delivery_days` | float | |
| `avg_delivery_delay`, `median_delivery_delay` | float | |
| `pct_late`, `pct_early`, `pct_on_time` | float | |
| `avg_freight`, `avg_order_value`, `freight_ratio` | float | |

## order_logistics_master.csv (Track C)
One row per order-**seller** pair (100,010 rows — more than 98,666 orders because some orders span multiple sellers; deduplicated to one row per order, keeping the highest-value item, before joining downstream). 28 columns: keys, timestamps, `processing_days`/`transport_days`/`delivery_days_calc`, `delivery_delay_days`/`days_early`/`days_late`/`delay_band`, `order_item_value`/`freight_value`/`freight_ratio`/`n_items`, `purchase_month`/`purchase_weekday`, `customer_state`/`same_state`/`distance_km`.

---

## 4. customers_master.csv (Track D)
One row per `customer_id` (99,441 rows). `customer_id`, `customer_unique_id` (the real person — use for repeat-customer logic), `customer_city`, `customer_state`, `lat`/`lng` (null for 279), `customer_order_count`.

## reviews_clean.csv (Track D)
One row per `order_id` (98,673 rows). `order_id`, `review_score` (1–5), `has_comment` (3.70 avg score w/ comment vs. 4.38 without), `days_to_review_response` (no relationship to score, ruled out).

**Known gap — resolved:** 646 delivered orders have no review, confirmed genuine non-response via two independent checks, concentrated where satisfaction was worst.

---

## 5. funnel_summary.csv (Track E)
One row per lead `origin` (11 rows). `origin`, `n_leads`, `n_won`, `conversion_rate`. **Standalone — confirmed twice not to merge into the main pipeline** (only 12.3% of active sellers have funnel records; only 45.1% of won deals become active sellers). `lead_type`/`business_type` (in the raw `closed_deals_dataset.csv`, not in this file) predict real seller performance for the 380-seller overlap — see Track E's report; not built into a shared file since the overlap is too small for a general-purpose join.

---

## 6. Team process documents
`Team_Tracking_Template.xlsx` (work log / task board / MoM, 3 tabs), `repo_starter.zip` (GitHub scaffolding — `docs/data_dictionary.md` inside it is now superseded by this file; push this version to the repo). Built early — verify with the user whether still current before relying on them.

---

## 7. analysis_master.csv (Track E) Built and Verified

One row per `order_id`, **99,441 rows × 69 columns**. Left-joined onto the `orders_master.csv` spine, so every order stays visible even where a downstream match is missing (canceled/unavailable/no-item orders correctly show nulls, not dropped rows).

**Verification performed:** row count matches the orders spine exactly; `order_id` confirmed unique; review-score distribution (11.52/3.17/8.24/19.30/57.77%), overall late rate (7.87%), and the 646-delivered-orders-with-no-review count all reproduce the exact figures already reported in the track findings — the join introduced no silent data loss or duplication.

### Full column list

**From `orders_master.csv` (Track A) — 21 cols:** `order_id`, `customer_id`, `order_status`, `purchase_ts`, `approved_ts`, `carrier_ts`, `delivered_ts`, `estimated_delivery_ts`, `approval_hours`, `carrier_handoff_days`, `delivery_days`, `delivery_delay_days`, `is_delivered`, `is_canceled`, `is_late`, `total_payment_value`, `payment_type_primary`, `max_installments`, `n_payment_rows`, `purchase_month`, `is_split_payment`

**From `order_products_summary.csv` (Track B) — 5 cols joined (order_id is the key, is_canceled/purchase_month already present):** `primary_category`, `n_items`, `n_distinct_categories`, `total_price`, `total_freight`

**From `reviews_clean.csv` (Track D) — 3 cols:** `review_score`, `has_comment`, `days_to_review_response`

**From `customers_master.csv` (Track D) — 5 cols:** `customer_unique_id`, `customer_city`, `customer_state`, `customer_lat`, `customer_lng`, `customer_order_count`

**From `order_logistics_master.csv` (Track C, deduplicated to one row per order) — 19 cols:** `seller_id`, `seller_state`, `processing_days`, `transport_days`, `delivery_days_calc`, `days_early`, `days_late`, `delay_band`, `order_item_value`, `freight_value`, `freight_ratio`, `purchase_weekday`, `same_state`, `distance_km`, `seller_city`, `seller_lat`, `seller_lng`

**From `sellers_master_enhanced.csv` (Track C, joined via `seller_id`) — 15 cols, all prefixed `seller_` to avoid collision with order-level columns of similar name:** `seller_low_confidence`, `seller_size_bucket`, `seller_n_orders`, `seller_avg_processing_days`, `seller_median_processing_days`, `seller_avg_transport_days`, `seller_median_transport_days`, `seller_avg_delivery_days`, `seller_median_delivery_days`, `seller_avg_delivery_delay`, `seller_median_delivery_delay`, `seller_pct_late`, `seller_pct_early`, `seller_pct_on_time`, `seller_avg_freight`, `seller_avg_order_value`, `seller_freight_ratio`

**Not included (by design):** `funnel_summary.csv` / raw funnel data — confirmed three times now (E's original pass, E's Section 7, and this build) to stay a standalone story, not part of the order-level join.

### Important nuance caught during verification — read before charting

**`total_price`/`total_freight` (Track B, order-summed) are NOT the same thing as `order_item_value`/`freight_value` (Track C, single-item-grain from the logistics dedup).** For single-item orders they're identical; for multi-item orders (1,278 rows, ~1.3% of the file) they diverge — e.g. one order has `total_price = 130.40` but `order_item_value = 90.90`, because Track B summed all items in the order while Track C's dedup convention kept only the *highest-value single item's* own price/freight (consistent with the "primary category = highest-priced item" rule, but this means the two freight/price pairs answer different questions). **Use `total_price`/`total_freight` for order-level economics (what did the customer actually pay); use `order_item_value`/`freight_value`/`freight_ratio` only when you specifically want the primary item's own figures** (e.g. matching Track D's driver-ranking correlations, which were computed on this Track C pair). Don't mix the two pairs in the same chart without labeling which is which.

### Null patterns (all explained, none are data-quality surprises)

| Column group | Null count | Reason |
|---|---|---|
| `primary_category`, `n_items`, `total_price`, `total_freight`, `seller_*`, `order_item_value`, `freight_value`, `delay_band`, `same_state`, `purchase_weekday` | 775 | Orders with no items at all (no seller, no product → nothing to join) |
| `review_score`, `has_comment`, `days_to_review_response` | 768 | 646 of these are delivered orders with genuine non-response (resolved, see reviews_clean.csv above); remaining ~122 are non-delivered orders that were never eligible for a review request |
| `delivered_ts`, `delivery_days`, `delivery_delay_days`, `transport_days`, `days_early`, `days_late` | 2,965 | Not yet delivered / canceled / unavailable — no delivery event occurred |
| `carrier_ts`, `carrier_handoff_days`, `processing_days` | 1,783–1,797 | No carrier handoff recorded yet |
| `approved_ts`, `approval_hours` | 160 | No approval timestamp (14 of these are delivered orders per Track A) |
| `customer_lat`/`lng` | 279 | No zip match |
| `seller_lat`/`lng` | 991 | 775 no-seller orders + 216 more where the seller's own geolocation lookup failed (7 sellers per Track C, appearing across many orders) |
| `distance_km` | 1,265 | 775 no-seller orders + 490 more with a seller but missing customer or seller coordinates |
| `delay_band = "Unknown"` | 2,190 | Orders with a seller assigned but no delivery outcome yet — mostly `shipped` (1,106), `canceled` (455), `invoiced` (312), `processing` (301); only 8 are `delivered`, an edge case worth a quick look before final reporting |
| `total_payment_value`, `payment_type_primary`, `max_installments`, `n_payment_rows` | 1 | The single order with no payment record (Track A finding #7) |

**Reusable bucket edges (from `reviews_clean.csv`'s documentation, applies to `delivery_delay_days`):** `bins=[-200, -7, 0, 3, 7, 999]`, `labels=['5+ days early','on-time/early','1-3 days late','4-7 days late','8+ days late']`. Note this is a *different* cut than the `delay_band` column already built into `analysis_master.csv` (`3+ days early` / `1-2 days early` / `1-2 days late` / `3-7 days late` / `8+ days late` / `Unknown`) — pick one convention per chart and state which you're using; don't mix bucket definitions across a report.

### Basic descriptive stats worth having on hand for chart-scaling decisions
- `purchase_ts` spans 2016-09-04 to 2018-10-17.
- `freight_ratio` (item-grain): median 0.224, mean 0.308, right-skewed (max 21.4 — an extreme outlier worth a quick sanity check, not necessarily an error, before using in a chart with a linear axis).
- Row grain is confirmed one-per-order throughout — safe to treat as the base table for any order-level chart without further deduplication.
