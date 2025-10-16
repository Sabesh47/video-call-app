import streamlit as st
import random
import string
import base64
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Video KYC App",
    page_icon="🎥",
    layout="wide"
)

def generate_room_code():
    """Generate a simple 4-character room code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# Initialize session state with persistence
if 'room_code' not in st.session_state:
    st.session_state.room_code = ''
if 'in_call' not in st.session_state:
    st.session_state.in_call = False
if 'is_agent' not in st.session_state:
    st.session_state.is_agent = False
if 'snapshots' not in st.session_state:
    st.session_state.snapshots = []
if 'session_timestamp' not in st.session_state:
    st.session_state.session_timestamp = None
if 'room_created_at' not in st.session_state:
    st.session_state.room_created_at = {}

# Signaling server
SIGNALING_SERVER = "wss://signaling-server-2g74.onrender.com"

def main():
    st.title("🎥 Video KYC Application")
    
    # Instructions
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        **For Agents:**
        1. Click "Start KYC Session" to create a room
        2. Share the room code with customer
        3. Click "Start Camera" when customer joins
        4. Use "Capture KYC Photo" to take customer snapshots
        5. Use "Start Recording" to record the entire call
        
        **For Customers:**
        1. Enter the room code provided by agent
        2. Click "Join Session"
        3. Click "Start Camera" to begin KYC
        
        **Features:**
        - Click on video to switch between large/small view
        - Flip camera button cycles through all available cameras
        - Agent can capture and save customer snapshots
        - Agent can record the entire call with both video and audio
        - Sessions persist across page refreshes for 30 minutes
        - Auto-reconnect on network interruptions
        """)
    
    st.markdown("---")
    
    if not st.session_state.in_call:
        # Main menu
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👨‍💼 Agent Portal")
            if st.button("🚀 Start KYC Session", type="primary", use_container_width=True):
                room_code = generate_room_code()
                st.session_state.room_code = room_code
                st.session_state.in_call = True
                st.session_state.is_agent = True
                st.session_state.session_timestamp = datetime.now()
                st.session_state.room_created_at[room_code] = datetime.now()
                st.rerun()
        
        with col2:
            st.subheader("👤 Customer Portal")
            with st.form("join_form"):
                room_input = st.text_input("Enter Room Code", max_chars=4, placeholder="e.g., A1B2")
                if st.form_submit_button("📞 Join Session", type="secondary", use_container_width=True):
                    if room_input:
                        st.session_state.room_code = room_input.upper()
                        st.session_state.in_call = True
                        st.session_state.is_agent = False
                        st.session_state.session_timestamp = datetime.now()
                        st.rerun()
    else:
        # Check session validity (30 minutes)
        if st.session_state.session_timestamp:
            time_elapsed = datetime.now() - st.session_state.session_timestamp
            if time_elapsed > timedelta(minutes=30):
                st.warning("⚠️ Session expired. Please start a new session.")
                if st.button("Start New Session"):
                    st.session_state.in_call = False
                    st.session_state.room_code = ''
                    st.session_state.is_agent = False
                    st.session_state.session_timestamp = None
                    st.rerun()
                return
        
        # Video call interface
        role = "Agent" if st.session_state.is_agent else "Customer"
        
        # Session info bar
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.success(f"✅ **Room: {st.session_state.room_code}** | Role: {role}")
        with col2:
            if st.session_state.session_timestamp:
                elapsed = datetime.now() - st.session_state.session_timestamp
                minutes = int(elapsed.total_seconds() // 60)
                seconds = int(elapsed.total_seconds() % 60)
                st.info(f"⏱️ Session Time: {minutes:02d}:{seconds:02d}")
        with col3:
            if st.button("❌ End", type="primary", use_container_width=True):
                st.session_state.in_call = False
                st.session_state.room_code = ''
                st.session_state.is_agent = False
                st.session_state.session_timestamp = None
                st.rerun()
        
        if st.session_state.is_agent:
            st.info(f"💡 Share this room code with customer: **{st.session_state.room_code}**")
        else:
            st.info(f"📱 Connected to KYC session: **{st.session_state.room_code}**")
        
        st.markdown("---")
        
        # Real-time video call interface
        st.components.v1.html(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html, body {{
            height: 100%;
            overflow: auto;
            -webkit-overflow-scrolling: touch;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 10px;
            padding-bottom: 40px;
            overflow-x: hidden;
            overflow-y: auto;
        }}
        .video-container {{
            position: relative;
            width: 100%;
            height: 40vh;
            max-height: 400px;
            background: #000;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            margin-bottom: 15px;
        }}
        #remoteVideo {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            background: #1a1a1a;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }}
        #localVideo {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 200px;
            height: 150px;
            object-fit: cover;
            border-radius: 12px;
            border: 3px solid #fff;
            box-shadow: 0 5px 20px rgba(0,0,0,0.4);
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 10;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }}
        #localVideo.large {{
            width: 100%;
            height: 100%;
            bottom: 0;
            right: 0;
            border-radius: 0;
            border: none;
        }}
        #remoteVideo.small {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 200px;
            height: 150px;
            object-fit: cover;
            border-radius: 12px;
            border: 3px solid #fff;
            box-shadow: 0 5px 20px rgba(0,0,0,0.4);
        }}
        .video-label {{
            position: absolute;
            top: 15px;
            left: 15px;
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            backdrop-filter: blur(10px);
            z-index: 10;
        }}
        .status {{
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0,0,0,0.85);
            color: #4ade80;
            padding: 6px 14px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
            z-index: 10;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4ade80;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .controls {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-top: 15px;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
            padding: 0 10px;
            padding-bottom: 30px;
        }}
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 16px 24px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            min-height: 56px;
            text-align: center;
            white-space: nowrap;
        }}
        .btn:hover:not(:disabled) {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
        }}
        .btn:active:not(:disabled) {{
            transform: translateY(0);
        }}
        .btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
            background: #6b7280;
        }}
        .btn-capture {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .btn-flip {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        .btn-mute {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }}
        .btn-video {{
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        }}
        .btn-record {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        .btn-record.recording {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            animation: pulse-btn 2s infinite;
        }}
        @keyframes pulse-btn {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}
        #connectionStatus {{
            text-align: center;
            color: white;
            margin-bottom: 10px;
            font-size: 13px;
            font-weight: 500;
            padding: 10px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .connection-spinner {{
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .snapshot-preview {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 50px rgba(0,0,0,0.5);
            z-index: 1000;
            max-width: 90%;
            display: none;
        }}
        .snapshot-preview.show {{
            display: block;
            animation: fadeIn 0.3s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translate(-50%, -45%); }}
            to {{ opacity: 1; transform: translate(-50%, -50%); }}
        }}
        .snapshot-preview img {{
            max-width: 100%;
            max-height: 60vh;
            border-radius: 10px;
        }}
        .snapshot-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
            justify-content: center;
        }}
        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 999;
            display: none;
        }}
        .overlay.show {{
            display: block;
            animation: fadeIn 0.3s ease;
        }}
        .reconnecting-banner {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 12px;
            text-align: center;
            font-weight: 600;
            z-index: 1001;
            display: none;
            animation: slideDown 0.3s ease;
        }}
        .reconnecting-banner.show {{
            display: block;
        }}
        @keyframes slideDown {{
            from {{ transform: translateY(-100%); }}
            to {{ transform: translateY(0); }}
        }}
        @media (max-width: 768px) {{
            body {{
                padding: 8px;
                padding-bottom: 60px;
            }}
            .video-container {{
                height: 35vh;
                max-height: 300px;
                margin-bottom: 10px;
            }}
            .controls {{
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
                padding-bottom: 20px;
                margin-top: 10px;
            }}
            .btn {{
                padding: 12px 10px;
                font-size: 13px;
                min-height: 48px;
            }}
            #localVideo {{
                width: 100px;
                height: 75px;
                bottom: 10px;
                right: 10px;
                border: 2px solid #fff;
            }}
            #connectionStatus {{
                font-size: 12px;
                padding: 8px;
                margin-bottom: 8px;
            }}
        }}
        @media (max-width: 480px) {{
            body {{
                padding: 8px;
                padding-bottom: 80px;
            }}
            .video-container {{
                height: 30vh;
                max-height: 250px;
                margin-bottom: 10px;
            }}
            .controls {{
                grid-template-columns: 1fr;
                gap: 8px;
                padding-bottom: 20px;
                margin-top: 8px;
            }}
            .btn {{
                font-size: 14px;
                padding: 14px 18px;
                min-height: 50px;
            }}
            #localVideo {{
                width: 80px;
                height: 60px;
                bottom: 8px;
                right: 8px;
                border: 2px solid #fff;
            }}
        }}
    </style>
