/**
 * JARVIS Enhanced Interface - Dynamic Core Animation & Advanced Features
 */

class EnhancedJARVIS {
    constructor() {
        this.socket = io();
        this.isListening = false;
        this.isSpeaking = false;
        this.currentMood = 'ready';
        this.theme = 'dark';
        this.particles = [];
        this.commandCount = 0;
        this.startTime = Date.now();
        
        // Core elements
        this.jarvisCore = document.getElementById('jarvis-core');
        this.moodText = document.getElementById('mood-text');
        this.activityText = document.getElementById('activity-text');
        this.coreText = document.getElementById('core-text');
        
        // Initialize
        this.init();
    }
    
    init() {
        console.log('🤖 JARVIS Enhanced Interface Initializing...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize components
        this.initializeParticles();
        this.initializeCamera();
        this.initializeChat();
        this.initializeStatusUpdates();
        
        // Start animations
        this.startCoreAnimations();
        this.updateTimestamp();
        
        // Set initial mood
        this.setMood('ready', 'Initializing systems...');
        
        console.log('✅ JARVIS Enhanced Interface Ready!');
    }
    
    setupEventListeners() {
        // Chat input
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        
        if (chatInput && sendBtn) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
            
            sendBtn.addEventListener('click', () => {
                this.sendMessage();
            });
        }
        
        // Voice controls
        const listenBtn = document.getElementById('listen-btn');
        if (listenBtn) {
            listenBtn.addEventListener('click', () => {
                this.toggleListening();
            });
        }
        
        // Photo button
        const photoBtn = document.getElementById('photo-btn');
        if (photoBtn) {
            photoBtn.addEventListener('click', () => {
                this.takePhoto();
            });
        }
        
        // Socket events
        this.socket.on('response', (data) => {
            this.handleResponse(data);
        });
        
        this.socket.on('status_update', (data) => {
            this.updateSystemStatus(data);
        });
        
        this.socket.on('camera_frame', (data) => {
            this.updateCameraFeed(data);
        });
        
        // Core interaction
        if (this.jarvisCore) {
            this.jarvisCore.addEventListener('click', () => {
                this.coreInteraction();
            });
        }
    }
    
    initializeParticles() {
        const particleField = document.getElementById('particle-field');
        if (!particleField) return;
        
        // Create floating particles
        for (let i = 0; i < 20; i++) {
            this.createParticle(particleField);
        }
        
        // Continuously spawn particles
        setInterval(() => {
            if (this.particles.length < 30) {
                this.createParticle(particleField);
            }
        }, 2000);
    }
    
    createParticle(container) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 8 + 's';
        particle.style.animationDuration = (8 + Math.random() * 4) + 's';
        
        container.appendChild(particle);
        this.particles.push(particle);
        
