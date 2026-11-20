
import os
import re
import streamlit as st
from google import genai


# --------------------------------
# Gemini接続
# --------------------------------

def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。")

    return genai.Client(api_key=api_key)


# --------------------------------
# Geminiモデルの切り替え
# --------------------------------

MODEL_CANDIDATES = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]


def generate_with_fallback(prompt, max_output_tokens=6000):
    client = get_gemini_client()
    last_error = None

    for model_name in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "max_output_tokens": max_output_tokens,
                },
            )

            if response and response.text:
                return response.text.strip()

        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(
        f"すべてのGeminiモデルで生成に失敗しました。"
        f"最終エラー：{last_error}"
    )


# --------------------------------
# 商品情報取得
# --------------------------------

def get_product_info(item):
    if not item:
        return {}

    return {
        "name": item.get("name", "未登録"),
        "price": item.get("price", "未確認"),
        "url": item.get("url", ""),
        "affiliate_url": item.get("affiliate_url", ""),
        "shop_name": item.get("shop_name", "未確認"),
        "review_average": item.get("review_average", "未確認"),
        "review_count": item.get("review_count", "未確認"),
        "source_type": item.get("source_type", "未確認"),
        "verification_status": item.get(
            "verification_status",
            "未確認"
        ),
        "verified_by_user": item.get(
            "verified_by_user",
            False
        ),
        "is_demo": item.get("is_demo", False),
    }


def format_product_info(item):
    info = get_product_info(item)

    if not info:
        return "商品情報なし"

    return f"""
商品名：{info["name"]}
価格：{info["price"]}
商品ページ：{info["url"]}
アフィリエイトURL：{info["affiliate_url"]}
ショップ名：{info["shop_name"]}
評価：{info["review_average"]}
口コミ件数：{info["review_count"]}
情報取得元：{info["source_type"]}
確認状態：{info["verification_status"]}
ユーザー確認：{info["verified_by_user"]}
デモ商品：{info["is_demo"]}
"""


# --------------------------------
# 商品情報の確認状態
# --------------------------------

def is_product_verified(item):
    if not item:
        return False

    if item.get("is_demo", False):
        return False

    if item.get("verification_status") != "確認済み":
        return False

    if not item.get("verified_by_user", False):
        return False

    product_url = (item.get("url") or "").strip()
    affiliate_url = (item.get("affiliate_url") or "").strip()

    if not product_url or not affiliate_url:
        return False

    return True


# --------------------------------
# 根拠が必要な表現の検出
# --------------------------------

UNVERIFIED_CLAIM_PATTERNS = [
    (
        r"話題の|話題になっている|注目の|注目されている",
        "話題・注目の根拠が必要"
    ),
    (
        r"人気の|人気商品|人気ブランド|大人気|高い人気",
        "人気を示す根拠が必要"
    ),
    (
        r"口コミで高評価|高評価が多い|評判が良い|好評",
        "口コミ・評判の根拠が必要"
    ),
    (
        r"売れている|売れ筋|ランキング上位|ベストセラー",
        "販売実績・ランキングの根拠が必要"
    ),
    (
        r"ダメージを軽減|ダメージを抑え|傷みにくい|髪を傷めない",
        "ダメージ軽減効果の根拠が必要"
    ),
    (
        r"ツヤが出る|ツヤ髪|艶髪|髪にツヤを与え",
        "仕上がり効果の根拠が必要"
    ),
    (
        r"水分を保つ|水分を閉じ込め|潤いを保つ|保湿効果",
        "保湿・水分効果の根拠が必要"
    ),
    (
        r"速い立ち上がり|すぐに使える|急速に温まる|高速加熱",
        "加熱時間の根拠が必要"
    ),
    (
        r"短時間で|時短になる|素早くスタイリング|効率よく",
        "時間短縮効果の根拠が必要"
    ),
    (
        r"高性能|優れた性能|抜群の性能|圧倒的",
        "性能を裏付ける根拠が必要"
    ),
    (
        r"軽量|軽い設計|コンパクト|持ち運びやすい",
        "重量・寸法の根拠が必要"
    ),
    (
        r"初心者でも簡単|誰でも使いやすい|使いやすい設計",
        "使いやすさの根拠が必要"
    ),
    (
        r"おすすめです|おすすめできる|最適です|最適な商品",
        "推薦理由の具体性が必要"
    ),
]


