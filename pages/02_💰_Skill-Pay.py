import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from modules.formater import Title, Footer
from modules.importer import SQLImport
from modules.importer import DataImport
from google.cloud import bigquery

# Title page and footer
title = "🛠️ Skills"
t = Title().page_config(title)
f = Footer().footer()

############################ 
# Create drop down filter options
############################ 
select_all = "Select All"
# Job sort, count, and filter list data
title_query = """
    SELECT job_title, COUNT(job_title) AS job_title_count
    FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact
    GROUP BY job_title
    ORDER BY job_title_count DESC
"""
job_agg = 'job_title'
job_count = SQLImport().sql_df_query(title_query)
jobs = list(job_count.job_title)
jobs.insert(0, select_all)

############################ 
# Sidebar filter build
############################ 

# Number skill selctor for slider
skill_dict = {"All" : 1000, "Top 10": 10, "Top 20": 20, "Top 50 ": 50 }

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
st.markdown("## 💰 Pay for Skills 🛠️")
job_choice = st.selectbox("Job Title:", jobs)
keyword_list = {'All': 'keywords_all', 'Languages': 'keywords_programming', 'Tools': 'keywords_analyst_tools', 'Databases': 'keywords_databases', 'Cloud': 'keywords_cloud', 'Libraries': 'keywords_libraries', 'Frameworks': 'keywords_webframeworks'} # , 'Async': 'keywords_async' 
#  "OS's": 'keywords_os', 'Async': 'keywords_async'
# Missing 'sync' in database
keyword_choice = st.radio('Skills:', keyword_list.keys(), horizontal=True) # label_visibility="collapsed"

############################ 
# Every keyword column info to merge
############################ 
keyword_df = pd.DataFrame()
for key, value in keyword_list.items():
    keyword_query = """
        SELECT keywords.element
        FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_skills,
            UNNEST({value}.list) AS keywords   
        GROUP BY keywords.element
        """.format(value=value)
    # NOTE: BAD PRACTICE to use f-string in SQL query, liable to injection attack... but "should" be safe here
    keyword_values = SQLImport().sql_df_query(keyword_query)
    keyword_values['keyword'] = value
    # keyword_df = keyword_df.append(keyword_values)
    keyword_df = pd.concat([keyword_df, keyword_values], ignore_index=True)

############################ 
# Skill pay query
############################ 
if job_choice == select_all:
    job_choice_query = ''
    job_config = None
else:
    job_choice_query = f"WHERE job_title = @job_choice"
    job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("job_choice", "STRING", job_choice)
    ]
)
skill_query = """
    SELECT
        keywords.element AS skill,
        ROUND(AVG(salary_year)) AS avg_salary,
        APPROX_QUANTILES(salary_year,2)[OFFSET(1)] AS med_salary,
        COUNT(m.job_id) AS job_count
    FROM
        `job-listings-366015`.gsearch_job_listings_clean.gsearch_salary AS m
    LEFT JOIN `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact AS f ON
        f.job_id = m.job_id
    LEFT JOIN `job-listings-366015`.gsearch_job_listings_clean.gsearch_skills AS s ON
    m.job_id = s.job_id,
        UNNEST(keywords_all.list) AS keywords
    {job_choice_query}
    GROUP BY
        skill
    HAVING
        job_count > 1
    ORDER BY
        med_salary DESC
""".format(job_choice_query=job_choice_query)

skill_pay = SQLImport().sql_df_query(skill_query, job_config)

# merge skill_pay with keyword_df to get all keywords
skill_pay = skill_pay.join(keyword_df.set_index('element'), on='skill')

# filter skill_pay by keyword column values
skill_pay = skill_pay[skill_pay.keyword == keyword_list[keyword_choice]]

