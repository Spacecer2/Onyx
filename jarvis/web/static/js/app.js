// JARVIS Web Interface - JavaScript Application

class JARVISWebApp {
    constructor() {
        this.socket = null;
        this.isListening = false;
        this.startTime = Date.now();
        this.photoCount = 0;
        
        this.initializeSocket();
        this.initializeElements();
        this.bindEvents();
        this.startUptime();
        this.requestCameraFrame();
    }
    
    initializeSocket() {
        this.socket = io();
        
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to JARVIS');
            this.showNotification('Connected to JARVIS', 'success');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from JARVIS');
            this.showNotification('Disconnected from JARVIS', 'error');
        });
        
        // Status updates
        this.socket.on('status_update', (data) => {
            this.handleStatusUpdate(data);
        });
        
        // Speech events
        this.socket.on('speech_transcribed', (data) => {
            this.addMessage(data.text, 'user', data.timestamp);
        });
        
        this.socket.on('jarvis_response', (data) => {
            this.addMessage(data.text, 'jarvis', data.timestamp);
            this.playNotificationSound();
        });
        
        // Camera events
        this.socket.on('camera_frame', (data) => {
            this.updateCameraFeed(data.image);
        });
        
        // Error handling
        this.socket.on('error', (data) => {
            this.showNotification(data.message, 'error');
        });
    }
    
    initializeElements() {
        // Get DOM elements
        this.elements = {
            textInput: document.getElementById('text-input'),
            sendBtn: document.getElementById('send-btn'),
            listenBtn: document.getElementById('listen-btn'),
            photoBtn: document.getElementById('photo-btn'),
            chatMessages: document.getElementById('chat-messages'),
            cameraFeed: document.getElementById('camera-feed'),
            asrStatus: document.getElementById('asr-status'),
            ttsStatus: document.getElementById('tts-status'),
            cameraStatus: document.getElementById('camera-status'),
            deviceInfo: document.getElementById('device-info'),
            photosCount: document.getElementById('photos-count'),
            uptime: document.getElementById('uptime'),
            initTime: document.getElementById('init-time'),
            notifications: document.getElementById('notifications')
        };
        
        // Set initial timestamp
        this.elements.initTime.textContent = this.formatTime(Date.now());
    }
    
    bindEvents() {
        // Text input events
        this.elements.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendTextCommand();
            }
        });
        
        this.elements.sendBtn.addEventListener('click', () => {
            this.sendTextCommand();
        });
        
        // Voice control
        this.elements.listenBtn.addEventListener('click', () => {
            this.toggleListening();
        });
        
        // Photo capture
        this.elements.photoBtn.addEventListener('click', () => {
            this.takePhoto();
        });
        
        // Request status on load
        this.requestStatus();
    }
    
    sendTextCommand() {
        const text = this.elements.textInput.value.trim();
        if (!text) return;
        
        // Add user message
        this.addMessage(text, 'user');
        
        // Clear input
        this.elements.textInput.value = '';
        
        // Send to JARVIS
        this.socket.emit('text_command', { text: text });
    }
    
    toggleListening() {
        if (this.isListening) {
            this.socket.emit('stop_listening');
        } else {
            this.socket.emit('start_listening');
        }
    }
    
    takePhoto() {
        this.elements.photoBtn.classList.add('loading');
        
        fetch('/api/photo', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification(data.message, 'success');
                    this.photoCount++;
                    this.elements.photosCount.textContent = this.photoCount;
                } else {
                    this.showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                this.showNotification('Failed to take photo', 'error');
            })
            .finally(() => {
                this.elements.photoBtn.classList.remove('loading');
            });
    }
    
    addMessage(text, sender, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(timestamp || Date.now());
        
        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);
        messageDiv.appendChild(contentDiv);
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        
        // Animate message appearance
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        
        requestAnimationFrame(() => {
            messageDiv.style.transition = 'all 0.3s ease-out';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        });
    }
    
    updateCameraFeed(imageData) {
        if (imageData) {
            this.elements.cameraFeed.src = imageData;
            this.elements.cameraStatus.classList.add('active');
        } else {
            this.elements.cameraFeed.src = '';
            this.elements.cameraStatus.classList.remove('active');
        }
    }
    
    handleStatusUpdate(data) {
        console.log('Status update:', data);
        
        switch (data.type) {
            case 'connected':
                if (data.status) {
                    this.updateSystemStatus(data.status);
                }
                break;
                
            case 'listening_started':
                this.isListening = true;
                this.elements.listenBtn.classList.add('listening', 'active');
                this.elements.listenBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="6" y="4" width="4" height="16"></rect>
                        <rect x="14" y="4" width="4" height="16"></rect>
                    </svg>
                    Stop
                `;
                this.showNotification('Voice listening started', 'success');
                break;
                
            case 'listening_stopped':
                this.isListening = false;
                this.elements.listenBtn.classList.remove('listening', 'active');
                this.elements.listenBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                        <line x1="8" y1="23" x2="16" y2="23"></line>
                    </svg>
                    Listen
                `;
                this.showNotification('Voice listening stopped', 'success');
                break;
                
            case 'speech_detected':
                this.showNotification('Voice detected, processing...', 'success');
                break;
                
            case 'error':
                this.showNotification(data.message, 'error');
                break;
        }
    }
    
    updateSystemStatus(status) {
        // Update status indicators
        this.updateStatusIndicator('asr-status', status.system_info?.asr_available);
        this.updateStatusIndicator('tts-status', status.system_info?.tts_available);
        this.updateStatusIndicator('camera-status', status.system_info?.camera_active);
        
        // Update system info
        if (status.system_info?.device) {
            this.elements.deviceInfo.textContent = status.system_info.device;
        }
        
        if (status.system_info?.photos_taken !== undefined) {
            this.photoCount = status.system_info.photos_taken;
            this.elements.photosCount.textContent = this.photoCount;
        }
    }
    
    updateStatusIndicator(elementId, isActive) {
        const element = this.elements[elementId.replace('-', '')];
        if (element) {
            if (isActive) {
                element.classList.add('active');
                element.classList.remove('error');
            } else {
                element.classList.remove('active');
                element.classList.add('error');
            }
        }
    }
    
    requestStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                this.updateSystemStatus(data);
            })
            .catch(error => {
                console.error('Failed to get status:', error);
            });
    }
    
    requestCameraFrame() {
        this.socket.emit('request_camera_frame');
        
        // Request frames periodically
        setInterval(() => {
            this.socket.emit('request_camera_frame');
        }, 1000 / 15); // 15 FPS
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        this.elements.notifications.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
    
    playNotificationSound() {
        const audio = document.getElementById('notification-sound');
        if (audio) {
            audio.play().catch(e => {
                // Ignore audio play errors (user interaction required)
            });
        }
    }
    
    startUptime() {
        setInterval(() => {
            const uptime = Date.now() - this.startTime;
            this.elements.uptime.textContent = this.formatUptime(uptime);
        }, 1000);
    }
    
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }
    
    formatUptime(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.jarvisApp = new JARVISWebApp();
});
