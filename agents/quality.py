import re
import streamlit as st
from google import genai


# ==========================================
# Gemini 接続
# ==========================================

def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        raise RuntimeError("Gemini APIキーが設定されていません。")

    return genai.Client(api_key=api_key)


# ==========================================
# Geminiモデルのフォールバック
# ==========================================

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
                    max_output_tokens=max_tokens,
                    temperature=0.2
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


# ==========================================
# 商品情報の整理
# ==========================================

def get_product_info(selected_item=None):
    product = selected_item or {}

    return {
        "name": product.get("name", "未登録"),
        "price": product.get("price", "未確認"),
        "shop_name": product.get("shop_name", "未確認"),
        "review_average": product.get("review_average", "未確認"),
        "review_count": product.get("review_count", "未確認"),

        # 通常の商品ページURL
        "product_url": product.get("url", "未設定"),

        # アフィリエイトURL
        "affiliate_url": product.get("affiliate_url", "未設定"),

        "verification_status": product.get(
            "verification_status",
            "未確認"
        ),

        "verified_by_user": product.get(
            "verified_by_user",
            False
        ),

        "is_demo": product.get(
            "is_demo",
            False
        ),
    }


def format_product_info(selected_item=None):
    info = get_product_info(selected_item)

    return f"""
商品名：{info["name"]}
価格：{info["price"]}
ショップ：{info["shop_name"]}
評価：{info["review_average"]}
口コミ件数：{info["review_count"]}
通常の商品ページURL：{info["product_url"]}
アフィリエイトURL：{info["affiliate_url"]}
確認状態：{info["verification_status"]}
ユーザー確認済み：{info["verified_by_user"]}
デモ商品：{info["is_demo"]}
"""


# ==========================================
# 商品情報の確認状態
# ==========================================

def is_product_verified(selected_item=None):
    info = get_product_info(selected_item)

    return (
        info["verification_status"] == "確認済み"
        and info["verified_by_user"] is True
        and info["product_url"] not in ("", None, "未設定")
        and info["affiliate_url"] not in ("", None, "未設定")
        and info["is_demo"] is not True
    )


# ==========================================
# 未確認の仕様・性能表現の検出
# ==========================================

def detect_unverified_claims(
    body,
    selected_item=None,
    article_type="一般記事"
):
    """
    商品情報に根拠がない状態で、仕様・性能を断定する
    表現が含まれていないか簡易検出する。

    この検出は完全な事実確認ではなく、
    公開前の注意喚起を目的とする。
    """

    if article_type != "アフィリエイト記事":
        return []

    info = get_product_info(selected_item)

    claims = []

    # 商品確認ができていない場合の検出対象
    product_verified = is_product_verified(selected_item)

    if not product_verified:

        patterns = [
            (
                r"立ち上がり.{0,20}(早い|速い|スピーディー|短い)",
                "立ち上がり速度の根拠が未確認です。"
            ),
            (
                r"温度.{0,20}(調整|設定|変更|切り替え)",
                "温度調整機能の根拠が未確認です。"
            ),
            (
                r"(プレート|パネル).{0,30}(加工|構造|素材|滑り|摩擦)",
                "プレートの仕様・素材・性能の根拠が未確認です。"
            ),
            (
                r"(髪|毛髪).{0,30}(ダメージを軽減|傷みにくい|負担を軽減)",
                "髪へのダメージ軽減効果の根拠が未確認です。"
            ),
            (
                r"(キューティクル|ツヤ|艶).{0,30}(整える|改善|保護|向上)",
                "髪への効果の根拠が未確認です。"
            ),
            (
                r"(軽量|軽い|コンパクト|持ちやすい)",
                "重量・サイズ・使用感の根拠が未確認です。"
            ),
            (
                r"(高速|速乾|時短|短時間).{0,30}(できる|実現|効果|便利)",
                "時間短縮効果の根拠が未確認です。"
            ),
            (
                r"(高性能|優れた性能|高機能|抜群の性能)",
                "性能を評価する根拠が未確認です。"
            ),
            (
                r"(口コミ|レビュー|評判).{0,30}(高い|良い|人気|好評)",
                "口コミ・評判の根拠が未確認です。"
            ),
            (
                r"(売れている|人気商品|話題の商品|注目を集めている)",
                "人気・販売実績を示す根拠が未確認です。"
            ),
        ]

        for pattern, message in patterns:
            if re.search(pattern, body):
                claims.append(message)

    # 価格未確認時の価格断定
    if info["price"] in ("未確認", "未登録", "", None):
        if re.search(
            r"(価格が高い|高価格|高めの価格|リーズナブル|安価|低価格)",
            body
        ):
            claims.append(
                "価格情報が未登録のため、価格に関する評価を確認できません。"
            )

    # 口コミ未確認時の口コミ断定
    if (
        info["review_average"] in ("未確認", "未登録", "", None)
        or info["review_count"] in ("未確認", "未登録", "", None)
    ):
        if re.search(
            r"(口コミで|レビューで|評価が高い|高評価|多くの人が支持)",
            body
        ):
            claims.append(
                "口コミ・評価情報が未登録のため、評価に関する記述を確認できません。"
            )

    return list(dict.fromkeys(claims))


