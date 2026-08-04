import plotly.express as px
import streamlit as st
import pandas as pd
import json
import numpy as np

# ==========================================
# 1. LOAD AND CLEAN DATA
# ==========================================

@st.cache_data
def process_job_data(file_path):

    optimized_dtypes = {
        'employmentTypes': 'category',
        'metadata_isPostedOnBehalf': 'boolean',
        'metadata_jobPostId': 'string',
        'metadata_repostCount': 'Int16',
        'metadata_totalNumberJobApplication': 'Int32',
        'metadata_totalNumberOfView': 'Int32',
        'minimumYearsExperience': 'Int8',
        'numberOfVacancies': 'Int16',
        'positionLevels': 'category',
        'postedCompany_name': 'string',
        'salary_maximum': 'float32',
        'salary_minimum': 'float32',
        'salary_type': 'category',
        'status_jobStatus': 'category',
        'title': 'string',
        'average_salary': 'float32'
    }

    date_cols = [
        'metadata_expiryDate',
        'metadata_newPostingDate',
        'metadata_originalPostingDate'
    ]

    df = pd.read_csv(
        file_path,
        dtype=optimized_dtypes,
        parse_dates=date_cols,
        dayfirst=True,
        low_memory=False
    )

    # Remove empty occupationId
    if 'occupationId' in df.columns:
        df = df.drop(columns=['occupationId'])

    # Remove extreme values
    bad_rows = (
        (df['minimumYearsExperience'] > 50) |
        (df['salary_maximum'] > 1000000)
    )

    df = df[~bad_rows]

    # Parse categories
    def extract_categories(json_str):

        if pd.isna(json_str):
            return []

        try:
            parsed = json.loads(json_str)

            return [
                item.get('category')
                for item in parsed
                if 'category' in item
            ]

        except (json.JSONDecodeError, TypeError):
            return []

    df['parsed_categories'] = df['categories'].apply(
        extract_categories
    )

    df = df.drop(columns=['categories'])

    # Remove rows missing important information
    df = df.dropna(
        subset=['title', 'metadata_jobPostId']
    )

    return df


# ==========================================
# 2. STREAMLIT DASHBOARD
# ==========================================

st.title("Singapore-Talent-Intelligence- Dashboard")

# Load cleaned data
df_clean = process_job_data("SGJobData.csv")

st.success("Data loaded and cleaned successfully!")


# ==========================================
# 3. BASIC INFORMATION
# ==========================================

st.write("Number of cleaned records:", len(df_clean))


# ==========================================
# 4. HIGHEST PAYING JOB CATEGORIES
# ==========================================

