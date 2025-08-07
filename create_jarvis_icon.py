#!/usr/bin/env python3
"""
Create JARVIS Icon for Desktop Entry
"""

import os
from pathlib import Path

def create_jarvis_icon():
    """Create a simple JARVIS icon using SVG"""
    
    # Create static directory if it doesn't exist
    static_dir = Path("jarvis/web/static")
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # SVG icon content
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="jarvisGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#0099cc;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0066aa;stop-opacity:1" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge> 
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <!-- Background circle -->
  <circle cx="64" cy="64" r="60" fill="url(#jarvisGradient)" filter="url(#glow)" opacity="0.9"/>
  
  <!-- Inner circle -->
  <circle cx="64" cy="64" r="45" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.7"/>
  
  <!-- Center dot -->
  <circle cx="64" cy="64" r="8" fill="#ffffff" opacity="0.9"/>
  
  <!-- Arc segments (JARVIS-style) -->
  <path d="M 64 19 A 45 45 0 0 1 109 64" fill="none" stroke="#ffffff" stroke-width="3" opacity="0.8"/>
  <path d="M 109 64 A 45 45 0 0 1 64 109" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.6"/>
  <path d="M 64 109 A 45 45 0 0 1 19 64" fill="none" stroke="#ffffff" stroke-width="3" opacity="0.8"/>
  <path d="M 19 64 A 45 45 0 0 1 64 19" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.6"/>
  
  <!-- Corner elements -->
  <circle cx="64" cy="19" r="3" fill="#ffffff" opacity="0.9"/>
  <circle cx="109" cy="64" r="3" fill="#ffffff" opacity="0.7"/>
  <circle cx="64" cy="109" r="3" fill="#ffffff" opacity="0.9"/>
  <circle cx="19" cy="64" r="3" fill="#ffffff" opacity="0.7"/>
  
  <!-- Text -->
  <text x="64" y="75" font-family="Arial, sans-serif" font-size="12" font-weight="bold" 
        text-anchor="middle" fill="#ffffff" opacity="0.9">JARVIS</text>
</svg>'''
    
    # Save SVG icon
    svg_path = static_dir / "jarvis-icon.svg"
    with open(svg_path, 'w') as f:
        f.write(svg_content)
    
    print(f"✅ SVG icon created: {svg_path}")
    
    # Try to create PNG version using cairosvg if available
    try:
        import cairosvg
        png_path = static_dir / "jarvis-icon.png"
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=128, output_height=128)
        print(f"✅ PNG icon created: {png_path}")
        return str(png_path)
    except ImportError:
        print("⚠️ cairosvg not available, using SVG icon")
        return str(svg_path)
    except Exception as e:
        print(f"⚠️ Could not create PNG icon: {e}")
        return str(svg_path)

def install_desktop_file():
    """Install the desktop file to the applications directory"""
    
    # Desktop file path
    desktop_file = Path("jarvis-ai-assistant.desktop")
    
    if not desktop_file.exists():
        print("❌ Desktop file not found")
        return False
    
    # Make launcher script executable
    launcher_script = Path("launch_jarvis_desktop.sh")
    if launcher_script.exists():
        os.chmod(launcher_script, 0o755)
        print(f"✅ Made launcher script executable: {launcher_script}")
    
    # User applications directory
    user_apps_dir = Path.home() / ".local/share/applications"
    user_apps_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy desktop file
    import shutil
    dest_path = user_apps_dir / "jarvis-ai-assistant.desktop"
    shutil.copy2(desktop_file, dest_path)
    
    # Make desktop file executable
    os.chmod(dest_path, 0o755)
    
    print(f"✅ Desktop file installed: {dest_path}")
    
    # Update desktop database
    try:
        import subprocess
        subprocess.run(["update-desktop-database", str(user_apps_dir)], 
                      capture_output=True, check=False)
        print("✅ Desktop database updated")
    except Exception as e:
        print(f"⚠️ Could not update desktop database: {e}")
    
    return True

def main():
    """Main function"""
    print("🎨 Creating JARVIS Desktop Integration")
    print("=" * 50)
    
    # Create icon
    icon_path = create_jarvis_icon()
    
    # Install desktop file
    if install_desktop_file():
        print("\n🎉 JARVIS Desktop Integration Complete!")
        print("\n📋 What's Available:")
        print("   • Application Menu: Search for 'JARVIS AI Assistant'")
        print("   • Right-click Actions: Web Interface, Terminal, Docker")
        print("   • Desktop Shortcut: Copy .desktop file to Desktop")
        print("   • Command Line: ./launch_jarvis_desktop.sh")
        
        print("\n🚀 Quick Start:")
        print("   1. Open Application Menu")
        print("   2. Search for 'JARVIS'")
        print("   3. Click 'JARVIS AI Assistant'")
        print("   4. Web interface opens automatically!")
        
        print("\n💡 Pro Tips:")
        print("   • Pin to taskbar for quick access")
        print("   • Right-click for different launch modes")
        print("   • Use './launch_jarvis_desktop.sh --help' for options")
        
    else:
        print("❌ Desktop integration failed")

if __name__ == "__main__":
    main()