        // Remove particle after animation
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
            const index = this.particles.indexOf(particle);
            if (index > -1) {
                this.particles.splice(index, 1);
            }
        }, 12000);
    }
    
    initializeCamera() {
        const canvas = document.getElementById('camera-canvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Request camera feed
        this.socket.emit('start_camera');
        
        // Draw placeholder
        this.drawCameraPlaceholder(ctx, canvas.width, canvas.height);
    }
    
    drawCameraPlaceholder(ctx, width, height) {
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, width, height);
        
        ctx.fillStyle = '#00d4ff';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Camera Initializing...', width/2, height/2);
        
        // Draw scanning effect
        const gradient = ctx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, 'transparent');
        gradient.addColorStop(0.5, 'rgba(0, 212, 255, 0.5)');
        gradient.addColorStop(1, 'transparent');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, height/2 - 1, width, 2);
    }
    
    initializeChat() {
        // Add welcome message
        this.addMessage('system', 'JARVIS Enhanced Interface initialized. All systems operational.', true);
        
        // Update initial timestamp
        const initTime = document.getElementById('init-time');
        if (initTime) {
            initTime.textContent = new Date().toLocaleTimeString();
        }
    }
    
    initializeStatusUpdates() {
        // Update system info periodically
        setInterval(() => {
            this.updateUptime();
            this.updateSystemInfo();
        }, 1000);
        
        // Request initial status
        this.socket.emit('get_status');
    }
    
    startCoreAnimations() {
        // Enhanced core pulse based on mood
        setInterval(() => {
            this.updateCoreAnimation();
        }, 100);
        
        // Mood-based color cycling
        setInterval(() => {
            this.cycleMoodColors();
        }, 3000);
    }
    
    setMood(mood, activity = '') {
        if (this.currentMood === mood) return;
        
        console.log(`🎭 JARVIS Mood: ${mood} - ${activity}`);
        
        this.currentMood = mood;
        
        // Update core classes
        if (this.jarvisCore) {
            this.jarvisCore.className = `jarvis-core ${mood}`;
        }
        
        // Update text
        if (this.moodText) {
            this.moodText.textContent = mood.toUpperCase();
        }
        
        if (this.activityText && activity) {
            this.activityText.textContent = activity;
        }
        
        if (this.coreText) {
            this.coreText.textContent = mood.toUpperCase();
        }
        
        // Update status indicators
        this.updateStatusIndicators(mood);
        
        // Trigger special effects
        this.triggerMoodEffects(mood);
    }
    
    updateStatusIndicators(mood) {
        const indicators = {
            'audio-indicator': mood === 'listening' || mood === 'speaking',
            'camera-indicator': true,
            'ai-indicator': mood === 'thinking',
            'system-indicator': true
        };
        
        Object.entries(indicators).forEach(([id, active]) => {
            const indicator = document.getElementById(id);
            if (indicator) {
                const dot = indicator.querySelector('.indicator-dot');
                if (dot) {
                    dot.className = `indicator-dot ${active ? 'active' : 'online'}`;
                }
            }
        });
    }
    
    triggerMoodEffects(mood) {
        // Create mood-specific particle bursts
        const particleField = document.getElementById('particle-field');
        if (!particleField) return;
        
        const colors = {
            'ready': '#00d4ff',
            'listening': '#00ff88',
            'speaking': '#ff6600',
            'thinking': '#9966ff',
            'error': '#ff3366'
        };
        
        // Burst effect
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.background = colors[mood] || colors.ready;
                particle.style.left = '50%';
                particle.style.top = '50%';
                particle.style.transform = `translate(-50%, -50%) translate(${(Math.random() - 0.5) * 200}px, ${(Math.random() - 0.5) * 200}px)`;
                particle.style.animationDuration = '2s';
                
                particleField.appendChild(particle);
                
                setTimeout(() => {
                    if (particle.parentNode) {
                        particle.parentNode.removeChild(particle);
                    }
                }, 2000);
            }, i * 100);
        }
    }
    
    updateCoreAnimation() {
        if (!this.jarvisCore) return;
        
        // Dynamic rotation based on mood
        const rotationSpeeds = {
            'ready': 1,
            'listening': 3,
            'speaking': 5,
            'thinking': 2,
            'error': 0.5
        };
        
        const speed = rotationSpeeds[this.currentMood] || 1;
        const rings = this.jarvisCore.querySelectorAll('.core-ring');
        
        rings.forEach((ring, index) => {
            const currentRotation = parseFloat(ring.style.transform?.match(/rotate\(([^)]+)deg\)/)?.[1] || 0);
            const newRotation = currentRotation + speed * (index % 2 === 0 ? 1 : -1);
            ring.style.transform = `rotate(${newRotation}deg)`;
        });
    }
    
    cycleMoodColors() {
        if (this.currentMood === 'ready') {
            // Subtle color cycling for ready state
            const hue = (Date.now() / 50) % 360;
            document.documentElement.style.setProperty('--mood-ready', `hsl(${hue}, 100%, 50%)`);
        }
    }
    
    sendMessage() {
        const input = document.getElementById('chat-input');
        if (!input || !input.value.trim()) return;
        
        const message = input.value.trim();
        input.value = '';
        
        // Add user message
        this.addMessage('user', message);
        
        // Set thinking mood
        this.setMood('thinking', 'Processing your request...');
        
        // Send to server
        this.socket.emit('message', { text: message });
        
        this.commandCount++;
        this.updateCommandCount();
    }
    
    addMessage(type, content, isSystem = false) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = content;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();
        
        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);
        messageDiv.appendChild(messageContent);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    handleResponse(data) {
        // Add assistant message
        this.addMessage('assistant', data.response);
        
        // Set speaking mood
        this.setMood('speaking', 'Responding...');
        
        // Return to ready after speaking
        setTimeout(() => {
            this.setMood('ready', 'Ready for commands');
        }, 2000);
    }
    
    toggleListening() {
        this.isListening = !this.isListening;
        
        const listenBtn = document.getElementById('listen-btn');
        if (listenBtn) {
            listenBtn.classList.toggle('active', this.isListening);
        }
        
        if (this.isListening) {
            this.setMood('listening', 'Listening for voice input...');
            this.socket.emit('start_listening');
        } else {
            this.setMood('ready', 'Voice input stopped');
            this.socket.emit('stop_listening');
        }
    }
    
    takePhoto() {
        this.setMood('thinking', 'Capturing photo...');
        this.socket.emit('take_photo');
        
        setTimeout(() => {
            this.setMood('ready', 'Photo captured');
        }, 1500);
    }
    
    coreInteraction() {
        // Easter egg - core interaction
        this.setMood('thinking', 'Core accessed');
        
        // Create ripple effect
        const ripple = document.createElement('div');
        ripple.style.position = 'absolute';
        ripple.style.width = '100px';
        ripple.style.height = '100px';
        ripple.style.border = '2px solid var(--jarvis-blue)';
        ripple.style.borderRadius = '50%';
        ripple.style.left = '50%';
        ripple.style.top = '50%';
        ripple.style.transform = 'translate(-50%, -50%)';
        ripple.style.animation = 'rippleEffect 1s ease-out forwards';
        ripple.style.pointerEvents = 'none';
        
        this.jarvisCore.appendChild(ripple);
        
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
            this.setMood('ready', 'Ready for commands');
        }, 1000);
    }
    
    updateCameraFeed(data) {
        const canvas = document.getElementById('camera-canvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        
        img.src = 'data:image/jpeg;base64,' + data.frame;
    }
    
    updateSystemStatus(data) {
        // Update header status indicators
        const statusItems = {
            'audio-status-header': data.audio_available,
            'camera-status-header': data.camera_available,
            'ai-status-header': data.ai_available
        };
        
        Object.entries(statusItems).forEach(([id, status]) => {
            const element = document.getElementById(id);
            if (element) {
                const dot = element.querySelector('.status-dot');
                if (dot) {
                    dot.className = `status-dot ${status ? 'online' : ''}`;
                }
            }
        });
        
        // Update system status text
        const statusText = document.getElementById('system-status-text');
        if (statusText) {
            statusText.textContent = data.overall_status || 'Online';
        }
    }
    
    updateTimestamp() {
        const timestamp = document.getElementById('timestamp');
        if (timestamp) {
            setInterval(() => {
                timestamp.textContent = new Date().toLocaleTimeString();
            }, 1000);
        }
    }
    
    updateUptime() {
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            const uptime = Date.now() - this.startTime;
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            const seconds = Math.floor((uptime % 60000) / 1000);
            
            uptimeElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    updateCommandCount() {
        const commandCountElement = document.getElementById('command-count');
        if (commandCountElement) {
            commandCountElement.textContent = this.commandCount.toString();
        }
    }
    
    updateSystemInfo() {
        // Update resolution display
        const resolutionElement = document.getElementById('camera-resolution');
        if (resolutionElement) {
            const canvas = document.getElementById('camera-canvas');
            if (canvas) {
                resolutionElement.textContent = `${canvas.width}x${canvas.height}`;
            }
        }
    }
}

// Add ripple effect CSS
const style = document.createElement('style');
style.textContent = `
@keyframes rippleEffect {
    0% {
        transform: translate(-50%, -50%) scale(0);
        opacity: 1;
    }
    100% {
        transform: translate(-50%, -50%) scale(3);
        opacity: 0;
    }
}
`;
document.head.appendChild(style);

// Initialize JARVIS when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.jarvis = new EnhancedJARVIS();
});

// Export for global access
window.EnhancedJARVIS = EnhancedJARVIS;
