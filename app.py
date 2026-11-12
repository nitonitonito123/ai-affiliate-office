
import time
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
from agents.rakuten import search_rakuten_items
from agents.quality import check_article_quality
from agents.quality import revise_article


# --------------------------------
# ページ設定
# --------------------------------

st.set_page_config(
    page_title="AI Affiliate Office",
    page_icon="🤖",
    layout="wide"
)

init_db()

if "selected_rakuten_item" not in st.session_state:
    st.session_state["selected_rakuten_item"] = None

if "article_revision" not in st.session_state:
    st.session_state["article_revision"] = 0

if st.session_state.pop("apply_selected_item_to_topic", False):
    selected_item = st.session_state.get("selected_rakuten_item")

    if selected_item:
        st.session_state["topic_input"] = selected_item.get("name", "")


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


# --------------------------------
# 記事の種類
# --------------------------------

article_type = st.radio(
    "記事の種類",
    ["一般記事", "アフィリエイト記事"],
    horizontal=True,
    key="article_type"
)

if article_type == "一般記事":

    st.info(
        "📘 一般記事：節約・暮らし・知識など、"
        "読者に役立つ情報を中心に作成します。"
    )

else:

    st.info(
        "🛒 アフィリエイト記事：商品情報をもとに、"
        "特徴・メリット・注意点を紹介する記事を作成します。"
    )


topic = st.text_input(
    "記事のテーマ",
    placeholder="例：初心者におすすめの節約方法",
    key="topic_input"
)


# --------------------------------
# 選択中の商品表示
# --------------------------------

selected_item = st.session_state.get("selected_rakuten_item")

if selected_item:

    st.success(
        f"🛒 選択中の商品：{selected_item.get('name', '商品名未取得')}"
    )

    if selected_item.get("is_demo"):
        st.warning("この商品は動作確認用の仮データです。")

    if st.button("選択した商品を解除する"):

        st.session_state["selected_rakuten_item"] = None
        st.rerun()


# --------------------------------
# 手動商品登録
# --------------------------------

st.subheader("📝 商品情報の手動登録")

st.caption(
    "楽天APIが利用できない場合も、"
    "商品情報を入力して紹介記事を作成できます。"
)

with st.form("manual_product_form"):

    manual_name = st.text_input(
        "商品名",
        placeholder="例：ワイヤレスイヤホン"
    )

    manual_price = st.number_input(
        "販売価格（円）",
        min_value=0,
        value=0,
        step=100
    )

    manual_shop = st.text_input(
        "販売ショップ",
        placeholder="例：〇〇ショップ"
    )

    manual_review = st.number_input(
        "商品評価（未確認の場合は0）",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.1
    )

    manual_review_count = st.number_input(
        "口コミ件数（未確認の場合は0）",
        min_value=0,
        value=0,
        step=1
    )

    manual_url = st.text_input(
        "商品ページURL",
        placeholder="https://..."
    )

    manual_submit = st.form_submit_button(
        "📦 この商品を記事作成に設定する",
        use_container_width=True
    )


if manual_submit:

    if not manual_name.strip():

        st.warning("商品名を入力してください。")

    else:

        st.session_state["selected_rakuten_item"] = {
            "name": manual_name.strip(),
            "price": manual_price if manual_price > 0 else "未確認",
            "shop_name": manual_shop.strip() or "未確認",
            "review_average": (
                manual_review if manual_review > 0 else "未確認"
            ),
            "review_count": (
                manual_review_count
                if manual_review_count > 0
                else "未確認"
            ),
            "affiliate_url": "",
            "url": manual_url.strip(),
            "image": "",
            "is_demo": False
        }

        st.session_state["apply_selected_item_to_topic"] = True

        st.success("商品情報を記事作成に設定しました！")
        st.rerun()


# --------------------------------
# 記事ジャンル・文字数
# --------------------------------

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


# --------------------------------
# ボボの記事生成
# --------------------------------

