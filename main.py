import os
from flask import Flask, render_template, request, jsonify
from downloader import extract_info

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(silent=True)
        if not data or 'url' not in data or not str(data['url']).strip():
            return jsonify({'success': False, 'error': 'يرجى تقديم رابط فيديو صالح.'}), 400

        url = str(data['url']).strip()
        result = extract_info(url)
        return jsonify(result)

    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except RuntimeError as re:
        return jsonify({'success': False, 'error': str(re)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f"عذراً، حدث خطأ أثناء معالجة الطلب: {str(e)}"}), 500

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'حدث خطأ داخلي في السيرفر. يرجى المحاولة لاحقاً.'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'success': False, 'error': 'الصفحة المطلوبة غير موجودة.'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)