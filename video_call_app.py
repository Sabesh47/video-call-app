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
        
        **For Customers:**
        1. Enter the room code provided by agent
        2. Click "Join Session"
        3. Click "Start Camera" to begin KYC
        
        **Features:**
        - Click on video to switch between large/small view
        - Flip camera button for front/back camera
        - Agent can capture and save customer snapshots
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
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .btn:hover:not(:disabled) {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }}
        .btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .btn-capture {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .btn-flip {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
            #localVideo {{
                width: 120px;
                height: 90px;
                bottom: 10px;
                right: 10px;
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
        let currentCamera = 'user'; // 'user' or 'environment'
        let capturedSnapshot = null;
        
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

        async function startCall() {{
            try {{
                // First, get initial camera access with basic permissions
                localStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ 
                        width: {{ ideal: 1280, max: 1920 }}, 
                        height: {{ ideal: 720, max: 1080 }},
                        frameRate: {{ ideal: 30, max: 30 }},
                        aspectRatio: 16/9
                    }},
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
                
                // Now enumerate cameras after getting permission
                await getAvailableCameras();
                
                // Enable flip button if multiple cameras available
                if (availableCameras.length > 1) {{
                    document.getElementById('flipBtn').disabled = false;
                    console.log(`Flip camera enabled - ${{availableCameras.length}} cameras available`);
                }} else {{
                    document.getElementById('flipBtn').disabled = true;
                    document.getElementById('flipBtn').title = 'Only one camera detected';
                    console.log('Flip camera disabled - only 1 camera found');
                }}
                
                if (isAgent) {{
                    document.getElementById('captureBtn').disabled = false;
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
            if (!localStream || availableCameras.length <= 1) {{
                alert('Multiple cameras not detected on your device.');
                return;
            }}
            
            // Switch to next camera
            currentCameraIndex = (currentCameraIndex + 1) % availableCameras.length;
            console.log(`Switching to camera ${{currentCameraIndex + 1}} of ${{availableCameras.length}}`);
            
            try {{
                const newStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ 
                        deviceId: {{ exact: availableCameras[currentCameraIndex] }},
                        width: {{ ideal: 1280, max: 1920 }}, 
                        height: {{ ideal: 720, max: 1080 }},
                        frameRate: {{ ideal: 30, max: 30 }},
                        aspectRatio: 16/9
                    }},
                    audio: {{
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 48000,
                        channelCount: 1
                    }}
                }});
                
                // Replace video track in peer connection
                const videoTrack = newStream.getVideoTracks()[0];
                const audioTrack = newStream.getAudioTracks()[0];
                
                const senders = peerConnection.getSenders();
                
                // Replace video track
                const videoSender = senders.find(s => s.track && s.track.kind === 'video');
                if (videoSender) {{
                    await videoSender.replaceTrack(videoTrack);
                    
                    // Reapply encoding parameters
                    const parameters = videoSender.getParameters();
                    if (parameters.encodings && parameters.encodings.length > 0) {{
                        parameters.encodings[0].maxBitrate = 2500000;
                        parameters.encodings[0].maxFramerate = 30;
                        parameters.encodings[0].scaleResolutionDownBy = 1.0;
                        await videoSender.setParameters(parameters);
                    }}
                }}
                
                // Replace audio track
                const audioSender = senders.find(s => s.track && s.track.kind === 'audio');
                if (audioSender) {{
                    await audioSender.replaceTrack(audioTrack);
                }}
                
                // Stop old tracks
                localStream.getTracks().forEach(track => track.stop());
                
                // Update local stream
                localStream = newStream;
                localVideo.srcObject = localStream;
                
                console.log('Camera switched successfully');
            }} catch (err) {{
                console.error('Error flipping camera:', err);
                alert(`Could not switch camera: ${{err.message}}`);
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

        // Get all available cameras
        async function getAvailableCameras() {{
            try {{
                const devices = await navigator.mediaDevices.enumerateDevices();
                availableCameras = devices
                    .filter(device => device.kind === 'videoinput' && device.deviceId)
                    .map(device => device.deviceId);
                
                console.log(`Found ${{availableCameras.length}} camera(s)`);
                
                // Log camera details for debugging
                const videoDevices = devices.filter(device => device.kind === 'videoinput');
                videoDevices.forEach((device, index) => {{
                    console.log(`  Camera ${{index + 1}}: ${{device.label || 'Camera ' + (index + 1)}}`);
                }});
                
                return availableCameras;
            }} catch (err) {{
                console.error('Error enumerating devices:', err);
                return [];
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
