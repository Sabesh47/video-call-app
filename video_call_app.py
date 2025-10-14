import streamlit as st
import random
import string

st.set_page_config(
    page_title="Video Call App",
    page_icon="📹",
    layout="wide"
)

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# ⚠️ IMPORTANT: Replace this URL after deploying the signaling server!
# It will look like: wss://your-app-name.onrender.com
SIGNALING_SERVER = "wss://signaling-server-2g74.onrender.com"

if 'room_code' not in st.session_state:
    st.session_state.room_code = ''
if 'in_call' not in st.session_state:
    st.session_state.in_call = False
if 'is_host' not in st.session_state:
    st.session_state.is_host = False

def main():
    st.title("📹 Real-Time Video Call")
    
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        1. **Host**: Click "Start Video Call" to create a room
        2. **Guest**: Enter the room code and click "Join Call"
        3. Click "Start Camera" to enable video/audio
        4. Share your room code with others!
        
        **Signaling Server Status:** `{}`
        """.format(SIGNALING_SERVER))
    
    st.markdown("---")
    
    if not st.session_state.in_call:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Host a Call")
            if st.button("🚀 Start Video Call", type="primary", use_container_width=True):
                room_code = generate_room_code()
                st.session_state.room_code = room_code
                st.session_state.in_call = True
                st.session_state.is_host = True
                st.rerun()
        
        with col2:
            st.subheader("🚪 Join a Call")
            with st.form("join_form"):
                room_input = st.text_input("Room Code", max_chars=4, placeholder="e.g., A1B2")
                if st.form_submit_button("🎬 Join Call", type="secondary", use_container_width=True):
                    if room_input:
                        st.session_state.room_code = room_input.upper()
                        st.session_state.in_call = True
                        st.session_state.is_host = False
                        st.rerun()
    else:
        role = "Host" if st.session_state.is_host else "Guest"
        st.success(f"✅ **Room: {st.session_state.room_code}** | You are the {role}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"💡 Share this room code: **{st.session_state.room_code}**")
        with col2:
            if st.button("❌ Leave Call", type="primary", use_container_width=True):
                st.session_state.in_call = False
                st.session_state.room_code = ''
                st.session_state.is_host = False
                st.rerun()
        
        st.markdown("---")
        
        st.components.v1.html(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            padding: 10px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .video-container {{
            display: flex;
            flex-direction: column;
            gap: 15px;
            max-width: 100%;
            margin: 0 auto;
            padding: 10px;
        }}
        .video-box {{
            position: relative;
            background: #1a1a2e;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 2px solid rgba(255,255,255,0.1);
        }}
        .video-box video {{
            width: 100%;
            height: 250px;
            object-fit: cover;
            background: #000;
        }}
        .video-label {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: #4ade80;
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 11px;
        }}
        .controls {{
            text-align: center;
            margin-top: 15px;
        }}
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin: 0 5px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }}
        .btn:hover {{
            transform: translateY(-2px);
        }}
        .btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        #connectionStatus {{
            text-align: center;
            color: white;
            margin: 10px 0;
            font-size: 13px;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div id="connectionStatus">🔄 Connecting to signaling server...</div>
    
    <div class="video-container">
        <div class="video-box">
            <video id="localVideo" autoplay muted playsinline></video>
            <div class="video-label">📹 You ({role})</div>
            <div class="status" id="localStatus">Camera Off</div>
        </div>
        <div class="video-box">
            <video id="remoteVideo" autoplay playsinline></video>
            <div class="video-label">📺 Remote Participant</div>
            <div class="status" id="remoteStatus">Waiting...</div>
        </div>
    </div>

    <div class="controls">
        <button class="btn" id="startBtn" onclick="startCall()">🚀 Start Camera</button>
        <button class="btn" id="muteBtn" onclick="toggleMute()" disabled>🎤 Mute</button>
        <button class="btn" id="videoBtn" onclick="toggleVideo()" disabled>📹 Video Off</button>
    </div>

    <script>
        let localVideo = document.getElementById('localVideo');
        let remoteVideo = document.getElementById('remoteVideo');
        let localStream = null;
        let peerConnection = null;
        let ws = null;
        let isHost = {str(st.session_state.is_host).lower()};
        let roomCode = '{st.session_state.room_code}';
        let isMuted = false;
        let isVideoOff = false;
        
        const configuration = {{
            iceServers: [
                {{ urls: 'stun:stun.l.google.com:19302' }},
                {{ urls: 'stun:stun1.l.google.com:19302' }},
                {{
                    urls: 'turn:openrelay.metered.ca:80',
                    username: 'openrelayproject',
                    credential: 'openrelayproject'
                }},
                {{
                    urls: 'turn:openrelay.metered.ca:443',
                    username: 'openrelayproject',
                    credential: 'openrelayproject'
                }}
            ]
        }};

        function connectSignaling() {{
            const signalingServer = '{SIGNALING_SERVER}';
            ws = new WebSocket(signalingServer);
            
            ws.onopen = function() {{
                console.log('Connected to signaling server');
                document.getElementById('connectionStatus').textContent = '✅ Connected to server';
                document.getElementById('connectionStatus').style.color = '#4ade80';
                
                ws.send(JSON.stringify({{
                    type: 'join',
                    room: roomCode,
                    role: isHost ? 'host' : 'guest'
                }}));
            }};
            
            ws.onerror = function(error) {{
                console.error('WebSocket error:', error);
                document.getElementById('connectionStatus').textContent = '❌ Connection error';
                document.getElementById('connectionStatus').style.color = '#ef4444';
            }};
            
            ws.onclose = function() {{
                document.getElementById('connectionStatus').textContent = '⚠️ Disconnected';
                document.getElementById('connectionStatus').style.color = '#f59e0b';
                setTimeout(connectSignaling, 3000);
            }};
            
            ws.onmessage = async function(event) {{
                const message = JSON.parse(event.data);
                await handleSignalingMessage(message);
            }};
        }}

        async function handleSignalingMessage(message) {{
            console.log('Received:', message.type);
            
            switch (message.type) {{
                case 'ready':
                    document.getElementById('remoteStatus').textContent = 'Peer Ready';
                    if (isHost && peerConnection) {{
                        await createOffer();
                    }}
                    break;
                    
                case 'offer':
                    if (!isHost && peerConnection) {{
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
                    if (isHost && peerConnection) {{
                        await peerConnection.setRemoteDescription(new RTCSessionDescription(message.answer));
                    }}
                    break;
                    
                case 'ice-candidate':
                    if (peerConnection && message.candidate) {{
                        await peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
                    }}
                    break;
            }}
        }}

        async function startCall() {{
            try {{
                localStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ width: 1280, height: 720 }},
                    audio: {{
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }}
                }});
                
                localVideo.srcObject = localStream;
                document.getElementById('localStatus').textContent = 'Camera On';
                document.getElementById('startBtn').disabled = true;
                document.getElementById('muteBtn').disabled = false;
                document.getElementById('videoBtn').disabled = false;
                
                await initWebRTC();
            }} catch (err) {{
                console.error('Media error:', err);
                alert('Could not access camera/microphone');
            }}
        }}

        async function initWebRTC() {{
            peerConnection = new RTCPeerConnection(configuration);

            localStream.getTracks().forEach(track => {{
                peerConnection.addTrack(track, localStream);
            }});

            peerConnection.ontrack = function(event) {{
                if (!remoteVideo.srcObject) {{
                    remoteVideo.srcObject = event.streams[0];
                    document.getElementById('remoteStatus').textContent = 'Connected';
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
                console.log('Connection state:', peerConnection.connectionState);
                if (peerConnection.connectionState === 'connected') {{
                    document.getElementById('remoteStatus').textContent = 'Connected';
                }} else if (peerConnection.connectionState === 'disconnected') {{
                    document.getElementById('remoteStatus').textContent = 'Disconnected';
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
                    document.getElementById('videoBtn').textContent = isVideoOff ? '📹 Video On' : '📹 Video Off';
                    document.getElementById('localStatus').textContent = isVideoOff ? 'Camera Off' : 'Camera On';
                }}
            }}
        }}

        connectSignaling();
    </script>
</body>
</html>
        """, height=800)

if __name__ == "__main__":
    main()