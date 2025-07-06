#!/usr/bin/env python3
"""
Simple test endpoint for debugging Vercel deployment
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "Pookie B News Daily - MCP Test",
        "version": "1.0.0"
    })

@app.route('/api/test')
def test():
    return jsonify({
        "status": "success",
        "test": "endpoint working"
    })

if __name__ == '__main__':
    app.run(debug=True)