if st.button(
    "🤖 ボボに記事を作成させる",
    use_container_width=True
):

    if not topic.strip():

        st.warning("記事のテーマを入力してください。")

    elif (
        article_type == "アフィリエイト記事"
        and not st.session_state.get("selected_rakuten_item")
    ):

        st.warning(
            "アフィリエイト記事を作成するには、"
            "先に紹介する商品を選択してください。"
        )

    else:

        api_key = st.secrets.get("GEMINI_API_KEY", "")

        if not api_key:

            st.error("Gemini APIキーが設定されていません。")

        else:

            try:

                start_time = time.perf_counter()

                with st.spinner("ボボが記事を執筆しています..."):

                    client = genai.Client(api_key=api_key)

                    selected_item = st.session_state.get(
                        "selected_rakuten_item"
                    )

                    if article_type == "アフィリエイト記事":

                        product_details = f"""
【紹介する商品情報】

商品名：
{selected_item.get("name", "未取得")}

価格：
{selected_item.get("price", "未取得")}

ショップ：
{selected_item.get("shop_name", "未取得")}

評価：
{selected_item.get("review_average", "未取得")}

口コミ件数：
{selected_item.get("review_count", "未取得")}

商品URL：
{selected_item.get("affiliate_url") or selected_item.get("url") or "未設定"}
"""

                        article_rules = """
【アフィリエイト記事の執筆条件】

・商品を購入検討している読者に役立つ内容にする。
・商品の特徴を分かりやすく説明する。
・メリットだけでなく注意点やデメリットも書く。
・どのような人に向いているか説明する。
・購入前に確認すべきポイントを伝える。
・最後に自然な商品ページへの案内を入れる。
・広告・アフィリエイトリンクを使用する場合は、その旨が分かる表現を入れる。
・実際に使用していない商品について体験談を作らない。
・提供されていない機能や性能を捏造しない。
・未確認の価格、口コミ、評価を断定しない。
・商品URLは提供されたものだけを使用する。
"""

                        article_structure = """
【記事構成】
1. 読者の悩みや疑問
2. 商品の概要
3. 商品の特徴
4. メリット
5. 注意点・デメリット
6. 向いている人
7. 購入前の確認ポイント
8. まとめ・商品ページへの案内
"""

                        # テスト用データの場合の安全対策
                        if selected_item.get("is_demo"):

                            product_details += """
【重要：テスト用データ】
この商品情報はアプリの動作確認用の仮データです。
実在する商品の情報として扱わないでください。
価格・ショップ・評価・口コミ・性能を推測してはいけません。
記事タイトルの先頭に【テスト用・公開禁止】と付けてください。
購入を促すリンクや実際の販売情報があるような表現は禁止です。
"""

                            article_rules += """
・テスト用データを実際の商品情報として紹介しない。
・未確認の情報を事実として書かない。
・記事タイトルに【テスト用・公開禁止】を付ける。
・実際に販売されているような表現を使用しない。
"""

                    else:

                        product_details = """
【商品情報】
この記事は一般記事です。
商品情報や商品URLを使用する必要はありません。
選択中の商品があっても、商品紹介は行わないでください。
"""

                        article_rules = """
【一般記事の執筆条件】

・読者の悩みや疑問を解決する内容にする。
・正確で実用的な情報を提供する。
・具体例や実践方法を入れる。
・初心者にも分かりやすく説明する。
・メリットだけでなく注意点も説明する。
・根拠のない断定や誇張表現を避ける。
・未確認情報を事実として書かない。
・商品紹介や購入への誘導を無理に入れない。
・読者が記事を読んだ後に行動できる内容にする。
"""

                        article_structure = """
【記事構成】
1. 読者の悩みや疑問
2. テーマの概要
3. 知っておきたい重要なポイント
4. 具体例
5. 実践方法
6. 注意点
7. まとめ
"""

                    prompt = f"""
あなたはプロのWebライター「ボボ」です。
noteに掲載する完成度の高い記事を作成してください。

【記事の種類】
{article_type}

【テーマ】
{topic}

【ジャンル】
{genre}

【文字数】
{length}

{product_details}

{article_rules}

【共通執筆条件】
・自然で読みやすい日本語にする。
・タイトルと見出しを付ける。
・読者の悩みや疑問から始める。
・具体例を入れる。
・最後にまとめを入れる。
・そのままnoteに掲載できる形式にする。
・内容の水増しをしない。
・事実と意見を区別する。

{article_structure}

完成した記事だけを出力してください。
"""

                    generation_config = genai.types.GenerateContentConfig(
                        max_output_tokens=6000
                    )

                    try:

                        response = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=prompt,
                            config=generation_config
                        )

                        used_model = "gemini-3.5-flash-lite"

                    except Exception as e:

                        error_text = str(e)

                        if (
                            "503" in error_text
                            or "UNAVAILABLE" in error_text
                            or "404" in error_text
                            or "NOT_FOUND" in error_text
                        ):

                            st.warning(
                                "軽量モデルが利用できないため、"
                                "予備モデルに切り替えます..."
                            )

                            response = client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=prompt,
                                config=generation_config
                            )

                            used_model = "gemini-3.8-flash"

                        else:
                            raise

                    generated_text = response.text

                    elapsed = time.perf_counter() - start_time

                    if not generated_text:

                        st.error("記事を生成できませんでした。")

                    else:

                        st.session_state["generated_article"] = generated_text

                        st.session_state["generated_article_type"] = article_type

                        st.session_state["generated_selected_item"] = (
                            selected_item
                            if article_type == "アフィリエイト記事"
                            else None
                        )

                        st.session_state["article_revision"] = 0
                        st.session_state["generation_time"] = elapsed
                        st.session_state["generation_model"] = used_model

                        st.session_state.pop("quality_result", None)
                        st.session_state.pop("original_generated_article", None)
                        st.session_state.pop("previous_quality_result", None)
                        st.session_state.pop("quality_time", None)
                        st.session_state.pop("revision_time", None)

                        st.success(
                            f"記事が完成しました！ 処理時間：{elapsed:.1f}秒"
                        )

            except Exception as e:

                st.error(f"記事生成エラー：{e}")


