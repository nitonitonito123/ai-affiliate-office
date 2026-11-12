
import streamlit as st
import requests


RAKUTEN_API_URL = (
    "https://openapi.rakuten.co.jp/ichibams/api/"
    "IchibaItem/Search/20260701"
)


def search_rakuten_items(keyword, hits=10, sort="-reviewCount"):
    """楽天市場の商品情報を検索する"""

    # API認証情報
    try:
        application_id = st.secrets.get(
            "RAKUTEN_APPLICATION_ID", ""
        )
        access_key = st.secrets.get(
            "RAKUTEN_ACCESS_KEY", ""
        )
        affiliate_id = st.secrets.get(
            "RAKUTEN_AFFILIATE_ID", ""
        )
    except Exception as e:
        raise RuntimeError(
            f"楽天APIのSecretsを読み込めません: {e}"
        )

    if not application_id or not access_key:
        raise RuntimeError(
            "楽天APIの認証情報が未設定です。"
            "Streamlit Secretsを確認してください。"
        )

    if not keyword or not keyword.strip():
        raise ValueError(
            "検索キーワードを入力してください。"
        )

    # 検索パラメータ
    params = {
        "applicationId": application_id,
        "accessKey": access_key,
        "keyword": keyword.strip(),
        "hits": min(max(int(hits), 1), 30),
        "sort": sort,
        "format": "json",
        "formatVersion": 2,
        "availability": 1,
        "imageFlag": 1,
    }

    if affiliate_id:
        params["affiliateId"] = affiliate_id

    # API通信
    try:
        response = requests.get(
            RAKUTEN_API_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()
        data = response.json()

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "楽天APIがタイムアウトしました。"
            "時間をおいて再試行してください。"
        )

    except requests.exceptions.HTTPError as e:
        detail = response.text[:500]
        raise RuntimeError(
            f"楽天API HTTPエラー: {e}\n{detail}"
        )

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"楽天API通信エラー: {e}"
        )

    except ValueError:
        raise RuntimeError(
            "楽天APIから正常なJSONが返されませんでした。"
        )

    # 商品一覧取得
    raw_items = data.get(
        "Items",
        data.get("items", [])
    )

    items = []

    for entry in raw_items:

        item = entry.get(
            "Item",
            entry.get("item", entry)
        )

        # 商品画像
        images = (
            item.get("mediumImageUrls")
            or item.get("itemImageUrls")
            or item.get("smallImageUrls")
            or []
        )

        image_url = ""

        if images:
            first_image = images[0]

            if isinstance(first_image, dict):
                image_url = (
                    first_image.get("imageUrl")
                    or first_image.get("imageUrl1")
                    or ""
                )

            elif isinstance(first_image, str):
                image_url = first_image

        # アフィリエイトURL
        affiliate_url = item.get(
            "affiliateUrl", ""
        )

        # 商品情報を整理
        product = {
            "name": item.get("itemName", ""),
            "price": item.get("itemPrice", 0),
            "url": item.get("itemUrl", ""),
            "affiliate_url": affiliate_url,
            "image": image_url,
            "review_average": item.get(
                "reviewAverage", 0
            ),
            "review_count": item.get(
                "reviewCount", 0
            ),
            "shop_name": item.get(
                "shopName", ""
            ),
            "item_code": item.get(
                "itemCode", ""
            ),
            "availability": item.get(
                "availability", 0
            ),
            "catchcopy": item.get(
                "catchcopy", ""
            ),
            "caption": item.get(
                "itemCaption", ""
            ),
        }

        items.append(product)

    return items
