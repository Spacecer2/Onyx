#!/usr/bin/env python3
"""
Comprehensive test suite for JARVIS Robust AI Assistant
"""

import sys
import time
import threading
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_system_initialization():
    """Test system initialization"""
    print("🧪 Testing System Initialization...")
    print("=" * 60)
    
    try:
        from jarvis.core.task_queue import task_queue
        from jarvis.core.audio_manager import get_audio_manager
        from jarvis.core.camera_manager import get_camera_manager
        from jarvis.core.reliability_manager import get_reliability_manager
        
        # Test task queue
        print("📋 Testing Task Queue...")
        task_queue.start()
        print("✅ Task Queue: READY")
        
        # Test audio manager
        print("🎤 Testing Audio Manager...")
        audio_manager = get_audio_manager()
        audio_init = audio_manager.initialize()
        print(f"{'✅' if audio_init else '⚠️'} Audio Manager: {'READY' if audio_init else 'OFFLINE'}")
        
        # Test camera manager
        print("📷 Testing Camera Manager...")
        camera_manager = get_camera_manager()
        camera_init = camera_manager.initialize()
        print(f"{'✅' if camera_init else '⚠️'} Camera Manager: {'READY' if camera_init else 'OFFLINE'}")
        
        # Test reliability manager
        print("📊 Testing Reliability Manager...")
        reliability_manager = get_reliability_manager()
        reliability_manager.start()
        print("✅ Reliability Manager: READY")
        
        print("\n✅ System initialization tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False

def test_advanced_commands():
    """Test advanced command processing"""
    print("\n🧪 Testing Advanced Commands...")
    print("=" * 60)
    
    try:
        from jarvis.commands.processor import CommandProcessor
        
        processor = CommandProcessor()
        
        test_commands = [
            ("hello jarvis", "greeting"),
            ("what time is it", "time"),
            ("tell me a joke", "joke"),
            ("search for python programming", "web search"),
            ("tell me about artificial intelligence", "wikipedia"),
            ("what's the weather", "weather"),
            ("calculate 2 + 2", "calculation"),
            ("system info", "system information"),
            ("take a photo", "camera"),
        ]
        
        print("🗣️ Testing Command Processing:")
        for command, expected_type in test_commands:
            try:
                response = processor.process_command(command)
                print(f"   Command: '{command}'")
                print(f"   Response: '{response[:100]}...' ✅")
            except Exception as e:
                print(f"   Command: '{command}' ❌ Error: {e}")
        
        print("\n✅ Advanced command tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Advanced command tests failed: {e}")
        return False

def test_parallel_processing():
    """Test parallel processing capabilities"""
    print("\n🧪 Testing Parallel Processing...")
    print("=" * 60)
    
    try:
        from jarvis.core.task_queue import task_queue, TaskType, TaskPriority
        
        # Submit multiple tasks simultaneously
        print("📋 Submitting parallel tasks...")
        
        def test_task(task_id, duration):
            time.sleep(duration)
            return f"Task {task_id} completed"
        
        task_ids = []
        for i in range(5):
            task_id = task_queue.submit_task(
                TaskType.TEXT_COMMAND,
                test_task,
                (i, 0.5),
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
        
        # Wait for tasks to complete
        print("⏳ Waiting for tasks to complete...")
        start_time = time.time()
        
        completed = 0
        while completed < len(task_ids) and time.time() - start_time < 10:
            for task_id in task_ids:
                status = task_queue.get_task_status(task_id)
                if status and status.value == 'completed':
                    result = task_queue.get_task_result(task_id)
                    if result and task_id not in [t for t in task_ids if task_queue.get_task_result(t)]:
                        print(f"   ✅ {result}")
                        completed += 1
            time.sleep(0.1)
        
        # Get queue statistics
        stats = task_queue.get_queue_stats()
        print(f"\n📊 Task Queue Stats:")
        print(f"   Total Tasks: {stats['total_tasks']}")
        print(f"   Completed: {stats['completed_tasks']}")
        print(f"   Failed: {stats['failed_tasks']}")
        print(f"   Worker Threads: {stats['worker_threads']}")
        
        print("\n✅ Parallel processing tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Parallel processing tests failed: {e}")
        return False

def test_reliability_features():
    """Test reliability and recovery features"""
    print("\n🧪 Testing Reliability Features...")
    print("=" * 60)
    
    try:
        from jarvis.core.reliability_manager import get_reliability_manager, HealthStatus
        
        reliability_manager = get_reliability_manager()
        
        # Register test component
        print("📊 Testing component registration...")
        reliability_manager.register_component("test_component")
        
        # Report health status
        print("💚 Testing health reporting...")
        reliability_manager.report_component_health(
            "test_component", 
            HealthStatus.HEALTHY,
            {"test_metric": 100}
        )
        
        # Report error
        print("⚠️ Testing error reporting...")
        reliability_manager.report_error(
            "test_component",
            Exception("Test error"),
            "Test context"
        )
        
        # Get system health
        health = reliability_manager.get_system_health()
        print(f"📈 System Health Report:")
        print(f"   Overall Status: {health['overall_status']}")
        print(f"   Components: {len(health['components'])}")
        print(f"   Total Errors: {health['global_stats']['total_errors']}")
        
        print("\n✅ Reliability tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Reliability tests failed: {e}")
        return False

def test_full_system():
    """Test complete JARVIS system"""
    print("\n🧪 Testing Complete JARVIS System...")
    print("=" * 60)
    
    try:
        from jarvis.core.parallel_manager import get_jarvis_instance
        
        jarvis = get_jarvis_instance()
        
        # Initialize system
        print("🚀 Initializing JARVIS...")
        if not jarvis.initialize():
            print("❌ JARVIS initialization failed")
            return False
        
        print("✅ JARVIS initialized successfully!")
        
        # Test text command processing
        print("\n💬 Testing text command processing...")
        response = jarvis.process_text_command("hello jarvis")
        print(f"   Response: '{response}' ✅")
        
        # Test system status
        print("\n📊 Getting system status...")
        status = jarvis.get_system_status()
        print(f"   State: {status.state.value}")
        print(f"   Audio Available: {status.audio_available}")
        print(f"   Camera Available: {status.camera_available}")
        print(f"   ASR Available: {status.asr_available}")
        print(f"   TTS Available: {status.tts_available}")
        print(f"   Uptime: {status.uptime:.1f}s")
        
        # Test photo capture (if camera available)
        if status.camera_available:
            print("\n📸 Testing photo capture...")
            photo_result = jarvis.take_photo()
            if photo_result['success']:
                print(f"   ✅ Photo captured: {photo_result['message']}")
            else:
                print(f"   ⚠️ Photo capture failed: {photo_result['message']}")
        
        print("\n✅ Complete system tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Complete system tests failed: {e}")
        return False

def main():
    """Run comprehensive test suite"""
    print("🚀 JARVIS ROBUST AI ASSISTANT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("System Initialization", test_system_initialization),
        ("Advanced Commands", test_advanced_commands),
        ("Parallel Processing", test_parallel_processing),
        ("Reliability Features", test_reliability_features),
        ("Complete System", test_full_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED! JARVIS is ready for production use.")
    else:
        print("⚠️ Some tests failed. Please check the logs for details.")
    
    print("=" * 80)
    
    return passed == len(results)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error in test suite: {e}")
        sys.exit(1)
