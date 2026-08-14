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
            return jsonify({'success': False, 'error': 'يرجى تقديم رابط فيديو صالح.'}), 200

        url = str(data['url']).strip()
        result = extract_info(url)
        return jsonify(result), 200

    except Exception as e:
        # إرجاع الخطأ بتنسيق JSON واضح دون تحطيم السيرفر بـ 500
        return jsonify({'success': False, 'error': str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)