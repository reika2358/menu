# 📸 写真で献立提案システム

冷蔵庫の写真を撮るだけで、AIが献立を提案してくれる無料システムです。

## ✨ 機能

- 📷 写真をアップロード（ドラッグ&ドロップ対応）
- 🤖 Gemini API（無料枠）で食材を認識
- 🍽️ 写真の食材を使った献立を自動提案
- 💰 完全無料で利用可能（Gemini APIの無料枠内）

## 🚀 セットアップ手順

### 1. Gemini APIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. APIキーをコピー

### 2. プロジェクトのセットアップ

```bash
# 必要なパッケージをインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`を`.env`にコピーして、APIキーを設定：

```bash
cp .env.example .env
```

`.env`ファイルを開いて、取得したAPIキーを設定：

```
GEMINI_API_KEY=あなたのAPIキー
```

または、環境変数として直接設定：

```bash
export GEMINI_API_KEY=あなたのAPIキー
```

### 4. アプリケーションの起動

```bash
python app.py
```

ブラウザで `http://localhost:5000` にアクセス

## 📝 使い方

1. 冷蔵庫や食材の写真を撮る
2. ブラウザで写真をアップロード（ドラッグ&ドロップも可）
3. 「献立を生成する」ボタンをクリック
4. AIが提案する献立を確認！

## 💡 技術スタック

- **バックエンド**: Python Flask
- **AI**: Google Gemini API (gemini-flash-latest - 無料枠)
- **フロントエンド**: HTML, CSS, JavaScript
- **デプロイ**: Render / Railway (無料枠あり)

## 🚀 本番環境向けの改善点

- ✅ **エラーハンドリング**: 詳細なエラーメッセージとログ機能
- ✅ **画像最適化**: 自動リサイズでメモリ使用量を削減
- ✅ **セキュリティ**: ファイル形式とサイズの検証
- ✅ **パフォーマンス**: 画像処理の最適化
- ✅ **ログ機能**: 問題の追跡とデバッグが容易

## 📊 Gemini APIの無料枠について

- Gemini Flashモデルは無料枠で利用可能
- 1日あたりのリクエスト数に制限がありますが、個人利用には十分
- 詳細は[Gemini API Pricing](https://ai.google.dev/pricing)を確認

## ⚠️ 注意事項

- APIキーは他人に公開しないでください
- `.env`ファイルは`.gitignore`に追加することを推奨
- 大量のリクエストを送ると無料枠を超える可能性があります

## 🐛 トラブルシューティング

### APIキーが設定されていないエラー

環境変数`GEMINI_API_KEY`が正しく設定されているか確認してください。

### 画像がアップロードできない

- ファイルサイズが16MB以下か確認
- 対応形式（PNG, JPG, JPEG, GIF, WEBP）か確認

## 🌐 インターネットで公開する方法（他の人も使えるようにする）

### 方法1: Render（無料枠あり）でデプロイ

1. **GitHubにプッシュ**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <あなたのGitHubリポジトリURL>
   git push -u origin main
   ```

2. **Renderでアプリを作成**
   - [Render](https://render.com) にアクセスしてアカウント作成
   - 「New +」→「Web Service」を選択
   - GitHubリポジトリを接続
   - 以下の設定を行う：
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Environment Variables**:
       - `GEMINI_API_KEY`: あなたのAPIキー
       - `FLASK_ENV`: `production`

3. **デプロイ完了**
   - Renderが自動的にデプロイします
   - 完了後、`https://your-app-name.onrender.com` でアクセス可能

### 方法2: ngrok（一時的な共有に便利）

```bash
# ngrokをインストール
brew install ngrok  # Macの場合

# アプリを起動
python app.py

# 別のターミナルでngrokを起動
ngrok http 8080
```

ngrokが生成したURL（例：`https://xxxx.ngrok.io`）を他の人に共有できます。

### 方法3: Railway（無料枠あり）

1. [Railway](https://railway.app) にアクセス
2. 「New Project」→「Deploy from GitHub repo」
3. リポジトリを選択
4. 環境変数 `GEMINI_API_KEY` を設定
5. 自動デプロイ完了

## 📄 ライセンス

MIT License
