# Climate Credit Risk & Transition Finance Analytics


<img width="1598" height="984" alt="image" src="https://github.com/user-attachments/assets/4b898160-f7bd-4b85-830f-5a4f62e6b75d" />


## Overview

This project examines a practical banking question:

**How can borrower emissions and climate transition scenarios be translated into credit-risk insights and financing decisions?**

The model translates climate exposure into **financial stress, credit metrics, and portfolio-level decision support**.

## What the Project Does

**Borrower Data → Climate Scenarios → Financial Stress → Credit Metrics → Portfolio Risk → Transition Finance**

The Python workflow:

- validates borrower and scenario inputs;
- applies climate transition stress scenarios;
- estimates impacts on EBITDA, leverage, DSCR, and expected credit loss;
- aggregates borrower results at portfolio level;
- runs sensitivity analysis;
- performs QA and reconciliation checks;
- prepares outputs for Excel and Power BI reporting.

## Key Findings

- ServicesCo generates the highest expected credit loss in the modeled portfolio.
- Expected credit loss increases as carbon prices rise.
- Borrowers show different levels of sensitivity to transition stress.
- The analysis helps identify where climate exposure may translate into higher credit risk.

## Tools and Methods

**Python:** pandas, NumPy, openpyxl  
**Financial analysis:** EBITDA, leverage, DSCR, expected credit loss  
**Climate analysis:** transition risk, carbon-price scenarios, financed emissions concepts  
**Modeling:** stress testing, sensitivity analysis, QA/reconciliation  
**Reporting:** Excel and Power BI

## Project Structure

```text
data/        Raw and processed model inputs
src/         Python analytical pipeline
outputs/     Stress-test, sensitivity, QA, and reporting outputs
main.py      Pipeline execution

```

Key Takeaway

Financed emissions are only the starting point.

The more decision-useful question is:

What do those emissions mean for cash flow, credit quality, and capital allocation?

This project connects:

climate data → financial impact → credit risk → portfolio analytics → transition finance

```

Run the Model

pip install -r requirements.txt
python main.py

```
Disclaimer
This is an independent portfolio project developed for analytical and professional practice using public, modeled, and illustrative inputs. It does not represent the internal data, methodologies, credit policies, or investment recommendations of any financial institution.



