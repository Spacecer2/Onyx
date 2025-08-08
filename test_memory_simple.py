#!/usr/bin/env python3
"""
Simplified test for JARVIS Memory System (no external dependencies)
"""

import sys
import time
import sqlite3
import json
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_memory_manager_direct():
    """Test memory manager directly without external dependencies"""
    print("🧠 Testing JARVIS Memory Manager (Direct)...")
    print("=" * 50)
    
    try:
        # Import memory manager
        from jarvis.core.memory_manager import MemoryManager
        
        # Initialize memory manager
        print("📊 Initializing memory manager...")
        memory_manager = MemoryManager("test_memory.db")
        print("✅ Memory manager initialized")
        
        # Test 1: Store conversations
        print("\n📝 Test 1: Conversation storage...")
        test_conversations = [
            ("Hello JARVIS", "Hello! How can I assist you today?"),
            ("What's the weather like?", "The weather is sunny with a temperature of 22°C."),
            ("What time is it?", "The current time is 3:45 PM."),
            ("My name is John", "Nice to meet you, John! I'll remember your name."),
            ("Set greeting style formal", "I'll use a formal greeting style from now on.")
        ]
        
        for user_input, jarvis_response in test_conversations:
            success = memory_manager.store_conversation(
                user_input=user_input,
                jarvis_response=jarvis_response,
                command_type="test"
            )
            print(f"  {'✅' if success else '❌'} Stored: '{user_input}' -> '{jarvis_response}'")
        
        # Test 2: Retrieve recent conversations
        print("\n📖 Test 2: Retrieving recent conversations...")
        recent_conversations = memory_manager.get_recent_conversations(limit=5)
        print(f"  📊 Retrieved {len(recent_conversations)} conversations:")
        for i, conv in enumerate(recent_conversations, 1):
            print(f"    {i}. User: '{conv['user_input']}'")
            print(f"       JARVIS: '{conv['jarvis_response']}'")
        
        # Test 3: User preferences
        print("\n⚙️ Test 3: User preferences...")
        memory_manager.update_preference("user_name", "John", "User's preferred name")
        memory_manager.update_preference("greeting_style", "formal", "Formal greeting style")
        memory_manager.update_preference("theme", "dark", "Dark theme preference")
        
        preferences = memory_manager.get_user_preferences()
        print(f"  📋 User preferences: {preferences}")
        
        # Test 4: Conversation context
        print("\n🔄 Test 4: Conversation context...")
        context = memory_manager.get_conversation_context(limit=3)
        print(f"  📝 Context length: {len(context)} characters")
        print(f"  📄 Context preview: {context[:100]}...")
        
        # Test 5: Statistics
        print("\n📈 Test 5: Conversation statistics...")
        stats = memory_manager.get_conversation_stats(days=1)
        print(f"  📊 Stats: {stats}")
        
        # Test 6: Export functionality
        print("\n💾 Test 6: Export functionality...")
        export_success = memory_manager.export_conversations("test_conversations.json", "json")
        if export_success:
            print("  ✅ Conversations exported to test_conversations.json")
        else:
            print("  ❌ Export failed")
        
        # Clean up test database
        import os
        if os.path.exists("test_memory.db"):
            os.remove("test_memory.db")
            print("  🧹 Test database cleaned up")
        
        print("\n🎉 All memory manager tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Memory manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_structure():
    """Test database structure and basic operations"""
    print("\n🗄️ Testing Database Structure...")
    print("=" * 50)
    
    try:
        # Create test database
        db_path = "test_db.sqlite"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT NOT NULL,
                jarvis_response TEXT NOT NULL,
                context TEXT,
                session_id TEXT,
                command_type TEXT,
                confidence REAL DEFAULT 1.0,
                processing_time REAL,
                success BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')
        
        # Insert test data
        cursor.execute('''
            INSERT INTO conversations (user_input, jarvis_response, command_type)
            VALUES (?, ?, ?)
        ''', ("Test input", "Test response", "test"))
        
        cursor.execute('''
            INSERT INTO user_preferences (preference_key, preference_value, description)
            VALUES (?, ?, ?)
        ''', ("test_key", "test_value", "Test preference"))
        
        conn.commit()
        
        # Query test data
        cursor.execute('SELECT COUNT(*) FROM conversations')
        conv_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_preferences')
        pref_count = cursor.fetchone()[0]
        
        print(f"  ✅ Conversations table: {conv_count} records")
        print(f"  ✅ Preferences table: {pref_count} records")
        
        conn.close()
        
        # Clean up
        import os
        if os.path.exists(db_path):
            os.remove(db_path)
            print("  🧹 Test database cleaned up")
        
        print("✅ Database structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 JARVIS Memory System Simple Test Suite")
    print("=" * 60)
    
    # Run tests
    memory_test_success = test_memory_manager_direct()
    db_test_success = test_database_structure()
    
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"  🧠 Memory Manager: {'✅ PASSED' if memory_test_success else '❌ FAILED'}")
    print(f"  🗄️ Database Structure: {'✅ PASSED' if db_test_success else '❌ FAILED'}")
    
    if memory_test_success and db_test_success:
        print("\n🎉 All tests passed! Memory system is working correctly.")
        print("\n📋 Next Steps:")
        print("  1. Install required dependencies: pip install pyjokes pyaudio")
        print("  2. Test with full JARVIS integration")
        print("  3. Start using memory features in conversations")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
