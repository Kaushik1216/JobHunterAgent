import streamlit as st
import pandas as pd
from pathlib import Path
from job_agent.config import get_settings
from job_agent.storage.database import DatabaseManager
from job_agent.storage.repository import JobRepository
from job_agent.models.enums import JobStatus
from job_agent.dashboard.components import (
    render_summary_cards, render_jobs_table, render_job_detail, render_status_updater
)

def main() -> None:
    st.set_page_config(
        page_title="Job Agent Dashboard",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Job Discovery Agent")
    st.caption("Autonomous LinkedIn job discovery & evaluation dashboard")
    
    settings = get_settings()
    db = DatabaseManager(settings.db_path)
    db.connect()
    db.run_migrations()
    repo = JobRepository(db)
    
    stats = repo.get_run_stats()
    render_summary_cards(stats)
    
    st.divider()
    
    # Load jobs
    jobs = repo.get_all_jobs()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filtered_df = render_jobs_table(jobs)
        
    with col2:
        if not filtered_df.empty:
            st.subheader("Job Details")
            selected_hash = st.selectbox("Select a Job", filtered_df["Hash"], format_func=lambda h: filtered_df[filtered_df["Hash"] == h].iloc[0]["Company"] + " - " + filtered_df[filtered_df["Hash"] == h].iloc[0]["Title"])
            if selected_hash:
                job = next((j for j in jobs if j.url_hash() == selected_hash), None)
                if job:
                    render_job_detail(job)
                    
                    def on_update(h, s):
                        repo.update_status(h, s)
                        
                    render_status_updater(job, on_update)
        
    st.divider()
    
    if st.button("Export to CSV"):
        df = pd.DataFrame([j.model_dump() for j in jobs])
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="jobs_export.csv",
            mime="text/csv"
        )
        
    db.close()

if __name__ == "__main__":
    main()