# --------------------------------
# 生成時間表示
# --------------------------------

if st.session_state.get("generation_time") is not None:

    st.metric(
        "記事生成時間",
        f"{st.session_state['generation_time']:.1f}秒"
    )

    st.caption(
        f"使用モデル：{st.session_state.get('generation_model', '未確認')}"
    )


# --------------------------------
# グミの品質チェック
# --------------------------------

st.divider()
st.subheader("📋 グミの品質チェック")
st.caption("記事の種類に合わせて公開前の品質を確認します。")

if st.session_state.get("generated_article"):

    generated_article_type = st.session_state.get(
        "generated_article_type",
        "一般記事"
    )

    st.caption(f"チェック対象：{generated_article_type}")

    if st.button(
        "🔍 グミに品質チェックさせる",
        use_container_width=True
    ):

        try:

            start_time = time.perf_counter()

            with st.spinner("グミが記事を確認しています..."):

                selected_item = st.session_state.get(
                    "generated_selected_item"
                )

                article_text = st.session_state["generated_article"]

                article_lines = article_text.splitlines()

                article_title = next(
                    (
                        line.lstrip("# ").strip()
                        for line in article_lines
                        if line.strip()
                    ),
                    "無題の記事"
                )

                quality_result = check_article_quality(
                    title=article_title,
                    body=article_text,
                    selected_item=selected_item,
                    article_type=generated_article_type
                )

                elapsed = time.perf_counter() - start_time

                st.session_state["quality_result"] = quality_result
                st.session_state["quality_time"] = elapsed

            st.success(
                f"品質チェック完了！ 処理時間：{elapsed:.1f}秒"
            )

        except Exception as e:

            st.error(f"品質チェックエラー：{e}")


# --------------------------------
# 品質チェック時間表示
# --------------------------------

if st.session_state.get("quality_time") is not None:

    st.metric(
        "品質チェック時間",
        f"{st.session_state['quality_time']:.1f}秒"
    )


# --------------------------------
# グミのチェック結果表示
# --------------------------------

if st.session_state.get("quality_result"):

    st.markdown("### 📝 グミのチェック結果")

    st.markdown(st.session_state["quality_result"])

    st.divider()

    st.subheader("🛠️ ボボによる自動修正")

    st.caption(
        "グミの指摘を反映し、記事の種類に合わせて修正します。"
    )

    if st.button(
        "✍️ ボボに記事を自動修正させる",
        use_container_width=True
    ):

        try:

            start_time = time.perf_counter()

            with st.spinner("ボボがグミの指摘を反映しています..."):

                current_article = st.session_state["generated_article"]

                quality_result = st.session_state["quality_result"]

                selected_item = st.session_state.get(
                    "generated_selected_item"
                )

                generated_article_type = st.session_state.get(
                    "generated_article_type",
                    "一般記事"
                )

                revised_article = revise_article(
                    title=next(
                        (
                            line.lstrip("# ").strip()
                            for line in current_article.splitlines()
                            if line.strip()
                        ),
                        "無題の記事"
                    ),
                    body=current_article,
                    quality_result=quality_result,
                    selected_item=selected_item,
                    article_type=generated_article_type
                )

                elapsed = time.perf_counter() - start_time

                if not revised_article or not revised_article.strip():

                    st.error("修正後の記事が空でした。")

                else:

                    st.session_state["original_generated_article"] = (
                        current_article
                    )

                    st.session_state["previous_quality_result"] = (
                        quality_result
                    )

                    st.session_state["generated_article"] = (
                        revised_article.strip()
                    )

                    st.session_state["article_revision"] += 1

                    st.session_state["revision_time"] = elapsed

                    st.session_state.pop("quality_result", None)
                    st.session_state.pop("quality_time", None)

                    st.success(
                        f"ボボが記事を修正しました！ 処理時間：{elapsed:.1f}秒"
                    )

                    st.info(
                        "修正後の記事をグミに再チェックさせてください。"
                    )

        except Exception as e:

            st.error(f"記事の自動修正エラー：{e}")


