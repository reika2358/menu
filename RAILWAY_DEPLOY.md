# 🚂 Railwayでデプロイする方法

Renderの無料プランはメモリ制限（512MB）が厳しいため、Railwayに移行することをおすすめします。

## Railwayのメリット

- ✅ 無料枠あり（500時間/月）
- ✅ メモリ制限が緩い（より多くのメモリが使える）
- ✅ スリープしない（常時起動可能）
- ✅ デプロイが簡単

## デプロイ手順

### ステップ1: Railwayにアカウント作成

1. [Railway](https://railway.app) にアクセス
2. 「Start a New Project」をクリック
3. 「Login with GitHub」を選択
4. GitHubアカウントでログイン

### ステップ2: プロジェクトを作成

1. 「New Project」をクリック
2. 「Deploy from GitHub repo」を選択
3. `reika2358/menu` リポジトリを選択

### ステップ3: 環境変数を設定

1. プロジェクトの「Variables」タブを開く
2. 「New Variable」をクリック
3. 以下を追加：
   - **Key**: `GEMINI_API_KEY`
   - **Value**: `AIzaSyAhp75yudkjf-jtILgQ2ReQSRMC0e2-MfE`
4. 「Add」をクリック

### ステップ4: デプロイ設定

Railwayは自動的に以下を検出します：
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

もし自動検出されない場合：
1. 「Settings」タブを開く
2. 「Build Command」に `pip install -r requirements.txt` を設定
3. 「Start Command」に `gunicorn app:app` を設定

### ステップ5: デプロイ完了

- Railwayが自動的にデプロイを開始します
- 数分待つと完了します
- 完了後、`https://your-app-name.up.railway.app` のようなURLが表示されます

## デプロイ後の確認

1. 表示されたURLにアクセス
2. 写真をアップロード
3. 献立が生成されるか確認

## トラブルシューティング

### デプロイが失敗する場合

- 「Logs」タブでエラーログを確認
- 環境変数が正しく設定されているか確認

### メモリ不足エラーが出る場合

- Railwayの無料プランでもメモリ制限がありますが、Renderより緩いです
- それでもエラーが出る場合は、画像サイズをさらに小さくする必要があります
