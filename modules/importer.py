import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery

class SQLImport:
    """"
    Import data from BigQuery
    """
    def __init__(self):
        # Create API client.
        self.credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        self.client = bigquery.Client(credentials=self.credentials)

    # Return a dataframe
    @st.experimental_memo(ttl=600)
    def sql_df_query(_self, query, _job_config=None):
        query_job = _self.client.query(query, _job_config)
        df = query_job.to_dataframe()
        # fix formatting issue of keywords columns that is imported as a dict of lists of dicts 🥵
        for col in list(df.columns.values):
            # if column contains 'keyword' then fix formatting
            if 'keyword' in col:
                # extract dict items keywords column
                df[col]= df[col].apply(lambda dict: " " if dict == None else [item["element"] for item in dict["list"]])
                df[col] = df[col].apply(lambda row: [x.strip(" ") for x in row]) #had to make this multi-line to get it to work
        return df

    # Return rows as a list of dicts
    # Uses st.experimental_memo to only rerun when the query changes or after 10 min.
    @st.experimental_memo(ttl=600)
    def sql_row_query(self, query, job_config=None):
        query_job = self.client.query(query, job_config=job_config)
        rows_raw = query_job.result()
        # Convert to list of dicts. Required for st.experimental_memo to hash the return value.
        rows = [dict(row) for row in rows_raw]
        return rows

class DataImport:
    """"
    Import data from CSV file on Google Cloud
    """
    def __init__(self):
        pass

    @st.experimental_memo(ttl=60*60) # ttl of one hour to keep memory in cache
    def fetch_and_clean_data(_self):
        data_url = 'https://storage.googleapis.com/gsearch_share/gsearch_jobs.csv'
        jobs_data = pd.read_csv(data_url).replace("'","", regex=True)
        jobs_data.date_time = pd.to_datetime(jobs_data.date_time)
        jobs_data = jobs_data.drop(labels=['Unnamed: 0', 'index'], axis=1, errors='ignore')
        jobs_data.description_tokens = jobs_data.description_tokens.str.strip("[]").str.split(",") # fix major formatting issues with tokens
        jobs_data.description_tokens = jobs_data.description_tokens.apply(lambda row: [x.strip(" ") for x in row]) # remove whitespace from tokens
        return jobs_data

