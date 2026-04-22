"""
Dallas County HMDA Denial Disparity Analysis — 2022 + 2023
Filters to conventional home purchase applications and computes tract-level
denial metrics with Black/White disparity ratios.
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path("/home/user/workspace/hmda")
OUT = Path("/home/user/workspace/outputs")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "tables").mkdir(exist_ok=True)

# ---- Load both years, keep only needed columns ----
keep_cols = [
    "activity_year", "county_code", "census_tract",
    "action_taken", "loan_type", "loan_purpose",
    "applicant_race-1", "applicant_race-2", "applicant_race-3",
    "applicant_race-4", "applicant_race-5",
    "co-applicant_race-1",
    "applicant_ethnicity-1", "derived_race",
]

dfs = []
for yr in (2022, 2023):
    df = pd.read_csv(DATA / f"hmda_{yr}_48113.csv", usecols=keep_cols, low_memory=False)
    dfs.append(df)
lar = pd.concat(dfs, ignore_index=True)
print(f"Total LAR rows (2022+2023, Dallas Co): {len(lar):,}")

# ---- Filter: conventional (loan_type=1) + home purchase (loan_purpose=1) ----
conv_purch = lar[(lar["loan_type"] == 1) & (lar["loan_purpose"] == 1)].copy()
print(f"Conventional home-purchase rows: {len(conv_purch):,}")

# ---- Keep decisioned actions for denial-rate math ----
# action_taken: 1=originated, 2=approved-not-accepted, 3=denied,
#   4=withdrawn-by-applicant, 5=file-closed-incomplete, 7=preapproval-denied,
#   8=preapproval-approved-not-accepted
# Standard denial-rate denominator: exclude withdrawn (4) and incomplete (5);
# include preapproval denials if action=7 is present.
decisioned = conv_purch[conv_purch["action_taken"].isin([1, 2, 3, 7, 8])].copy()
decisioned["is_denied"] = decisioned["action_taken"].isin([3, 7]).astype(int)
print(f"Decisioned rows: {len(decisioned):,}  |  Denied: {decisioned['is_denied'].sum():,}")

# ---- Clean census tract: 11-digit GEOID (HMDA already reports full GEOID) ----
decisioned["GEOID"] = decisioned["census_tract"].astype("Int64").astype(str).str.zfill(11)
decisioned = decisioned[decisioned["GEOID"].str.startswith("48113")]

# ---- Race flags: race_code 3 = Black/African American, 5 = White ----
# HMDA allows up to 5 race codes per applicant; common practice: use race-1 as primary
# Also standard: "Black alone" = race-1==3 and race-2..5 NaN; "White alone" = race-1==5 and others NaN
r1 = pd.to_numeric(decisioned["applicant_race-1"], errors="coerce")
r2 = pd.to_numeric(decisioned["applicant_race-2"], errors="coerce")
r3 = pd.to_numeric(decisioned["applicant_race-3"], errors="coerce")
r4 = pd.to_numeric(decisioned["applicant_race-4"], errors="coerce")
r5 = pd.to_numeric(decisioned["applicant_race-5"], errors="coerce")

decisioned["is_black"] = (r1 == 3) & r2.isna() & r3.isna() & r4.isna() & r5.isna()
decisioned["is_white"] = (r1 == 5) & r2.isna() & r3.isna() & r4.isna() & r5.isna()

print(f"Black-alone applicants: {decisioned['is_black'].sum():,}")
print(f"White-alone applicants: {decisioned['is_white'].sum():,}")

# ---- Tract-level aggregation ----
def tract_metrics(g):
    apps = len(g)
    dens = g["is_denied"].sum()
    black_apps = g["is_black"].sum()
    black_den = g.loc[g["is_black"], "is_denied"].sum()
    white_apps = g["is_white"].sum()
    white_den = g.loc[g["is_white"], "is_denied"].sum()

    denial_rate = dens / apps if apps else np.nan
    black_rate = black_den / black_apps if black_apps >= 10 else np.nan
    white_rate = white_den / white_apps if white_apps >= 10 else np.nan
    disparity = (black_rate / white_rate) if (pd.notna(black_rate) and pd.notna(white_rate) and white_rate > 0) else np.nan

    return pd.Series({
        "total_applications": apps,
        "total_denials": int(dens),
        "denial_rate": denial_rate,
        "black_applications": int(black_apps),
        "black_denials": int(black_den),
        "black_denial_rate": black_rate,
        "white_applications": int(white_apps),
        "white_denials": int(white_den),
        "white_denial_rate": white_rate,
        "disparity_ratio_bw": disparity,
    })

tract = decisioned.groupby("GEOID").apply(tract_metrics).reset_index()
print(f"\nTracts with ≥1 conv purchase application: {len(tract):,}")
print(f"Tracts with valid disparity ratio: {tract['disparity_ratio_bw'].notna().sum():,}")
print(f"County median denial rate: {tract['denial_rate'].median():.4f}")
print(f"County-wide denial rate (apps-weighted): {tract['total_denials'].sum()/tract['total_applications'].sum():.4f}")

# County-level aggregates for annotation
overall_apps = tract["total_applications"].sum()
overall_dens = tract["total_denials"].sum()
overall_rate = overall_dens / overall_apps
black_apps_tot = tract["black_applications"].sum()
black_den_tot = tract["black_denials"].sum()
white_apps_tot = tract["white_applications"].sum()
white_den_tot = tract["white_denials"].sum()
black_rate_tot = black_den_tot / black_apps_tot if black_apps_tot else np.nan
white_rate_tot = white_den_tot / white_apps_tot if white_apps_tot else np.nan
county_disparity = black_rate_tot / white_rate_tot if white_rate_tot else np.nan

print(f"\n--- County-wide (weighted) ---")
print(f"Overall denial rate:  {overall_rate:.3%}")
print(f"Black denial rate:    {black_rate_tot:.3%}  (n={black_apps_tot:,})")
print(f"White denial rate:    {white_rate_tot:.3%}  (n={white_apps_tot:,})")
print(f"Disparity (B/W):      {county_disparity:.2f}x")

# ---- Save tract CSV ----
out_csv = OUT / "tables" / "dallas_hmda_tract_denials_2022_2023.csv"
tract.to_csv(out_csv, index=False)
print(f"\nWrote {out_csv}")

# Save county summary
summary = pd.DataFrame([{
    "scope": "Dallas County (48113) — Conventional Home Purchase, 2022+2023",
    "total_applications": int(overall_apps),
    "total_denials": int(overall_dens),
    "overall_denial_rate": overall_rate,
    "black_applications": int(black_apps_tot),
    "black_denial_rate": black_rate_tot,
    "white_applications": int(white_apps_tot),
    "white_denial_rate": white_rate_tot,
    "disparity_ratio_bw": county_disparity,
    "median_tract_denial_rate": tract["denial_rate"].median(),
}])
summary.to_csv(OUT / "tables" / "dallas_hmda_county_summary_2022_2023.csv", index=False)
print(f"Wrote county summary")
