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
import gc  # ガベージコレクション用

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
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max（メモリ節約のため）
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # キャッシュ無効化

# アップロードフォルダを作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 画像の最大サイズ（ピクセル）- メモリ節約のため小さく設定
MAX_IMAGE_SIZE = (400, 400)  # 無料プランのメモリ制限（512MB）に対応 - 最小サイズ

# Gemini APIの設定
# 環境変数からAPIキーを取得（.envファイルから読み込むことも可能）
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()

# APIキーの検証
if GEMINI_API_KEY:
    # APIキーの形式をチェック（AIzaで始まる必要がある）
    if not GEMINI_API_KEY.startswith('AIza'):
        logger.error(f"APIキーの形式が正しくありません。AIzaで始まる必要があります。")
        model = None
    elif len(GEMINI_API_KEY) < 30:
        logger.error(f"APIキーの長さが短すぎます。")
        model = None
    else:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # 無料枠で使えるFlashモデル（利用可能なモデル名に変更）
            model = genai.GenerativeModel('gemini-flash-latest')
            logger.info("Gemini APIが正常に設定されました")
        except ValueError as e:
            model = None
            logger.error(f"Gemini APIの設定に失敗しました（値エラー）: {str(e)}")
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
            # アスペクト比を保ちながらリサイズ
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.info(f"画像をリサイズしました: {width}x{height} -> {image.size[0]}x{image.size[1]}")
        
        # メモリを節約するため、新しい画像オブジェクトを作成
        # RGB形式に変換（メモリ効率が良い）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
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
        
        # 画像を読み込む（メモリ効率を最適化）
        try:
            image_data = file.read()
            if len(image_data) == 0:
                return jsonify({'error': '画像ファイルが空です'}), 400
            
            # メモリ効率のため、一度だけ読み込む
            image = Image.open(io.BytesIO(image_data))
            # RGB形式に変換（メモリ効率が良い）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 画像を最適化（リサイズ）
            image = optimize_image(image)
            
            # 元のデータをメモリから削除
            del image_data
            
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
            logger.info(f"APIキーの先頭: {GEMINI_API_KEY[:10]}...")  # デバッグ用（先頭10文字のみ）
            
            # 画像サイズをログに記録
            logger.info(f"送信する画像サイズ: {image.size[0]}x{image.size[1]}")
            
            # Gemini APIにリクエスト送信
            # メモリ効率を最適化するため、画像を小さなJPEGバイト形式に変換
            img_buffer = None
            try:
                # 画像をJPEG形式に変換（品質を下げてメモリ使用量を最小化）
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='JPEG', quality=65, optimize=True)
                img_data = img_buffer.getvalue()
                img_buffer.close()
                img_buffer = None
                
                # データサイズを確認
                data_size_kb = len(img_data) / 1024
                logger.info(f"送信する画像データサイズ: {data_size_kb:.1f}KB")
                
                # メモリを節約するため、画像オブジェクトを削除
                del image
                
                # Gemini APIに送信
                response = model.generate_content([
                    prompt,
                    {
                        "mime_type": "image/jpeg",
                        "data": img_data
                    }
                ])
                
                # データを削除
                del img_data
                
            except Exception as api_error:
                # エラーが発生した場合
                if img_buffer:
                    img_buffer.close()
                error_msg = str(api_error)
                logger.error(f"Gemini API呼び出しエラー: {error_msg}")
                raise  # エラーを再発生させて上位のハンドラーで処理
            
            # レスポンスの検証
            if not response:
                logger.error("Gemini APIからの応答がNoneです")
                return jsonify({'error': '献立の生成に失敗しました。もう一度お試しください。'}), 500
            
            # テキストを安全に取得
            menu_text = None
            try:
                # まず通常の方法で取得を試みる
                menu_text = response.text
            except AttributeError:
                # response.textが存在しない場合、partsから取得を試みる
                try:
                    if hasattr(response, 'parts') and response.parts:
                        menu_text = ''.join([part.text for part in response.parts if hasattr(part, 'text')])
                    elif hasattr(response, 'candidates') and response.candidates:
                        # candidatesから取得を試みる
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            menu_text = ''.join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                    else:
                        menu_text = str(response)
                except Exception as e:
                    logger.error(f"レスポンスからテキストを取得できませんでした: {str(e)}")
                    logger.error(f"レスポンスオブジェクト: {type(response)}")
                    return jsonify({'error': '献立の生成に失敗しました。もう一度お試しください。'}), 500
            
            if not menu_text or len(menu_text.strip()) == 0:
                logger.error("Gemini APIからの応答テキストが空です")
                logger.error(f"レスポンスオブジェクト: {response}")
                return jsonify({'error': '献立の生成に失敗しました。もう一度お試しください。'}), 500
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"献立生成が完了しました。処理時間: {elapsed_time:.2f}秒")
            
            # メモリを明示的に解放
            gc.collect()
            
            return jsonify({
                'success': True,
                'menu': menu_text
            })
        except ValueError as e:
            # APIキーの形式エラーなど
            error_msg = str(e)
            logger.error(f"Gemini API呼び出しエラー（値エラー）: {error_msg}\n{traceback.format_exc()}")
            if "pattern" in error_msg.lower() or "string" in error_msg.lower() or "match" in error_msg.lower():
                return jsonify({'error': 'APIキーの形式が正しくありません。Renderの環境変数を確認してください。'}), 500
            return jsonify({'error': 'AIによる献立生成中にエラーが発生しました。しばらく時間をおいてから再度お試しください。'}), 500
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini API呼び出しエラー: {error_msg}\n{traceback.format_exc()}")
            # より詳細なエラーメッセージを返す
            if "API key" in error_msg or "authentication" in error_msg.lower():
                return jsonify({'error': 'APIキーが無効です。環境変数を確認してください。'}), 500
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                return jsonify({'error': 'APIの利用制限に達しました。しばらく時間をおいてから再度お試しください。'}), 500
            else:
                return jsonify({'error': f'AIによる献立生成中にエラーが発生しました: {error_msg[:100]}'}), 500
    
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