def detect_unverified_claims(article, item=None):
    warnings = []

    if not article:
        return warnings

    for pattern, message in UNVERIFIED_CLAIM_PATTERNS:
        if re.search(pattern, article):
            warnings.append(message)

    info = get_product_info(item)

    if info:
        price = str(info.get("price", "未確認"))
        review_count = str(info.get("review_count", "未確認"))
        review_average = str(info.get("review_average", "未確認"))

        if (
            price in ("", "未確認", "未登録", "None", "0")
            and re.search(r"価格|円|値段|購入時", article)
        ):
            warnings.append("価格情報が未確認")

        if (
            review_count in ("", "未確認", "未登録", "None", "0")
            and re.search(r"口コミ|レビュー|評価|評判", article)
        ):
            warnings.append("口コミ件数が未確認")

        if (
            review_average in ("", "未確認", "未登録", "None", "0")
            and re.search(r"高評価|評価が高い|星[0-9]", article)
        ):
            warnings.append("商品評価が未確認")

    return list(dict.fromkeys(warnings))


# --------------------------------
# PR表記チェック
# --------------------------------

def has_pr_disclosure(article):
    if not article:
        return False

    disclosure_patterns = [
        r"PR",
        r"広告",
        r"アフィリエイト広告",
        r"プロモーション",
        r"広告を含み",
    ]

    for pattern in disclosure_patterns:
        if re.search(pattern, article, re.IGNORECASE):
            return True

    return False


def has_intro_disclosure(article):
    if not article:
        return False

    # 冒頭500文字以内にPR・広告表示があることを確認
    intro = article[:500]

    disclosure_patterns = [
        r"PR",
        r"広告",
        r"アフィリエイト広告",
        r"プロモーション",
    ]

    for pattern in disclosure_patterns:
        if re.search(pattern, intro, re.IGNORECASE):
            return True

    return False


# --------------------------------
# 品質チェックルール
# --------------------------------

def get_evaluation_rules(article_type):
    if article_type == "アフィリエイト記事":
        return """
【アフィリエイト記事の厳格ルール】

1. 未確認の商品情報を事実として書かない。
2. 価格、口コミ件数、評価は確認できた場合のみ記載する。
3. 人気・話題・売れ筋などは根拠がない限り使用禁止。
4. 性能・効果を断定しない。
5. 商品情報と本文の内容を照合する。
6. 実際に使用したような体験談を捏造しない。
7. 公式情報で確認できない仕様を書かない。
8. メリット・デメリットを公平に説明する。
9. PR・広告表示を記事冒頭に置く。
10. アフィリエイトリンクの直前または近くにも広告表示を置く。
11. 読者に誤解を与える表現を禁止する。
12. 根拠のない推薦・ランキングを禁止する。
13. 商品購入を急かす過度な表現を禁止する。

【公開判定】

以下の問題が1つでも残っている場合、
「公開推奨」と判定してはいけません。

・未確認情報を断定している
・根拠のない性能・効果・人気表現がある
・PR表記が記事冒頭にない
・商品情報と本文が矛盾している
・広告リンクがない
・商品情報が未確認

判定は次の3種類のみ。

「公開推奨」
「修正後に公開推奨」
「公開非推奨」
"""

    return """
【一般記事のルール】

1. 誤情報を含めない。
2. 根拠のない断定を避ける。
3. 読者の悩みを解決する具体的な内容にする。
4. 誇張表現を避ける。
5. 読みやすい構成にする。
6. 内容の重複を避ける。
7. 実体験を捏造しない。

一般記事はアフィリエイトリンクやPR表記を必須としない。
"""


# --------------------------------
# 点数をコード側で強制制限
# --------------------------------

