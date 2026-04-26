# ARDS Trial Enrollment County Prioritization

## Overview

This project ranks U.S. counties for potential ARDS clinical trial enrollment prioritization.

GEn1E Lifesciences developed a drug for ARDS and wanted to identify counties where clinical trials may have stronger enrollment potential. Since direct county-level ARDS incidence data was not provided, this analysis uses county-level mortality data for ARDS-related conditions as proxy signals.

## Data Used

The repository includes county-level mortality files for:

- Sepsis
- Pneumonia
- Hypertension

The primary fields used are:

- County name
- FIPS county code
- Year
- Deaths
- Population
- Crude mortality rate

The expected data files are included in the project folder:

```text
Sepsis.txt
Pneumonia.txt
Hypertension.txt
```

## Methodology

### 1. Parsing and Cleaning

The parser reads tab-separated disease files and converts them into county-year records.

Cleaning steps include:

- Using FIPS codes as unique county identifiers
- Removing extra whitespace
- Splitting county and state fields
- Converting valid numeric fields into integers or floats
- Treating suppressed, unreliable, missing, blank, and invalid values as unusable
- Avoiding treating missing values as zero

### 2. Aggregation

Each county-disease pair is aggregated across valid years.

Metrics created include:

- Total deaths
- Average yearly deaths
- Average crude mortality rate
- Latest available population
- Valid death years
- Valid rate years
- Missing or unusable year counts

### 3. County Dictionary

The aggregated disease summaries are merged into one county-centered dictionary keyed by FIPS code.

Each county stores:

- County name
- State
- Latest population
- Latest population year
- Nested disease summaries for sepsis, pneumonia, and hypertension

### 4. Scoring

Sepsis and pneumonia are used as the primary ARDS proxy diseases.

The model calculates:

```text
ARDS volume score = 0.60 × average sepsis deaths + 0.40 × average pneumonia deaths
```

```text
ARDS rate score = 0.60 × average sepsis crude rate + 0.40 × average pneumonia crude rate
```

Both scores are normalized using min-max normalization:

```text
normalized score = (county score - minimum score) / (maximum score - minimum score)
```

Final score:

```text
Final ARDS score = 0.75 × normalized volume score + 0.25 × normalized rate score
```

Volume is weighted more heavily because clinical trial enrollment depends on having enough potential patients. Crude mortality rate is still included to capture disease concentration.

### 5. Filtering

Counties are filtered to improve reliability and feasibility:

- At least 3 valid years of sepsis data
- At least 3 valid years of pneumonia data
- Population of at least 250,000

## Interactive Ranking Options

The program allows counties to be ranked by:

- Average yearly sepsis deaths
- Average sepsis crude mortality rate
- Average yearly pneumonia deaths
- Average pneumonia crude mortality rate
- Average yearly hypertension deaths
- Average hypertension crude mortality rate
- Final ARDS prioritization score

For disease-specific rankings, the printed score represents the selected disease metric. For the final ARDS ranking, the printed score represents the normalized ARDS prioritization score.

## Project Structure

```text
ARDS-Trial-Enrollment/
├── main.py
├── parser.py
├── county_dictionary.py
├── scoring.py
├── README.md
├── Sepsis.txt
├── Pneumonia.txt
└── Hypertension.txt
```

## How to Run

Clone or download the repository, then open the project folder in a terminal or VS Code.

From inside the project folder, run:

```bash
python3 main.py
```

Follow the interactive menu prompts to choose a ranking method and number of counties to display.

## Output

The program prints ranked counties with:

- Rank
- FIPS code
- County
- State
- Population
- Score or selected ranking metric
- Average sepsis deaths
- Average pneumonia deaths
- Average sepsis crude mortality rate
- Average pneumonia crude mortality rate

## Notes and Limitations

- This is a county-level prioritization model, not a final hospital site selection tool.
- Sepsis and pneumonia mortality are used as ARDS-related proxy signals.
- Crude mortality rates are not age-adjusted.
- Hypertension is included as secondary context but is not part of the final ARDS score.
- Hospital-level feasibility, ICU capacity, investigator availability, and trial infrastructure would need separate validation.

## Potential Next Steps

- Identify hospitals and ICU centers in top-ranked counties
- Validate enrollment feasibility using hospital-level data
- Refine the model with direct ARDS incidence or ICU admission data if available
- Incorporate hospital trial infrastructure and investigator availability