salary_by_sector = (
    df_clean.explode('parsed_categories')
    .groupby('parsed_categories')['average_salary']
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

salary_by_sector = salary_by_sector.rename(
    columns={'parsed_categories': 'Sectors'})

st.subheader("Highest Paying Job Sectors")

st.dataframe(
    salary_by_sector.head(10),
    use_container_width=True
)

chart_data = salary_by_sector.head(10).sort_values(
    "average_salary",
    ascending=True
)

fig = px.bar(
    chart_data,
    x="average_salary",
    y="Sectors",
    orientation="h",
    title="Top 10 Highest Paying Job Sectors",
    labels={
        "average_salary": "Average Salary ($)",
        "Sectors": "Sector"
    }
)

fig.update_layout(
    height=700,
    font=dict(size=18),
    title_font=dict(size=28),
    xaxis=dict(
        title_font=dict(size=20),
        tickfont=dict(size=16)
    ),
    yaxis=dict(
        title_font=dict(size=20),
        tickfont=dict(size=16)
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# SECTORS EXPERIENCING SKILLS GAPS
# ==========================================

st.subheader("Which sectors may be struggling to find enough applicants?")
st.caption(
    "Sectors with fewer applications per vacancy may indicate a potential skills gap."
)

# Explode categories
df_exploded = df_clean.explode('parsed_categories')

# Calculate sector metrics
sector_metrics = df_exploded.groupby('parsed_categories').agg(
    total_postings=('metadata_jobPostId', 'count'),
    total_vacancies=('numberOfVacancies', 'sum'),
    total_applications=('metadata_totalNumberJobApplication', 'sum'),
    avg_repost_count=('metadata_repostCount', 'mean'),
    avg_salary=('average_salary', 'mean'),
    avg_years_exp=('minimumYearsExperience', 'mean')
).reset_index()

sector_metrics = sector_metrics.rename(
    columns={'parsed_categories': 'Sectors'}
)

# Only include sectors with at least 30 postings
sector_metrics = sector_metrics[
    sector_metrics['total_postings'] >= 30
]

# Calculate applications per vacancy
sector_metrics['apps_per_vacancy'] = (
    sector_metrics['total_applications'] /
    sector_metrics['total_vacancies']
).replace([np.inf, -np.inf], np.nan)

# Identify potential skills gaps
shortages = sector_metrics.sort_values(
    by=['avg_repost_count', 'apps_per_vacancy'],
    ascending=[False, True]
).dropna(subset=['apps_per_vacancy'])

# Select columns to display
columns_to_display = [
    'Sectors',
    'total_vacancies',
    'avg_repost_count',
    'apps_per_vacancy',
    'avg_salary'
]

# # Display table
# st.dataframe(
#     shortages[columns_to_display].head(10),
#     use_container_width=True
# )
# shortage_chart_data = shortages.head(10).sort_values(
#     "apps_per_vacancy",
#     ascending=False
# )
# fig = px.bar(
#     shortage_chart_data,
#     x="apps_per_vacancy",
#     y="Sectors",
#     orientation="h",
#     title="Top 10 Sectors with Lowest Applications per Vacancy",
#     labels={
#         "apps_per_vacancy": "Applications per Vacancy",
#         "Sectors": "Sector"
#     }
# )

# fig.update_layout(
#     height=600,
#     font=dict(size=16),
#     title_font=dict(size=24),
#     xaxis=dict(
#         title_font=dict(size=18),
#         tickfont=dict(size=14)
#     ),
#     yaxis=dict(
#         title_font=dict(size=18),
#         tickfont=dict(size=14)
#     )
# )

# st.plotly_chart(
#     fig,
#     use_container_width=True
# )
# ==========================================
# HIGHEST TALENT DEMAND BY SECTOR
# ==========================================

st.subheader("Which sectors have the highest talent demand?")

st.caption(
    "Sectors with more vacancies represent higher employer demand for talent."
)

# Field categories with the highest talent demand
high_demand = (
    df_clean
    .explode('parsed_categories')
    .groupby('parsed_categories')
    .agg(
        total_postings=('metadata_jobPostId', 'count'),
        total_vacancies=('numberOfVacancies', 'sum'),
        total_applications=('metadata_totalNumberJobApplication', 'sum'),
        avg_reposts=('metadata_repostCount', 'mean')
    )
    .reset_index()
)

# Rename category to Sectors
high_demand = high_demand.rename(
    columns={'parsed_categories': 'Sectors'}
)

# Only include sectors with at least 30 job postings
high_demand = high_demand[
    high_demand['total_postings'] >= 30
]

# Calculate applications per vacancy
high_demand['applications_per_vacancy'] = (
    high_demand['total_applications'] /
    high_demand['total_vacancies']
).replace([np.inf, -np.inf], np.nan)

# Sort by highest demand
high_demand = high_demand.sort_values(
    by=['total_vacancies', 'applications_per_vacancy'],
    ascending=[False, True]
).dropna(subset=['applications_per_vacancy'])


# ------------------------------------------
# TABLE
# ------------------------------------------

st.dataframe(
    high_demand.head(10),
    use_container_width=True
)


# ------------------------------------------
# BAR CHART
# ------------------------------------------

high_demand_chart = high_demand.head(10).sort_values(
    'total_vacancies',
    ascending=True
)

fig = px.bar(
    high_demand_chart,
    x='total_vacancies',
    y='Sectors',
    orientation='h',
    title='Top 10 Sectors with Highest Demand',
    labels={
        'total_vacancies': 'Total Vacancies',
        'Sectors': 'Sector'
    }
)

fig.update_layout(
    height=600,
    font=dict(size=16),
    title_font=dict(size=24),
    xaxis=dict(
        title_font=dict(size=18),
        tickfont=dict(size=14)
    ),
    yaxis=dict(
        title_font=dict(size=18),
        tickfont=dict(size=14)
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)
# ==========================================
# HIGH DEMAND VS LOW APPLICATIONS
# ==========================================

st.subheader("Which sectors have high demand and low applicant supply?")

st.caption(
    "Sectors with many vacancies and fewer applications per vacancy "
    "may indicate a potential skills gap."
)

# Create sector-level data
sector_comparison = (
    df_clean
    .explode('parsed_categories')
    .groupby('parsed_categories')
    .agg(
        total_postings=('metadata_jobPostId', 'count'),
        total_vacancies=('numberOfVacancies', 'sum'),
        total_applications=('metadata_totalNumberJobApplication', 'sum')
    )
    .reset_index()
)

# Rename sector column
sector_comparison = sector_comparison.rename(
    columns={'parsed_categories': 'Sectors'}
)

# Remove sectors with too few postings
sector_comparison = sector_comparison[
    sector_comparison['total_postings'] >= 30
]

# Calculate applications per vacancy
sector_comparison['applications_per_vacancy'] = (
    sector_comparison['total_applications'] /
    sector_comparison['total_vacancies']
).replace([np.inf, -np.inf], np.nan)

# Remove invalid values
sector_comparison = sector_comparison.dropna(
    subset=['applications_per_vacancy']
)
demand_chart = high_demand.sort_values(
    'total_vacancies',
    ascending=True
)


# ==========================================
# FIND HIGH-DEMAND SECTORS
# ==========================================

high_demand = sector_comparison.sort_values(
    'total_vacancies',
    ascending=False
).head(10)

# ==========================================
# FIND LOW APPLICATIONS PER VACANCY
# ==========================================

low_applications = sector_comparison.sort_values(
    'applications_per_vacancy',
    ascending=True
).head(10)

# ==========================================
# DISPLAY BOTH
# ==========================================

st.write("### Highest Demand Sectors")

st.dataframe(
    high_demand[
        [
            'Sectors',
            'total_vacancies',
            'total_applications',
            'applications_per_vacancy'
        ]
    ],
    use_container_width=True
)


st.write("### Lowest Applications per Vacancy")

st.dataframe(
    low_applications[
        [
            'Sectors',
            'total_vacancies',
            'total_applications',
            'applications_per_vacancy'
        ]
    ],
    use_container_width=True
)

# ==========================================
# SECTORS APPEARING IN BOTH
# ==========================================

high_demand_sectors = set(high_demand['Sectors'])
low_supply_sectors = set(low_applications['Sectors'])

potential_gaps = sector_comparison[
    sector_comparison['Sectors'].isin(
        high_demand_sectors & low_supply_sectors
    )
].sort_values(
    'applications_per_vacancy',
    ascending=True
)

st.write("### Potential Skills Gaps")

st.caption(
    "These sectors have both high vacancy demand and relatively "
    "low applications per vacancy."
)

st.dataframe(
    potential_gaps[
        [
            'Sectors',
            'total_vacancies',
            'total_applications',
            'applications_per_vacancy'
        ]
    ],
    use_container_width=True
)
fig = px.scatter(
    sector_comparison,
    x="total_vacancies",
    y="applications_per_vacancy",
    hover_name="Sectors",
    size="total_vacancies",
    title="High Demand vs Applications per Vacancy",
    labels={
        "total_vacancies": "Total Vacancies",
        "applications_per_vacancy": "Applications per Vacancy"
    }
)

fig.update_layout(
    height=600,
    font=dict(size=16),
    title_font=dict(size=24),
    xaxis=dict(
        title_font=dict(size=18),
        tickfont=dict(size=14)
    ),
    yaxis=dict(
        title_font=dict(size=18),
        tickfont=dict(size=14)
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)
st.caption(
    "Sectors in the bottom-right have high vacancy demand "
    "but relatively fewer applications per vacancy, indicating "
    "a potential skills gap."
)

