#!/usr/bin/env python3
"""
Simple Jerry Status Server using only built-in Python modules
"""

import http.server
import socketserver
import urllib.request
import urllib.error
from datetime import datetime


class JerryStatusServer:
    def check_chromadb(self):
        """Check if ChromaDB is responding"""
        try:
            # Try v2 API first (current), fallback to v1 if needed
            endpoints = [
                'http://localhost:8000/api/v1/heartbeat',  # Keep for compatibility
                'http://localhost:8000/',  # Basic health check
            ]
            
            for endpoint in endpoints:
                try:
                    req = urllib.request.Request(endpoint)
                    with urllib.request.urlopen(req, timeout=2) as response:
                        if response.getcode() == 200:
                            return {'status': 'running', 'details': f'ChromaDB responding at {endpoint}'}on
import urllib.request
import urllib.error
from datetime import datetime
import threading
import socket

# Simple HTML page
HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <title>Jerry AI - Production Status</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #2c3e50; margin-bottom: 30px; }
        .service { margin: 15px 0; padding: 15px; border-radius: 5px; border-left: 4px solid; }
        .service.running { background: #d4edda; border-color: #28a745; }
        .service.failed { background: #f8d7da; border-color: #dc3545; }
        .service.unknown { background: #fff3cd; border-color: #ffc107; }
        .service-name { font-weight: bold; font-size: 1.1em; }
        .service-status { margin-top: 5px; }
        .timestamp { text-align: center; color: #6c757d; margin-top: 30px; }
        .jerry-info { background: #e3f2fd; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .refresh-btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 20px 0; }
        .refresh-btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Jerry AI - Production Status</h1>
            <p>Australian Energy Advisor Assistant</p>
        </div>
        
        <div class="jerry-info">
            <h3>About Jerry</h3>
            <p>Jerry is a grandfatherly Australian energy advisor with deep expertise in Australian energy standards and regulations. He provides practical, actionable advice for renewable energy and smart home automation.</p>
            <p><strong>Current Status:</strong> Infrastructure deployment in progress</p>
        </div>
        
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Status</button>
        
        <h2>Service Status</h2>
        
        <div class="service running">
            <div class="service-name">📊 ChromaDB Vector Database</div>
            <div class="service-status">Port: 8000</div>
            <div class="service-status">✅ Container running successfully</div>
            <div class="service-status">Status: Ready for vector operations</div>
        </div>
        
        <div class="service failed">
            <div class="service-name">🧠 Model Service</div>
            <div class="service-status">Port: 8001 - Local LLM inference</div>
            <div class="service-status">❌ Requires build tools (gcc, cmake) for llama-cpp-python</div>
            <div class="service-status">Note: Running on immutable bootc system</div>
        </div>
        
        <div class="service failed">
            <div class="service-name">🔍 RAG Service</div>
            <div class="service-status">Port: 8002 - Vector search and retrieval</div>
            <div class="service-status">❌ Depends on Model Service</div>
        </div>
        
        <div class="service failed">
            <div class="service-name">🤖 Agent Service</div>
            <div class="service-status">Port: 8003 - LangChain conversation agent</div>
            <div class="service-status">❌ Depends on Model Service</div>
        </div>
        
        <div class="service failed">
            <div class="service-name">💬 Web Chat Interface</div>
            <div class="service-status">Port: 8004 - User interface</div>
            <div class="service-status">❌ Depends on Agent Service</div>
        </div>
        
        <div class="timestamp">Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</div>
        
        <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
            <h4>Deployment Progress:</h4>
            <ul>
                <li>✅ Podman container runtime configured</li>
                <li>✅ ChromaDB vector database deployed and running</li>
                <li>✅ Project dependencies identified</li>
                <li>❌ Model service requires compilation tools</li>
                <li>❌ Full service stack pending model service</li>
            </ul>
            <h4>Alternative Deployment Options:</h4>
            <ol>
                <li><strong>Container-based:</strong> Use pre-built containers with compiled dependencies</li>
                <li><strong>External Model:</strong> Connect to external API (OpenAI, etc.) instead of local model</li>
                <li><strong>Toolbox Environment:</strong> Use Fedora toolbox with build tools</li>
            </ol>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: #d1ecf1; border-radius: 5px;">
            <h4>🚀 Currently Running Services:</h4>
            <p><strong>ChromaDB:</strong> <a href="http://localhost:8000" target="_blank">http://localhost:8000</a></p>
            <p><strong>This Dashboard:</strong> <a href="http://localhost:8080" target="_blank">http://localhost:8080</a></p>
        </div>
    </div>
</body>
</html>"""

class SimpleStatusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Check ChromaDB status
            chromadb_status = self.check_chromadb()
            
            status = {
                'chromadb': chromadb_status,
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(status, indent=2).encode())
        else:
            self.send_error(404)
    
    def check_chromadb(self):
        """Check if ChromaDB is responding"""
        try:
            req = urllib.request.Request('http://localhost:8000/api/v1/heartbeat')
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return {'status': 'running', 'details': 'ChromaDB responding normally'}
                else:
                    return {'status': 'failed', 'details': f'HTTP {response.status}'}
        except urllib.error.URLError:
                    continue  # Try next endpoint
            
            return {'status': 'failed', 'details': 'ChromaDB not responding to any endpoints'}
        except Exception as e:
            return {'status': 'failed', 'details': f'ChromaDB check failed: {str(e)}'}
        except Exception as e:
            return {'status': 'failed', 'details': f'Error: {e}'}

def check_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except socket.error:
            return False

if __name__ == "__main__":
    PORT = 8080
    
    # Check if port is available
    if not check_port_available(PORT):
        print(f"Port {PORT} is already in use. Trying port 8081...")
        PORT = 8081
        if not check_port_available(PORT):
            print(f"Port {PORT} is also in use. Exiting.")
            exit(1)
    
    print("Starting Jerry Production Status Dashboard...")
    print(f"Dashboard available at: http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    
    try:
        with socketserver.TCPServer(("", PORT), SimpleStatusHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")