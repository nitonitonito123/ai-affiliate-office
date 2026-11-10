
import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SECRET_KEY"]
    return create_client(url, key)


def init_db():
    client = get_client()
    client.table("tasks").select("id").limit(1).execute()
    client.table("articles").select("id").limit(1).execute()


def get_tasks():
    client = get_client()
    result = (
        client.table("tasks")
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    return result.data or []


def get_articles():
    client = get_client()
    result = (
        client.table("articles")
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    return result.data or []


def add_task(title, staff="", details="", priority="中"):
    client = get_client()
    client.table("tasks").insert({
        "title": title,
        "staff": staff,
        "details": details,
        "priority": priority,
        "status": "未着手"
    }).execute()


def update_task_status(task_id, status):
    client = get_client()
    client.table("tasks").update({
        "status": status
    }).eq("id", task_id).execute()


def delete_task(task_id):
    client = get_client()
    client.table("tasks").delete().eq("id", task_id).execute()


def add_article(title, body):
    client = get_client()
    client.table("articles").insert({
        "title": title,
        "body": body,
        "status": "下書き"
    }).execute()


def update_article(article_id, title, body):
    client = get_client()
    client.table("articles").update({
        "title": title,
        "body": body
    }).eq("id", article_id).execute()
