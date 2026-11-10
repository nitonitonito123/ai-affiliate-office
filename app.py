
import streamlit as st
from database import (
    init_db,
    get_articles,
    get_tasks,
    add_task,
    update_task_status,
    add_article,
    update_article
)
from google import genai
from agents.team import STAFF
from agents.research import create_research_plan

# --------------------------------
# ページ設定
# --------------------------------

st.set_page_config(
    page_title="AI Affiliate Office",
    page_icon="🤖",
    layout="wide"
)

init_db()

st.title("🤖 AI Affiliate Office")
st.caption("6人のAIスタッフと運営するアフィリエイト事務所")


# --------------------------------
# AIスタッフ表示
# --------------------------------

st.header("👥 AIスタッフ")

if isinstance(STAFF, dict):
    staff_items = list(STAFF.items())
else:
    staff_items = [
        (
            item.get("name", f"スタッフ{i + 1}"),
            item
        ) if isinstance(item, dict)
        else (str(item), {})
        for i, item in enumerate(STAFF)
    ]

staff_names = [str(name) for name, _ in staff_items]

cols = st.columns(3)

for i, (name, info) in enumerate(staff_items):
    if isinstance(info, dict):
        description = (
            info.get("description")
            or info.get("role")
            or info.get("job")
            or "AIスタッフ"
        )
    else:
        description = str(info)

    with cols[i % 3]:
        st.info(f"**{name}**\n\n{description}")


st.divider()


# --------------------------------
# ダッシュボード
# --------------------------------

st.header("📊 ダッシュボード")

tasks = get_tasks()
articles = get_articles()

total_tasks = len(tasks)
completed_tasks = sum(
    1 for task in tasks
    if task["status"] == "完了"
)

total_articles = len(articles)

col1, col2, col3 = st.columns(3)

col1.metric("登録タスク", total_tasks)
col2.metric("完了タスク", completed_tasks)
col3.metric("保存済み記事", total_articles)


st.divider()


# --------------------------------
# タスク登録
# --------------------------------

st.header("📝 タスク管理")

st.subheader("新しいタスクを登録")

with st.form("task_form"):
    task_title = st.text_input("タスク名")

    task_staff = st.selectbox(
        "担当スタッフ",
        staff_names
    )

    task_details = st.text_area("タスクの詳細")

    task_priority = st.selectbox(
        "優先度",
        ["高", "中", "低"],
        index=1
    )

    task_submit = st.form_submit_button(
        "タスクを登録",
        use_container_width=True
    )

    if task_submit:
        if task_title.strip():
            add_task(
                task_title.strip(),
                task_staff,
                task_details.strip(),
                task_priority
            )
            st.success("タスクを登録しました！")
            st.rerun()
        else:
            st.warning("タスク名を入力してください。")


# --------------------------------
# タスク一覧
# --------------------------------

st.subheader("📋 登録済みタスク")

tasks = get_tasks()

if tasks:
    for task in tasks:
        with st.expander(task["title"]):
            st.write(f"担当：{task['staff']}")
            st.write(f"優先度：{task['priority']}")

            if task.get("details"):
                st.write(f"詳細：{task['details']}")

            status_options = [
                "未着手",
                "進行中",
                "完了"
            ]

            current_status = task["status"]

            if current_status not in status_options:
                current_status = "未着手"

            new_status = st.selectbox(
                "進捗状況",
                status_options,
                index=status_options.index(current_status),
                key=f"task_status_{task['id']}"
            )

            if new_status != task["status"]:
                update_task_status(
                    task["id"],
                    new_status
                )
                st.rerun()
else:
    st.info("まだタスクは登録されていません。")


st.divider()


# --------------------------------
# AI記事生成
# --------------------------------

st.header("✍️ AI記事生成")
st.caption("ボボが記事の下書きを作成します。")

topic = st.text_input(
    "記事のテーマ",
    placeholder="例：初心者におすすめの節約方法"
)

genre = st.selectbox(
    "記事ジャンル",
    [
        "商品紹介",
        "節約・お金",
        "生活・暮らし",
        "美容・健康",
        "趣味・エンタメ",
        "その他"
    ]
)

length = st.selectbox(
    "記事の長さ",
    [
        "短め（約1,000文字）",
        "標準（約2,000文字）",
        "長め（約3,000文字）"
    ],
    index=1
)

