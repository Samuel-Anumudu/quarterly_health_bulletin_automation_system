# Phase 1 — Schema Scan Summary

Anchor table (assumed): **facilities.csv**

## Cross-file signals
- Columns common to all files: facility_id
- Top Facility ID candidates in facilities (ranked):
  - facility_id (score=7.5): name_id_hints=2; id_value_rate=1.00; missing_pct=0.00; uniqueness_ratio=1.00
  - facility_name (score=2.0): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=1.00
  - gps_lat (score=1.5): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=1.00
  - gps_lon (score=1.5): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=1.00
  - district (score=1.256): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.26

## clinical_neonatal.csv
- Shape: 1404 rows × 17 cols
- Columns: facility_id, reporting_month, total_deliveries, live_births, neonatal_deaths_0_7d, neonatal_deaths_8_28d, stillbirths, death_birth_asphyxia, death_prematurity, death_sepsis, death_congenital, death_other, avg_gestational_age, preterm_births_28_32w, preterm_births_32_37w, apgar_less_7_at_5min, birth_weight_less_2500g
- Suggested Facility ID columns (within this file):
  - facility_id (score=6.583): name_id_hints=2; id_value_rate=1.00; missing_pct=0.00; uniqueness_ratio=0.08
  - birth_weight_less_2500g (score=0.555): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.05
  - preterm_births_32_37w (score=0.541): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.04
  - apgar_less_7_at_5min (score=0.524): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.02
  - preterm_births_28_32w (score=0.518): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.02
- Best join key matches against facilities (value overlap rate):
  - facilities.facility_id  ⇐⇒  clinical_neonatal.csv.facility_id  (match_rate=1.0)
