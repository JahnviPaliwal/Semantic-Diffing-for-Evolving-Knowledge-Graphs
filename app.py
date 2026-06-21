"""
app.py – Flask entry point for Semantic KG Diff
Run: python backend/app.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from semantic_diff import extract_entities_and_relations, compute_diff, summarise_diff
from graph_utils import build_graph, visualise_diff, graph_to_json

def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static'),
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend'),
    )
    CORS(app)

    @app.route('/')
    def index():
        return send_from_directory(app.template_folder, 'index.html')

    @app.route('/api/diff', methods=['POST'])
    def diff():
        data = request.get_json()
        v1_text  = (data or {}).get('v1', '').strip()
        v2_text  = (data or {}).get('v2', '').strip()
        api_key  = (data or {}).get('api_key', '').strip()

        if not v1_text or not v2_text:
            return jsonify({'error': 'Both v1 and v2 text are required.'}), 400
        if not api_key:
            return jsonify({'error': 'Groq API key is required.'}), 400

        try:
            kg1 = extract_entities_and_relations(v1_text, api_key)
            kg2 = extract_entities_and_relations(v2_text, api_key)
            diff_result = compute_diff(kg1, kg2)
            summary = summarise_diff(diff_result, api_key)

            g1 = build_graph(kg1)
            g2 = build_graph(kg2)
            img_b64 = visualise_diff(g1, g2, diff_result)

            return jsonify({
                'kg1': kg1,
                'kg2': kg2,
                'diff': diff_result,
                'summary': summary,
                'graph_img': img_b64,
                'graph_json': {
                    'v1': graph_to_json(g1),
                    'v2': graph_to_json(g2),
                },
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5050))
    print(f'\n🔍  Semantic KG Diff running at http://localhost:{port}\n')
    app.run(host='0.0.0.0', port=port, debug=True)
