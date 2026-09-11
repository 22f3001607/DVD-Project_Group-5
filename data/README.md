# Data

The datasets are not committed to this repository since `analysis_master.csv` alone is ~92MB, and the full raw+processed set runs well past what's practical to version-control directly. All files are hosted here instead:

**Google Drive folder:** [Datasets](https://drive.google.com/drive/folders/1ALV7ElJbM7NVjogPuGVL0c40f8zfSrrZ)

## What to download and where it goes

To run **any notebook** in `notebooks/tracks/` or `notebooks/visualizations/`, or the **dashboard** in `dashboard/`, download the files below and place them directly in that same folder (or update the `DATA_DIR` variable at the top of the script/notebook to point wherever you put them).

| File | Used by | Size (approx.) |
|---|---|---|
| `analysis_master.csv` | All 6 visualization notebooks; the dashboard | ~92 MB |
| `order_items_dataset.csv` | Notebook 02 (SLA compliance), Notebook 03 (weight/volume vs. freight) | ~9 MB |
| `products_dataset.csv` | Notebook 03 (weight/volume vs. freight) | ~2 MB |
| `order_reviews_dataset.csv` | Notebook 04 (comment length), Notebook 06 (non-response proof) | ~14 MB |
| `marketing_qualified_leads_dataset.csv` | Notebook 05, Dashboard page 5 | <1 MB |
| `closed_deals_dataset.csv` | Notebook 05, Dashboard page 5 | <1 MB |

The 9 raw Olist CSVs (`orders_dataset.csv`, `order_payments_dataset.csv`, `customers_dataset.csv`, `sellers_dataset.csv`, `geolocation_dataset.csv`, etc.) and each track's processed intermediate outputs (`orders_master.csv`, `sellers_master_enhanced.csv`, `reviews_clean.csv`, and so on) are also in the same Drive folder, organized into `Raw Datasets/` and `Derived Datasets/` subfolders, for anyone who wants to re run the track notebooks from scratch rather than starting from `analysis_master.csv`.

## Important: never open a raw CSV in Excel

Excel silently reformats date columns to day-first order and truncates timestamp precision to the minute. If the file is then re-saved, the corruption becomes permanent. Use a text editor, VS Code, or load directly into pandas to inspect any raw file.

## Full schema reference

Every column in every file including `analysis_master.csv`'s complete 69-column schema, known null patterns, and a couple of documented naming nuances (e.g. `total_price` vs. `order_item_value`) — is in [`docs/data_dictionary.md`](../docs/data_dictionary.md).
