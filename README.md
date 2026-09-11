# A Visual Study of E-Commerce Orders, Delivery & Customer Satisfaction

An analysis of Olist's Brazilian e-commerce marketplace, identifying what drives customer satisfaction and where the marketplace is at risk, so leadership can grow without breaking the customer experience.

| Name | Roll No |
|---|---|
| Smit Pareshbhai Sabalpara | 22F3001607 |
| Harsh Patel | 22F1001058 |
| Naman Goel | 22F2001226 |
| Sunny Kumar Gupta | 23F1002609 |
| Renee Keerthana Paturi | 22F2001379 |


---

## What's in this repository

| Folder | Contents |
|---|---|
| `notebooks/tracks/` | The 5 original per-category analysis notebooks (Payments, Products, Sellers/Logistics, Customers/Reviews, Marketing Funnel) |
| `notebooks/visualizations/` | 6 notebooks building every chart in the final report, one per theme |
| `dashboard/` | Interactive Streamlit dashboard source (6 pages) |
| `docs/` | Data dictionary |
| `data/` | **Not the data itself**: see `data/README.md` for the download link and setup |

## The core story, in brief

1. **The mechanism and its paradox** : delivery delay predicts review score, and transport time (carrier-side, mostly outside a seller's control) drives the damage to any individual order's rating, while a seller's own processing speed better identifies which sellers are reliably good over time.
2. **Growth vs. quality is measurable** : delivery quality dipped at real points as the marketplace scaled, while acquisition efficiency improved over the same period.
3. **A speculative layer** : smaller, honestly-caveated findings not previously documented for this dataset (no holiday-season leniency, an early-delivery "ceiling effect," and more)

## Setup reproducing this work

**1. Clone this repository**
```bash
git clone https://github.com/22f3001607/DVD-Project_Group-5.git
cd DVD-Project_Group-5
```

**2. Get the data**
Data files are hosted separately (too large for git) see [`data/README.md`](data/README.md) for the download link and exactly where each file goes.

**3. Install dependencies**
```bash
pip install -r dashboard/requirements.txt
pip install jupyter pandas numpy matplotlib seaborn adjustText
```

**4. Run the notebooks**
Open any notebook in `notebooks/tracks/` or `notebooks/visualizations/` in Jupyter each expects the relevant CSV(s) in the same folder it's run from.

**5. Run the dashboard**
```bash
cd dashboard
streamlit run Home.py
```
Place the data files listed in `data/README.md` directly inside the `dashboard/` folder first.