# ==========================================
# 品質チェックの共通ルール
# ==========================================

def get_evaluation_rules(article_type):
    if article_type == "アフィリエイト記事":

        return """
【アフィリエイト記事の厳格評価基準】

以下の項目を必ず評価してください。

1. 商品情報と登録情報が一致しているか
2. 商品の機能・性能・価格を捏造していないか
3. 口コミ・評価・販売実績を捏造していないか
4. 未確認情報を事実として断定していないか
5. 通常の商品ページURLが設定されているか
6. アフィリエイトURLが設定されているか
7. メリットとデメリットが公平に説明されているか
8. 購入判断に必要な情報があるか
9. 読者に自然な購入導線があるか
10. 読みやすさ・構成・文章の自然さ

【厳守事項】

・商品情報に記載されていない性能や仕様は未確認扱い。
・商品情報にない機能を推測で補わない。
・未確認の価格、口コミ、評価、販売実績を事実として書かない。
・外部サイトを確認したと装わない。
・商品を実際に使用したような体験談を作らない。
・「髪が傷まない」「必ず効果がある」などの断定を厳しく評価する。
・「人気」「高評価」「話題」なども根拠がなければ問題として扱う。
・商品情報が不足している場合は、点数を高くしすぎない。
・商品ページURLとアフィリエイトURLを区別する。
・アフィリエイト記事で広告表記がない場合は指摘する。

【点数の基準】

90～100点：
事実確認が十分で、重大な問題がなく公開可能。

80～89点：
軽微な修正で公開できる。

60～79点：
情報不足、未確認の断定などがあり、修正が必要。

40～59点：
重大な問題が複数あり、再構成・修正が必要。

0～39点：
捏造、誤情報、重大な欠陥が多く公開非推奨。

未確認の機能・性能を断定している場合、
文章が読みやすくても高得点を与えないでください。
"""

    return """
【一般記事の評価基準】

以下の項目を評価してください。

1. 情報の正確性
2. 読者にとって役立つ内容か
3. 説明に具体性があるか
4. 論理的で分かりやすい構成か
5. タイトルと本文の内容が一致しているか
6. 見出しや文章の読みやすさ
7. 根拠のない断定や誇張がないか
8. 読者が実際に行動できる情報があるか

一般記事には商品紹介や販売目的の基準を適用しないでください。
商品情報がないこと、商品URLがないこと、
購入誘導がないことを減点しないでください。

記事のテーマに必要な情報が不足している場合は指摘してください。
外部サイトを確認したと装わないでください。
"""


# ==========================================
# 品質チェック
# ==========================================

def check_article_quality(
    title,
    body,
    selected_item=None,
    article_type="一般記事"
):
    """
    グミが記事を評価する。

    AIによる評価に加え、未確認情報を
    Python側で簡易検出する。
    """

    client = get_gemini_client()

    product_info = format_product_info(selected_item)

    local_claims = detect_unverified_claims(
        body,
        selected_item,
        article_type
    )

    product_verified = is_product_verified(selected_item)

    if article_type == "アフィリエイト記事":
        verification_status = (
            "確認済み"
            if product_verified
            else "未確認・情報不足"
        )
    else:
        verification_status = "一般記事のため対象外"

    evaluation_rules = get_evaluation_rules(article_type)

    prompt = f"""
あなたはAI Affiliate Officeの品質担当「グミ」です。

記事の種類に合わせて公平かつ厳格に品質を確認してください。
文章の読みやすさだけで高得点を与えないでください。

【記事の種類】
{article_type}

【商品確認状態】
{verification_status}

【タイトル】
{title}

【本文】
{body}

【登録商品情報】
{product_info}

【Pythonによる事前検出】
{local_claims if local_claims else "特に検出なし"}

{evaluation_rules}

【共通ルール】

・記事本文にある具体的な事実を確認してください。
・商品登録情報と本文を比較してください。
・事実と意見を区別してください。
・重大な問題と軽微な問題を区別してください。
・問題がない項目も確認結果に含めてください。
・記事の種類に合わない基準を適用しないでください。
・外部サイトを確認したと装わないでください。
・確認できない情報は「未確認」と明記してください。
・検出された未確認情報は必ず指摘してください。
・未確認情報を単に「一般的にあり得る」として合格にしないでください。
・点数は実際の内容に基づいて厳格に判断してください。

【出力形式】

【総合判定】
公開推奨 / 修正後に公開推奨 / 公開非推奨

【評価】
100点満点で採点

【商品情報確認状態】
確認済み / 未確認 / 情報不足 / 一般記事のため対象外

【重大な問題】
なければ「なし」と記載。

【修正推奨箇所】
修正前 → 修正案。
なければ「なし」。

【良い点】
簡潔に記載。

【最終アドバイス】
公開前に必要な対応を具体的に記載。

回答は簡潔かつ具体的にしてください。
"""

    ai_result = generate_with_fallback(
        client,
        prompt,
        max_tokens=2200
    )

    # ======================================
    # Python側の強制警告
    # ======================================

    warnings = []

    if article_type == "アフィリエイト記事":

        if not product_verified:
            warnings.append(
                "商品情報が確認済みではありません。"
                "商品ページURL、アフィリエイトURL、"
                "ユーザー確認状態を確認してください。"
            )

        if local_claims:
            warnings.append(
                "未確認の仕様・性能に関する表現を検出しました。"
            )

            for claim in local_claims:
                warnings.append(f"・{claim}")

    # ======================================
    # AIの点数に対する上限設定
    # ======================================

    score_limit = None

    if article_type == "アフィリエイト記事":

        if not product_verified:
            score_limit = 60

        elif local_claims:
            score_limit = 75

    result = ai_result

    if warnings:

        result += """

━━━━━━━━━━━━━━━━━━━━
【Pythonによる追加検査】
━━━━━━━━━━━━━━━━━━━━

"""

        result += "\n".join(warnings)

    if score_limit is not None:

        result += f"""

【追加の採点制限】

商品情報の確認状態または未確認情報の検出により、
AIの評価点に対する上限を {score_limit} 点に設定します。

AIが高得点を付けた場合でも、
未確認情報が残っているため公開前の修正が必要です。
"""

    return result


