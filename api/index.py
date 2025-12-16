from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re

app = Flask(__name__)
CORS(app)  # 允许跨域请求

def get_video_id(url_or_id):
    """从 URL 中提取 Video ID"""
    if len(url_or_id) == 11 and not '/' in url_or_id:
        return url_or_id
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id # 提取失败则原样返回尝试

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # 获取参数
    url = request.args.get('url') or request.args.get('video_id')
    lang = request.args.get('lang', 'zh') # 默认中文

    if not url:
        return jsonify({"error": "Please provide 'url' parameter"}), 400

    video_id = get_video_id(url)

    try:
        # 尝试获取字幕 (优先指定语言，其次中文，其次英文)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, 'zh-Hans', 'zh-Hant', 'en'])
        
        # 拼接全文
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            "video_id": video_id,
            "transcript_text": full_text,
            "transcript_json": transcript_list
        })

    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video"}), 404
    except NoTranscriptFound:
        return jsonify({"error": "No transcript found for this video"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Vercel 需要导出 app 作为 handler
# 对于 @vercel/python，直接导出 Flask app 即可