############################ 
# Graph results
############################
df = skill_pay.head(skill_dict[top_n_choice]) 
x = 'med_salary'
y = 'skill'
tooltip_1 = 'job_count'
tooltip_2 = 'avg_salary'
bars = alt.Chart(df, height=alt.Step(30) # adjust the spacing of the bars
).mark_bar(
    cornerRadiusBottomRight=5,
    cornerRadiusTopRight=5    
).encode(
    y=alt.Y(y, sort=None, title="", axis=alt.Axis(labelFontSize=20) ), # , labelAngle=-35
    x=alt.X(x, axis=None), # title="Median Pay per Skill", axis=alt.Axis(format='$,r', labelFontSize=17, titleFontSize=17)),
    color=alt.Color(x, legend=None, scale=alt.Scale(scheme='darkmulti')), 
    tooltip=[y, alt.Tooltip(x, format="$,r"), alt.Tooltip(tooltip_2, format="$,r"), alt.Tooltip(tooltip_1, format=",")]
)

text = bars.mark_text(
    align='left',
    baseline='middle',
    color='white',
    dx=3, 
    fontSize=20
).encode(
    text=alt.Text(x, format="$,r")
)

final_chart = alt.layer(bars, text
).configure_view(
    strokeWidth=0
).configure_scale(
    bandPaddingInner=0.2 # adjust the width of the bars
).configure_axis(
    grid=False
)

st.altair_chart(final_chart, use_container_width=True)

# # Aggregate skills daily
# def agg_skill_daily_data(jobs_df):
#     jobs_df['date'] = jobs_df.date_time.dt.date
#     first_date = jobs_all.date.min()
#     last_date = jobs_all.date.max()
#     list_dates = pd.date_range(first_date,last_date,freq='d')
#     list_dates = pd.DataFrame(list_dates)
#     list_dates = list_dates[0].dt.date
#     skill_daily_df = pd.DataFrame()
#     for date in list_dates:
#         date_df = jobs_df[jobs_df.date == date]
#         if len(date_df) == 0: # throws error if df is blank
#             continue
#         date_agg_df = pd.DataFrame(date_df.description_tokens.sum()).value_counts().rename_axis('keywords').reset_index(name='counts')
#         date_agg_df = date_agg_df[date_agg_df.keywords != '']
#         date_agg_df['skill_percent'] = date_agg_df.counts / len(date_df)
#         date_agg_df['date'] = date
#         skill_daily_df = pd.concat([date_agg_df, skill_daily_df], ignore_index=True, axis=0)
#     return skill_daily_df

# skill_daily_data = agg_skill_daily_data(jobs_all)
# skill_daily_data = skill_daily_data[skill_daily_data.keywords.isin(skill_all_time_list)]

# # Daily trend line chart
# source = skill_daily_data
# x = 'date'
# y = 'skill_percent'
# color = 'keywords'
# selector = alt.selection_single(encodings=['x', 'y'])
# hover = alt.selection_single(
#     fields=[x],
#     nearest=True,
#     on="mouseover",
#     empty="none",
# )
# lines = (
#     alt.Chart(source)
#     .mark_line(point="transparent")
#     .encode(x=alt.X(x, title="Date", axis=alt.Axis(labelFontSize=15, titleFontSize=17)), 
#         y=alt.Y(y, title="Likelyhood to be in Job Posting", 
#         axis=alt.Axis(format='%', labelFontSize=17, titleFontSize=17)), 
#         color=color) # Modified this
#     .transform_calculate(color='datum.delta < 0 ? "red" : "lightblue"') # doesn't show red for negative delta
# )
# points = (
#     lines.transform_filter(hover)
#     .mark_circle(size=65)
#     .encode(color=alt.Color("color:N", scale=None))
# )
# tooltips = (
#     alt.Chart(source)
#     .mark_rule(opacity=0)
#     .encode(
#         x=x,
#         y=y,
#         tooltip=[color, alt.Tooltip(y, format=".1%"), x],
#     )
#     .add_selection(hover)
# )
# daily_trend_chart = (lines + points + tooltips).interactive().configure_view(strokeWidth=0)

# if graph_choice == graph_list[0]:
#     st.altair_chart(all_time_chart, use_container_width=True)
# else:
#     st.altair_chart(daily_trend_chart, use_container_width=True)
