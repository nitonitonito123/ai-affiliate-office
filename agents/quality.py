
import streamlit as st
from google import genai


def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        raise RuntimeError("Gemini APIキーが設定されていません。")

    return genai.Client(api_key=api_key)


def generate_with_fallback(client, prompt, max_tokens=2500):
    models = [
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
    ]

    errors = []

    for model in models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    max_output_tokens=max_tokens
                )
            )

            if response.text and response.text.strip():
                return response.text.strip()

            errors.append(f"{model}: 応答が空でした")

        except Exception as e:
            errors.append(f"{model}: {str(e)[:150]}")

    raise RuntimeError(
        "すべてのGeminiモデルで処理できませんでした。\n"
        + "\n".join(errors)
    )


def check_article_quality(
    title,
    body,
    selected_item=None,
    article_type="一般記事"
):
    """グミが記事の種類に合わせて品質を確認する"""

    client = get_gemini_client()
    product = selected_item or {}

    product_info = f"""
商品名：{product.get("name", "未登録")}
価格：{product.get("price", "未確認")}
ショップ：{product.get("shop_name", "未確認")}
評価：{product.get("review_average", "未確認")}
口コミ件数：{product.get("review_count", "未確認")}
商品URL：{product.get("affiliate_url") or product.get("url") or "未設定"}
"""

    if article_type == "アフィリエイト記事":
        evaluation_rules = """
【アフィリエイト記事の評価基準】

以下の項目を確認してください。

1. 商品情報と登録情報が一致しているか
2. 商品の機能・性能・価格などを捏造していないか
3. 口コミ・評価・実績を捏造していないか
4. 未確認情報を事実として断定していないか
5. 商品URLが設定されているか
6. 商品の魅力や注意点が適切に説明されているか
7. 読者に自然な購入判断の導線があるか
8. 読みやすさ・見出し・構成が適切か

【重要】
・商品情報が未登録の場合は、その事実を明記してください。
・商品URLが未設定の場合は、問題点として指摘してください。
・外部サイトを確認したと装わないでください。
・未確認の価格や口コミを事実として扱わないでください。
・購入を強制するような誇張表現は指摘してください。
・商品情報が不足している場合、記事の内容だけで確認できる範囲を評価してください。
"""
    else:
        evaluation_rules = """
【一般記事の評価基準】

以下の項目を確認してください。

1. 情報の正確性
2. 読者にとって役立つ内容か
3. 説明に具体性があるか
4. 論理的で分かりやすい構成か
5. タイトルと本文の内容が一致しているか
6. 見出しや文章の読みやすさ
7. 根拠のない断定や誇張がないか
8. 読者が実際に行動できる情報があるか

【重要】
・一般記事は商品紹介を目的としていません。
・商品情報がないことを減点しないでください。
・商品URLがないことを減点しないでください。
・ショップ、価格、口コミ、商品評価がないことを減点しないでください。
・購入への誘導や販売用のCTAを要求しないでください。
・商品情報が未登録であることを問題として指摘しないでください。
・記事のテーマに必要な情報が不足している場合は指摘してください。
・外部サイトを確認したと装わないでください。
"""

    prompt = f"""
あなたはAI Affiliate Officeの品質担当「グミ」です。
記事の種類に合わせて、公平かつ厳密に品質を確認してください。

【記事の種類】
{article_type}

【タイトル】
{title}

【本文】
{body}

【登録商品情報】
{product_info}

{evaluation_rules}

【共通の確認ルール】
・存在しない情報や体験談を捏造していないか確認してください。
・事実と意見を区別してください。
・重大な問題と軽微な問題を区別してください。
・問題がない項目も確認結果に含めてください。
・記事の種類に合わない評価基準を適用しないでください。
・点数は実際の内容に基づいて判断してください。

【出力形式】

【総合判定】
公開推奨 / 修正後に公開推奨 / 公開非推奨

【評価】
100点満点で採点

【重大な問題】
なければ「なし」と記載。

【修正推奨箇所】
修正前 → 修正案。
なければ「なし」。

【良い点】
簡潔に記載。

【最終アドバイス】
公開前に必要な対応を簡潔に記載。

回答は簡潔かつ具体的にしてください。
"""

    return generate_with_fallback(
        client,
        prompt,
        max_tokens=1800
    )


def revise_article(
    title,
    body,
    quality_result,
    selected_item=None,
    article_type="一般記事"
):
    """ボボが記事の種類に合わせて修正する"""

    client = get_gemini_client()
    product = selected_item or {}

    product_info = f"""
商品名：{product.get("name", "未登録")}
価格：{product.get("price", "未確認")}
ショップ：{product.get("shop_name", "未確認")}
評価：{product.get("review_average", "未確認")}
口コミ件数：{product.get("review_count", "未確認")}
商品URL：{product.get("affiliate_url") or product.get("url") or "未設定"}
"""

    if article_type == "アフィリエイト記事":
        revision_rules = """
【アフィリエイト記事の修正ルール】

・重大な指摘を優先して修正する。
・登録された商品情報を優先する。
・商品情報にない機能や性能を追加しない。
・未確認の価格、口コミ、評価を捏造しない。
・実際に使用していない商品の体験談を作らない。
・誇張表現や根拠のない断定を削除する。
・商品URLがない場合は勝手に作らない。
・商品情報が不足している場合は、推測せず自然な表現にする。
・読者が購入を判断できるよう、商品の特徴や注意点を分かりやすく説明する。
・自然な購入導線を設ける。
"""
    else:
        revision_rules = """
【一般記事の修正ルール】

・重大な指摘を優先して修正する。
・読者にとって役立つ情報を増やす。
・文章の流れと論理構成を改善する。
・具体例や実践方法を必要に応じて加える。
・根拠のない断定や誇張表現を削除する。
・事実が確認できない内容を作らない。
・商品紹介や販売目的の文章を無理に追加しない。
・商品URLや購入への誘導を無理に追加しない。
・元の記事の有益な情報と構成はできるだけ残す。
"""

    prompt = f"""
あなたはAI Affiliate Officeの執筆担当「ボボ」です。
品質チェック結果を反映し、note掲載用の記事に修正してください。

【記事の種類】
{article_type}

【タイトル】
{title}

【元の記事】
{body}

【品質チェック結果】
{quality_result}

【登録商品情報】
{product_info}

{revision_rules}

【共通ルール】
・自然で読みやすい日本語にする。
・元の記事のテーマから逸脱しない。
・情報を水増しするための不要な文章を追加しない。
・品質チェックの指摘が誤っている場合は無理に採用しない。
・未確認情報を事実として書かない。

【出力】
修正後の記事だけを出力してください。
タイトルと見出しを含め、noteに掲載できる完成原稿にしてください。
"""

    return generate_with_fallback(
        client,
        prompt,
        max_tokens=6000
    )
