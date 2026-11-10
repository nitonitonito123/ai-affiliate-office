
import streamlit as st
from google import genai


def create_research_plan(keyword, category, budget, conditions=""):
    """クルミが商品リサーチの調査計画を作成する"""

    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )

    prompt = f"""
あなたはAI Affiliate Officeの
商品リサーチ担当「クルミ」です。

次の商品について、アフィリエイト向けの
商品リサーチ計画を作成してください。

【検索キーワード】
{keyword}

【商品ジャンル】
{category}

【想定予算】
{budget}円

【ユーザーの条件】
{conditions}

次の項目を日本語で整理してください。

1. 想定する購入者
2. 購入者が抱えている悩み
3. 商品を選ぶ際の重要な比較基準
4. 調査すべき商品候補の特徴
5. 価格帯の調査方針
6. 口コミ・評価で確認すべき点
7. note記事に向いている切り口
8. 楽天市場で使用する検索キーワード5個

【重要】
・実際に確認していない商品名、価格、売上、
  口コミ件数、評価を捏造しないこと。
・確認できない情報は「未確認」と記載すること。
・今回は調査計画の作成であり、
  実在商品の検索結果ではありません。
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        return response.text

    except Exception:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        return response.text
