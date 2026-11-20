import os
import re
import streamlit as st
from google import genai


# ==========================================
# Gemini接続
# ==========================================

def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。")

    return genai.Client(api_key=api_key)


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

    raise RuntimeError(
        f"Gemini生成に失敗しました。最終エラー：{last_error}"
    )


# ==========================================
# 商品情報
# ==========================================

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
            "verification_status", "未確認"
        ),
        "verified_by_user": item.get(
            "verified_by_user", False
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


def is_product_verified(item):
    if not item:
        return False

    if item.get("is_demo", False):
        return False

    if item.get("verification_status") != "確認済み":
        return False

    if not item.get("verified_by_user", False):
        return False

    if not (item.get("url") or "").strip():
        return False

    if not (item.get("affiliate_url") or "").strip():
        return False

    return True


# ==========================================
# 根拠が必要な表現
# ==========================================

UNVERIFIED_CLAIM_PATTERNS = [
    (
        r"話題の|話題になっている|注目の|注目されている|注目を集め",
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
        r"ダメージを軽減|ダメージを抑え|傷みにくい|髪を傷めない|負担を最小限",
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
        r"速い立ち上がり|すぐに使える|急速に温まる|高速加熱|立ち上がりが早",
        "加熱時間の根拠が必要"
    ),
    (
        r"短時間で|時短になる|素早くスタイリング|効率よく|時間を大幅に短縮",
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
        r"一度でしっかり|しっかりとクセを伸ばせ|確実に伸ばせ",
        "スタイリング効果の根拠が必要"
    ),
    (
        r"おすすめです|おすすめできる|最適です|最適な商品",
        "推薦理由の具体性が必要"
    ),
]


# ==========================================
# 未確認情報の透明な説明
# ==========================================

TRANSPARENT_PRICE_PATTERNS = [
    r"価格.{0,30}(?:未確認|未掲載|確認できません|確認してください|公式サイト|販売ページ)",
    r"値段.{0,30}(?:未確認|未掲載|確認できません|確認してください|公式サイト|販売ページ)",
    r"価格は.{0,40}(?:確認|公式サイト|販売ページ)",
    r"最新の価格.{0,40}(?:確認|公式サイト|販売ページ)",
    r"価格や仕様.{0,40}(?:確認|公式サイト|販売ページ)",
    r"販売価格.{0,40}(?:確認|公式サイト|販売ページ)",
    r"価格について.{0,40}(?:確認|公式サイト|販売ページ)",
    r"価格帯について.{0,40}(?:確認|公式サイト|販売ページ)",
    r"価格については.{0,40}(?:確認|公式サイト|販売ページ)",
    r"価格は.{0,40}(?:異なる|変わる|変動)",
]


def is_transparent_price_notice(article):
    if not article:
        return False

    return any(
        re.search(pattern, article)
        for pattern in TRANSPARENT_PRICE_PATTERNS
    )


# ==========================================
# 根拠確認表現の検出
# ==========================================

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

        price_unknown = price in (
            "", "未確認", "未登録", "None", "0"
        )

        # 価格が未確認でも、透明に説明している場合は警告しない
        if price_unknown and not is_transparent_price_notice(article):

            # 具体的な価格を記載している場合のみ警告
            if re.search(
                r"\d[\d,]*円|税込\d[\d,]*円",
                article
            ):
                warnings.append(
                    "価格情報が未確認なのに具体的価格を記載"
                )

        reviews_unknown = review_count in (
            "", "未確認", "未登録", "None", "0"
        )

        if reviews_unknown and re.search(
            r"口コミが多い|レビューが多い|口コミで|レビューで|評判が良い|高評価",
            article
        ):
            warnings.append(
                "口コミ・評判の根拠が未確認"
            )

        rating_unknown = review_average in (
            "", "未確認", "未登録", "None", "0"
        )

        if rating_unknown and re.search(
            r"評価が高い|高評価|星[0-9]|評価[0-9.]+",
            article
        ):
            warnings.append(
                "商品評価が未確認"
            )

    return list(dict.fromkeys(warnings))


# ==========================================
# PR表記
# ==========================================

def has_pr_disclosure(article):
    if not article:
        return False

    return bool(
        re.search(
            r"PR|広告|アフィリエイト広告|プロモーション|広告を含み",
            article,
            re.IGNORECASE
        )
    )


def has_intro_disclosure(article):
    if not article:
        return False

    intro = article[:500]

    return bool(
        re.search(
            r"PR|広告|アフィリエイト広告|プロモーション",
            intro,
            re.IGNORECASE
        )
    )


# ==========================================
# 評価基準
# ==========================================

def get_evaluation_rules(article_type):
    if article_type == "アフィリエイト記事":
        return """
【アフィリエイト記事の厳格ルール】

・未確認の商品情報を事実として書かない
・価格、口コミ件数、評価は確認できた場合のみ記載
・人気、話題、売れ筋は根拠がない限り使用禁止
・性能、効果を断定しない
・商品情報と本文を照合する
・体験談を捏造しない
・公式情報で確認できない仕様を書かない
・メリット、デメリットを公平に説明
・PR表記を冒頭500文字以内に配置
・アフィリエイトリンク付近にも広告表記
・読者に誤解を与える表現を禁止
・根拠のないランキングや推薦を禁止

【判定】

重大な問題が残っている場合「公開推奨」にしない。

価格未確認を透明に説明し、価格を断定していない場合、
それだけを重大な問題にしない。

根拠確認が必要な表現がある場合は、
その重大度を判断する。

軽微な表現上の問題だけで、
自動的に公開非推奨にしない。

判定は以下の3種類：

公開推奨
修正後に公開推奨
公開非推奨
"""

    return """
【一般記事のルール】

・誤情報を含めない
・根拠のない断定を避ける
・読者の悩みを解決する内容にする
・誇張表現を避ける
・読みやすい構成にする
・内容の重複を避ける
・実体験を捏造しない
"""


# ==========================================
# 点数処理
# ==========================================

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
            return max(0, min(100, int(match.group(1))))

    return None


def replace_score(text, score):
    pattern = r"【評価】\s*\d{1,3}\s*点"

    if re.search(pattern, text):
        return re.sub(
            pattern,
            f"【評価】 {score}点",
            text,
            count=1
        )

    return f"【評価】 {score}点\n\n{text}"


def replace_judgment(text, judgment):
    pattern = r"【総合判定】[^\n]*"

    if re.search(pattern, text):
        return re.sub(
            pattern,
            f"【総合判定】 {judgment}",
            text,
            count=1
        )

    return f"【総合判定】 {judgment}\n\n{text}"


# ==========================================
# 品質チェック
# ==========================================

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

    if article_type == "アフィリエイト記事":

        if not selected_item:
            hard_issues.append(
                "商品情報が登録されていません。"
            )

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

    prompt = f"""
あなたはAI Affiliate Officeの品質担当「グミ」です。

記事を厳格にチェックしてください。

【記事タイトル】
{title}

【記事種類】
{article_type}

【商品情報】
{product_info}

【商品情報確認済み】
{product_verified}

【プログラム検出問題】
{detected_claims}

【重大な問題】
{hard_issues}

【PR表記】
記事内：{disclosure_exists}
冒頭：{intro_disclosure_exists}

【記事本文】
{body}

{get_evaluation_rules(article_type)}

【重要な採点方針】

・100点満点で評価する
・重大な問題は大幅減点
・軽微な表現問題は適切な範囲で減点
・警告が1つあるだけで59点以下にしない
・透明性のある説明は評価する
・記事の構成、読みやすさ、情報の正確性を評価する
・根拠のない性能や人気を断定している場合は減点する
・問題の重大度と点数を比例させる

【出力形式】

【総合判定】 公開推奨 / 修正後に公開推奨 / 公開非推奨
【評価】 100点満点

【重大な問題】
なければ「なし」

【根拠確認が必要な表現】
文章と理由

【修正箇所】
修正前と修正案

【良い点】
記事の良い部分

【最終アドバイス】
公開前の必要作業
"""

    ai_result = generate_with_fallback(
        prompt,
        max_output_tokens=5000
    )

    if not ai_result:
        ai_result = "品質チェック結果を取得できませんでした。"

    # --------------------------------------
    # AI採点取得
    # --------------------------------------

    ai_score = extract_score(ai_result)

    if ai_score is None:
        ai_score = 50

    score_limit = 100
    forced_judgment = None

    # --------------------------------------
    # 重大問題による制限
    # --------------------------------------

    if article_type == "アフィリエイト記事":

        # 商品未確認
        if not product_verified:
            score_limit = min(score_limit, 49)
            forced_judgment = "公開非推奨"

        # PR表記不足
        if hard_issues:
            score_limit = min(score_limit, 49)
            forced_judgment = "公開非推奨"

        # ----------------------------------
        # 根拠確認表現
        # ----------------------------------

        # 軽微な問題は59点に固定しない
        # AIの評価を尊重し、最大79点に制限する
        if detected_claims:
            score_limit = min(score_limit, 79)

    # --------------------------------------
    # 最終点数
    # --------------------------------------

    final_score = min(ai_score, score_limit)

    # --------------------------------------
    # 点数に基づく判定
    # --------------------------------------

    if final_score < 60:
        final_judgment = "公開非推奨"

    elif final_score < 80:
        final_judgment = "修正後に公開推奨"

    else:
        final_judgment = "公開推奨"

    # 重大問題は強制的に公開非推奨
    if forced_judgment == "公開非推奨":
        final_judgment = "公開非推奨"

    # 根拠確認表現が残っている場合、
    # 公開推奨を禁止する
    if detected_claims and final_score >= 80:
        final_score = 79
        final_judgment = "修正後に公開推奨"

    # --------------------------------------
    # 結果の書き換え
    # --------------------------------------

    ai_result = replace_score(
        ai_result,
        final_score
    )

    ai_result = replace_judgment(
        ai_result,
        final_judgment
    )

    # --------------------------------------
    # プログラム判定理由
    # --------------------------------------

    notes = []

    if score_limit < 100:
        notes.append(
            f"プログラムによる点数上限：{score_limit}点"
        )

    if hard_issues:
        notes.extend(hard_issues)

    if detected_claims:
        notes.append(
            "根拠確認が必要な表現："
            + "、".join(detected_claims)
        )

    if notes:
        ai_result += "\n\n【プログラムによる判定】\n"
        ai_result += "\n".join(
            f"・{note}"
            for note in notes
        )

    return ai_result


# ==========================================
# アフィリエイトリンク保護
# ==========================================

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
            return article[
                start:end + len(AFFILIATE_BLOCK_END)
            ]

    return ""


# ==========================================
# ボボ自動修正
# ==========================================

def revise_article(
    title,
    body,
    quality_result,
    selected_item=None,
    article_type="一般記事"
):
    original_affiliate_block = extract_affiliate_block(body)

    product_info = format_product_info(selected_item)

    prompt = f"""
あなたはAI Affiliate Officeの執筆担当「ボボ」です。

グミの品質チェック結果に従って記事を修正してください。

【タイトル】
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

・指摘事項をすべて修正する
・未確認情報を削除する
・価格、口コミ、評価を創作しない
・人気、話題、売れ筋を根拠なく書かない
・性能や効果を断定しない
・体験談を捏造しない
・公式情報で確認できない仕様を書かない
・読者に誤解を与える表現を削除する
・読みやすい日本語にする
・元の記事の良い構成は維持する
・アフィリエイト記事は冒頭にPR表記を置く
・リンク付近にもPR表記を置く
・「こんにちは、ボボです」などの不要な挨拶を入れない
・記事本文のみを出力する

商品情報が未確認の場合は、
確認できる事実と確認が必要な情報を明確に区別する。

元のアフィリエイトリンク、商品名、URLを
勝手に変更しない。
"""

    revised_article = generate_with_fallback(
        prompt,
        max_output_tokens=6000
    )

    if not revised_article:
        return body

    revised_article = revised_article.strip()

    # --------------------------------------
    # 元のアフィリエイトリンクを復元
    # --------------------------------------

    if original_affiliate_block:

        if AFFILIATE_BLOCK_START in revised_article:
            revised_article = revised_article.split(
                AFFILIATE_BLOCK_START,
                1
            )[0].rstrip()

        revised_article = (
            revised_article.rstrip()
            + "\n\n"
            + original_affiliate_block
        )

    # --------------------------------------
    # 冒頭PR表記を強制
    # --------------------------------------

    if article_type == "アフィリエイト記事":

        if not has_intro_disclosure(revised_article):

            revised_article = (
                "※本記事にはアフィリエイト広告が含まれています。\n\n"
                + revised_article.lstrip()
            )

    return revised_article
