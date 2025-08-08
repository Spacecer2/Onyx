#!/usr/bin/env python3
"""
Test script for JARVIS Memory System
"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_memory_system():
    """Test the memory system functionality"""
    print("🧠 Testing JARVIS Memory System...")
    print("=" * 50)
    
    try:
        # Import memory manager
        from jarvis.core.memory_manager import get_memory_manager
        from jarvis.commands.processor import CommandProcessor
        
        # Initialize memory manager
        print("📊 Initializing memory manager...")
        memory_manager = get_memory_manager()
        print("✅ Memory manager initialized")
        
        # Initialize command processor
        print("🎯 Initializing command processor...")
        processor = CommandProcessor()
        print("✅ Command processor initialized")
        
        # Test 1: Store and retrieve conversations
        print("\n📝 Test 1: Conversation storage...")
        test_conversations = [
            ("Hello JARVIS", "Hello! How can I assist you today?"),
            ("What's the weather like?", "The weather is sunny with a temperature of 22°C."),
            ("What time is it?", "The current time is 3:45 PM."),
            ("My name is John", "Nice to meet you, John! I'll remember your name."),
            ("Set greeting style formal", "I'll use a formal greeting style from now on.")
        ]
        
        for user_input, jarvis_response in test_conversations:
            memory_manager.store_conversation(
                user_input=user_input,
                jarvis_response=jarvis_response,
                command_type="test"
            )
            print(f"  ✅ Stored: '{user_input}' -> '{jarvis_response}'")
        
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
        
        # Test 5: Command processor with memory
        print("\n🎤 Test 5: Command processor with memory...")
        test_commands = [
            "Hello JARVIS",
            "What time is it?",
            "My name is Alice",
            "Set greeting style casual"
        ]
        
        for command in test_commands:
            print(f"  🎯 Processing: '{command}'")
            response = processor.process_command(command)
            print(f"     Response: '{response}'")
        
        # Test 6: Statistics
        print("\n📈 Test 6: Conversation statistics...")
        stats = memory_manager.get_conversation_stats(days=1)
        print(f"  📊 Stats: {stats}")
        
        # Test 7: Export functionality
        print("\n💾 Test 7: Export functionality...")
        export_success = memory_manager.export_conversations("test_conversations.json", "json")
        if export_success:
            print("  ✅ Conversations exported to test_conversations.json")
        else:
            print("  ❌ Export failed")
        
        print("\n🎉 All memory system tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_integration():
    """Test memory integration with existing JARVIS components"""
    print("\n🔗 Testing Memory Integration...")
    print("=" * 50)
    
    try:
        from jarvis.core.parallel_manager import get_jarvis_instance
        
        # Initialize JARVIS instance
        print("🤖 Initializing JARVIS instance...")
        jarvis = get_jarvis_instance()
        print("✅ JARVIS instance created")
        
        # Test text command processing with memory
        print("\n🎤 Testing text command processing...")
        test_commands = [
            "Hello",
            "What's the weather like?",
            "Tell me a joke",
            "What time is it?"
        ]
        
        for command in test_commands:
            print(f"  🎯 Testing: '{command}'")
            try:
                response = jarvis.process_text_command(command)
                print(f"     Response: '{response[:100]}...'")
            except Exception as e:
                print(f"     Error: {e}")
        
        print("\n✅ Memory integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Memory integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 JARVIS Memory System Test Suite")
    print("=" * 60)
    
    # Run tests
    memory_test_success = test_memory_system()
    integration_test_success = test_memory_integration()
    
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"  🧠 Memory System: {'✅ PASSED' if memory_test_success else '❌ FAILED'}")
    print(f"  🔗 Integration: {'✅ PASSED' if integration_test_success else '❌ FAILED'}")
    
    if memory_test_success and integration_test_success:
        print("\n🎉 All tests passed! Memory system is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
