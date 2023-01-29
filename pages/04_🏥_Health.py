import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime
from modules.formater import Title, Footer
from modules.importer import SQLImport
from modules.importer import DataImport

# Title page and footer
title = "🏥 Health"
Title().page_config(title)
Footer().footer()

############################ 
# Import & clean data for health status
############################ 

# Init SQL Import
sql_init = SQLImport()

# Calculate number jobs and trend
count_query = """
SELECT COUNT(*) AS num_jobs,
FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact
"""
num_jobs = sql_init.sql_df_query(count_query)
num_jobs = num_jobs.num_jobs.iloc[0]

# Calculate number of missing dates
date_query = """
SELECT DISTINCT CAST(search_time AS DATE) AS search_date,
                COUNT(job_id) AS jobs_daily
FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact
GROUP BY search_date
ORDER BY search_date
"""
jobs_daily = sql_init.sql_df_query(date_query)
first_date = jobs_daily.search_date.min()
today_date = (datetime.datetime.today() - datetime.timedelta(hours=6)).date() # streamlit runs on UTC, showing missing date for next day before collect
date_count = pd.DataFrame(jobs_daily.search_date.value_counts())
missing_dates = list(pd.date_range(start=first_date, end=today_date).difference(pd.to_datetime(date_count.index)))

# Calculate average number of job postings a day
delta_days = (today_date - (first_date - datetime.timedelta(days=2))).days # first day was actually day prior but UTC
jobs_day = round(num_jobs/delta_days, 1)
try:
    jobs_today = jobs_daily[jobs_daily.search_date == datetime.date.today()]
    jobs_today = jobs_today.jobs_daily.fillna(0).iloc[0]
except IndexError: #Error when coming to new day and no values for new day
    try:
        jobs_today = jobs_daily[jobs_daily.search_date == datetime.date.today() - datetime.timedelta(days=1)]
        jobs_today = jobs_today.jobs_daily.fillna(0).iloc[0]
    except:
        jobs_today = 0 # kept getting index error on live dashboard
jobs_delta = 100 * (jobs_today - jobs_day) / jobs_day
jobs_delta = round(jobs_delta,1)

# calculate database size yesterday to today
jobs_yesterday = num_jobs - jobs_today
jobs_all_delta = ((num_jobs - jobs_yesterday) * 100) / jobs_yesterday
jobs_all_delta = round(jobs_all_delta,1)

# Date Display:
update_query = """
SELECT MAX(search_time) as last_update
FROM `job-listings-366015`.gsearch_job_listings_clean.gsearch_jobs_fact
"""
update_date = sql_init.sql_df_query(update_query)
update_date = update_date.last_update.iloc[0]
update_time = update_date.strftime("%H:%M")
update_time = f"{update_time} UTC"
update_date = update_date.strftime("%d-%b-%Y")

############################ 
# Visualize health of jobs data collection
############################ 

st.markdown("## 🏥 Health of Job Data Collection")
col1, col2, col3 = st.columns(3)
col1.metric("Jobs Last Updated", update_time, update_date, delta_color="off")
col2.metric("Jobs Added Today", f"{jobs_today:,}", f"{jobs_delta}%")
col3.metric("Jobs Database Size", f"{num_jobs:,}", f"{jobs_all_delta}%") # Calculate % increase

# Daily trend line chart
jobs_daily.search_date = pd.to_datetime(jobs_daily.search_date)
source = jobs_daily
x = 'search_date'
y = 'jobs_daily'
# color = 'keywords'
selector = alt.selection_single(encodings=['x', 'y'])
hover = alt.selection_single(
    fields=[x],
    nearest=True,
    on="mouseover",
    empty="none",
)
lines = (
    alt.Chart(source)
    .mark_line(point="transparent")
    .encode(x=alt.X(x, title="Date", axis=alt.Axis(labelFontSize=15, titleFontSize=17)), 
        y=alt.Y(y, title="Job Postings Collected", axis=alt.Axis(labelFontSize=17, titleFontSize=17)),
        color=alt.value("orange"),
    ) # .transform_calculate(color='datum.delta < 0 ? "red" : "lightblue"') # doesn't show red for negative delta
)
points = (
    lines.transform_filter(hover)
    .mark_circle(size=65)
    .encode(color=alt.Color("color:N", scale=None))
)
tooltips = (
    alt.Chart(source)
    .mark_rule(opacity=0)
    .encode(
        x=x,
        y=y,
        tooltip=[y, x],
    )
    .add_selection(hover)
)
jobs_daily_chart = (lines + points + tooltips).interactive().configure_view(strokeWidth=0)

st.write(f"#### 📈 Daily job scraping status")
st.altair_chart(jobs_daily_chart, use_container_width=True)
st.write(f"📆 Collecting data for {delta_days} days now since {first_date}... \n")

display_missing = st.checkbox("Show missing data (if any) 👇🏼")
if display_missing:
    if len(missing_dates) > 0:
        st.write("❌ Missing data for following dates:")
        for date in missing_dates:
            st.write(date)