- Candidate columns (patient volume):
  - total_deliveries (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - live_births (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - stillbirths (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - death_birth_asphyxia (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - preterm_births_28_32w (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (maternal indicators):
  - stillbirths (score=5.25): name_hints=2; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - total_deliveries (score=3.25): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - live_births (score=3.25): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - death_birth_asphyxia (score=3.25): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - preterm_births_28_32w (score=3.25): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (reporting / performance):
  - reporting_month (score=2.0): name_hints=1; numeric_rate=0.00; percent_rate=0.00; binary_like=False
  - total_deliveries (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - live_births (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - neonatal_deaths_0_7d (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - neonatal_deaths_8_28d (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False

## facilities.csv
- Shape: 117 rows × 18 cols
- Columns: facility_id, facility_name, district, province, tier_level, gps_lat, gps_lon, nicu_available, nicu_beds, incubators_functional, incubators_total, radiant_warmers, phototherapy_units, cpap_machines, resuscitation_tables, kangaroo_care_space, electricity_reliable, backup_generator
- Suggested Facility ID columns (within this file):
  - facility_id (score=7.5): name_id_hints=2; id_value_rate=1.00; missing_pct=0.00; uniqueness_ratio=1.00
  - facility_name (score=2.0): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=1.00
  - gps_lat (score=1.5): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=1.00
  - gps_lon (score=1.5): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=1.00
  - district (score=1.256): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.26
- Candidate columns (patient volume):
  - gps_lat (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - gps_lon (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - nicu_beds (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - incubators_functional (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - incubators_total (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (maternal indicators):
  - gps_lat (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - gps_lon (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - nicu_beds (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - incubators_functional (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - incubators_total (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (reporting / performance):
  - gps_lat (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - gps_lon (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - nicu_beds (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - incubators_functional (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - incubators_total (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False

## governance.csv
- Shape: 117 rows × 11 cols
- Columns: facility_id, newborn_protocol_exists, protocol_last_updated, death_audits_conducted_pct, staff_trained_on_protocol_pct, quality_improvement_active, supervision_visits_quarterly, hmis_reporting_completeness, bag_mask_ventilation_competency, thermal_care_protocol_compliance, infection_prevention_score
- Suggested Facility ID columns (within this file):
  - facility_id (score=7.5): name_id_hints=2; id_value_rate=1.00; missing_pct=0.00; uniqueness_ratio=1.00
  - newborn_protocol_exists (score=1.026): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.03
  - quality_improvement_active (score=1.017): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.02
  - death_audits_conducted_pct (score=0.979): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.48
  - staff_trained_on_protocol_pct (score=0.953): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.45
- Best join key matches against facilities (value overlap rate):
  - facilities.facility_id  ⇐⇒  governance.csv.facility_id  (match_rate=1.0)
- Candidate columns (patient volume):
  - supervision_visits_quarterly (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (maternal indicators):
  - supervision_visits_quarterly (score=1.25): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (reporting / performance):
  - death_audits_conducted_pct (score=5.0): name_hints=2; numeric_rate=0.00; percent_rate=1.00; binary_like=False
  - hmis_reporting_completeness (score=5.0): name_hints=2; numeric_rate=0.00; percent_rate=1.00; binary_like=False
  - staff_trained_on_protocol_pct (score=3.0): name_hints=1; numeric_rate=0.00; percent_rate=1.00; binary_like=False
  - infection_prevention_score (score=3.0): name_hints=1; numeric_rate=0.00; percent_rate=1.00; binary_like=False
  - supervision_visits_quarterly (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False

## healthcare_workers.csv
- Shape: 117 rows × 11 cols
- Columns: facility_id, total_nurses, neonatal_trained_nurses, midwives, obstetricians, pediatricians, neonatologists, anesthetists, last_neonatal_training_date, staff_per_delivery_2024, night_shift_coverage
- Suggested Facility ID columns (within this file):
  - facility_id (score=7.5): name_id_hints=2; id_value_rate=1.00; missing_pct=0.00; uniqueness_ratio=1.00
  - last_neonatal_training_date (score=1.333): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.33
  - total_nurses (score=0.829): name_id_hints=0; id_value_rate=0.01; missing_pct=0.00; uniqueness_ratio=0.32
  - midwives (score=0.654): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.15
  - neonatal_trained_nurses (score=0.577): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.08
- Best join key matches against facilities (value overlap rate):
  - facilities.facility_id  ⇐⇒  healthcare_workers.csv.facility_id  (match_rate=1.0)
- Candidate columns (patient volume):
  - staff_per_delivery_2024 (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - total_nurses (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - neonatal_trained_nurses (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - midwives (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - obstetricians (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (maternal indicators):
  - staff_per_delivery_2024 (score=3.25): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - obstetricians (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - total_nurses (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - neonatal_trained_nurses (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - midwives (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (reporting / performance):
  - night_shift_coverage (score=2.0): name_hints=1; numeric_rate=0.00; percent_rate=0.00; binary_like=False
  - total_nurses (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - neonatal_trained_nurses (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - midwives (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - obstetricians (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False

## operations.csv
- Shape: 117 rows × 13 cols
- Columns: facility_id, avg_referral_time_hrs, referrals_out_monthly, referrals_in_monthly, oxygen_cylinders_available, oxygen_concentrators, oxygen_plant, ambulance_available, kangaroo_care_practiced, essential_drugs_stockouts_days, antibiotics_available, surfactant_available, referral_feedback_rate
- Suggested Facility ID columns (within this file):
  - facility_id (score=7.5): name_id_hints=2; id_value_rate=1.00; missing_pct=0.00; uniqueness_ratio=1.00
  - antibiotics_available (score=1.034): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.03
  - kangaroo_care_practiced (score=1.026): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.03
  - oxygen_plant (score=1.017): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.02
  - ambulance_available (score=1.017): name_id_hints=0; id_value_rate=0.00; missing_pct=0.00; uniqueness_ratio=0.02
- Best join key matches against facilities (value overlap rate):
  - facilities.facility_id  ⇐⇒  operations.csv.facility_id  (match_rate=1.0)
- Candidate columns (patient volume):
  - avg_referral_time_hrs (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - referrals_out_monthly (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - referrals_in_monthly (score=3.0): name_hints=1; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - referral_feedback_rate (score=1.5): name_hints=1; numeric_rate=0.00; percent_rate=1.00; binary_like=False
  - oxygen_cylinders_available (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (maternal indicators):
  - antibiotics_available (score=2.0): name_hints=1; numeric_rate=0.00; percent_rate=0.00; binary_like=False
  - avg_referral_time_hrs (score=1.25): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - referrals_out_monthly (score=1.25): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - referrals_in_monthly (score=1.25): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - oxygen_cylinders_available (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
- Candidate columns (reporting / performance):
  - referral_feedback_rate (score=3.0): name_hints=1; numeric_rate=0.00; percent_rate=1.00; binary_like=False
  - avg_referral_time_hrs (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - referrals_out_monthly (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - referrals_in_monthly (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False
  - oxygen_cylinders_available (score=1.0): name_hints=0; numeric_rate=1.00; percent_rate=0.00; binary_like=False

