# Dashboard Project

Set out on this project intending it to be a short, fun project built in Python and Dash to explore layoff trends, AI adoption, job security, and salary changes across 20 major tech companies over the past two years. Useful in identifying upticks in layoff trends in comparison to open positions.

Primary features:
- Multi-select dropdown to filter by company
- Layoffs over time per company
- AI adoption level trends
- Job security score tracking
- All charts update dynamically based on company selection

Tools used:
- Python
- pandas, plotly, dash

Challenges + WIP features:
- Creating overlapping charts that are readable
- Comprehensive report
- The month column is written in abbreviated strings instead of integers, this was a minor challenge to convert before building the period column for time series plotting (first time encounter).
- Combining separate month and year columns into a single sortable data field required zero-padding to prevent faulty ordering.
- Port conflicts during debugging (likely a technical issue on my end though)
- AI replacement risk breakdown chart (how to execute efficiently?)
- Creating an export to PDF or CSV capability

Data source:
- https://www.kaggle.com/datasets/amaymishra11/tech-layoffs-and-hiring-trends-2026

Companies shown in dataset (A-Z):
- Adobe, Airbnb, Amazon, Anthropic, Apple, Databricks, Google, Intel, Meta, 
Microsoft, NVIDIA, Netflix, OpenAI, Oracle, Palantir, SAP, Salesforce, 
Spotify, Stripe, Uber

How to run: 
- Install pandas, ploty, dash
- Run
- Go to address shown in terminal 
