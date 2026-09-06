import streamlit as st
import pandas as pd
from job_agent.models.schemas import EvaluatedJob
from job_agent.models.enums import JobStatus

def render_summary_cards(stats: dict[str, int]) -> None:
    """Render summary metric cards: Total, Qualified, Applied, Skipped."""
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Jobs", stats.get("total", 0))
    with cols[1]:
        st.metric("Qualified", stats.get(JobStatus.NEW.value, 0))
    with cols[2]:
        st.metric("Applied", stats.get(JobStatus.APPLIED.value, 0))
    with cols[3]:
        st.metric("Archived/Skipped", stats.get(JobStatus.ARCHIVED.value, 0) + stats.get(JobStatus.SKIPPED.value, 0))

def render_jobs_table(jobs: list[EvaluatedJob]) -> pd.DataFrame:
    """Render a filterable, sortable jobs table."""
    if not jobs:
        st.info("No jobs available.")
        return pd.DataFrame()
        
    data = []
    for j in jobs:
        data.append({
            "Company": j.company,
            "Title": j.title,
            "Fit Score": j.fit_score,
            "Location": j.location,
            "Status": j.status.value,
            "Hash": j.url_hash()
        })
    df = pd.DataFrame(data)
    
    st.sidebar.subheader("Filters")
    companies = st.sidebar.multiselect("Company", df["Company"].unique())
    statuses = st.sidebar.multiselect("Status", df["Status"].unique(), default=[JobStatus.NEW.value])
    min_fit = st.sidebar.slider("Min Fit Score", 0.0, 1.0, 0.7, 0.05)
    
    filtered_df = df[df["Fit Score"] >= min_fit]
    if companies:
        filtered_df = filtered_df[filtered_df["Company"].isin(companies)]
    if statuses:
        filtered_df = filtered_df[filtered_df["Status"].isin(statuses)]
        
    st.dataframe(
        filtered_df[["Company", "Title", "Fit Score", "Location", "Status"]],
        use_container_width=True,
        hide_index=True
    )
    return filtered_df

def render_job_detail(job: EvaluatedJob) -> None:
    """Render detailed view for a single job."""
    st.subheader(f"{job.title} @ {job.company}")
    st.markdown(f"**Location:** {job.location}")
    st.markdown(f"**Fit Score:** `{job.fit_score:.2f}`")
    
    st.markdown("**Skills Match:**")
    cols = st.columns(2)
    with cols[0]:
        for skill in job.matched_skills:
            st.markdown(f"✅ {skill}")
    with cols[1]:
        for skill in job.missing_skills:
            st.markdown(f"❌ {skill}")
            
    st.info(f"**AI Summary:** {job.summary_reason}")
    st.link_button("Apply on LinkedIn", job.apply_url)

def render_status_updater(job: EvaluatedJob, on_update) -> None:
    """Render status update dropdown for a job."""
    new_status = st.selectbox(
        "Update Status",
        options=[s.value for s in JobStatus],
        index=[s.value for s in JobStatus].index(job.status.value),
        key=f"status_{job.url_hash()}"
    )
    if new_status != job.status.value:
        if st.button("Save Status"):
            on_update(job.url_hash(), JobStatus(new_status))
            st.success("Status updated!")
            st.rerun()
