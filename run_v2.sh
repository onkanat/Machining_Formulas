#!/bin/bash
# Machining Formulas V2 Launcher
# This script ensures proper Python environment with tkinter support

echo "🔧 Machining Formulas V2 Launcher"
echo "=================================="

# Check for Python with tkinter support
echo "📋 Python environment check..."

# Try different Python versions
PYTHON_CMD=""
for py_cmd in "python3.11" "python3.10" "python3.9" "python3"; do
    if command -v $py_cmd >/dev/null 2>&1; then
        if $py_cmd -c "import tkinter" 2>/dev/null; then
            PYTHON_CMD=$py_cmd
            echo "✅ Found compatible Python: $($py_cmd --version)"
            echo "📍 Path: $(which $py_cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ ERROR: No Python with tkinter support found!"
    echo ""
    echo "🔧 Solutions:"
    echo "1. Install Python with tkinter:"
    echo "   - Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "   - macOS: brew install python-tk"
    echo "   - Or download from python.org"
    echo ""
    echo "2. Use conda environment:"
    echo "   conda install tk"
    echo ""
    echo "3. Use pyenv with proper Python build:"
    echo "   env PYTHON_CONFIGURE_OPTS='--with-tcltk' pyenv install 3.11.x"
    exit 1
fi

# Check if required modules are installed
echo ""
echo "📦 Checking required modules..."

REQUIRED_MODULES=("requests" "markdown")
MISSING_MODULES=()

for module in "${REQUIRED_MODULES[@]}"; do
    if ! $PYTHON_CMD -c "import $module" 2>/dev/null; then
        MISSING_MODULES+=($module)
    else
        echo "✅ $module"
    fi
done

if [ ${#MISSING_MODULES[@]} -ne 0 ]; then
    echo ""
    echo "❌ Missing modules: ${MISSING_MODULES[*]}"
    echo "📦 Installing missing modules..."
    
    # Try to install missing modules
    if [ -f "requirements_v2.txt" ]; then
        $PYTHON_CMD -m pip install -r requirements_v2.txt
    else
        $PYTHON_CMD -m pip install "${MISSING_MODULES[@]}"
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install required modules"
        exit 1
    fi
fi

echo ""
echo "🚀 Starting Machining Formulas V2..."
echo "📍 Using: $PYTHON_CMD"
echo "📁 Working directory: $(pwd)"
echo ""

# Launch V2 GUI
$PYTHON_CMD v2_gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Failed to start V2 GUI"
    echo "🔧 Troubleshooting:"
    echo "1. Check if v2_gui.py exists in current directory"
    echo "2. Verify all dependencies are installed"
    echo "3. Check Python version compatibility"
    exit 1
fi

echo ""
echo "✅ V2 GUI closed successfully"