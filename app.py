
import streamlit as st
from database import (
    init_db, get_articles, get_tasks,
    add_task, update_task_status, delete_task
)
from agents.team import STAFF

st.set_page_config(
    page_title="AI Affiliate Office",
    page_icon="🐻",
    layout="wide"
)

init_db()

st.title("🐻 AI Affiliate Office")
st.caption("6体のAIスタッフでアフィリエイト運営を管理")

articles = get_articles()
tasks = get_tasks()

# ダッシュボード
c1, c2, c3, c4 = st.columns(4)
c1.metric("AIスタッフ", "6体")
c2.metric("記事数", len(articles))
c3.metric(
    "進行中タスク",
    sum(t["status"] == "進行中" for t in tasks)
)
c4.metric("累計報酬", "¥0")

st.divider()

# AIスタッフ
st.subheader("🤖 AIスタッフ")
cols = st.columns(3)

for i, person in enumerate(STAFF):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(
                f"### {person['emoji']} {person['name']}"
            )
            st.write(f"**担当：** {person['role']}")
            st.caption(person["description"])

st.divider()

# タスク登録
st.subheader("📝 タスク管理")

left, right = st.columns([1, 1])

with left:
    st.markdown("### 新しいタスクを登録")

    with st.form("task_form"):
        title = st.text_input(
            "タスク名",
            placeholder="例：冬向け人気商品を10件調査"
        )

        details = st.text_area(
            "詳細指示・作業内容",
            placeholder="調査する商品ジャンル、条件、必要な情報などを入力"
        )

        staff = st.selectbox(
            "担当スタッフ",
            [p["name"] for p in STAFF]
        )

        priority = st.selectbox(
            "優先度",
            ["高", "中", "低"],
            index=1
        )

        submitted = st.form_submit_button(
            "タスク登録",
            use_container_width=True
        )

        if submitted:
            if title.strip():
                add_task(
                    title.strip(),
                    staff,
                    details.strip(),
                    priority
                )
                st.success("タスクを登録しました。")
                st.rerun()
            else:
                st.warning("タスク名を入力してください。")

with right:
    st.markdown("### 📊 タスク状況")

    total = len(tasks)
    completed = sum(t["status"] == "完了" for t in tasks)
    in_progress = sum(t["status"] == "進行中" for t in tasks)
    not_started = sum(t["status"] == "未着手" for t in tasks)

    st.metric("全タスク数", total)
    st.metric("未着手", not_started)
    st.metric("進行中", in_progress)
    st.metric("完了", completed)

st.divider()

# タスク一覧
st.subheader("📋 登録済みタスク一覧")

if tasks:
    for task in tasks:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{task['title']}**")
                st.write(
                    f"担当：{task['staff']} ｜ "
                    f"優先度：{task['priority']}"
                )

                if task["details"]:
                    st.caption(task["details"])

                st.caption(
                    f"登録日時：{task['created_at']}"
                )

            with col2:
                status_options = [
                    "未着手", "進行中", "完了"
                ]

                current_status = task["status"]

                selected_status = st.selectbox(
                    "進捗状況",
                    status_options,
                    index=status_options.index(current_status)
                    if current_status in status_options else 0,
                    key=f"status_{task['id']}"
                )

                if selected_status != current_status:
                    update_task_status(
                        task["id"],
                        selected_status
                    )
                    st.rerun()

                if st.button(
                    "🗑️ このタスクを削除",
                    key=f"delete_{task['id']}"
                ):
                    delete_task(task["id"])
                    st.success("タスクを削除しました。")
                    st.rerun()
else:
    st.info("まだタスクはありません。")
st.divider()

# 開発状況
st.subheader("🚀 開発ロードマップ")

st.markdown("""
1. **基盤構築：完了**
2. **タスク管理機能：拡張中**
3. 商品リサーチ：楽天公式API接続
4. AI記事制作：記事の自動下書き生成
5. 公開支援：note向け原稿出力
6. 効果測定：クリック数・成果・報酬分析
""")

st.warning(
    "現在は開発用MVPです。"
    "AIによる実作業、楽天商品検索、note投稿、"
    "報酬連携は今後実装します。"
)
