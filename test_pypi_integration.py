#!/usr/bin/env python3
"""
TBN Protocol PyPI Integration Test

Tests the published PyPI package to ensure it works correctly.
Run this script to verify the package installation and basic functionality.
"""

import sys
import subprocess
import tempfile
import os

def run_test():
    """Test the PyPI package in a clean environment."""
    
    print("🧪 TBN Protocol PyPI Integration Test")
    print("=" * 50)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Testing in: {temp_dir}")
        
        # Create a test script
        test_script = os.path.join(temp_dir, "test_tbn.py")
        with open(test_script, "w", encoding="utf-8") as f:
            f.write("""
# Test script for TBN Protocol PyPI package
import sys

try:
    # Test 1: Import the package
    print("Test 1: Importing tbn package...")
    import tbn
    print(f"   Version: {tbn.__version__}")
    print(f"   Author: {tbn.__author__}")
    
    # Test 2: Import TBNClient
    print("Test 2: Importing TBNClient...")
    from tbn import TBNClient
    
    # Test 3: Create a client instance
    print("Test 3: Creating TBNClient instance...")
    client = TBNClient(
        bot_name="PyPITestBot",
        bot_type="SEARCH",
        server="https://tbn.hardinai.co.uk"
    )
    print(f"   Client: {client}")
    
    # Test 4: Test client methods exist
    print("Test 4: Checking client methods...")
    methods = ['register', 'search', 'verify', 'handshake', 'certify', 'list_bots', 'stats']
    for method in methods:
        if hasattr(client, method):
            print(f"   OK {method}()")
        else:
            print(f"   MISSING {method}()")
            sys.exit(1)
    
    print("\\nAll tests passed! PyPI package is working correctly.")
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Test failed: {e}")
    sys.exit(1)
""")
        
        # Run the test script
        print("\n🚀 Running integration test...")
        try:
            result = subprocess.run([
                sys.executable, test_script
            ], capture_output=True, text=True, cwd=temp_dir)
            
            if result.returncode == 0:
                print(result.stdout)
                print("✅ PyPI integration test PASSED!")
                return True
            else:
                print("❌ PyPI integration test FAILED!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Failed to run test: {e}")
            return False

def check_pypi_package():
    """Check if the package is available on PyPI."""
    print("\n🔍 Checking PyPI package availability...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "show", "tbn-protocol"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ tbn-protocol package is installed")
            print(result.stdout)
            return True
        else:
            print("❌ tbn-protocol package not found")
            print("Run: pip install tbn-protocol")
            return False
            
    except Exception as e:
        print(f"❌ Error checking package: {e}")
        return False

if __name__ == "__main__":
    print("TBN Protocol PyPI Integration Test")
    print("This script tests the published PyPI package")
    print()
    
    # Check if package is installed
    if not check_pypi_package():
        print("\n💡 Installing tbn-protocol package...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "tbn-protocol"
            ], check=True)
            print("✅ Package installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install package")
            sys.exit(1)
    
    # Run the integration test
    if run_test():
        print("\n🎉 SUCCESS: PyPI package is ready for use!")
        print("\nQuick start:")
        print("  pip install tbn-protocol")
        print("  python -c \"from tbn import TBNClient; print('Ready!')\"")
    else:
        print("\n❌ FAILED: PyPI package has issues")
        sys.exit(1)