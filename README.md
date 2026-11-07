# AI Affiliate Office

スマートフォンからも利用できる、AIアフィリエイト運営オフィスの開発用MVPです。

## 起動方法

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 現在できること
- 6体のスタッフと担当業務の表示
- タスクの登録・SQLite保存
- 記事・タスク管理の基盤

## まだ接続していない機能
- 楽天商品検索API
- AIによる商品調査・記事生成
- noteへの投稿連携
- アフィリエイト成果・報酬データ連携

## 開発上の注意
noteへの投稿は、利用可能な公式連携方法・契約条件を確認してから実装します。
初期版ではnote向け原稿を生成し、内容を人が確認して公開する方式です。
楽天の商品情報・画像・リンクは、楽天ウェブサービスおよび楽天アフィリエイトの最新利用条件に従って扱います。
