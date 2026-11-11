
import streamlit as st
from google import genai


def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        raise RuntimeError("Gemini APIキーが設定されていません。")

    return genai.Client(api_key=api_key)


def generate_with_fallback(client, prompt):
    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
    ]

    errors = []

    for model in models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            if response.text and response.text.strip():
                return response.text.strip()

            errors.append(f"{model}: 応答が空でした")

        except Exception as e:
            errors.append(f"{model}: {str(e)[:200]}")

    raise RuntimeError(
        "すべてのGeminiモデルで処理できませんでした。\n"
        + "\n".join(errors)
    )


def check_article_quality(title, body, selected_item=None):
    """グミが記事の品質を確認する"""

    client = get_gemini_client()
    product_info = selected_item or {}

    prompt = f"""
あなたはAI Affiliate Officeの品質確認担当「グミ」です。

以下の記事を公開前に厳しくチェックしてください。

【タイトル】
{title}

【記事本文】
{body}

【登録商品情報】
商品名：{product_info.get("name", "未登録")}
価格：{product_info.get("price", "未確認")}
ショップ：{product_info.get("shop_name", "未確認")}
評価：{product_info.get("review_average", "未確認")}
口コミ件数：{product_info.get("review_count", "未確認")}
商品URL：{product_info.get("affiliate_url") or product_info.get("url") or "未設定"}

【チェック項目】
1. 商品名・価格・ショップ情報の整合性
2. 未確認の口コミ・評価・販売実績
3. 根拠のない断定や誇張表現
4. 商品URL・アフィリエイトURLの有無
5. 読みやすさ・見出し・記事構成
6. 読者に誤解を与える表現
7. 修正が必要な文章と具体的な修正案

【重要】
・外部サイトを確認したように装わない。
・提供されていない情報を事実として扱わない。
・不明な情報は未確認とする。
・問題がない項目も明記する。

最後に次の形式で判定してください。

【総合判定】
公開推奨 / 修正後に公開推奨 / 公開非推奨

【評価】
100点満点

【重大な問題】

【修正推奨箇所】

【良い点】

【最終アドバイス】
"""

    return generate_with_fallback(client, prompt)


def revise_article(title, body, quality_result, selected_item=None):
    """ボボがグミの指摘を反映して記事を修正する"""

    client = get_gemini_client()
    product_info = selected_item or {}

    prompt = f"""
あなたはAI Affiliate Officeの執筆担当「ボボ」です。

グミの品質チェック結果をもとに、
以下の記事を修正してください。

【元の記事タイトル】
{title}

【元の記事本文】
{body}

【グミの品質チェック結果】
{quality_result}

【登録商品情報】
商品名：{product_info.get("name", "未登録")}
価格：{product_info.get("price", "未確認")}
ショップ：{product_info.get("shop_name", "未確認")}
評価：{product_info.get("review_average", "未確認")}
口コミ件数：{product_info.get("review_count", "未確認")}
商品URL：{product_info.get("affiliate_url") or product_info.get("url") or "未設定"}

【修正ルール】

1. グミが指摘した問題を可能な限り修正する。
2. 商品情報は登録された情報を優先する。
3. 未確認の価格・口コミ・評価を捏造しない。
4. 存在しない機能や性能を追加しない。
5. 実際に使用したような体験談を作らない。
6. 根拠のない断定や過剰な宣伝表現を削除する。
7. 商品URLがない場合は勝手に作らない。
8. 元の記事の有益な内容は残す。
9. 読者にとって自然で読みやすい文章にする。
10. 修正後の記事だけを出力する。

【重要】
グミの指摘に事実誤認がある場合は、
無理にその指摘を採用しないでください。

確認できない情報を推測で補わず、
必要に応じて「未確認」と記載してください。
"""

    return generate_with_fallback(client, prompt)
