from pathlib import Path

import streamlit as st
import plotly.express as px
import duckdb
import pandas as pd

st.set_page_config(page_title="Singapore Job Market Dashboard", layout="wide")

# Connect to an existing DuckDB database
@st.cache_data
def load_data():
    conn = duckdb.connect("data/jobsdb.db")
    df = conn.execute("""
        SELECT *
        FROM SGJobData_CleanedAndExploded limit 100000
        """).fetchdf()
    conn.close()
    return df

df = load_data()
st.title("Singapore Job Market Dashboard")

st.header("Overview")

with st.sidebar:
    st.header("Filters")
    category_options = sorted(df["parsed_categories"].dropna().unique())
    selected_categories = st.multiselect(
        "Industry", category_options, default=category_options)
    
    employee_type_options = sorted(df["employmentTypes"].dropna().unique())
    selected_employee_types = st.selectbox("Employment Type", ["All"] + employee_type_options)

    # Date range picker in sidebar
    date_range  = st.sidebar.date_input(
    "Posting Date Range",
    value=(
        df["metadata_originalPostingDate"].min().date(),
        max(df["metadata_originalPostingDate"].max(), df["metadata_newPostingDate"].max()).date())
    )
    
df_filtered = df[df["parsed_categories"].isin(selected_categories)]
if selected_employee_types != "All":
    df_filtered = df_filtered[df_filtered["employmentTypes"] == selected_employee_types]


if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df[
    (
        df["metadata_originalPostingDate"].between(start_date, end_date)
    ) &
    (
        df["metadata_newPostingDate"].between(start_date, end_date)
    )
]


col1, col2, col3 = st.columns(3)
col1.metric("Total Postings", len(df_filtered))
col2.metric("Industry", len(df_filtered["parsed_categories"].unique()))
col3.metric("Current Job Openings", df_filtered[df_filtered["status_jobStatus"] != "Closed"]["numberOfVacancies"].sum())
with st.expander("View raw data"):
    st.dataframe(df_filtered)

tab1,tab2 = st.tabs(["Job Vacancy Heatmap", "Job Level Mix"])

with tab1:
    st.subheader("Job Vacancy Heatmap")

    def experience_group(years):
        if years <= 2:
            return "Entry<br>(0-2) Yrs"
        elif years <= 5:
            return "Mid <br>(3-5) Yrs"
        elif years <= 10:
            return "Senior<br>(6-10) Yrs"
        else:
            return "Expert<br>(10+) Yrs"
        
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
        "experience_group": ["Entry(0-2) Yrs", "Mid <br>(3-5) Yrs", "Senior<br>(6-10) Yrs", "Expert<br>(10+) Yrs"],
        "parsed_categories": sorted(heatmap_data["parsed_categories"].unique())},
        text_auto=True
    )
    fig.update_layout(
        height=1000,
        xaxis=dict(tickfont=dict(size=10), side ="top"),
        xaxis_title="<b>Experience Level</b>",
        yaxis=dict(tickfont=dict(size=10)),
        yaxis_title="<b>Industry Category</b>",
        coloraxis_colorbar_title="<b>Number of Vacancies</b>"
    )
    
    st.plotly_chart(fig, use_container_width=True)
with tab2:

    st.subheader("Job Level Mix Within Each Industry")
   
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
        "parsed_categories": "Industry",
        "Percentage": "Percentage of Vacancies",
        "experience_group": "Experience Level"
    },
    barmode="stack",
    category_orders={
            "experience_group": ["Entry(0-2) Yrs", "Mid <br>(3-5) Yrs", "Senior<br>(6-10) Yrs", "Expert<br>(10+) Yrs"],
            "parsed_categories": sorted(heatmap_data["parsed_categories"].unique())}
    # text="Percentage",
    # text_auto=".0f"
)

fig.update_layout(
    height=1000,
    xaxis=dict(tickfont=dict(size=10), side ="top"),
    xaxis_title="<b>Percentage of Vacancies</b>",
    yaxis=dict(tickfont=dict(size=10)),
    yaxis_title="<b>Industry</b>",
    legend_title="<b>Experience Level</b>",
)
# fig.update_traces(
#     textposition="inside",
#     texttemplate="%{text}%"
# )

st.plotly_chart(fig, width='stretch')
