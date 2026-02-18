# 🚀 恒久的に公開する方法（PCを閉じても使える）

## Renderでデプロイする手順

### ステップ1: GitHubにプッシュ

1. **GitHubでリポジトリを作成**
   - [GitHub](https://github.com) にアクセス
   - 「New repository」をクリック
   - リポジトリ名を入力（例：`menu-suggestion-system`）
   - 「Create repository」をクリック

2. **ローカルでGitを初期化**
   ```bash
   cd "/Users/apple/Desktop/献立無料システム"
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
   git push -u origin main
   ```

### ステップ2: Renderでデプロイ

1. **Renderにアカウント作成**
   - [Render](https://render.com) にアクセス
   - 「Get Started for Free」をクリック
   - GitHubアカウントでログイン

2. **新しいWebサービスを作成**
   - 「New +」→「Web Service」を選択
   - GitHubリポジトリを選択
   - 以下の設定を入力：
     - **Name**: `menu-suggestion-system`（好きな名前）
     - **Region**: `Singapore`（日本に近い）
     - **Branch**: `main`
     - **Root Directory**: （空白のまま）
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`

3. **環境変数を設定**
   - 「Environment」タブを開く
   - 「Add Environment Variable」をクリック
   - 以下を追加：
     - **Key**: `GEMINI_API_KEY`
     - **Value**: あなたのGemini APIキー
   - 「Save Changes」をクリック

4. **デプロイ開始**
   - 「Create Web Service」をクリック
   - 数分待つとデプロイが完了します
   - 完了後、`https://your-app-name.onrender.com` でアクセス可能

### ステップ3: 確認

- デプロイが完了したら、表示されたURLにアクセス
- 写真をアップロードして動作確認

## ⚠️ 注意事項

- Renderの無料枠は15分間アクセスがないとスリープします
- 初回アクセス時に少し時間がかかることがあります
- 無料枠でも十分に使えますが、使用量が多い場合は有料プランが必要になる場合があります

## 🔄 更新方法

コードを変更したら：

```bash
git add .
git commit -m "Update"
git push
```

Renderが自動的に再デプロイします。
