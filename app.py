from pathlib import Path

import streamlit as st
import plotly.express as px
import duckdb
import pandas as pd
import json
import numpy as np

# ==========================================
# STREAMLIT DASHBOARD
# ==========================================

# 1. Connect to database
# Connect to an existing DuckDB database
@st.cache_data
def load_data():
    conn = duckdb.connect("data/db/jobsdb.db")
    df = conn.execute("""
        SELECT *
        FROM SGJobData_CleanedAndExploded
        """).fetchdf()
    conn.close()
    return df

df = load_data()

# 2. Layout
st.set_page_config(page_title="Singapore-Talent-Intelligence- Dashboard", layout="wide")
st.title("Singapore-Talent-Intelligence- Dashboard")

st.header("Overview")

with st.sidebar:
    st.header("Filters")
    st.sidebar.image("logo.jpg",use_container_width=True)
    category_options = sorted(df["parsed_categories"].dropna().unique())
    selected_categories = st.multiselect(
        "Industry", category_options, default=category_options)
    
    employee_type_options = sorted(df["employmentTypes"].dropna().unique())
    selected_employee_types = st.selectbox("Employment Type", ["All"] + employee_type_options)

    default_range = (
        df["metadata_originalPostingDate"].min().date(),
        max(df["metadata_originalPostingDate"].max(), df["metadata_newPostingDate"].max()).date())

    if "date_filter" not in st.session_state:
        st.session_state.date_filter = default_range

    def reset_date():
        st.session_state.date_filter = default_range

    date_range = st.sidebar.date_input("Posting Date range", key="date_filter")

    st.sidebar.button("Reset date range", on_click=reset_date)
    #if len(st.session_state.date_filter) == 2:
    #    start_date, end_date = st.session_state.date_filter
    

    # # Date range picker in sidebar
    # date_range  = st.sidebar.date_input(
    # "Posting Date Range",
    # value=(
    #     df["metadata_originalPostingDate"].min().date(),
    #     max(df["metadata_originalPostingDate"].max(), df["metadata_newPostingDate"].max()).date())
    # )
    
# ============================================================
# APPLY SIDEBAR FILTERS
# ============================================================

# Start with a copy of the complete dataframe
df_filtered = df.copy()

# ------------------------------------------------------------
# 1. Industry filter
# ------------------------------------------------------------
if selected_categories:
    df_filtered = df_filtered[
        df_filtered["parsed_categories"].isin(selected_categories)
    ]

# ------------------------------------------------------------
# 2. Employment Type filter
# ------------------------------------------------------------
if selected_employee_types != "All":
    df_filtered = df_filtered[
        df_filtered["employmentTypes"] == selected_employee_types
    ]

# ------------------------------------------------------------
# 3. Date filter
# ------------------------------------------------------------
if len(date_range) == 2:

    start_date, end_date = map(pd.Timestamp, date_range)

    df_filtered = df_filtered[
        (
            (
                df_filtered["metadata_originalPostingDate"] >= start_date
            )
            &
            (
                df_filtered["metadata_originalPostingDate"] <= end_date
            )
        )
        |
        (
            (
                df_filtered["metadata_newPostingDate"] >= start_date
            )
            &
            (
                df_filtered["metadata_newPostingDate"] <= end_date
            )
        )
    ]

elif len(date_range) == 1:
    st.warning("Please select an end date")

# 3. Basic KPI Info
col1, col2, col3 = st.columns(3)
col1.metric("Total Postings", len(df_filtered["metadata_jobPostId"].unique()))
col2.metric("Sectors", len(df_filtered["parsed_categories"].unique()))
df_clean = df_filtered.drop_duplicates("metadata_jobPostId")
df_clean=df_clean[df_clean["status_jobStatus"] != "Closed"]
col3.metric("Current Job Openings", df_clean["numberOfVacancies"].sum())

with st.expander("View raw data"):
    st.dataframe(df_filtered.head(10))

# 4. Visualizations
tab1, tab2 = st.tabs(["Sectors Analysis", "Job Level Analysis"])

