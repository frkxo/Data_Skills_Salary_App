import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime
from modules.formater import Title, Footer
from modules.importer import SQLImport
from modules.grapher import GraphDF

############################ 
# Title page and footer
############################

title = "💸 Salary"
Title().page_config(title)
Footer().footer()

############################ 
# Import data from BigQuery
############################ 

sql_query = """
SELECT
	job_title,
	search_term,
	salary_avg,
	salary_min,
	salary_max,
	salary_year,
	salary_hour,
	search_location,
	job_location,
	job_schedule_type,
	job_via,
	s.keywords_all AS job_keywords
FROM
	`job-listings-366015`.gsearch_job_listings_clean.gsearch_salary AS d
LEFT JOIN `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact AS f ON
	f.job_id = d.job_id
LEFT JOIN `job-listings-366015`.gsearch_job_listings_clean.gsearch_skills AS s
                   ON
	s.job_id = d.job_id
"""

jobs_all = SQLImport().sql_df_query(sql_query)

############################ 
# Create drop down filters
############################ 
# Number skill selctor for slider
skill_dict = {"Top 10": 10, "Top 25": 25, "All" : 1000}

select_all = "Select All"
# # Job sort, count, and filter list data
# job_agg = 'job_title'
# job_count = jobs_all[job_agg].value_counts().rename_axis('jobs').reset_index(name='counts')
# jobs = list(job_count.jobs)
# jobs.insert(0, select_all)

# location sort, count, and filter list data
location_agg = 'job_location'
location_count = jobs_all[location_agg].value_counts().rename_axis('locations').reset_index(name='counts')
locations = list(location_count.locations)
locations.insert(0, select_all)

# Skill sort, count, and filter list data
skill_count = pd.DataFrame(jobs_all.job_keywords.sum()).value_counts().rename_axis('keywords').reset_index(name='counts')
skill_count = skill_count[skill_count.keywords != '']
skills = list(skill_count.keywords)
skills.insert(0, select_all)

# Platform sort, count, and filter list data
platform_count = jobs_all.job_via.value_counts().rename_axis('platforms').reset_index(name='counts')
platform = list(platform_count.platforms)
platform.insert(0, select_all)

# Other Filter data for slicers
job_type = pd.DataFrame(jobs_all.job_schedule_type.drop_duplicates())
job_type = job_type[job_type.job_schedule_type.notna()]
job_type = list(job_type.job_schedule_type)
job_type.insert(0, select_all)

with st.sidebar:
    st.markdown("# 💰 Filters")
    # job_choice = st.selectbox("Job Title:", jobs)
    top_n_choice = st.radio("Data Skills:", list(skill_dict.keys()))
    job_type_choice = st.radio("Job Type:", job_type)
    location_choice = st.selectbox("Location:", locations)
    skills_choice = st.selectbox("Data Skill:", skills)
    platform_choice = st.selectbox("Social Platform:", platform)

############################ 
# Graph salary histogram
############################ 
# Top page build
st.markdown("## 💸 Salary for Data Nerds")
salary_dict = {"Annual": "salary_year", "Hourly": "salary_hour"}
salary_choice = st.radio('Salary aggregation:', list(salary_dict.keys()), horizontal=True)

# Side column filter data transform
# if job_choice != select_all:
#     jobs_all = jobs_all[jobs_all[job_agg] == job_choice]
if location_choice != select_all:
    jobs_all = jobs_all[jobs_all[location_agg] == location_choice]
if skills_choice != select_all:
    jobs_all = jobs_all[jobs_all.job_keywords.apply(lambda x: skills_choice in x)]
if platform_choice != select_all:
    jobs_all = jobs_all[jobs_all.job_via.apply(lambda x: platform_choice in x)]
if job_type_choice != select_all:
    jobs_all = jobs_all[jobs_all.job_schedule_type.apply(lambda x: job_type_choice in str(x))]

# Man page filter data transform
salary_column = salary_dict[salary_choice]
column = jobs_all[salary_column]
bins = 'auto'

# Make filtered dataframe
salary_df = jobs_all[['job_title', salary_column, location_agg, 'job_keywords']] # select columns
salary_df = salary_df[salary_df[salary_column].notna()]
salary_df[salary_column] = salary_df[salary_column].astype(int)

salary_agg = salary_df.groupby('job_title').agg({salary_column: ['mean', 'median', 'min', 'max', 'count']})
salary_agg.columns = salary_agg.columns.droplevel(0)
salary_agg = salary_agg.reset_index()
salary_agg = salary_agg.sort_values(by='count', ascending=False)
salary_agg = salary_agg[salary_agg['min'] != salary_agg['max']] # remove jobs from same company posting multiple times

############################ 
# Graph results
############################
df = salary_agg.head(skill_dict[top_n_choice]).sort_values(by='median', ascending=False)
x = 'median'
y = 'job_title'
x_format = '$,.0f'
tooltip_1 = 'min'
tooltip1_format = '$,.0f'
tooltip_2 = 'max'
tooltip2_format = '$,.0f'
tooltip_3 = 'count'
tooltip3_format = ','

final_chart = GraphDF().bar_chart(df=df, x=x, y=y, tooltip_1=tooltip_1, tooltip_2=tooltip_2, tooltip_3=tooltip_3, x_format=x_format, tooltip1_format=tooltip1_format, tooltip2_format=tooltip2_format, tooltip3_format=tooltip3_format, x_labelFontSize=12)

st.altair_chart(final_chart, use_container_width=True)

# # Final visualizations
# try: 
#     selector = alt.selection_single(encodings=['x', 'y'])
#     salary_chart = alt.Chart(salary_df).mark_bar(
#         cornerRadiusTopLeft=10,
#         cornerRadiusTopRight=10    
#     ).encode(
#         x=alt.X(salary_column, title="Salary", axis=alt.Axis(format='$,f', labelFontSize=20, titleFontSize=17), bin = alt.BinParams(maxbins = 50)), # bins = len(salary_df[salary_column])/4
#         y=alt.Y('count()', title="Count of Job Postings", axis=alt.Axis(labelFontSize=17, titleFontSize=17)),
#         # color=alt.condition(selector, 'count()', alt.value('lightgray')),
#         tooltip=[alt.Tooltip(salary_column, format="$,"), 'count()']
#     ).add_selection(
#         selector
#     ).configure_view(
#         strokeWidth=0
#     )
#     st.altair_chart(salary_chart, use_container_width=True)
#     display_table = st.checkbox("Show table of salaries below 👇🏼")
#     if display_table:
#         st.markdown("#### 💵 Table of Salaries")
#         st.dataframe(salary_df)
# except:
#     st.markdown("# 🙅‍♂️ No results")