def extract_score(text):
    if not text:
        return None

    patterns = [
        r"【評価】\s*(\d{1,3})\s*点",
        r"評価[：:\s]*?(\d{1,3})\s*/\s*100",
        r"(\d{1,3})\s*/\s*100点",
        r"(\d{1,3})\s*点",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            score = int(match.group(1))
            return max(0, min(100, score))

    return None


def replace_score(text, score):
    if not text:
        text = ""

    patterns = [
        r"【評価】\s*\d{1,3}\s*点",
        r"評価[：:\s]*?\d{1,3}\s*/\s*100",
        r"\d{1,3}\s*/\s*100点",
        r"\d{1,3}\s*点",
    ]

    for pattern in patterns:
        if re.search(pattern, text):
            text = re.sub(
                pattern,
                f"【評価】 {score}点",
                text,
                count=1
            )
            return text

    return f"【評価】 {score}点\n\n{text}"


def replace_judgment(text, judgment):
    if not text:
        text = ""

    patterns = [
        r"【総合判定】[^\n]*",
        r"総合判定[：:].*[^\n]*",
    ]

    for pattern in patterns:
        if re.search(pattern, text):
            text = re.sub(
                pattern,
                f"【総合判定】 {judgment}",
                text,
                count=1
            )
            return text

    return f"【総合判定】 {judgment}\n\n{text}"


# --------------------------------
# 品質チェック
# --------------------------------

def check_article_quality(
    title,
    body,
    selected_item=None,
    article_type="一般記事"
):
    product_info = format_product_info(selected_item)

    detected_claims = detect_unverified_claims(
        body,
        selected_item
    )

    product_verified = is_product_verified(selected_item)

    disclosure_exists = has_pr_disclosure(body)
    intro_disclosure_exists = has_intro_disclosure(body)

    hard_issues = []
    soft_issues = []

    # 商品情報確認
    if article_type == "アフィリエイト記事":
        if not selected_item:
            hard_issues.append("商品情報が登録されていません。")

        elif not product_verified:
            hard_issues.append(
                "商品情報が未確認、またはURL不足です。"
            )

        if not disclosure_exists:
            hard_issues.append(
                "PR・広告表記が記事内にありません。"
            )

        if not intro_disclosure_exists:
            hard_issues.append(
                "記事冒頭500文字以内にPR・広告表記がありません。"
            )

        if detected_claims:
            soft_issues.extend(detected_claims)

    prompt = f"""
あなたはAI Affiliate Officeの品質担当「グミ」です。

記事を厳格にチェックしてください。
特にアフィリエイト記事は、読者への誤情報を絶対に許容しません。

【記事タイトル】
{title}

【記事種類】
{article_type}

【商品情報】
{product_info}

【商品情報確認済み】
{product_verified}

【プログラムが検出した問題】
{detected_claims}

【プログラムが検出した重大な問題】
{hard_issues}

【プログラムが検出したPR表記】
記事内：{disclosure_exists}
冒頭：{intro_disclosure_exists}

【記事本文】
{body}

{get_evaluation_rules(article_type)}

【出力形式】

【総合判定】 公開推奨 / 修正後に公開推奨 / 公開非推奨
【評価】 100点満点の点数

【重大な問題】
問題がなければ「なし」

【根拠確認が必要な表現】
具体的な文章と、問題の理由を記載

【修正箇所】
修正が必要な文章と修正案

【良い点】
記事の良い部分

【最終アドバイス】
公開前に必要な作業

注意：
問題がある場合は高得点をつけないでください。
未確認情報や根拠のない断定が残っている場合、
絶対に「公開推奨」と判定しないでください。
"""

    ai_result = generate_with_fallback(
        prompt,
        max_output_tokens=5000
    )

    if not ai_result:
        ai_result = "品質チェック結果を取得できませんでした。"

    # --------------------------------
    # コードによる強制判定
    # --------------------------------

    score = extract_score(ai_result)

    if score is None:
        score = 50

    score_limit = 100
    forced_judgment = None

    if article_type == "アフィリエイト記事":

        # 商品確認ができていない場合
        if not product_verified:
            score_limit = min(score_limit, 49)
            forced_judgment = "公開非推奨"

        # 商品情報がない、URL不足、PR表示不足
        if hard_issues:
            score_limit = min(score_limit, 49)
            forced_judgment = "公開非推奨"

        # 根拠不足表現が検出された場合
        if detected_claims:
            score_limit = min(score_limit, 59)

            if forced_judgment is None:
                forced_judgment = "修正後に公開推奨"

        # PR表記の冒頭不足
        if not intro_disclosure_exists:
            score_limit = min(score_limit, 59)
            forced_judgment = "修正後に公開推奨"

        # 問題がある場合は公開推奨を禁止
        if hard_issues or detected_claims:
            forced_judgment = (
                "公開非推奨"
                if hard_issues
                else "修正後に公開推奨"
            )

    # AIの点数を実際に制限する
    final_score = min(score, score_limit)

    # 点数から判定を強制
    if forced_judgment:
        final_judgment = forced_judgment

    elif final_score >= 80:
        final_judgment = "公開推奨"

    elif final_score >= 60:
        final_judgment = "修正後に公開推奨"

    else:
        final_judgment = "公開非推奨"

    ai_result = replace_score(
        ai_result,
        final_score
    )

    ai_result = replace_judgment(
        ai_result,
        final_judgment
    )

    # --------------------------------
    # 強制判定の説明を追加
    # --------------------------------

    enforcement_notes = []

    if score_limit < 100:
        enforcement_notes.append(
            f"プログラムによる点数上限：{score_limit}点"
        )

    if hard_issues:
        enforcement_notes.extend(hard_issues)

    if detected_claims:
        enforcement_notes.append(
            "根拠確認が必要な表現："
            + "、".join(detected_claims)
        )

    if enforcement_notes:
        ai_result += "\n\n【プログラムによる強制判定】\n"
        ai_result += "\n".join(
            f"・{note}"
            for note in enforcement_notes
        )

    return ai_result


# --------------------------------
# アフィリエイトブロック抽出
# --------------------------------

AFFILIATE_BLOCK_START = "<!-- AFFILIATE_BLOCK_START -->"
AFFILIATE_BLOCK_END = "<!-- AFFILIATE_BLOCK_END -->"


def extract_affiliate_block(article):
    if not article:
        return ""

    if (
        AFFILIATE_BLOCK_START in article
        and AFFILIATE_BLOCK_END in article
    ):
        start = article.find(AFFILIATE_BLOCK_START)
        end = article.find(AFFILIATE_BLOCK_END)

        if end >= start:
            return article[start:end + len(AFFILIATE_BLOCK_END)]

    return ""


# --------------------------------
# ボボによる自動修正
# --------------------------------

def revise_article(
    title,
    body,
    quality_result,
    selected_item=None,
    article_type="一般記事"
):
    original_affiliate_block = extract_affiliate_block(body)

    product_info = format_product_info(selected_item)

    detected_claims = detect_unverified_claims(
        body,
        selected_item
    )

    prompt = f"""
あなたはAI Affiliate Officeの執筆担当「ボボ」です。

グミの品質チェック結果に従い、記事を修正してください。

【記事タイトル】
{title}

【記事種類】
{article_type}

【商品情報】
{product_info}

【品質チェック結果】
{quality_result}

【現在の記事】
{body}

【修正ルール】

1. グミの指摘事項をすべて修正する。
2. 未確認情報は削除する。
3. 未確認の価格・口コミ・評価を作らない。
4. 未確認の人気・話題・売れ筋表現を削除する。
5. 未確認の性能・効果を断定しない。
6. 実際に使用したような体験談を作らない。
7. 公式情報で確認できない仕様を書かない。
8. 読者に誤解を与える表現を削除する。
9. 商品情報が不足している場合は、確認できない旨を明記する。
10. 読みやすい日本語に修正する。
11. 元の記事の構成と良い点は可能な限り維持する。
12. アフィリエイト記事の場合、記事冒頭に「PR」「広告」などの
    明確な表示を追加する。
13. アフィリエイトリンクの近くにも広告表示を配置する。
14. 「こんにちは、ボボです」などの不要な挨拶を入れない。
15. 記事本文のみを出力する。修正解説は不要。

【アフィリエイト記事の追加ルール】

商品情報が確認済みでも、確認できていない性能や効果を
勝手に追加してはいけません。

確認できる情報だけを使用してください。

元の記事のアフィリエイトリンク・商品名・URLは
変更しないでください。

"""

    revised_article = generate_with_fallback(
        prompt,
        max_output_tokens=6000
    )

    if not revised_article:
        return body

    revised_article = revised_article.strip()

    # --------------------------------
    # 元のリンクブロックを保護
    # --------------------------------

    if original_affiliate_block:

        # 修正版にリンクブロックが複数あれば一度除去
        if AFFILIATE_BLOCK_START in revised_article:
            revised_article = revised_article.split(
                AFFILIATE_BLOCK_START,
                1
            )[0].rstrip()

        # 元の正しいリンクブロックを末尾に復元
        revised_article = (
            revised_article.rstrip()
            + "\n\n"
            + original_affiliate_block
        )

    # --------------------------------
    # PR表記を記事冒頭に強制挿入
    # --------------------------------

    if article_type == "アフィリエイト記事":

        if not has_intro_disclosure(revised_article):

            disclosure = (
                "※本記事にはアフィリエイト広告が含まれています。\n\n"
            )

            revised_article = (
                disclosure
                + revised_article.lstrip()
            )

    return revised_article
