
import streamlit as st
from database import (
    init_db, get_articles, get_tasks,
    add_task, update_task_status, add_article
)
from google import genai
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
else:
    st.info("まだタスクはありません。")

st.divider()

# AI記事自動生成
st.divider()
st.subheader("✍️ ボボ：AI記事自動生成")

topic = st.text_input(
    "記事のテーマ",
    placeholder="例：初心者向けの節約術"
)

genre = st.selectbox(
    "記事ジャンル",
    ["節約・お金", "商品レビュー", "暮らし・生活", "仕事・副業", "エンタメ", "その他"]
)

length = st.selectbox(
    "記事の文字数",
    ["1500文字", "3000文字", "4000文字", "5000文字"]
)

if st.button("🤖 ボボに記事を作成させる", use_container_width=True):
    if not topic.strip():
        st.warning("記事のテーマを入力してください。")
    else:
        api_key = st.secrets.get("GEMINI_API_KEY", "")

        if not api_key:
            st.error("Gemini APIキーが設定されていません。")
        else:
            try:
                with st.spinner("ボボが記事を執筆しています..."):
                    client = genai.Client(api_key=api_key)

                    prompt = f"""
あなたはnote専門のプロのWebライターです。
執筆担当AIスタッフ「ボボ」として記事を作成してください。

テーマ：{topic}
ジャンル：{genre}
文字数の目安：{length}

条件：
・読者にとって役立つ具体的な内容にする
・読みやすい自然な日本語にする
・タイトルを最初に付ける
・見出しを適切に使う
・根拠のない数字や事実を作らない
・最後にまとめを入れる
・noteに投稿できるMarkdown形式にする
・タイトルと本文を出力する
"""

                    response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt,
    config=genai.types.GenerateContentConfig(
        thinking_config=genai.types.ThinkingConfig(
            thinking_level="LOW"
        )
    )
)

                    generated_text = response.text

                    if not generated_text:
                        st.error("記事を生成できませんでした。")
                    else:
                        st.session_state["generated_article"] = generated_text
                        st.success("記事が完成しました！")

            except Exception as e:
                st.error(f"記事生成エラー：{e}")

if "generated_article" in st.session_state:
    st.markdown("### 📝 生成された記事")

    edited_article = st.text_area(
        "記事内容（編集できます）",
        value=st.session_state["generated_article"],
        height=500,
        key="article_editor"
    )

    if st.button("💾 記事を下書き保存", use_container_width=True):
        if edited_article.strip():
            lines = edited_article.strip().splitlines()
            article_title = topic.strip()

            for line in lines:
                clean_line = line.strip().lstrip("#").strip()
                if clean_line:
                    article_title = clean_line
                    break

            add_article(article_title, edited_article.strip())
            st.success("記事を下書き保存しました！")
            del st.session_state["generated_article"]
            st.rerun()
        else:
            st.warning("記事内容を入力してください。")

# 保存済み記事
st.divider()
st.subheader("📚 保存済み記事")

saved_articles = get_articles()

if saved_articles:
    for article in saved_articles:
        with st.expander(article["title"]):
            st.caption(f"状態：{article['status']}")
            st.markdown(article["body"])
else:
    st.info("まだ保存された記事はありません。")

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
