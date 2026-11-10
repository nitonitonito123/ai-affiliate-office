
import streamlit as st
import requests


RAKUTEN_API_URL = (
    "https://openapi.rakuten.co.jp/ichibams/api/"
    "IchibaItem/Search/20260701"
)


def search_rakuten_items(keyword, hits=10, sort="-reviewCount"):
    """楽天市場の商品情報を検索する"""

    application_id = st.secrets.get("RAKUTEN_APPLICATION_ID", "")
    access_key = st.secrets.get("RAKUTEN_ACCESS_KEY", "")
    affiliate_id = st.secrets.get("RAKUTEN_AFFILIATE_ID", "")

    if not application_id or not access_key:
        raise RuntimeError(
            "楽天APIの認証情報が未設定です。"
            "楽天APIの利用準備が完了してから設定してください。"
        )

    if not keyword or not keyword.strip():
        raise ValueError("検索キーワードを入力してください。")

    params = {
        "applicationId": application_id,
        "accessKey": access_key,
        "keyword": keyword.strip(),
        "hits": min(max(int(hits), 1), 30),
        "sort": sort,
        "format": "json",
        "formatVersion": 2,
    }

    if affiliate_id:
        params["affiliateId"] = affiliate_id

    response = requests.get(
        RAKUTEN_API_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    raw_items = data.get("Items", data.get("items", []))
    items = []

    for entry in raw_items:
        item = entry.get("Item", entry.get("item", entry))

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

        items.append({
            "name": item.get("itemName", ""),
            "price": item.get("itemPrice", 0),
            "url": item.get("itemUrl", ""),
            "affiliate_url": item.get("affiliateUrl", ""),
            "image": image_url,
            "review_average": item.get("reviewAverage", 0),
            "review_count": item.get("reviewCount", 0),
            "shop_name": item.get("shopName", ""),
        })

    return items
