import streamlit as st
import pandas as pd
from modules.formater import Title, Footer
from modules.importer import SQLImport
from modules.grapher import GraphDF
from google.cloud import bigquery

############################ 
# Title page and footer
############################

title = "🛠️ Skills"
t = Title().page_config(title)
f = Footer().footer()

############################ 
# Create drop down filter options
############################ 

jobs = SQLImport().job_titles()

############################ 
# Sidebar filter build
############################ 

# Number skill selctor for slider
skill_dict = {"All" : 1000, "Top 10": 10, "Top 25": 25}

# # Job type filter data for slicers
# schedule_type_query = """
# SELECT job_schedule_type, COUNT(job_schedule_type) AS job_schedule_type_count
# FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact
# GROUP BY job_schedule_type
# ORDER BY job_schedule_type_count DESC
# """
# job_type = SQLImport().sql_df_query(schedule_type_query)
# job_type = job_type[job_type.job_schedule_type.notna()]
# job_type = list(job_type.job_schedule_type)
# job_type.insert(0, select_all)

# # location sort, count, and filter list data
# location_query = """
# SELECT job_location, COUNT(job_location) AS job_location_count
# FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact
# GROUP BY job_location
# ORDER BY job_location_count DESC
# """
# location_agg = 'job_location'
# location_count = SQLImport().sql_df_query(location_query)
# locations = list(location_count.job_location)
# locations.insert(0, select_all)

# # Platform sort, count, and filter for slicer
# platform_query = """
# SELECT job_via, COUNT(job_via) AS job_via_count
# FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact
# GROUP BY job_via
# ORDER BY job_via_count DESC
# """
# platform = SQLImport().sql_df_query(platform_query)
# platform = list(platform.job_via)
# platform.insert(0, select_all)

with st.sidebar:
    st.markdown("# 🛠️ Filters")
    top_n_choice = st.radio("Data Skills:", list(skill_dict.keys()))
    # job_type_choice = st.radio("Job Type:", job_type)
    # location_choice = st.selectbox("Location:", locations)
    # platform_choice = st.selectbox("Social Platform:", platform)

############################ 
# Top page build
############################ 

st.markdown("## 🛠️ Top Skills for Data Nerds 🤓")

job_choice = st.selectbox("Job Title:", jobs)

############################ 
# Keyword generation & slicer
############################ 

keyword_list = {'All': 'keywords_all', 'Languages': 'keywords_programming', 'Tools': 'keywords_analyst_tools', 'Databases': 'keywords_databases', 'Cloud': 'keywords_cloud', 'Libraries': 'keywords_libraries', 'Frameworks': 'keywords_webframeworks'} # , 'Async': 'keywords_async' 
#  "OS's": 'keywords_os', 'Async': 'keywords_async'
# Missing 'sync' in database

keyword_choice = st.radio('Skills:', keyword_list.keys(), horizontal=True) # label_visibility="collapsed"

keyword_df = SQLImport().keywords()

############################ 
# Skill percentage query
############################ 

if job_choice != "Select All":
    job_choice_query = f"WHERE job_title = @job_choice"
else:
    job_choice_query = ''
skill_query = """
    SELECT keywords.element                                             AS skill,
        COUNT(f.job_id) / (SELECT COUNT(*)
                                    FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact
                                    {job_choice_query}) AS skill_percent,
        COUNT(f.job_id)                                              AS skill_count
    FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_skills AS s, 
        UNNEST(keywords_all.list) AS keywords 
            LEFT JOIN `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact AS f ON f.job_id = s.job_id 
    {job_choice_query}
    GROUP BY skill 
    ORDER BY skill_count DESC
""".format(job_choice_query=job_choice_query)

skill_count = SQLImport().sql_df_query(skill_query, job_choice=job_choice)

# merge skill_count with keyword_df to get all keywords
skill_count = skill_count.join(keyword_df.set_index('element'), on='skill')

# filter skill_count by keyword column values
skill_count = skill_count[skill_count.keyword == keyword_list[keyword_choice]]

############################ 
# Graph results
############################
df = skill_count.head(skill_dict[top_n_choice]) 
x = 'skill_percent'
x_format = '.1%'
y = 'skill'
tooltip_1 = 'skill_count'
tooltip1_format = ','

final_chart = GraphDF().bar_chart(df=df, x=x, y=y, tooltip_1=tooltip_1, x_format=x_format, tooltip1_format=tooltip1_format)

st.altair_chart(final_chart, use_container_width=True)