</head>
<body>
    <div class="reconnecting-banner" id="reconnectingBanner">
        <div class="connection-spinner"></div>
        Reconnecting...
    </div>
    
    <div id="connectionStatus">
        <div class="connection-spinner"></div>
        Connecting to server...
    </div>
    
    <div class="video-container" id="videoContainer">
        <video id="remoteVideo" autoplay playsinline></video>
        <video id="localVideo" autoplay muted playsinline onclick="switchView()"></video>
        <div class="video-label" id="mainLabel">Customer</div>
        <div class="status" id="connectionState">
            <div class="status-dot"></div>
            <span>Waiting...</span>
        </div>
    </div>

    <div class="controls">
        <button class="btn" id="startBtn" onclick="startCall()">
            <span>🚀</span>
            <span>Start Camera</span>
        </button>
        <button class="btn btn-mute" id="muteBtn" onclick="toggleMute()" disabled>
            <span>🎤</span>
            <span>Mute</span>
        </button>
        <button class="btn btn-video" id="videoBtn" onclick="toggleVideo()" disabled>
            <span>📹</span>
            <span>Stop Video</span>
        </button>
        <button class="btn btn-flip" id="flipBtn" onclick="flipCamera()" disabled>
            <span>🔄</span>
            <span>Flip Camera</span>
        </button>
        {('<button class="btn btn-capture" id="captureBtn" onclick="captureSnapshot()" disabled><span>📸</span><span>Capture Photo</span></button>' if st.session_state.is_agent else '')}
        {('<button class="btn btn-record" id="recordBtn" onclick="toggleRecording()" disabled><span>⏺️</span><span>Start Recording</span></button>' if st.session_state.is_agent else '')}
    </div>

    <div class="overlay" id="overlay" onclick="closePreview()"></div>
    <div class="snapshot-preview" id="snapshotPreview">
        <h3 style="margin-bottom: 15px; text-align: center;">KYC Snapshot</h3>
        <img id="snapshotImg" src="" alt="Snapshot">
        <div class="snapshot-buttons">
            <button class="btn" onclick="saveSnapshot()">💾 Save</button>
            <button class="btn" onclick="retakeSnapshot()">🔄 Retake</button>
            <button class="btn" onclick="closePreview()">❌ Cancel</button>
        </div>
    </div>

    <script>
        let localVideo = document.getElementById('localVideo');
        let remoteVideo = document.getElementById('remoteVideo');
        let localStream = null;
        let peerConnection = null;
        let ws = null;
        let isAgent = {str(st.session_state.is_agent).lower()};
        let roomCode = '{st.session_state.room_code}';
        let isMuted = false;
        let isVideoOff = false;
        let isLargeView = false;
        let currentFacingMode = 'user';
        let availableCameras = [];
        let currentCameraIndex = 0;
        let capturedSnapshot = null;
        let mediaRecorder = null;
        let recordedChunks = [];
        let isRecording = false;
        let reconnectAttempts = 0;
        let maxReconnectAttempts = 10;
        let reconnectTimer = null;
        let sessionActive = true;
        let heartbeatInterval = null;
        let lastPongTime = Date.now();
        
        // Session persistence with localStorage
        const SESSION_KEY = 'videokyc_session';
        const SESSION_DURATION = 30 * 60 * 1000; // 30 minutes
        
        // Save session to localStorage
        function saveSession() {{
            const session = {{
                roomCode: roomCode,
                isAgent: isAgent,
                timestamp: Date.now(),
                inCall: true
            }};
            localStorage.setItem(SESSION_KEY, JSON.stringify(session));
        }}
        
        // Load session from localStorage
        function loadSession() {{
            try {{
                const saved = localStorage.getItem(SESSION_KEY);
                if (saved) {{
                    const session = JSON.parse(saved);
                    const age = Date.now() - session.timestamp;
                    
                    if (age < SESSION_DURATION && session.roomCode === roomCode) {{
                        console.log('Restored session:', session);
                        return true;
                    }} else {{
                        localStorage.removeItem(SESSION_KEY);
                    }}
                }}
            }} catch (e) {{
                console.error('Error loading session:', e);
            }}
            return false;
        }}
        
        // Clear session
        function clearSession() {{
            localStorage.removeItem(SESSION_KEY);
        }}

        const configuration = {{
            iceServers: [
                {{ urls: 'stun:stun.l.google.com:19302' }},
                {{ urls: 'stun:stun1.l.google.com:19302' }},
                {{ urls: 'stun:stun2.l.google.com:19302' }},
                {{ urls: 'stun:stun3.l.google.com:19302' }},
                {{ urls: 'stun:stun4.l.google.com:19302' }},
                {{
                    urls: 'turn:openrelay.metered.ca:80',
                    username: 'openrelayproject',
                    credential: 'openrelayproject'
                }},
                {{
                    urls: 'turn:openrelay.metered.ca:443',
                    username: 'openrelayproject',
                    credential: 'openrelayproject'
                }},
                {{
                    urls: 'turn:openrelay.metered.ca:443?transport=tcp',
                    username: 'openrelayproject',
                    credential: 'openrelayproject'
                }}
            ],
            iceCandidatePoolSize: 10,
            bundlePolicy: 'max-bundle',
            rtcpMuxPolicy: 'require',
            iceTransportPolicy: 'all'
        }};

        function connectSignaling() {{
            if (!sessionActive) return;
            
            const signalingServer = '{SIGNALING_SERVER}';
            
            try {{
                ws = new WebSocket(signalingServer);
                
                ws.onopen = function() {{
                    console.log('Connected to signaling server');
                    reconnectAttempts = 0;
                    document.getElementById('connectionStatus').innerHTML = '<div class="status-dot" style="background: #4ade80;"></div>Connected to server';
                    document.getElementById('connectionStatus').style.background = 'rgba(74, 222, 128, 0.3)';
                    document.getElementById('reconnectingBanner').classList.remove('show');
                    
                    // Join room
                    ws.send(JSON.stringify({{
                        type: 'join',
                        room: roomCode,
                        role: isAgent ? 'agent' : 'customer'
                    }}));
                    
                    // Start heartbeat
                    startHeartbeat();
                    
                    // Save session
                    saveSession();
                }};
                
                ws.onerror = function(error) {{
                    console.error('WebSocket error:', error);
                    document.getElementById('connectionStatus').innerHTML = '❌ Connection error';
                    document.getElementById('connectionStatus').style.background = 'rgba(239, 68, 68, 0.3)';
                }};
                
                ws.onclose = function(event) {{
                    console.log('WebSocket closed:', event.code, event.reason);
                    stopHeartbeat();
                    
                    if (!sessionActive) return;
                    
                    document.getElementById('connectionStatus').innerHTML = '<div class="connection-spinner"></div>Disconnected - Reconnecting...';
                    document.getElementById('connectionStatus').style.background = 'rgba(251, 146, 60, 0.3)';
                    document.getElementById('reconnectingBanner').classList.add('show');
                    
                    // Attempt reconnection with exponential backoff
                    if (reconnectAttempts < maxReconnectAttempts) {{
                        reconnectAttempts++;
                        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
                        console.log(`Reconnecting in ${{delay}}ms (attempt ${{reconnectAttempts}})`);
                        
                        reconnectTimer = setTimeout(() => {{
                            connectSignaling();
                        }}, delay);
                    }} else {{
                        document.getElementById('connectionStatus').innerHTML = '❌ Connection failed - Please refresh';
                        document.getElementById('connectionStatus').style.background = 'rgba(239, 68, 68, 0.3)';
                        alert('Connection lost. Please refresh the page to rejoin.');
                    }}
                }};
                
                ws.onmessage = async function(event) {{
                    const message = JSON.parse(event.data);
                    await handleSignalingMessage(message);
                }};
                
            }} catch (error) {{
                console.error('Error connecting to signaling server:', error);
                document.getElementById('connectionStatus').innerHTML = '❌ Cannot connect to server';
            }}
        }}
        
        function startHeartbeat() {{
            stopHeartbeat();
            lastPongTime = Date.now();
            
            heartbeatInterval = setInterval(() => {{
                if (ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{ type: 'ping' }}));
                    
                    // Check if we haven't received pong in 10 seconds
                    if (Date.now() - lastPongTime > 10000) {{
                        console.warn('No pong received, connection may be dead');
                        ws.close();
                    }}
                }}
            }}, 5000); // Send ping every 5 seconds
        }}
        
        function stopHeartbeat() {{
            if (heartbeatInterval) {{
                clearInterval(heartbeatInterval);
                heartbeatInterval = null;
            }}
        }}

        async function handleSignalingMessage(message) {{
            console.log('Received message:', message.type);
            
            // Update pong time for heartbeat
            if (message.type === 'pong') {{
                lastPongTime = Date.now();
                return;
            }}
            
            switch (message.type) {{
                case 'ready':
                    document.getElementById('connectionState').innerHTML = '<div class="status-dot"></div><span>Peer Ready</span>';
                    if (isAgent && peerConnection) {{
                        await createOffer();
                    }}
                    break;
                    
                case 'offer':
                    if (!isAgent && peerConnection) {{
                        await peerConnection.setRemoteDescription(new RTCSessionDescription(message.offer));
                        const answer = await peerConnection.createAnswer();
                        await peerConnection.setLocalDescription(answer);
                        ws.send(JSON.stringify({{
                            type: 'answer',
                            room: roomCode,
                            answer: answer
                        }}));
                    }}
                    break;
                    
                case 'answer':
                    if (isAgent && peerConnection) {{
                        await peerConnection.setRemoteDescription(new RTCSessionDescription(message.answer));
                    }}
                    break;
                    
                case 'ice-candidate':
                    if (peerConnection && message.candidate) {{
                        try {{
                            await peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
                        }} catch (e) {{
                            console.error('Error adding ice candidate:', e);
                        }}
                    }}
                    break;
                    
                case 'peer-disconnected':
                    document.getElementById('connectionState').innerHTML = '<div class="status-dot" style="background: #f59e0b;"></div><span>Peer Disconnected</span>';
                    break;
            }}
        }}

        async function enumerateCameras() {{
            try {{
                const tempStream = await navigator.mediaDevices.getUserMedia({{ video: true }});
                tempStream.getTracks().forEach(track => track.stop());
                
                const devices = await navigator.mediaDevices.enumerateDevices();
                availableCameras = devices.filter(device => device.kind === 'videoinput');
                
                console.log('Available cameras:', availableCameras.length);
                availableCameras.forEach((camera, index) => {{
                    console.log(`Camera ${{index}}: ${{camera.label || 'Camera ' + (index + 1)}}`);
                }});
                
                if (availableCameras.length > 0) {{
                    const firstCamera = availableCameras[0].label.toLowerCase();
                    currentFacingMode = firstCamera.includes('front') || firstCamera.includes('user') ? 'user' : 'environment';
                }}
            }} catch (err) {{
                console.error('Error enumerating cameras:', err);
                availableCameras = [];
            }}
        }}

        async function startCall() {{
            try {{
                await enumerateCameras();
                
                const videoConstraints = availableCameras.length > 0 
                    ? {{ 
                        deviceId: {{ exact: availableCameras[currentCameraIndex].deviceId }},
                        width: {{ ideal: 1280, max: 1920 }}, 
                        height: {{ ideal: 720, max: 1080 }},
                        frameRate: {{ ideal: 30, max: 30 }}
                    }}
                    : {{ 
                        facingMode: currentFacingMode,
                        width: {{ ideal: 1280, max: 1920 }}, 
                        height: {{ ideal: 720, max: 1080 }},
                        frameRate: {{ ideal: 30, max: 30 }}
                    }};
                
                localStream = await navigator.mediaDevices.getUserMedia({{
                    video: videoConstraints,
                    audio: {{
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 48000,
                        channelCount: 1
                    }}
                }});
                
                localVideo.srcObject = localStream;
                document.getElementById('startBtn').disabled = true;
                document.getElementById('muteBtn').disabled = false;
                document.getElementById('videoBtn').disabled = false;
                document.getElementById('flipBtn').disabled = false;
                
                if (isAgent) {{
                    document.getElementById('captureBtn').disabled = false;
                    document.getElementById('recordBtn').disabled = false;
                }}
                
                await initWebRTC();
            }} catch (err) {{
                console.error('Media error:', err);
                alert('Could not access camera/microphone. Please check permissions and try again.');
            }}
        }}

        async function initWebRTC() {{
            peerConnection = new RTCPeerConnection(configuration);

            localStream.getTracks().forEach(track => {{
                const sender = peerConnection.addTrack(track, localStream);
                
                if (track.kind === 'video') {{
                    const parameters = sender.getParameters();
                    if (!parameters.encodings) {{
                        parameters.encodings = [{{}}];
                    }}
                    
                    parameters.encodings[0].maxBitrate = 2500000;
                    parameters.encodings[0].maxFramerate = 30;
                    parameters.encodings[0].scaleResolutionDownBy = 1.0;
                    parameters.encodings[0].priority = 'high';
                    parameters.encodings[0].networkPriority = 'high';
                    
                    sender.setParameters(parameters).catch(err => {{
                        console.warn('Could not set encoding parameters:', err);
                    }});
                }}
            }});

            peerConnection.ontrack = function(event) {{
                if (!remoteVideo.srcObject) {{
                    remoteVideo.srcObject = event.streams[0];
                    document.getElementById('connectionState').innerHTML = '<div class="status-dot"></div><span>Connected</span>';
                    monitorVideoQuality();
                }}
            }};

            peerConnection.onicecandidate = function(event) {{
                if (event.candidate && ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{
                        type: 'ice-candidate',
                        room: roomCode,
                        candidate: event.candidate
                    }}));
                }}
            }};

            peerConnection.onconnectionstatechange = function() {{
                const state = peerConnection.connectionState;
                console.log('Connection state:', state);
                
                const statusEl = document.getElementById('connectionState');
                if (state === 'connected') {{
                    statusEl.innerHTML = '<div class="status-dot"></div><span>Connected</span>';
                    statusEl.querySelector('.status-dot').style.background = '#4ade80';
                }} else if (state === 'connecting') {{
                    statusEl.innerHTML = '<div class="status-dot" style="background: #60a5fa;"></div><span>Connecting...</span>';
                }} else if (state === 'disconnected') {{
                    statusEl.innerHTML = '<div class="status-dot" style="background: #f59e0b;"></div><span>Disconnected</span>';
                }} else if (state === 'failed') {{
                    statusEl.innerHTML = '<div class="status-dot" style="background: #ef4444;"></div><span>Failed</span>';
                    // Try to restart ICE
                    console.log('Connection failed, restarting ICE...');
                    peerConnection.restartIce();
                }}
            }};
            
            peerConnection.oniceconnectionstatechange = function() {{
                console.log('ICE connection state:', peerConnection.iceConnectionState);
                if (peerConnection.iceConnectionState === 'failed') {{
                    console.log('ICE failed, attempting restart...');
                    peerConnection.restartIce();
                }}
            }};

            if (ws && ws.readyState === WebSocket.OPEN) {{
                ws.send(JSON.stringify({{
                    type: 'ready',
                    room: roomCode
                }}));
            }}
        }}

        async function createOffer() {{
            try {{
                const offer = await peerConnection.createOffer({{
                    offerToReceiveAudio: true,
                    offerToReceiveVideo: true
                }});
                await peerConnection.setLocalDescription(offer);
                ws.send(JSON.stringify({{
                    type: 'offer',
                    room: roomCode,
                    offer: offer
                }}));
            }} catch (err) {{
                console.error('Error creating offer:', err);
            }}
        }}

        function toggleMute() {{
            if (localStream) {{
                const audioTrack = localStream.getAudioTracks()[0];
                if (audioTrack) {{
                    audioTrack.enabled = !audioTrack.enabled;
                    isMuted = !audioTrack.enabled;
                    const btn = document.getElementById('muteBtn');
                    btn.innerHTML = isMuted ? '<span>🔇</span><span>Unmute</span>' : '<span>🎤</span><span>Mute</span>';
                }}
            }}
        }}

        function toggleVideo() {{
            if (localStream) {{
                const videoTrack = localStream.getVideoTracks()[0];
                if (videoTrack) {{
                    videoTrack.enabled = !videoTrack.enabled;
                    isVideoOff = !videoTrack.enabled;
                    const btn = document.getElementById('videoBtn');
                    btn.innerHTML = isVideoOff ? '<span>📹</span><span>Start Video</span>' : '<span>📹</span><span>Stop Video</span>';
                }}
            }}
        }}

        async function flipCamera() {{
            if (!localStream) return;
            
            currentCameraIndex = (currentCameraIndex + 1) % availableCameras.length;
            
            if (availableCameras.length === 0) {{
                alert('No cameras available to switch');
                return;
            }}
            
            if (availableCameras.length === 1) {{
                alert('Only one camera available on this device');
                return;
            }}
            
            const nextCamera = availableCameras[currentCameraIndex];
            console.log('Switching to camera:', nextCamera.label);
            
            try {{
                const oldVideoTrack = localStream.getVideoTracks()[0];
                if (oldVideoTrack) {{
                    oldVideoTrack.stop();
                }}
                
                const newStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ 
                        deviceId: {{ exact: nextCamera.deviceId }},
                        width: {{ ideal: 1280, max: 1920 }}, 
                        height: {{ ideal: 720, max: 1080 }},
                        frameRate: {{ ideal: 30, max: 30 }}
                    }}
                }});
                
                const newVideoTrack = newStream.getVideoTracks()[0];
                
                const videoSender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'video');
                if (videoSender) {{
                    await videoSender.replaceTrack(newVideoTrack);
                    
                    const parameters = videoSender.getParameters();
                    if (parameters.encodings && parameters.encodings.length > 0) {{
                        parameters.encodings[0].maxBitrate = 2500000;
                        parameters.encodings[0].maxFramerate = 30;
                        parameters.encodings[0].scaleResolutionDownBy = 1.0;
                        parameters.encodings[0].priority = 'high';
                        parameters.encodings[0].networkPriority = 'high';
                        await videoSender.setParameters(parameters).catch(e => console.warn('Encoding params:', e));
                    }}
                }}
                
                localStream.removeTrack(oldVideoTrack);
                localStream.addTrack(newVideoTrack);
                localVideo.srcObject = localStream;
                
                if (isRecording && mediaRecorder) {{
                    await stopAndRestartRecording();
                }}
                
                console.log('Camera flipped successfully to:', nextCamera.label);
            }} catch (err) {{
                console.error('Error flipping camera:', err);
                alert('Could not flip camera: ' + err.message);
                currentCameraIndex = (currentCameraIndex - 1 + availableCameras.length) % availableCameras.length;
            }}
        }}

        function switchView() {{
            isLargeView = !isLargeView;
            
            if (isLargeView) {{
                localVideo.classList.add('large');
                remoteVideo.classList.add('small');
                document.getElementById('mainLabel').textContent = isAgent ? 'Agent' : 'Customer';
            }} else {{
                localVideo.classList.remove('large');
                remoteVideo.classList.remove('small');
                document.getElementById('mainLabel').textContent = isAgent ? 'Customer' : 'Agent';
            }}
        }}

        function captureSnapshot() {{
            if (!remoteVideo.srcObject) {{
                alert('No customer video available to capture!');
                return;
            }}
            
            const canvas = document.createElement('canvas');
            canvas.width = remoteVideo.videoWidth;
            canvas.height = remoteVideo.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(remoteVideo, 0, 0, canvas.width, canvas.height);
            
            capturedSnapshot = canvas.toDataURL('image/jpeg', 0.95);
            document.getElementById('snapshotImg').src = capturedSnapshot;
            document.getElementById('overlay').classList.add('show');
            document.getElementById('snapshotPreview').classList.add('show');
        }}

        function saveSnapshot() {{
            if (capturedSnapshot) {{
                const link = document.createElement('a');
                link.download = `KYC_${{roomCode}}_${{new Date().toISOString().slice(0,19).replace(/:/g,'-')}}.jpg`;
                link.href = capturedSnapshot;
                link.click();
                closePreview();
                
                // Show success message
                const statusEl = document.getElementById('connectionStatus');
                const originalContent = statusEl.innerHTML;
                statusEl.innerHTML = '✅ Snapshot saved successfully!';
                statusEl.style.background = 'rgba(74, 222, 128, 0.3)';
                setTimeout(() => {{
                    statusEl.innerHTML = originalContent;
                }}, 3000);
            }}
        }}

        function retakeSnapshot() {{
            closePreview();
            setTimeout(() => captureSnapshot(), 100);
        }}

        function closePreview() {{
            document.getElementById('overlay').classList.remove('show');
            document.getElementById('snapshotPreview').classList.remove('show');
            capturedSnapshot = null;
        }}
        
        async function toggleRecording() {{
            if (!isRecording) {{
                await startRecording();
            }} else {{
                await stopRecording();
            }}
        }}
        
        async function startRecording() {{
            try {{
                const canvas = document.createElement('canvas');
                canvas.width = 1920;
                canvas.height = 1080;
                const ctx = canvas.getContext('2d', {{ 
                    alpha: false,
                    desynchronized: true 
                }});
                
                const canvasStream = canvas.captureStream(60);
                
                const audioContext = new AudioContext({{ sampleRate: 48000 }});
                const audioDestination = audioContext.createMediaStreamDestination();
                
                if (localStream && localStream.getAudioTracks().length > 0) {{
                    const localAudioSource = audioContext.createMediaStreamSource(
                        new MediaStream([localStream.getAudioTracks()[0]])
                    );
                    localAudioSource.connect(audioDestination);
                }}
                
                if (remoteVideo.srcObject && remoteVideo.srcObject.getAudioTracks().length > 0) {{
                    const remoteAudioSource = audioContext.createMediaStreamSource(
                        new MediaStream([remoteVideo.srcObject.getAudioTracks()[0]])
                    );
                    remoteAudioSource.connect(audioDestination);
                }}
                
                const recordStream = new MediaStream([
                    ...canvasStream.getVideoTracks(),
                    ...audioDestination.stream.getAudioTracks()
                ]);
                
                const options = {{
                    mimeType: 'video/webm;codecs=vp9,opus',
                    videoBitsPerSecond: 8000000,
                    audioBitsPerSecond: 256000
                }};
                
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                    options.mimeType = 'video/webm;codecs=vp8,opus';
                    options.videoBitsPerSecond = 5000000;
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                        options.mimeType = 'video/webm';
                        options.videoBitsPerSecond = 5000000;
                    }}
                }}
                
                mediaRecorder = new MediaRecorder(recordStream, options);
                recordedChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {{
                    if (event.data && event.data.size > 0) {{
                        recordedChunks.push(event.data);
                    }}
                }};
                
                mediaRecorder.onstop = () => {{
                    const blob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `KYC_Recording_${{roomCode}}_${{new Date().toISOString().slice(0,19).replace(/:/g,'-')}}.webm`;
                    link.click();
                    URL.revokeObjectURL(url);
                    recordedChunks = [];
                    
                    // Show success message
                    const statusEl = document.getElementById('connectionStatus');
                    const originalContent = statusEl.innerHTML;
                    statusEl.innerHTML = '✅ Recording saved successfully!';
                    statusEl.style.background = 'rgba(74, 222, 128, 0.3)';
                    setTimeout(() => {{
                        statusEl.innerHTML = originalContent;
                    }}, 3000);
                }};
                
                mediaRecorder.start(100);
                isRecording = true;
                
                const btn = document.getElementById('recordBtn');
                btn.innerHTML = '<span>⏹️</span><span>Stop Recording</span>';
                btn.classList.add('recording');
                
                const drawVideos = () => {{
                    if (!isRecording) return;
                    
                    ctx.fillStyle = '#000';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    
                    ctx.imageSmoothingEnabled = true;
                    ctx.imageSmoothingQuality = 'high';
                    
                    if (remoteVideo.srcObject && remoteVideo.readyState >= 2) {{
                        const videoAspect = remoteVideo.videoWidth / remoteVideo.videoHeight;
                        const canvasAspect = canvas.width / canvas.height;
                        let drawWidth, drawHeight, drawX, drawY;
                        
                        if (videoAspect > canvasAspect) {{
                            drawHeight = canvas.height;
                            drawWidth = drawHeight * videoAspect;
                            drawX = (canvas.width - drawWidth) / 2;
                            drawY = 0;
                        }} else {{
                            drawWidth = canvas.width;
                            drawHeight = drawWidth / videoAspect;
                            drawX = 0;
                            drawY = (canvas.height - drawHeight) / 2;
                        }}
                        
                        ctx.drawImage(remoteVideo, drawX, drawY, drawWidth, drawHeight);
                    }}
                    
                    if (localStream && localVideo.readyState >= 2) {{
                        const pipWidth = 384;
                        const pipHeight = 288;
                        const pipX = canvas.width - pipWidth - 30;
                        const pipY = canvas.height - pipHeight - 30;
                        
                        ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
                        ctx.shadowBlur = 20;
                        ctx.shadowOffsetX = 0;
                        ctx.shadowOffsetY = 5;
                        
                        ctx.fillStyle = '#fff';
                        ctx.fillRect(pipX - 4, pipY - 4, pipWidth + 8, pipHeight + 8);
                        
                        ctx.shadowColor = 'transparent';
                        ctx.shadowBlur = 0;
                        
                        ctx.drawImage(localVideo, pipX, pipY, pipWidth, pipHeight);
                    }}
                    
                    const indicatorSize = 20;
                    const indicatorX = 40;
                    const indicatorY = 40;
                    
                    ctx.fillStyle = 'rgba(239, 68, 68, 0.95)';
                    ctx.beginPath();
                    ctx.arc(indicatorX, indicatorY, indicatorSize * (0.8 + Math.sin(Date.now() / 500) * 0.2), 0, 2 * Math.PI);
                    ctx.fill();
                    
                    ctx.fillStyle = '#fff';
                    ctx.font = 'bold 24px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                    ctx.fillText('REC', indicatorX + indicatorSize + 15, indicatorY + 8);
                    
                    const timestamp = new Date().toLocaleTimeString('en-US', {{ hour12: false }});
                    ctx.font = 'bold 20px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                    const timeWidth = ctx.measureText(timestamp).width;
                    
                    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
                    ctx.fillRect(canvas.width - timeWidth - 60, 20, timeWidth + 40, 40);
                    
                    ctx.fillStyle = '#fff';
                    ctx.fillText(timestamp, canvas.width - timeWidth - 40, 48);
                    
                    requestAnimationFrame(drawVideos);
                }};
                
                drawVideos();
                console.log('Recording started at Full HD quality');
                
            }} catch (err) {{
                console.error('Error starting recording:', err);
                alert('Could not start recording: ' + err.message);
                isRecording = false;
            }}
        }}
        
        async function stopRecording() {{
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
                isRecording = false;
                
                const btn = document.getElementById('recordBtn');
                btn.innerHTML = '<span>⏺️</span><span>Start Recording</span>';
                btn.classList.remove('recording');
                
                console.log('Recording stopped');
            }}
        }}
        
        async function stopAndRestartRecording() {{
            if (isRecording) {{
                const wasRecording = true;
                await stopRecording();
                setTimeout(async () => {{
                    if (wasRecording) {{
                        await startRecording();
                    }}
                }}, 500);
            }}
        }}

        function monitorVideoQuality() {{
            if (!peerConnection) return;
            
            setInterval(async () => {{
                if (!peerConnection) return;
                
                try {{
                    const stats = await peerConnection.getStats();
                    let inboundVideo = null;
                    
                    stats.forEach(report => {{
                        if (report.type === 'inbound-rtp' && report.kind === 'video') {{
                            inboundVideo = report;
                        }}
                    }});
                    
                    if (inboundVideo) {{
                        const fps = inboundVideo.framesPerSecond || 0;
                        const packetsLost = inboundVideo.packetsLost || 0;
                        
                        const statusEl = document.getElementById('connectionState');
                        const dotEl = statusEl.querySelector('.status-dot');
                        const textEl = statusEl.querySelector('span');
                        
                        if (fps < 15 || packetsLost > 50) {{
                            textEl.textContent = 'Poor Quality';
                            dotEl.style.background = '#f59e0b';
                        }} else if (fps >= 25) {{
                            textEl.textContent = 'HD Quality';
                            dotEl.style.background = '#4ade80';
                        }} else {{
                            textEl.textContent = 'Good Quality';
                            dotEl.style.background = '#60a5fa';
                        }}
                    }}
                }} catch (err) {{
                    console.error('Error getting stats:', err);
                }}
            }}, 3000);
        }}

        // Cleanup on page unload
        window.addEventListener('beforeunload', function(e) {{
            sessionActive = false;
            
            if (isRecording) {{
                stopRecording();
            }}
            if (peerConnection) {{
                peerConnection.close();
            }}
            if (ws) {{
                ws.close();
            }}
            
            stopHeartbeat();
            if (reconnectTimer) {{
                clearTimeout(reconnectTimer);
            }}
            
            // Don't clear session - allow rejoin
            // clearSession();
        }});
        
        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', function() {{
            if (document.hidden) {{
                console.log('Tab hidden');
            }} else {{
                console.log('Tab visible');
                // Check connection health when tab becomes visible
                if (ws && ws.readyState !== WebSocket.OPEN) {{
                    console.log('Reconnecting after tab visible...');
                    connectSignaling();
                }}
            }}
        }});
        
        // Handle online/offline events
        window.addEventListener('online', function() {{
            console.log('Network online');
            document.getElementById('connectionStatus').innerHTML = '<div class="connection-spinner"></div>Reconnecting...';
            if (!ws || ws.readyState !== WebSocket.OPEN) {{
                reconnectAttempts = 0;
                connectSignaling();
            }}
        }});
        
        window.addEventListener('offline', function() {{
            console.log('Network offline');
            document.getElementById('connectionStatus').innerHTML = '❌ Network offline';
            document.getElementById('connectionStatus').style.background = 'rgba(239, 68, 68, 0.3)';
        }});

        // Initialize connection
        console.log('Initializing Video KYC session');
        console.log('Room:', roomCode, 'Role:', isAgent ? 'Agent' : 'Customer');
        
        // Load saved session if exists
        loadSession();
        
        // Connect to signaling server
        connectSignaling();
    </script>
</body>
</html>
        """, height=900)

        # Show captured snapshots (Agent only)
        if st.session_state.is_agent and st.session_state.snapshots:
            st.markdown("---")
            st.subheader("📸 Captured KYC Snapshots")
            cols = st.columns(3)
            for idx, snapshot in enumerate(st.session_state.snapshots):
                with cols[idx % 3]:
                    st.image(snapshot, caption=f"Snapshot {idx + 1}", use_container_width=True)

if __name__ == "__main__":
    main()
