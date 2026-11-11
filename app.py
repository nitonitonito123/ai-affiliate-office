
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
        f"🛒 紹介予定商品：{selected_item.get('name', '商品名未取得')}"
    )

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
            "image": ""
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

    else:

        api_key = st.secrets.get("GEMINI_API_KEY", "")

        if not api_key:

            st.error("Gemini APIキーが設定されていません。")

        else:

            try:

                with st.spinner("ボボが記事を執筆しています..."):

                    client = genai.Client(api_key=api_key)

                    selected_item = st.session_state.get(
                        "selected_rakuten_item"
                    )

                    if selected_item:

                        product_details = f"""
【紹介する商品情報】

商品名：
{selected_item.get("name", "未取得")}

価格：
{selected_item.get("price", "未取得")}円

ショップ：
{selected_item.get("shop_name", "未取得")}

評価：
{selected_item.get("review_average", "未取得")} / 5

口コミ件数：
{selected_item.get("review_count", "未取得")}件

商品URL：
{selected_item.get("affiliate_url") or selected_item.get("url", "未取得")}
"""

                    else:

                        product_details = """
【紹介する商品情報】
商品は指定されていません。
記事テーマに沿って一般的な記事を作成してください。
"""

                    prompt = f"""
あなたはプロのWebライターであり、
AI Affiliate Officeの執筆担当「ボボ」です。

noteに投稿する記事を作成してください。

【テーマ】
{topic}

【ジャンル】
{genre}

【文字数】
{length}

{product_details}

【執筆ルール】

・読者にとって役立つ内容にする
・自然で読みやすい日本語を使う
・タイトルを最初に付ける
・見出しを適切に使用する
・具体例を入れる
・最後にまとめを入れる
・そのままnoteの下書きに使える形式にする
・購入を検討している読者の疑問に答える
・メリットだけでなく注意点も説明する
・過度な購入誘導や誇張表現を避ける

【商品情報に関する重要ルール】

・提供された商品情報を優先して使用する
・確認できていない性能、機能、効果を捏造しない
・実際に確認していない口コミ内容を作らない
・価格、評価、口コミ件数を変更しない
・不明な情報は「未確認」と記載する
・商品URLは提供されたものをそのまま記載する
・商品を実際に使用したかのような体験談を書かない

【記事構成】

1. 読者の悩みや疑問
2. 商品の概要
3. 商品の特徴
4. メリット
5. 注意点・デメリット
6. 商品選びのポイント
7. まとめ

タイトルと本文を分けず、
完成した記事として出力してください。
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
                                "通常モデルが混雑中です。"
                                "予備モデルに切り替えます..."
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
# グミの品質チェック
# --------------------------------

st.divider()
st.subheader("📋 グミの品質チェック")
st.caption("ボボが生成した記事をグミが公開前に確認します。")

if st.session_state.get("generated_article"):

    if st.button(
        "🔍 グミに品質チェックさせる",
        use_container_width=True
    ):

        try:
            with st.spinner("グミが記事を確認しています..."):

                selected_item = st.session_state.get(
                    "selected_rakuten_item"
                )

                quality_result = check_article_quality(
                    title=st.session_state["generated_article"].splitlines()[0].lstrip("# ").strip(),
                    body=st.session_state["generated_article"],
                    selected_item=selected_item
                )

                st.session_state["quality_result"] = quality_result

        except Exception as e:
            st.error(f"品質チェックエラー：{e}")

if st.session_state.get("quality_result"):

    st.markdown("### 📝 グミのチェック結果")
    st.markdown(st.session_state["quality_result"])

    if st.button("品質チェック結果を閉じる"):
        st.session_state.pop("quality_result", None)
        st.rerun()


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

        st.session_state.pop("generated_article", None)

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
    "手動商品登録機能を搭載しています。"
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
    "楽天APIの認証情報を設定すると商品情報を取得できます。"
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
        "🛒 楽天市場の商品を検索",
        use_container_width=True
    )


if rakuten_submit:

    if not rakuten_keyword.strip():

        st.warning("検索キーワードを入力してください。")

    else:

        try:

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

                st.info("該当する商品は見つかりませんでした。")

        except Exception as e:

            st.error(f"楽天商品検索エラー：{e}")


# --------------------------------
# 楽天市場 商品検索結果
# --------------------------------

if "rakuten_results" in st.session_state:

    st.subheader("📦 楽天市場の商品検索結果")

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

                st.markdown(
                    f"**{item.get('name', '商品名未取得')}**"
                )

                price = item.get("price", 0)

                if price:

                    st.write(f"価格：{price:,}円")

                else:

                    st.write("価格：未取得")

                st.write(
                    f"ショップ：{item.get('shop_name', '未取得')}"
                )

                st.write(
                    f"評価：{item.get('review_average', 0)} / 5"
                )

                st.write(
                    f"口コミ件数：{item.get('review_count', 0)}件"
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

                    if item.get("affiliate_url"):

                        st.caption("アフィリエイトURL")

                    else:

                        st.caption(
                            "通常の商品URLです。"
                            "アフィリエイトURLは未取得です。"
                        )

                if st.button(
                    "✍️ この記事で紹介する",
                    key=f"select_rakuten_item_{index}",
                    use_container_width=True
                ):

                    st.session_state["selected_rakuten_item"] = item

                    st.session_state["apply_selected_item_to_topic"] = True

                    st.success("商品を記事作成に設定しました！")
                    st.rerun()
