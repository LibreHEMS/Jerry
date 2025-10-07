"""
Web Chat Server for Jerry AI Assistant.

This module provides a web-based chat interface with authentication
and authorization, designed to work with Cloudflare Tunnel.
"""

import json
import logging
import uuid
from datetime import datetime

import httpx
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from pydantic import Field

from ..utils.auth import TokenManager
from ..utils.auth import UserSession
from ..utils.config import Config
from ..utils.config import load_config
from ..utils.health import health_check
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Chat message model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response: str | None = None
    response_timestamp: datetime | None = None


class ChatSession(BaseModel):
    """Chat session model."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    messages: list[ChatMessage] = Field(default_factory=list)


class ConnectionManager:
    """WebSocket connection manager for real-time chat."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_sessions: dict[str, str] = {}  # user_id -> session_id

    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        """Connect a WebSocket client."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.user_sessions[user_id] = session_id
        logger.info(f"User {user_id} connected to session {session_id}")

    def disconnect(self, session_id: str, user_id: str):
        """Disconnect a WebSocket client."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        logger.info(f"User {user_id} disconnected from session {session_id}")

    async def send_personal_message(self, message: str, session_id: str):
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections.values():
            await connection.send_text(message)


class WebChatServer:
    """Web Chat Server for Jerry AI Assistant."""

    def __init__(self, config: Config):
        """Initialize the web chat server."""
        self.config = config
        self.app = FastAPI(
            title="Jerry AI Web Chat",
            description="Secure web chat interface for Jerry AI Assistant",
            version="1.0.0",
            docs_url="/docs" if config.environment != "production" else None,
            redoc_url="/redoc" if config.environment != "production" else None,
        )

        # Security middleware
        self.app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=config.web_chat.allowed_hosts or ["*"]
        )

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=config.web_chat.cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )

        # Initialize components
        self.token_manager = TokenManager(config)
        self.connection_manager = ConnectionManager()
        self.chat_sessions: dict[str, ChatSession] = {}
        self.security = HTTPBearer()

        # Agent service client
        self.agent_service_url = config.agent_service_url
        self.http_client = httpx.AsyncClient(timeout=30.0)

        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def chat_interface():
            """Serve the main chat interface."""
            return self._get_chat_html()

        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return await health_check()

        @self.app.post("/auth/login")
        async def login(request: Request):
            """Handle authentication via Cloudflare Access headers."""
            # Extract user info from Cloudflare Access headers
            cf_access_email = request.headers.get("cf-access-authenticated-user-email")
            cf_access_user = request.headers.get("cf-access-authenticated-user")

            if not cf_access_email:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Create user session
            user_session = UserSession(
                user_id=cf_access_user or cf_access_email,
                email=cf_access_email,
                authenticated_at=datetime.utcnow(),
            )

            # Generate JWT token
            token = self.token_manager.create_token(user_session)

            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {"id": user_session.user_id, "email": user_session.email},
            }

        @self.app.get("/auth/user")
        async def get_current_user(
            user_session: UserSession = Depends(self._get_current_user),
        ):
            """Get current authenticated user."""
            return {
                "id": user_session.user_id,
                "email": user_session.email,
                "authenticated_at": user_session.authenticated_at,
            }

        @self.app.post("/chat/session")
        async def create_chat_session(
            user_session: UserSession = Depends(self._get_current_user),
        ):
            """Create a new chat session."""
            session = ChatSession(user_id=user_session.user_id)
            self.chat_sessions[session.session_id] = session

            return {"session_id": session.session_id, "created_at": session.created_at}

        @self.app.get("/chat/session/{session_id}")
        async def get_chat_session(
            session_id: str, user_session: UserSession = Depends(self._get_current_user)
        ):
            """Get chat session details."""
            if session_id not in self.chat_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.chat_sessions[session_id]
            if session.user_id != user_session.user_id:
                raise HTTPException(status_code=403, detail="Access denied")

            return session

        @self.app.post("/chat/session/{session_id}/message")
        async def send_message(
            session_id: str,
            message: str,
            user_session: UserSession = Depends(self._get_current_user),
        ):
            """Send a message in a chat session."""
            if session_id not in self.chat_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.chat_sessions[session_id]
            if session.user_id != user_session.user_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Create chat message
            chat_message = ChatMessage(user_id=user_session.user_id, message=message)

            try:
                # Send to agent service
                response = await self._send_to_agent(
                    message, session_id, user_session.user_id
                )
                chat_message.response = response
                chat_message.response_timestamp = datetime.utcnow()

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                chat_message.response = (
                    "Sorry, I encountered an error processing your message."
                )
                chat_message.response_timestamp = datetime.utcnow()

            # Add to session
            session.messages.append(chat_message)
            session.last_activity = datetime.utcnow()

            # Send via WebSocket if connected
            await self.connection_manager.send_personal_message(
                json.dumps(
                    {
                        "type": "response",
                        "message_id": chat_message.id,
                        "response": chat_message.response,
                        "timestamp": chat_message.response_timestamp.isoformat(),
                    }
                ),
                session_id,
            )

            return chat_message

        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str, token: str):
            """WebSocket endpoint for real-time chat."""
            try:
                # Validate token
                user_session = self.token_manager.verify_token(token)

                # Verify session access
                if session_id not in self.chat_sessions:
                    await websocket.close(code=4004, reason="Session not found")
                    return

                session = self.chat_sessions[session_id]
                if session.user_id != user_session.user_id:
                    await websocket.close(code=4003, reason="Access denied")
                    return

                # Connect WebSocket
                await self.connection_manager.connect(
                    websocket, user_session.user_id, session_id
                )

                try:
                    while True:
                        data = await websocket.receive_text()
                        message_data = json.loads(data)

                        if message_data.get("type") == "message":
                            # Process message
                            message = message_data.get("message", "")
                            if message.strip():
                                # This will be handled by the REST endpoint
                                # WebSocket is primarily for receiving responses
                                pass

                except WebSocketDisconnect:
                    pass
                finally:
                    self.connection_manager.disconnect(session_id, user_session.user_id)

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close(code=4000, reason="Authentication failed")

    async def _get_current_user(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> UserSession:
        """Get current authenticated user from JWT token."""
        try:
            return self.token_manager.verify_token(credentials.credentials)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )

    async def _send_to_agent(self, message: str, session_id: str, user_id: str) -> str:
        """Send message to agent service and get response."""
        try:
            payload = {
                "message": message,
                "session_id": session_id,
                "user_id": user_id,
                "context": {
                    "source": "web_chat",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            response = await self.http_client.post(
                f"{self.agent_service_url}/agent/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "Sorry, I couldn't process your message.")

        except httpx.RequestError as e:
            logger.error(f"Agent service request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def _get_chat_html(self) -> str:
        """Get the chat interface HTML."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Jerry AI Assistant</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .chat-container {
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                    width: 90%;
                    max-width: 800px;
                    height: 80vh;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                .chat-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                }
                .chat-messages {
                    flex: 1;
                    padding: 20px;
                    overflow-y: auto;
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }
                .message {
                    padding: 12px 16px;
                    border-radius: 18px;
                    max-width: 80%;
                    word-wrap: break-word;
                }
                .message.user {
                    background: #667eea;
                    color: white;
                    align-self: flex-end;
                }
                .message.bot {
                    background: #f1f3f4;
                    color: #333;
                    align-self: flex-start;
                }
                .chat-input {
                    display: flex;
                    padding: 20px;
                    border-top: 1px solid #eee;
                    gap: 10px;
                }
                #messageInput {
                    flex: 1;
                    padding: 12px 16px;
                    border: 2px solid #eee;
                    border-radius: 25px;
                    outline: none;
                    font-size: 16px;
                }
                #messageInput:focus {
                    border-color: #667eea;
                }
                #sendButton {
                    padding: 12px 24px;
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: background 0.3s;
                }
                #sendButton:hover {
                    background: #5a6fd8;
                }
                .status {
                    padding: 10px 20px;
                    text-align: center;
                    font-size: 14px;
                    color: #666;
                    border-top: 1px solid #eee;
                }
                .typing {
                    display: none;
                    padding: 12px 16px;
                    border-radius: 18px;
                    background: #f1f3f4;
                    color: #666;
                    align-self: flex-start;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="chat-header">
                    <h1>🤖 Jerry AI Assistant</h1>
                    <p>Your intelligent assistant for energy management</p>
                </div>
                <div class="chat-messages" id="chatMessages">
                    <div class="message bot">
                        Hello! I'm Jerry, your AI assistant for energy management and home automation. How can I help you today?
                    </div>
                </div>
                <div class="typing" id="typingIndicator">
                    Jerry is typing...
                </div>
                <div class="chat-input">
                    <input type="text" id="messageInput" placeholder="Type your message here..." />
                    <button id="sendButton">Send</button>
                </div>
                <div class="status" id="status">Connected</div>
            </div>

            <script>
                class ChatClient {
                    constructor() {
                        this.token = null;
                        this.sessionId = null;
                        this.websocket = null;
                        this.messageInput = document.getElementById('messageInput');
                        this.sendButton = document.getElementById('sendButton');
                        this.chatMessages = document.getElementById('chatMessages');
                        this.status = document.getElementById('status');
                        this.typingIndicator = document.getElementById('typingIndicator');

                        this.init();
                    }

                    async init() {
                        try {
                            await this.authenticate();
                            await this.createSession();
                            this.setupWebSocket();
                            this.setupEventListeners();
                            this.updateStatus('Connected');
                        } catch (error) {
                            console.error('Initialization error:', error);
                            this.updateStatus('Error: Authentication failed');
                        }
                    }

                    async authenticate() {
                        const response = await fetch('/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' }
                        });

                        if (!response.ok) {
                            throw new Error('Authentication failed');
                        }

                        const data = await response.json();
                        this.token = data.access_token;
                    }

                    async createSession() {
                        const response = await fetch('/chat/session', {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${this.token}`,
                                'Content-Type': 'application/json'
                            }
                        });

                        if (!response.ok) {
                            throw new Error('Session creation failed');
                        }

                        const data = await response.json();
                        this.sessionId = data.session_id;
                    }

                    setupWebSocket() {
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}?token=${this.token}`;

                        this.websocket = new WebSocket(wsUrl);

                        this.websocket.onopen = () => {
                            this.updateStatus('Connected');
                        };

                        this.websocket.onmessage = (event) => {
                            const data = JSON.parse(event.data);
                            if (data.type === 'response') {
                                this.hideTyping();
                                this.addMessage(data.response, 'bot');
                            }
                        };

                        this.websocket.onclose = () => {
                            this.updateStatus('Disconnected');
                        };

                        this.websocket.onerror = (error) => {
                            console.error('WebSocket error:', error);
                            this.updateStatus('Connection error');
                        };
                    }

                    setupEventListeners() {
                        this.sendButton.addEventListener('click', () => this.sendMessage());
                        this.messageInput.addEventListener('keypress', (e) => {
                            if (e.key === 'Enter') {
                                this.sendMessage();
                            }
                        });
                    }

                    async sendMessage() {
                        const message = this.messageInput.value.trim();
                        if (!message) return;

                        this.addMessage(message, 'user');
                        this.messageInput.value = '';
                        this.showTyping();

                        try {
                            const response = await fetch(`/chat/session/${this.sessionId}/message`, {
                                method: 'POST',
                                headers: {
                                    'Authorization': `Bearer ${this.token}`,
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ message })
                            });

                            if (!response.ok) {
                                throw new Error('Failed to send message');
                            }

                        } catch (error) {
                            console.error('Send message error:', error);
                            this.hideTyping();
                            this.addMessage('Sorry, there was an error sending your message.', 'bot');
                        }
                    }

                    addMessage(text, sender) {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = `message ${sender}`;
                        messageDiv.textContent = text;
                        this.chatMessages.appendChild(messageDiv);
                        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                    }

                    showTyping() {
                        this.typingIndicator.style.display = 'block';
                        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                    }

                    hideTyping() {
                        this.typingIndicator.style.display = 'none';
                    }

                    updateStatus(message) {
                        this.status.textContent = message;
                    }
                }

                // Initialize chat client when page loads
                document.addEventListener('DOMContentLoaded', () => {
                    new ChatClient();
                });
            </script>
        </body>
        </html>
        """

    async def cleanup(self):
        """Cleanup resources."""
        await self.http_client.aclose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = load_config()
    setup_logging(config)

    server = WebChatServer(config)
    return server.app


# Global app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    config = load_config()

    uvicorn.run(
        "src.services.web_chat_server:app",
        host=config.web_chat.host,
        port=config.web_chat.port,
        log_level=config.logging.level.lower(),
        access_log=True,
        reload=config.environment == "development",
    )
