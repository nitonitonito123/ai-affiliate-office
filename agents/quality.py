
import streamlit as st
from google import genai


def check_article_quality(title, body, selected_item=None):
    """グミがAI記事の品質を確認する"""

    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        raise RuntimeError("Gemini APIキーが設定されていません。")

    client = genai.Client(api_key=api_key)

    product_info = selected_item or {}

    prompt = f"""
あなたはAI Affiliate Officeの
商品情報・品質確認担当「グミ」です。

以下の記事を公開前に厳しくチェックしてください。

【記事タイトル】
{title}

【記事本文】
{body}

【登録されている商品情報】
商品名：{product_info.get("name", "未登録")}
価格：{product_info.get("price", "未確認")}
ショップ：{product_info.get("shop_name", "未確認")}
評価：{product_info.get("review_average", "未確認")}
口コミ件数：{product_info.get("review_count", "未確認")}
商品URL：{product_info.get("url", "") or product_info.get("affiliate_url", "未設定")}

次の項目を確認してください。

1. 商品名・価格・ショップ情報の整合性
2. 口コミ・評価・販売実績などの未確認情報
3. 根拠のない断定や誇張表現
4. アフィリエイトリンクの設定状況
5. 読みやすさ、見出し、記事構成
6. 読者に誤解を与える表現
7. 修正が必要な文章と具体的な修正案

【重要なルール】
・記事にない情報を勝手に補わない。
・登録情報と異なる情報は指摘する。
・未確認情報は未確認と判定する。
・実際に外部サイトを確認したように装わない。
・商品URLがない場合は、そのことを指摘する。
・問題がない項目も明記する。

最後に次の形式で総合判定してください。

【総合判定】
公開推奨 / 修正後に公開推奨 / 公開非推奨

【評価】
100点満点

【重大な問題】

【修正推奨箇所】

【良い点】

【最終アドバイス】
"""

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
                return response.text

            errors.append(f"{model}: 応答が空でした")

        except Exception as e:
            errors.append(f"{model}: {str(e)[:200]}")
            continue

    raise RuntimeError(
        "品質チェックを実行できませんでした。\n"
        + "\n".join(errors)
    )
