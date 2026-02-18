from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
from werkzeug.utils import secure_filename
import base64
import io
from PIL import Image
from dotenv import load_dotenv
import logging
from datetime import datetime
import traceback

# .envファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# アップロード設定
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max（最適化のため）
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # キャッシュ無効化

# アップロードフォルダを作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 画像の最大サイズ（ピクセル）
MAX_IMAGE_SIZE = (2048, 2048)  # メモリ節約のため

# Gemini APIの設定
# 環境変数からAPIキーを取得（.envファイルから読み込むことも可能）
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # 無料枠で使えるFlashモデル（利用可能なモデル名に変更）
        model = genai.GenerativeModel('gemini-flash-latest')
        logger.info("Gemini APIが正常に設定されました")
    except Exception as e:
        model = None
        logger.error(f"Gemini APIの設定に失敗しました: {str(e)}")
else:
    model = None
    logger.warning("GEMINI_API_KEYが設定されていません。環境変数を設定してください。")


def allowed_file(filename):
    """ファイル拡張子が許可されているかチェック"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def optimize_image(image, max_size=MAX_IMAGE_SIZE):
    """画像を最適化（リサイズ）してメモリ使用量を削減"""
    try:
        # 画像サイズを取得
        width, height = image.size
        
        # 最大サイズを超えている場合はリサイズ
        if width > max_size[0] or height > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.info(f"画像をリサイズしました: {width}x{height} -> {image.size[0]}x{image.size[1]}")
        
        return image
    except Exception as e:
        logger.error(f"画像の最適化に失敗しました: {str(e)}")
        return image  # エラー時は元の画像を返す


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/generate-menu', methods=['POST'])
def generate_menu():
    """写真から献立を生成するAPI"""
    start_time = datetime.now()
    
    if not model:
        logger.error("Gemini APIキーが設定されていません")
        return jsonify({'error': 'サービスが利用できません。管理者にお問い合わせください。'}), 503
    
    try:
        # 画像データを取得
        if 'image' not in request.files:
            logger.warning("画像がアップロードされていません")
            return jsonify({'error': '画像がアップロードされていません'}), 400
        
        file = request.files['image']
        if file.filename == '':
            logger.warning("ファイル名が空です")
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"許可されていないファイル形式: {file.filename}")
            return jsonify({'error': '許可されていないファイル形式です。PNG, JPG, JPEG, GIF, WEBP形式のみ対応しています。'}), 400
        
        # 画像を読み込む
        try:
            image_data = file.read()
            if len(image_data) == 0:
                return jsonify({'error': '画像ファイルが空です'}), 400
            
            image = Image.open(io.BytesIO(image_data))
            # RGB形式に変換（一部の画像形式に対応）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 画像を最適化
            image = optimize_image(image)
            
            logger.info(f"画像を読み込みました: {file.filename}, サイズ: {image.size}")
        except Exception as e:
            logger.error(f"画像の読み込みに失敗しました: {str(e)}")
            return jsonify({'error': '画像の読み込みに失敗しました。有効な画像ファイルをアップロードしてください。'}), 400
        
        # プロンプトを作成
        prompt = """この写真に写っている食材を分析して、それを使った献立を提案してください。

以下の形式で回答してください：

【認識した食材】
- 食材1
- 食材2
- ...

【提案する献立】
1. メイン料理: [料理名]
   - 材料: [必要な材料]
   - 簡単な作り方: [簡潔な説明]

2. 副菜: [料理名]
   - 材料: [必要な材料]
   - 簡単な作り方: [簡潔な説明]

3. 汁物: [料理名]
   - 材料: [必要な材料]
   - 簡単な作り方: [簡潔な説明]

【ポイント】
- 写真に写っている食材を最大限活用すること
- 栄養バランスを考慮すること
- 簡単に作れるレシピを優先すること

日本語で回答してください。"""
        
        # Gemini APIで画像分析と献立生成
        try:
            logger.info("Gemini APIにリクエストを送信しています...")
            response = model.generate_content([prompt, image])
            
            if not response or not response.text:
                logger.error("Gemini APIからの応答が空です")
                return jsonify({'error': '献立の生成に失敗しました。もう一度お試しください。'}), 500
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"献立生成が完了しました。処理時間: {elapsed_time:.2f}秒")
            
            return jsonify({
                'success': True,
                'menu': response.text
            })
        except Exception as e:
            logger.error(f"Gemini API呼び出しエラー: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'AIによる献立生成中にエラーが発生しました。しばらく時間をおいてから再度お試しください。'}), 500
    
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'システムエラーが発生しました。しばらく時間をおいてから再度お試しください。'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """APIの状態を確認"""
    return jsonify({
        'status': 'ok',
        'gemini_configured': model is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    """ファイルサイズが大きすぎる場合のエラーハンドラー"""
    logger.warning("ファイルサイズが大きすぎます")
    return jsonify({'error': 'ファイルサイズが大きすぎます。10MB以下の画像をアップロードしてください。'}), 413


@app.errorhandler(500)
def internal_error(error):
    """内部エラーのハンドラー"""
    logger.error(f"内部エラー: {str(error)}")
    return jsonify({'error': 'サーバーエラーが発生しました。しばらく時間をおいてから再度お試しください。'}), 500


if __name__ == '__main__':
    # 本番環境では環境変数PORTを使用、開発環境では8080を使用
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"アプリケーションを起動します。ポート: {port}, デバッグモード: {debug}")
    app.run(debug=debug, host='0.0.0.0', port=port)
