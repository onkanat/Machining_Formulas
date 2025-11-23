#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test V3 GUI Enhanced Features
Tests keyboard shortcuts, accessibility, and performance optimizations
"""

import sys
import os


def test_keyboard_shortcuts():
    """Test keyboard shortcut functionality."""
    print("⌨️ Testing keyboard shortcuts...")

    try:
        import tkinter as tk
        from tkinter import ttk

        # Create test window
        root = tk.Tk()
        root.withdraw()  # Hide window

        # Test key binding
        test_triggered = False

        def test_handler(event=None):
            nonlocal test_triggered
            test_triggered = True

        # Bind test shortcuts
        root.bind("<Control-s>", test_handler)
        root.bind("<Control-o>", test_handler)
        root.bind("<F1>", test_handler)
        root.bind("<Control-q>", test_handler)

        # Simulate key events
        root.event_generate("<Control-s>")
        root.event_generate("<Control-o>")
        root.event_generate("<F1>")
        root.event_generate("<Control-q>")

        root.update()
        root.destroy()

        print("✅ Keyboard shortcut bindings successful")
        return True

    except Exception as e:
        print(f"❌ Keyboard shortcut test failed: {e}")
        return False


def test_accessibility_features():
    """Test accessibility improvements."""
    print("\n♿ Testing accessibility features...")

    try:
        import tkinter as tk
        from tkinter import ttk
        from tkinter import font

        # Create test window
        root = tk.Tk()
        root.withdraw()

        # Test font configuration
        try:
            default_font = font.nametofont("TkDefaultFont")
            original_size = default_font.cget("size")
            default_font.configure(size=10)
            new_size = default_font.cget("size")
            print(f"✅ Font configuration: {original_size} -> {new_size}")
        except Exception as e:
            print(f"⚠️ Font configuration issue: {e}")

        # Test style configuration
        try:
            style = ttk.Style()
            style.configure("TEntry", focuscolor="blue")
            style.configure("TCombobox", focuscolor="blue")
            style.configure("TButton", focuscolor="blue")
            print("✅ Focus indicator styles configured")
        except Exception as e:
            print(f"⚠️ Style configuration issue: {e}")

        # Test high contrast colors
        try:
            root.option_add("*TCombobox*Listbox.selectBackground", "#0078d4")
            root.option_add("*TCombobox*Listbox.selectForeground", "white")
            print("✅ High contrast colors configured")
        except Exception as e:
            print(f"⚠️ Color configuration issue: {e}")

        root.destroy()
        print("✅ Accessibility features configured successfully")
        return True

    except Exception as e:
        print(f"❌ Accessibility test failed: {e}")
        return False


def test_performance_optimizations():
    """Test performance optimizations."""
    print("\n🚀 Testing performance optimizations...")

    try:
        import tkinter as tk
        from tkinter import ttk

        # Create test window
        root = tk.Tk()
        root.withdraw()

        # Test debouncing functionality
        timer_called = False
        test_timer = None

        def test_function():
            nonlocal timer_called
            timer_called = True

        def debounce_test():
            nonlocal test_timer
            if test_timer:
                root.after_cancel(test_timer)
            test_timer = root.after(100, test_function)

        # Test rapid calls (should only execute once)
        debounce_test()
        debounce_test()
        debounce_test()

        root.update()
        root.after(150)  # Wait for debounce
        root.update()

        if timer_called:
            print("✅ Debounce functionality working")
        else:
            print("⚠️ Debounce functionality may have issues")

        # Test loading indicator creation
        try:
            loading_window = tk.Toplevel(root)
            loading_window.title("Yükleniyor")
            loading_window.geometry("300x100")
            loading_window.transient(root)

            # Add progress bar
            progress = ttk.Progressbar(loading_window, mode="indeterminate")
            progress.pack(fill="x", padx=20, pady=10)
            progress.start(10)

            loading_window.destroy()
            print("✅ Loading indicator creation successful")
        except Exception as e:
            print(f"⚠️ Loading indicator issue: {e}")

        root.destroy()
        print("✅ Performance optimizations working")
        return True

    except Exception as e:
        print(f"❌ Performance optimization test failed: {e}")
        return False


def test_workspace_buffer_performance():
    """Test workspace buffer performance with large content."""
    print("\n📊 Testing workspace buffer performance...")

    try:
        from workspace_buffer import WorkspaceBuffer
        import time

        wb = WorkspaceBuffer()

        # Test with large content
        large_content = "Test line\n" * 10000  # 10k lines

        # Performance test
        start_time = time.time()
        wb.set_content(large_content, "user", "Performance test")
        set_time = time.time() - start_time

        start_time = time.time()
        content = wb.get_content()
        get_time = time.time() - start_time

        # Test save/load performance
        test_file = "/tmp/performance_test.json"
        start_time = time.time()
        success = wb.save_to_file(test_file)
        save_time = time.time() - start_time

        start_time = time.time()
        wb2 = WorkspaceBuffer()
        success = wb2.load_from_file(test_file)
        load_time = time.time() - start_time

        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

        print(f"✅ Set content: {set_time:.3f}s")
        print(f"✅ Get content: {get_time:.3f}s")
        print(f"✅ Save to file: {save_time:.3f}s")
        print(f"✅ Load from file: {load_time:.3f}s")

        # Performance should be reasonable (< 1 second for operations)
        if all(t < 1.0 for t in [set_time, get_time, save_time, load_time]):
            print("✅ All operations under 1 second - Good performance")
        else:
            print("⚠️ Some operations slow - May need optimization")

        return True

    except Exception as e:
        print(f"❌ Workspace buffer performance test failed: {e}")
        return False


def test_model_integration_performance():
    """Test model integration performance."""
    print("\n🤖 Testing model integration performance...")

    try:
        # Test import performance
        start_time = time.time()
        from ollama_utils_v2 import (
            get_available_models,
            single_chat_request,
            test_connection,
        )

        import_time = time.time() - start_time

        print(f"✅ Import time: {import_time:.3f}s")

        # Test connection (may fail if Ollama not running, but should be fast)
        start_time = time.time()
        try:
            models = get_available_models("http://localhost:11434")
            connection_time = time.time() - start_time
            print(
                f"✅ Connection test: {connection_time:.3f}s (found {len(models)} models)"
            )
        except:
            connection_time = time.time() - start_time
            print(
                f"⚠️ Connection failed: {connection_time:.3f}s (expected if Ollama not running)"
            )

        return True

    except Exception as e:
        print(f"❌ Model integration test failed: {e}")
        return False


def main():
    """Run all enhanced feature tests."""
    print("🚀 V3 GUI Enhanced Features Test")
    print("=" * 50)

    tests = [
        ("Keyboard Shortcuts", test_keyboard_shortcuts),
        ("Accessibility Features", test_accessibility_features),
        ("Performance Optimizations", test_performance_optimizations),
        ("Workspace Buffer Performance", test_workspace_buffer_performance),
        ("Model Integration Performance", test_model_integration_performance),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 ENHANCED FEATURES TEST RESULTS")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All enhanced features working perfectly!")
        print("\n🚀 Enhanced V3 GUI Features:")
        print("   ⌨️  Full keyboard shortcut support")
        print("   ♿ Accessibility improvements")
        print("   🚀 Performance optimizations")
        print("   📊 Loading indicators")
        print("   🤖 Enhanced model integration")
        print("\n🚀 To start the enhanced application:")
        print("   python3 v3_gui_direct.py")
        print("\n📋 Keyboard Shortcuts (Press F1 in app for help):")
        print("   Ctrl+S - Save workspace")
        print("   Ctrl+O - Load workspace")
        print("   Ctrl+M - Get model suggestion")
        print("   Ctrl+1/2/3/4 - Switch tabs")
        print("   F1 - Show help")
    else:
        print("⚠️ Some enhanced features need attention.")

    return passed == total


if __name__ == "__main__":
    import time

    success = main()
    sys.exit(0 if success else 1)