# --------------------------------
# 自動修正時間表示
# --------------------------------

if st.session_state.get("revision_time") is not None:

    st.metric(
        "自動修正時間",
        f"{st.session_state['revision_time']:.1f}秒"
    )


# --------------------------------
# 修正前の記事との比較
# --------------------------------

if st.session_state.get("original_generated_article"):

    with st.expander("📄 修正前の記事を確認する"):

        st.text_area(
            "修正前の記事",
            value=st.session_state["original_generated_article"],
            height=300,
            disabled=True,
            key="original_article_preview"
        )

    if st.session_state.get("previous_quality_result"):

        with st.expander("📋 修正前の品質チェック結果"):

            st.markdown(
                st.session_state["previous_quality_result"]
            )


# --------------------------------
# 生成記事の確認・保存
# --------------------------------

if st.session_state.get("generated_article"):

    st.subheader("📄 生成された記事")

    generated_text = st.session_state["generated_article"]

    revision = st.session_state.get("article_revision", 0)

    generated_article_type = st.session_state.get(
        "generated_article_type",
        "一般記事"
    )

    st.caption(f"記事の種類：{generated_article_type}")

    st.caption(
        f"記事の修正回数：{revision}回"
    )

    generated_item = st.session_state.get(
        "generated_selected_item"
    )

    if generated_item and generated_item.get("is_demo"):
        st.error(
            "この記事はテスト用データを使用しています。"
            "実際の商品情報を確認するまで公開しないでください。"
        )

    st.text_area(
        "記事内容",
        value=generated_text,
        height=400,
        key=f"generated_article_preview_{revision}"
    )

    if st.button(
        "📚 この記事を保存する",
        use_container_width=True
    ):

        article_lines = generated_text.splitlines()

        title = next(
            (
                line.lstrip("# ").strip()
                for line in article_lines
                if line.strip()
            ),
            "無題の記事"
        )

        add_article(
            title,
            generated_text
        )

        st.session_state.pop("generated_article", None)
        st.session_state.pop("generated_article_type", None)
        st.session_state.pop("generated_selected_item", None)
        st.session_state.pop("quality_result", None)
        st.session_state.pop("original_generated_article", None)
        st.session_state.pop("previous_quality_result", None)
        st.session_state.pop("generation_time", None)
        st.session_state.pop("quality_time", None)
        st.session_state.pop("revision_time", None)

        st.session_state["article_revision"] = 0

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

        if not edited_title.strip() or not edited_body.strip():

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
- 楽天アフィリエイトAPIとの連携強化
- 商品リサーチの自動化
- 商品紹介記事の品質チェック
- アクセス数・収益分析
- note投稿作業の効率化
""")

st.caption(
    "現在は記事生成・保存・編集、タスク管理、"
    "商品リサーチ計画、楽天商品検索、"
    "手動商品登録、記事品質チェック、"
    "AIによる記事自動修正機能を搭載しています。"
)


st.divider()


# --------------------------------
# 商品リサーチ計画
# --------------------------------

st.header("🔎 商品リサーチ")
st.write("クルミが商品リサーチの調査計画を作成します。")

with st.form("product_research_form"):

    research_keyword = st.text_input(
        "検索キーワード",
        placeholder="例：ワイヤレスイヤホン"
    )

    research_category = st.selectbox(
        "商品ジャンル",
        [
            "家電",
            "日用品",
            "食品・飲料",
            "美容・健康",
            "ファッション",
            "趣味・アウトドア",
            "その他"
        ]
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


st.divider()


# --------------------------------
# 楽天市場 商品検索
# --------------------------------

st.header("🛒 楽天市場 商品検索")

st.caption(
    "楽天API接続後は実際の商品を検索できます。"
    "現在はデモ検索でも動作確認できます。"
)

search_mode = st.radio(
    "検索方法",
    ["デモ商品でテスト", "楽天APIで検索"],
    horizontal=True,
    key="rakuten_search_mode"
)

if search_mode == "デモ商品でテスト":

    st.info(
        "現在はテスト用の仮データを使用します。"
        "実際の価格・評価・販売情報ではありません。"
    )

else:

    st.warning(
        "楽天APIの認証情報が必要です。"
        "楽天ウェブサービスの登録画面が復旧するまで、"
        "実際の商品検索は利用できない可能性があります。"
    )


with st.form("rakuten_search_form"):

    rakuten_keyword = st.text_input(
        "商品検索キーワード",
        placeholder="例：ワイヤレスイヤホン"
    )

    rakuten_hits = st.selectbox(
        "取得する商品数",
        [5, 10, 20, 30],
        index=1
    )

    rakuten_sort = st.selectbox(
        "検索結果の並び順",
        [
            "-reviewCount",
            "-reviewAverage",
            "+itemPrice",
            "-itemPrice"
        ],
        format_func=lambda value: {
            "-reviewCount": "口コミ件数が多い順",
            "-reviewAverage": "評価が高い順",
            "+itemPrice": "価格が安い順",
            "-itemPrice": "価格が高い順"
        }[value]
    )

    rakuten_submit = st.form_submit_button(
        "🛒 商品を検索",
        use_container_width=True
    )


if rakuten_submit:

    if not rakuten_keyword.strip():

        st.warning("検索キーワードを入力してください。")

    else:

        try:

            if search_mode == "デモ商品でテスト":

                with st.spinner("テスト用商品データを準備しています..."):

                    rakuten_results = [
                        {
                            "name": (
                                f"【テスト用】{rakuten_keyword.strip()}"
                            ),
                            "price": "未確認",
                            "url": "",
                            "affiliate_url": "",
                            "image": "",
                            "review_average": "未確認",
                            "review_count": "未確認",
                            "shop_name": "テスト用ショップ",
                            "item_code": "DEMO-001",
                            "availability": "未確認",
                            "catchcopy": "アプリ動作確認用の商品データです。",
                            "caption": "実際の商品情報ではありません。",
                            "is_demo": True
                        }
                    ]

                st.session_state["rakuten_results"] = rakuten_results

                st.session_state["rakuten_search_keyword"] = (
                    rakuten_keyword.strip()
                )

                st.success(
                    "テスト用商品データを1件準備しました。"
                )

            else:

                with st.spinner("楽天市場の商品を検索しています..."):

                    rakuten_results = search_rakuten_items(
                        keyword=rakuten_keyword.strip(),
                        hits=rakuten_hits,
                        sort=rakuten_sort
                    )

                st.session_state["rakuten_results"] = rakuten_results

                st.session_state["rakuten_search_keyword"] = (
                    rakuten_keyword.strip()
                )

                if rakuten_results:

                    st.success(
                        f"{len(rakuten_results)}件の商品が見つかりました。"
                    )

                else:

                    st.info(
                        "該当する商品は見つかりませんでした。"
                    )

        except Exception as e:

            st.error(f"商品検索エラー：{e}")


# --------------------------------
# 楽天市場 商品検索結果
# --------------------------------

if "rakuten_results" in st.session_state:

    st.subheader("📦 商品検索結果")

    st.caption(
        f"検索キーワード："
        f"{st.session_state.get('rakuten_search_keyword', '')}"
    )

    for index, item in enumerate(
        st.session_state["rakuten_results"]
    ):

        with st.container(border=True):

            col_image, col_info = st.columns([1, 3])

            with col_image:

                if item.get("image"):

                    st.image(
                        item["image"],
                        use_container_width=True
                    )

                else:

                    st.write("画像なし")

            with col_info:

                if item.get("is_demo"):
                    st.warning("テスト用の仮データ")

                st.markdown(
                    f"**{item.get('name', '商品名未取得')}**"
                )

                price = item.get("price", "未確認")

                if isinstance(price, (int, float)) and price > 0:

                    st.write(f"価格：{price:,.0f}円")

                else:

                    st.write(f"価格：{price}")

                st.write(
                    f"ショップ：{item.get('shop_name', '未取得')}"
                )

                st.write(
                    f"評価：{item.get('review_average', '未確認')} / 5"
                )

                st.write(
                    f"口コミ件数：{item.get('review_count', '未確認')}件"
                )

                product_url = (
                    item.get("affiliate_url")
                    or item.get("url")
                )

                if product_url:

                    st.link_button(
                        "商品ページを開く",
                        product_url,
                        use_container_width=True
                    )

                elif item.get("is_demo"):

                    st.caption(
                        "テストデータのため商品URLはありません。"
                    )

                else:

                    st.caption(
                        "商品URL・アフィリエイトURLは未取得です。"
                    )

                if st.button(
                    "✍️ この記事で紹介する",
                    key=f"select_rakuten_item_{index}",
                    use_container_width=True
                ):

                    st.session_state["selected_rakuten_item"] = item

                    st.session_state[
                        "apply_selected_item_to_topic"
                    ] = True

                    st.success(
                        "商品を記事作成に設定しました！"
                    )

                    st.rerun()