if st.button(
    "🤖 ボボに記事を作成させる",
    use_container_width=True
):
    if not topic.strip():
        st.warning("記事のテーマを入力してください。")

    else:
        api_key = st.secrets.get("GEMINI_API_KEY", "")

        if not api_key:
            st.error("Gemini APIキーが設定されていません。")

        else:
            try:
                with st.spinner("ボボが記事を執筆しています..."):

                    client = genai.Client(
                        api_key=api_key
                    )

                    prompt = f"""
あなたはプロのWebライターです。
noteに投稿する記事を作成してください。

【テーマ】
{topic}

【ジャンル】
{genre}

【文字数】
{length}

【執筆ルール】
・読者にとって役立つ内容にする
・自然で読みやすい日本語を使う
・タイトルを最初に付ける
・見出しを適切に使用する
・具体例を入れる
・誇張や根拠のない断定を避ける
・最後にまとめを入れる
・そのままnoteの下書きに使える形式にする

タイトルと本文を分けず、完成した記事として出力してください。
"""

                    try:
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=prompt,
                            config=genai.types.GenerateContentConfig(
                                thinking_config=genai.types.ThinkingConfig(
                                    thinking_level="LOW"
                                )
                            )
                        )

                    except Exception as e:
                        error_text = str(e)

                        if (
                            "503" in error_text
                            or "UNAVAILABLE" in error_text
                        ):
                            st.warning(
                                "通常モデルが混雑中です。予備モデルに切り替えます..."
                            )

                            response = client.models.generate_content(
                                model="gemini-3.5-flash-lite",
                                contents=prompt
                            )
                        else:
                            raise

                    generated_text = response.text

                    if not generated_text:
                        st.error("記事を生成できませんでした。")

                    else:
                        st.session_state["generated_article"] = generated_text
                        st.success("記事が完成しました！")

            except Exception as e:
                st.error(f"記事生成エラー：{e}")


# --------------------------------
# 生成記事の確認・保存
# --------------------------------

if st.session_state.get("generated_article"):

    st.subheader("📄 生成された記事")

    generated_text = st.session_state["generated_article"]

    st.text_area(
        "記事内容",
        value=generated_text,
        height=400,
        key="generated_article_preview"
    )

    if st.button(
        "📚 この記事を保存する",
        use_container_width=True
    ):
        title = generated_text.splitlines()[0].strip()

        title = title.lstrip("#").strip()

        if not title:
            title = "無題の記事"

        add_article(
            title,
            generated_text
        )

        st.session_state.pop(
            "generated_article",
            None
        )

        st.success("記事を保存しました！")
        st.rerun()


st.divider()


# --------------------------------
# 保存済み記事・編集機能
# --------------------------------

st.header("📚 保存済み記事")

saved_articles = get_articles()

if saved_articles:

    article_options = {
        f"{article['title']}（ID：{article['id']}）": article
        for article in saved_articles
    }

    selected_title = st.selectbox(
        "編集する記事を選択",
        list(article_options.keys())
    )

    selected_article = article_options[selected_title]

    st.subheader("✏️ 記事の編集")

    edited_title = st.text_input(
        "記事タイトル",
        value=selected_article["title"],
        key=f"title_{selected_article['id']}"
    )

    edited_body = st.text_area(
        "記事本文",
        value=selected_article["body"],
        height=400,
        key=f"body_{selected_article['id']}"
    )

    if st.button(
        "💾 記事を更新",
        use_container_width=True
    ):
        if (
            not edited_title.strip()
            or not edited_body.strip()
        ):
            st.warning("タイトルと本文を入力してください。")

        else:
            update_article(
                selected_article["id"],
                edited_title.strip(),
                edited_body.strip()
            )

            st.success("記事を更新しました！")
            st.rerun()

    st.divider()

    st.subheader("📖 保存済み記事一覧")

    for article in saved_articles:
        with st.expander(article["title"]):
            st.caption(f"状態：{article['status']}")
            st.markdown(article["body"])

else:
    st.info("まだ保存された記事はありません。")


st.divider()


# --------------------------------
# 今後の開発予定
# --------------------------------

st.header("🚀 今後の開発予定")

st.markdown("""
- 楽天アフィリエイトAPIとの連携
- 商品リサーチの自動化
- 商品紹介記事の品質チェック
- アクセス数・収益分析
- note投稿作業の効率化
""")

st.caption(
    "現在は記事生成・保存・編集とタスク管理が利用できます。"
    "外部サービスとの自動連携は今後の開発項目です。"
)


st.divider()

st.header("🔎 商品リサーチ")
st.write("クルミが商品リサーチの調査計画を作成します。")

with st.form("product_research_form"):
    research_keyword = st.text_input(
        "検索キーワード",
        placeholder="例：ワイヤレスイヤホン"
    )

    research_category = st.selectbox(
        "商品ジャンル",
        ["家電", "日用品", "食品・飲料", "美容・健康",
         "ファッション", "趣味・アウトドア", "その他"]
    )

    research_budget = st.number_input(
        "想定予算（円）",
        min_value=0,
        value=5000,
        step=500
    )

    research_target = st.text_area(
        "リサーチの条件",
        placeholder="例：口コミが多く、コストパフォーマンスが良い商品"
    )

    research_submit = st.form_submit_button(
        "🔍 クルミに調査させる",
        use_container_width=True
    )

if research_submit:
    if not research_keyword.strip():
        st.warning("検索キーワードを入力してください。")
    else:
        try:
            with st.spinner("クルミが調査計画を作成しています..."):
                research_result = create_research_plan(
                    research_keyword.strip(),
                    research_category,
                    research_budget,
                    research_target.strip()
                )

            st.session_state["research_result"] = research_result
            st.success("クルミの調査計画が完成しました！")

        except Exception as e:
            st.error(f"リサーチエラー：{e}")

if st.session_state.get("research_result"):
    st.subheader("📋 クルミのリサーチ結果")

    st.markdown(st.session_state["research_result"])

    if st.button("🗑️ リサーチ結果を閉じる"):
        st.session_state.pop("research_result", None)
        st.rerun()
