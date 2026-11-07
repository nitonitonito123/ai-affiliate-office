import streamlit as st
from database import init_db, get_articles, get_tasks, add_task
from agents.team import STAFF

st.set_page_config(page_title="AI Affiliate Office", page_icon="🐻", layout="wide")
init_db()

st.title("🐻 AI Affiliate Office")
st.caption("6体のAIスタッフで、商品企画・記事制作・品質確認・収益分析を支援する管理オフィス")

articles = get_articles()
tasks = get_tasks()

c1, c2, c3, c4 = st.columns(4)
c1.metric("AIスタッフ", "6体")
c2.metric("記事数", len(articles))
c3.metric("進行中タスク", sum(t["status"] == "進行中" for t in tasks))
c4.metric("累計報酬", "¥0", help="楽天アフィリエイトの実績データ連携後に集計")

st.divider()
st.subheader("AIスタッフ")
cols = st.columns(3)
for i, person in enumerate(STAFF):
    with cols[i % 3]:
        st.container(border=True)
        st.markdown(f"### {person['emoji']} {person['name']}")
        st.write(f"**担当：** {person['role']}")
        st.caption(person["description"])

st.divider()
left, right = st.columns([1, 1])
with left:
    st.subheader("タスクを追加")
    with st.form("task_form"):
        title = st.text_input("タスク名", placeholder="例：冬向け人気商品を調査")
        staff = st.selectbox("担当スタッフ", [p["name"] for p in STAFF])
        submitted = st.form_submit_button("タスク登録", use_container_width=True)
        if submitted:
            if title.strip():
                add_task(title.strip(), staff)
                st.success("タスクを登録しました。")
                st.rerun()
            else:
                st.warning("タスク名を入力してください。")

with right:
    st.subheader("最近のタスク")
    if tasks:
        for task in tasks[:10]:
            st.write(f"**{task['title']}** — {task['staff']} · {task['status']}")
    else:
        st.info("まだタスクはありません。左側から登録できます。")

st.divider()
st.subheader("開発ロードマップ")
st.markdown("""
1. **基盤構築（現在）**：画面・スタッフ定義・SQLiteタスク管理
2. 商品リサーチ：楽天公式API接続、取得情報の保存
3. AI記事制作：商品情報に基づく下書き生成・事実確認
4. 公開支援：note向け原稿出力、人による最終確認と公開
5. 効果測定：クリック・成果・報酬の取り込みと改善提案
""")
st.warning("現在は開発用MVPです。商品検索・AI生成・note投稿・報酬連携はまだ接続していません。")