with tab1:

    # ============================================================
    # HIGHEST PAYING JOB SECTORS
    # ============================================================
    with st.expander("Highest Paying Job Sectors"):

        st.subheader("Highest Paying Job Sectors")

        salary_by_sector = (
            df_filtered.groupby("parsed_categories")["average_salary"]
            .mean()
            .round()
            .sort_values(ascending=False)
            .reset_index()
        )

        salary_by_sector = salary_by_sector.rename(
            columns={"parsed_categories": "Sectors"}
        )

        salary_by_sector["average_salary"] = (
            salary_by_sector["average_salary"]
            .round()
            .astype(int)
        )

        st.dataframe(
            salary_by_sector.head(10),
            use_container_width=True,
            hide_index=True
        )

        chart_data = (
            salary_by_sector.head(10)
            .sort_values("average_salary", ascending=True)
        )

        fig = px.bar(
            chart_data,
            x="average_salary",
            y="Sectors",
            orientation="h",
            title="Top 10 Highest Paying Job Sectors",
            color_discrete_sequence=["#2E7D32"],
            labels={
                "average_salary": "Average Salary ($)",
                "Sectors": "Sector"
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

    # ============================================================
    # PREPARE SECTOR DATA
    # ============================================================

    sector_data = (
        df_filtered.groupby("parsed_categories")
        .agg(
            total_postings=("metadata_jobPostId", "count"),
            total_vacancies=("numberOfVacancies", "sum"),
            total_applications=(
                "metadata_totalNumberJobApplication",
                "sum"
            ),
            avg_reposts=("metadata_repostCount", "mean")
        )
        .reset_index()
    )

    # Rename sector column
    sector_data = sector_data.rename(
        columns={"parsed_categories": "Sectors"}
    )

    # Same filter for BOTH analyses
    sector_data = sector_data[
        sector_data["total_postings"] >= 30
    ]

    # Calculate applications per vacancy
    sector_data["applications_per_vacancy"] = (
        sector_data["total_applications"]
        / sector_data["total_vacancies"]
    ).replace(
        [np.inf, -np.inf],
        np.nan
    )

    # Remove invalid values
    sector_data = sector_data.dropna(
        subset=["applications_per_vacancy"]
    )

    # Optional: round applications per vacancy
    sector_data["applications_per_vacancy"] = (
        sector_data["applications_per_vacancy"]
        .round(2)
        #.astype(int)
    )

    # ============================================================
    # HIGHEST TALENT DEMAND
    # ============================================================

    with st.expander("Which sectors have the highest talent demand?"):

        st.caption(
            "Sectors with more vacancies represent higher "
            "employer demand for talent."
        )

        high_demand = (
            sector_data
            .sort_values(
                "total_vacancies",
                ascending=False
            )
            .head(10)
        )

        st.dataframe(
            high_demand[
                [
                    "Sectors",
                    "total_vacancies",
                    "total_applications",
                    "applications_per_vacancy"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        high_demand_chart = (
            high_demand
            .sort_values(
                "total_vacancies",
                ascending=True
            )
        )

        fig = px.bar(
            high_demand_chart,
            x="total_vacancies",
            y="Sectors",
            orientation="h",
            title="Top 10 Sectors with Highest Talent Demand",
            color_discrete_sequence=["#00897B"],
            labels={
                "total_vacancies": "Total Vacancies",
                "Sectors": "Sector"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ============================================================
    # LOWEST APPLICATIONS PER VACANCY
    # ============================================================

    with st.expander(
        "Which sectors may be struggling to find enough applicants?"
    ):

        st.caption(
            "Sectors with fewer applications per vacancy may "
            "indicate a potential skills gap."
        )

        low_applications = (
            sector_data
            .sort_values(
                "applications_per_vacancy",
                ascending=True
            )
            .head(10)
        )

        st.dataframe(
            low_applications[
                [
                    "Sectors",
                    "total_vacancies",
                    "total_applications",
                    "applications_per_vacancy"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        low_applications_chart = (
            low_applications
            .sort_values(
                "applications_per_vacancy",
                ascending=False
            )
        )

        fig = px.bar(
            low_applications_chart,
            x="applications_per_vacancy",
            y="Sectors",
            orientation="h",
            title="Top 10 Sectors with Lowest Applications per Vacancy",
            color_discrete_sequence=["#3F51B5"],
            labels={
                "applications_per_vacancy": "Applications per Vacancy",
                "Sectors": "Sector"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ============================================================
    # POTENTIAL SKILLS GAPS
    # ============================================================

    with st.expander("Which sectors show potential skills gaps?"):

        st.caption(
            "These sectors have high vacancy demand and relatively "
            "low applications per vacancy."
        )

        # Get sectors appearing in BOTH top 10 lists
        high_demand_sectors = set(
            high_demand["Sectors"]
        )

        low_supply_sectors = set(
            low_applications["Sectors"]
        )

        potential_gaps = (
            sector_data[
                sector_data["Sectors"].isin(
                    high_demand_sectors
                    & low_supply_sectors
                )
            ]
            .sort_values(
                "applications_per_vacancy",
                ascending=True
            )
        )

        # Show table
        st.dataframe(
            potential_gaps[
                [
                    "Sectors",
                    "total_vacancies",
                    "total_applications",
                    "applications_per_vacancy"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # ========================================================
        # SCATTER PLOT
        # ========================================================

        fig = px.scatter(
            sector_data,
            x="total_vacancies",
            y="applications_per_vacancy",
            hover_name="Sectors",
            color="Sectors",
            size="total_vacancies",
            title="High Talent Demand vs Applicant Supply",
            labels={
                "total_vacancies": "Total Vacancies",
                "applications_per_vacancy":
                    "Applications per Vacancy"
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
            "Sectors toward the bottom-right have high vacancy demand "
            "but relatively fewer applications per vacancy, which may "
            "indicate a potential skills gap."
        )
with tab2:
    with st.expander("Job Vacancy Heatmap"):
        st.subheader("Job Vacancy Heatmap")

        def experience_group(years):
            if years <= 2:
                return "Entry"
            elif years <= 5:
                return "Mid"
            elif years <= 10:
                return "Senior"
            else:
                return "Expert"
            
        df_filtered["experience_group"] = df_filtered["minimumYearsExperience"].map(experience_group)

        # Create a frequency table
        heatmap_data = (
            df_filtered.groupby(["parsed_categories", "experience_group", "numberOfVacancies"])
            .size()
            .reset_index(name="count")
        )

        fig = px.density_heatmap(
            heatmap_data,
            x="experience_group",
            y="parsed_categories",
            z="count",
            color_continuous_scale="Blues",
            category_orders={
            "experience_group": ["Entry", "Mid", "Senior", "Expert"],
            "parsed_categories": sorted(heatmap_data["parsed_categories"].unique())},
            text_auto=True
        )

        fig.update_xaxes(
                    ticktext=["Entry<br>(0-2) Yrs", "Mid<br>(3-5) Yrs", "Senior<br>(6-10) Yrs", "Expert<br>(10+) Yrs"], 
                    tickvals=["Entry", "Mid", "Senior", "Expert"]
        )
        fig.update_layout(
            height=1000,
            xaxis=dict(tickfont=dict(size=10), side ="top"),
            xaxis_title="<b>Experience Level</b>",
            yaxis=dict(tickfont=dict(size=10)),
            yaxis_title="<b>Sector</b>",
            coloraxis_colorbar_title="<b>Number of Vacancies</b>"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    with st.expander("Job Level Mix Within Each Sector"):
        st.subheader("Job Level Mix Within Each Sector")
    
        industry_joblevel = (
        df_filtered.groupby(["parsed_categories", "experience_group"])
        .size()
        .reset_index(name="numberOfVacancies")
        )
    
        # Calculate percentage within each industry
        industry_joblevel["Percentage"] = (
        industry_joblevel["numberOfVacancies"]
        / industry_joblevel.groupby("parsed_categories")["numberOfVacancies"].transform("sum")
        * 100
        )
        
        fig = px.bar(
        industry_joblevel,
        x="Percentage",
        y="parsed_categories",
        color="experience_group",
        labels={
            "parsed_categories": "Sector",
            "Percentage": "Percentage of Vacancies",
            "experience_group": "Experience Level"
        },
        barmode="stack",
        category_orders={
                "experience_group": ["Entry", "Mid", "Senior", "Expert"],
                "parsed_categories": sorted(heatmap_data["parsed_categories"].unique())}
        # text="Percentage",
        # text_auto=".0f"
    )
        fig.update_xaxes(
            ticktext=["Entry<br>(0-2) Yrs", "Mid<br>(3-5) Yrs", "Senior<br>(6-10) Yrs", "Expert<br>(10+) Yrs"], 
            tickvals=["Entry", "Mid", "Senior", "Expert"]
        )


        fig.update_layout(
            height=1000,
            xaxis=dict(tickfont=dict(size=10), side ="top"),
            xaxis_title="<b>Percentage of Vacancies</b>",
            yaxis=dict(tickfont=dict(size=10)),
            yaxis_title="<b>Sector</b>",
            legend_title="<b>Experience Level</b>",
        )
        # fig.update_traces(
        #     textposition="inside",
        #     texttemplate="%{text}%"
        # )

        st.plotly_chart(fig, width='stretch')
