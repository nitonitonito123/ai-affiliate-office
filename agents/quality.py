
import streamlit as st
from google import genai


def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        raise RuntimeError("Gemini APIキーが設定されていません。")

    return genai.Client(api_key=api_key)


def generate_with_fallback(client, prompt):
    # 高速モデルを最優先にする
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
                contents=prompt
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


def check_article_quality(title, body, selected_item=None):
    """グミが記事の品質を確認する"""

    client = get_gemini_client()
    product = selected_item or {}

    prompt = f"""
あなたはAI Affiliate Officeの品質担当「グミ」です。

以下の記事を公開前に確認してください。

【タイトル】
{title}

【本文】
{body}

【登録商品情報】
商品名：{product.get("name", "未登録")}
価格：{product.get("price", "未確認")}
ショップ：{product.get("shop_name", "未確認")}
評価：{product.get("review_average", "未確認")}
口コミ件数：{product.get("review_count", "未確認")}
商品URL：{product.get("affiliate_url") or product.get("url") or "未設定"}

【確認項目】
1. 商品情報と登録情報の整合性
2. 口コミ・評価・実績の捏造
3. 誇張表現や根拠のない断定
4. 商品URLの有無
5. 読みやすさ・見出し・構成
6. 読者に誤解を与える表現

【重要ルール】
・外部サイトを確認したと装わない。
・登録されていない情報は事実として扱わない。
・問題がない項目も明記する。
・修正案は具体的に示す。

以下の形式で簡潔に回答してください。

【総合判定】
公開推奨 / 修正後に公開推奨 / 公開非推奨

【評価】
100点満点

【重大な問題】

【修正推奨箇所】
修正前と修正案を示す。

【良い点】

【最終アドバイス】
"""

    return generate_with_fallback(client, prompt)


def revise_article(title, body, quality_result, selected_item=None):
    """ボボが品質チェック結果を反映して記事を修正する"""

    client = get_gemini_client()
    product = selected_item or {}

    prompt = f"""
あなたはAI Affiliate Officeの執筆担当「ボボ」です。

グミの品質チェック結果を反映し、記事を完成させてください。

【タイトル】
{title}

【元の記事】
{body}

【グミの指摘】
{quality_result}

【登録商品情報】
商品名：{product.get("name", "未登録")}
価格：{product.get("price", "未確認")}
ショップ：{product.get("shop_name", "未確認")}
評価：{product.get("review_average", "未確認")}
口コミ件数：{product.get("review_count", "未確認")}
商品URL：{product.get("affiliate_url") or product.get("url") or "未設定"}

【修正ルール】
1. グミの重大な指摘を優先して修正する。
2. 元の記事の有益な情報は残す。
3. 商品情報は登録情報を優先する。
4. 未確認の価格・口コミ・評価を捏造しない。
5. 存在しない機能や性能を追加しない。
6. 使用していない商品の体験談を作らない。
7. 誇張表現や根拠のない断定を削除する。
8. URLがない場合は勝手に作らない。
9. 自然で読みやすい日本語にする。
10. グミの指摘が誤っている場合は無理に採用しない。

【出力】
修正後の記事だけを出力してください。
タイトルと見出しを含め、noteに掲載できる完成原稿にしてください。
"""

    return generate_with_fallback(client, prompt)