# ==========================================
# アフィリエイトブロック保護
# ==========================================

def extract_affiliate_block(body):
    start_marker = "<!-- AFFILIATE_BLOCK_START -->"
    end_marker = "<!-- AFFILIATE_BLOCK_END -->"

    if start_marker not in body or end_marker not in body:
        return ""

    try:
        start = body.index(start_marker)
        end = body.index(end_marker) + len(end_marker)

        return body[start:end]

    except ValueError:
        return ""


# ==========================================
# 記事修正
# ==========================================

def revise_article(
    title,
    body,
    quality_result,
    selected_item=None,
    article_type="一般記事"
):
    """
    ボボが品質チェックの指摘を反映して修正する。
    未確認情報の削除・表現変更を優先する。
    """

    client = get_gemini_client()

    product_info = format_product_info(selected_item)

    affiliate_block = extract_affiliate_block(body)

    if article_type == "アフィリエイト記事":

        revision_rules = """
【アフィリエイト記事の厳格修正ルール】

・品質チェックの重大な指摘を優先して修正する。
・登録商品情報を優先する。
・商品情報にない機能や性能を追加しない。
・未確認の価格、口コミ、評価を捏造しない。
・実際に使用していない商品の体験談を作らない。
・誇張表現や根拠のない断定を削除する。
・未確認の性能は断定せず、削除するか確認を促す表現に変更する。
・「髪へのダメージを軽減」などの効果は根拠がなければ断定しない。
・「立ち上がりが早い」などの性能は根拠がなければ削除する。
・商品URLがない場合は勝手に作らない。
・商品情報が不足している場合は推測せず、購入前の確認事項として書く。
・メリットとデメリットを公平に書く。
・購入を強制する表現を使わない。
・自然で読みやすい文章にする。
・記事のテーマと有益な情報は維持する。
・不要な水増しをしない。
"""

    else:

        revision_rules = """
【一般記事の修正ルール】

・品質チェックの重大な指摘を優先して修正する。
・読者に役立つ情報を増やす。
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

品質チェック結果を反映し、
note掲載用の記事に修正してください。

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
・不明な機能や性能を推測で補わない。
・不明な情報は削除するか、確認が必要な旨を自然に記載する。
・商品を使用した体験談を捏造しない。
・記事の内容を具体的に改善する。
・修正前と同じ問題が残らないよう確認する。

【アフィリエイトリンク保護】

以下のアフィリエイトブロックが元の記事に存在する場合、
リンクURLと広告表記を変更せず、
修正後の記事にも必ず残してください。

【元のアフィリエイトブロック】
{affiliate_block if affiliate_block else "元記事にアフィリエイトブロックはありません。"}

【出力】

修正後の記事だけを出力してください。

タイトルと見出しを含め、
noteに掲載できる完成原稿にしてください。

修正理由、採点、解説は出力しないでください。
"""

    revised = generate_with_fallback(
        client,
        prompt,
        max_tokens=6000
    )

    # ======================================
    # アフィリエイトブロックの保護
    # ======================================

    if affiliate_block:

        start_marker = "<!-- AFFILIATE_BLOCK_START -->"
        end_marker = "<!-- AFFILIATE_BLOCK_END -->"

        if (
            start_marker not in revised
            or end_marker not in revised
        ):

            # AIがブロックを削除した場合、元のブロックを復元
            revised = revised.rstrip() + "\n\n" + affiliate_block

    return revised.strip()
