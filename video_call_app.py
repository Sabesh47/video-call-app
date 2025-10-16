import streamlit as st
import random
import string
import base64
from datetime import datetime

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
                        st.rerun()
    else:
        # Video call interface
        role = "Agent" if st.session_state.is_agent else "Customer"
        st.success(f"✅ **Room: {st.session_state.room_code}** | You are: {role}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.session_state.is_agent:
                st.info(f"💡 Share this room code with customer: **{st.session_state.room_code}**")
            else:
                st.info(f"📱 Connected to KYC session: **{st.session_state.room_code}**")
        with col2:
            if st.button("❌ End Session", type="primary", use_container_width=True):
                st.session_state.in_call = False
                st.session_state.room_code = ''
                st.session_state.is_agent = False
                st.rerun()
        
        st.markdown("---")
        
        # Real-time video call interface
        st.components.v1.html(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 15px;
        }}
        .video-container {{
            position: relative;
            width: 100%;
            height: 75vh;
            background: #000;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
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
        }}
        .controls {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-top: 20px;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
            padding: 0 10px;
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
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}
        #connectionStatus {{
            text-align: center;
            color: white;
            margin-bottom: 15px;
            font-size: 14px;
            font-weight: 500;
            padding: 10px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
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
        }}
        @media (max-width: 768px) {{
            .controls {{
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }}
            .btn {{
                padding: 14px 16px;
                font-size: 14px;
                min-height: 52px;
            }}
            #localVideo {{
                width: 120px;
                height: 90px;
                bottom: 10px;
                right: 10px;
            }}
            .video-container {{
                height: 60vh;
            }}
        }}
        @media (max-width: 480px) {{
            .controls {{
                grid-template-columns: 1fr;
            }}
            .btn {{
                font-size: 15px;
                padding: 16px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div id="connectionStatus">🔄 Connecting to server...</div>
    
    <div class="video-container" id="videoContainer">
        <video id="remoteVideo" autoplay playsinline></video>
        <video id="localVideo" autoplay muted playsinline onclick="switchView()"></video>
        <div class="video-label" id="mainLabel">Customer</div>
        <div class="status" id="connectionState">Waiting...</div>
    </div>

    <div class="controls">
        <button class="btn" id="startBtn" onclick="startCall()">🚀 Start Camera</button>
        <button class="btn" id="muteBtn" onclick="toggleMute()" disabled>🎤 Mute</button>
        <button class="btn" id="videoBtn" onclick="toggleVideo()" disabled>📹 Stop Video</button>
        <button class="btn btn-flip" id="flipBtn" onclick="flipCamera()" disabled>🔄 Flip Camera</button>
        {('<button class="btn btn-capture" id="captureBtn" onclick="captureSnapshot()" disabled>📸 Capture KYC Photo</button>' if st.session_state.is_agent else '')}
        {('<button class="btn" id="recordBtn" onclick="toggleRecording()" disabled style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">⏺️ Start Recording</button>' if st.session_state.is_agent else '')}
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
        
        // Persist session state
        sessionStorage.setItem('roomCode', roomCode);
        sessionStorage.setItem('isAgent', isAgent);
        sessionStorage.setItem('inCall', 'true');

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
            const signalingServer = '{SIGNALING_SERVER}';
            ws = new WebSocket(signalingServer);
            
            ws.onopen = function() {{
                console.log('Connected to signaling server');
                document.getElementById('connectionStatus').innerHTML = '✅ Connected to server';
                document.getElementById('connectionStatus').style.background = 'rgba(74, 222, 128, 0.3)';
                
                ws.send(JSON.stringify({{
                    type: 'join',
                    room: roomCode,
                    role: isAgent ? 'agent' : 'customer'
                }}));
            }};
            
            ws.onerror = function(error) {{
                console.error('WebSocket error:', error);
                document.getElementById('connectionStatus').innerHTML = '❌ Connection error';
                document.getElementById('connectionStatus').style.background = 'rgba(239, 68, 68, 0.3)';
            }};
            
            ws.onclose = function() {{
                document.getElementById('connectionStatus').innerHTML = '⚠️ Disconnected - Reconnecting...';
                document.getElementById('connectionStatus').style.background = 'rgba(251, 146, 60, 0.3)';
                setTimeout(connectSignaling, 3000);
            }};
            
            ws.onmessage = async function(event) {{
                const message = JSON.parse(event.data);
                await handleSignalingMessage(message);
            }};
        }}

        async function handleSignalingMessage(message) {{
            console.log('Received message:', message.type);
            
            switch (message.type) {{
                case 'ready':
                    document.getElementById('connectionState').textContent = 'Peer Ready';
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
            }}
        }}

        async function enumerateCameras() {{
            try {{
                // Request permissions first
                const tempStream = await navigator.mediaDevices.getUserMedia({{ video: true }});
                tempStream.getTracks().forEach(track => track.stop());
                
                // Now enumerate devices
                const devices = await navigator.mediaDevices.enumerateDevices();
                availableCameras = devices.filter(device => device.kind === 'videoinput');
                
                console.log('Available cameras:', availableCameras.length);
                availableCameras.forEach((camera, index) => {{
                    console.log(`Camera ${{index}}: ${{camera.label || 'Camera ' + (index + 1)}}`);
                }});
                
                // Set initial facing mode based on first camera
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
                // Enumerate available cameras first
                await enumerateCameras();
                
                // Get initial camera device ID
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
                alert('Could not access camera/microphone. Please check permissions.');
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
                    
                    // High-quality encoding parameters
                    parameters.encodings[0].maxBitrate = 2500000; // 2.5 Mbps for HD quality
                    parameters.encodings[0].maxFramerate = 30;
                    parameters.encodings[0].scaleResolutionDownBy = 1.0; // No downscaling
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
                    document.getElementById('connectionState').textContent = 'Connected';
                    document.getElementById('connectionState').style.color = '#4ade80';
                    
                    // Monitor video quality
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
                document.getElementById('connectionState').textContent = state.charAt(0).toUpperCase() + state.slice(1);
                
                if (state === 'connected') {{
                    document.getElementById('connectionState').style.color = '#4ade80';
                }} else if (state === 'disconnected' || state === 'failed') {{
                    document.getElementById('connectionState').style.color = '#ef4444';
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
                const offer = await peerConnection.createOffer();
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
                    document.getElementById('muteBtn').textContent = isMuted ? '🔇 Unmute' : '🎤 Mute';
                }}
            }}
        }}

        function toggleVideo() {{
            if (localStream) {{
                const videoTrack = localStream.getVideoTracks()[0];
                if (videoTrack) {{
                    videoTrack.enabled = !videoTrack.enabled;
                    isVideoOff = !videoTrack.enabled;
                    document.getElementById('videoBtn').textContent = isVideoOff ? '📹 Start Video' : '📹 Stop Video';
                }}
            }}
        }}

        async function flipCamera() {{
            if (!localStream) return;
            
            // Move to next camera
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
                // Stop current video track
                const oldVideoTrack = localStream.getVideoTracks()[0];
                if (oldVideoTrack) {{
                    oldVideoTrack.stop();
                }}
                
                // Get new video stream with specific camera
                const newStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ 
                        deviceId: {{ exact: nextCamera.deviceId }},
                        width: {{ ideal: 1280, max: 1920 }}, 
                        height: {{ ideal: 720, max: 1080 }},
                        frameRate: {{ ideal: 30, max: 30 }}
                    }}
                }});
                
                const newVideoTrack = newStream.getVideoTracks()[0];
                
                // Replace video track in peer connection
                const videoSender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'video');
                if (videoSender) {{
                    await videoSender.replaceTrack(newVideoTrack);
                    
                    // Reapply encoding parameters for quality
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
                
                // Update local stream
                localStream.removeTrack(oldVideoTrack);
                localStream.addTrack(newVideoTrack);
                localVideo.srcObject = localStream;
                
                // Update recording stream if recording
                if (isRecording && mediaRecorder) {{
                    await stopAndRestartRecording();
                }}
                
                console.log('Camera flipped successfully to:', nextCamera.label);
            }} catch (err) {{
                console.error('Error flipping camera:', err);
                alert('Could not flip camera: ' + err.message);
                // Revert to previous camera
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
            
            capturedSnapshot = canvas.toDataURL('image/jpeg', 0.9);
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
                alert('KYC snapshot saved successfully!');
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
                // Create a composite stream with both local and remote video/audio
                const canvas = document.createElement('canvas');
                canvas.width = 1280;
                canvas.height = 720;
                const ctx = canvas.getContext('2d');
                
                // Capture canvas stream
                const canvasStream = canvas.captureStream(30);
                
                // Create audio context to mix audio streams
                const audioContext = new AudioContext();
                const audioDestination = audioContext.createMediaStreamDestination();
                
                // Add local audio
                if (localStream && localStream.getAudioTracks().length > 0) {{
                    const localAudioSource = audioContext.createMediaStreamSource(
                        new MediaStream([localStream.getAudioTracks()[0]])
                    );
                    localAudioSource.connect(audioDestination);
                }}
                
                // Add remote audio
                if (remoteVideo.srcObject && remoteVideo.srcObject.getAudioTracks().length > 0) {{
                    const remoteAudioSource = audioContext.createMediaStreamSource(
                        new MediaStream([remoteVideo.srcObject.getAudioTracks()[0]])
                    );
                    remoteAudioSource.connect(audioDestination);
                }}
                
                // Combine video and audio streams
                const recordStream = new MediaStream([
                    ...canvasStream.getVideoTracks(),
                    ...audioDestination.stream.getAudioTracks()
                ]);
                
                // Setup MediaRecorder
                const options = {{
                    mimeType: 'video/webm;codecs=vp9,opus',
                    videoBitsPerSecond: 2500000
                }};
                
                // Fallback for Safari/iOS
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                    options.mimeType = 'video/webm;codecs=vp8,opus';
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                        options.mimeType = 'video/webm';
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
                }};
                
                mediaRecorder.start(1000); // Collect data every second
                isRecording = true;
                
                document.getElementById('recordBtn').textContent = '⏹️ Stop Recording';
                document.getElementById('recordBtn').style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
                
                // Draw both videos onto canvas
                const drawVideos = () => {{
                    if (!isRecording) return;
                    
                    ctx.fillStyle = '#000';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    
                    // Draw remote video (customer) - larger
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
                    
                    // Draw local video (agent) - smaller, picture-in-picture
                    if (localStream && localVideo.readyState >= 2) {{
                        const pipWidth = 240;
                        const pipHeight = 180;
                        const pipX = canvas.width - pipWidth - 20;
                        const pipY = canvas.height - pipHeight - 20;
                        
                        // Draw border
                        ctx.strokeStyle = '#fff';
                        ctx.lineWidth = 3;
                        ctx.strokeRect(pipX - 2, pipY - 2, pipWidth + 4, pipHeight + 4);
                        
                        ctx.drawImage(localVideo, pipX, pipY, pipWidth, pipHeight);
                    }}
                    
                    // Add recording indicator
                    ctx.fillStyle = 'rgba(239, 68, 68, 0.9)';
                    ctx.beginPath();
                    ctx.arc(30, 30, 12, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    ctx.fillStyle = '#fff';
                    ctx.font = 'bold 16px Arial';
                    ctx.fillText('REC', 50, 38);
                    
                    // Add timestamp
                    const timestamp = new Date().toLocaleTimeString();
                    ctx.fillText(timestamp, canvas.width - 120, 38);
                    
                    requestAnimationFrame(drawVideos);
                }};
                
                drawVideos();
                console.log('Recording started');
                
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
                
                document.getElementById('recordBtn').textContent = '⏺️ Start Recording';
                document.getElementById('recordBtn').style.background = 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)';
                
                console.log('Recording stopped');
            }}
        }}
        
        async function stopAndRestartRecording() {{
            // Helper function to restart recording when camera flips
            if (isRecording) {{
                const wasRecording = true;
                await stopRecording();
                // Wait a bit for the camera to stabilize
                setTimeout(async () => {{
                    if (wasRecording) {{
                        await startRecording();
                    }}
                }}, 500);
            }}
        }}

        // Monitor and adjust video quality based on network conditions
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
                        const bytesReceived = inboundVideo.bytesReceived || 0;
                        const packetsLost = inboundVideo.packetsLost || 0;
                        
                        console.log(`Video Stats - FPS: ${{fps}}, Packets Lost: ${{packetsLost}}`);
                        
                        // Show quality indicator
                        if (fps < 15 || packetsLost > 50) {{
                            document.getElementById('connectionState').textContent = 'Poor Quality';
                            document.getElementById('connectionState').style.color = '#f59e0b';
                        }} else if (fps >= 25) {{
                            document.getElementById('connectionState').textContent = 'HD Quality';
                            document.getElementById('connectionState').style.color = '#4ade80';
                        }} else {{
                            document.getElementById('connectionState').textContent = 'Good Quality';
                            document.getElementById('connectionState').style.color = '#60a5fa';
                        }}
                    }}
                }} catch (err) {{
                    console.error('Error getting stats:', err);
                }}
            }}, 3000); // Check every 3 seconds
        }}

        // Optimize sender parameters based on network
        async function optimizeBitrate(targetBitrate) {{
            if (!peerConnection) return;
            
            const senders = peerConnection.getSenders();
            for (const sender of senders) {{
                if (sender.track && sender.track.kind === 'video') {{
                    const parameters = sender.getParameters();
                    if (parameters.encodings && parameters.encodings.length > 0) {{
                        parameters.encodings[0].maxBitrate = targetBitrate;
                        try {{
                            await sender.setParameters(parameters);
                            console.log(`Bitrate adjusted to: ${{targetBitrate}}`);
                        }} catch (err) {{
                            console.error('Error setting bitrate:', err);
                        }}
                    }}
                }}
            }}
        }}

        // Auto-reconnect on page refresh
        window.addEventListener('beforeunload', function() {{
            if (isRecording) {{
                stopRecording();
            }}
            if (peerConnection) {{
                peerConnection.close();
            }}
            if (ws) {{
                ws.close();
            }}
        }});

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
