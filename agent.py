import os
import subprocess
import re
from typing import List

# File paths (using raw strings for Windows paths)
C_CODE_FILE = r"c_code\sample.c"
FIXED_FILE = r"fixes\sample_fixed.c"
TEST_FILE = r"tests\test_sample.c"
EXECUTABLE_FILE = os.path.abspath(r"tests\test_exec.exe")

def run_cppcheck(file_path: str) -> str:
    """Run static analysis using cppcheck."""
    print(f"🔍 Running cppcheck on {file_path}...")
    try:
        result = subprocess.run(
            ["cppcheck", "--enable=all", "--quiet", file_path],
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stderr
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Cppcheck warning: {e.stderr}")
        return e.stderr
    except FileNotFoundError:
        print("❌ Cppcheck not found. Please install it first.")
        exit(1)

def run_gcc_syntax_check(file_path: str) -> str:
    """Run GCC syntax-only check."""
    print(f"🔍 Running GCC syntax check on {file_path}...")
    try:
        result = subprocess.run(
            ["gcc", "-fsyntax-only", file_path],
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stderr
    except subprocess.CalledProcessError as e:
        return e.stderr
    except FileNotFoundError:
        print("❌ GCC not found. Please install it first.")
        exit(1)

def read_code() -> str:
    """Read original C source code."""
    if not os.path.exists(C_CODE_FILE):
        print(f"❌ Missing input file: {C_CODE_FILE}")
        print("Please create a 'c_code' folder and add sample.c")
        exit(1)
    
    with open(C_CODE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        if not content.strip():
            print("❌ The C file is empty")
            exit(1)
        return content

def send_to_mistral(c_code: str, cppcheck_output: str, gcc_output: str) -> str:
    """Send code and errors to local Mistral model via Ollama."""
    # Verify Ollama is running
    try:
        subprocess.run(["ollama", "--version"], 
                      check=True, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
    except:
        print("❌ Ollama not running! Please start it first with 'ollama serve'")
        exit(1)

    # Build the prompt safely
    prompt_parts = [
        "You are a C programming expert. Analyze this code:\n\n",
        "C CODE:\n```c\n", c_code, "\n```\n\n",
        "STATIC ANALYSIS (cppcheck):\n", cppcheck_output, "\n\n",
        "COMPILER ERRORS (gcc):\n", gcc_output, "\n\n",
        "Provide ONLY the corrected C code inside a code block (```c). "
        "Include all original code with fixes applied."
    ]
    prompt = "".join(prompt_parts)

    print("🤖 Querying Mistral (this may take a moment)...")
    try:
        result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding='utf-8',  # Add this
        errors='replace'   # Replace undecodable chars
)
        
        if result.returncode != 0:
            print(f"❌ Ollama error: {result.stderr}")
            exit(1)
        return result.stdout
    except subprocess.TimeoutExpired:
        print("❌ Ollama timed out after 2 minutes")
        exit(1)

def extract_fixed_code(response: str) -> str:
    """Extract fixed C code from LLM response."""
    # More robust pattern matching
    patterns = [
        r"```c\n(.*?)```",  # Standard code block
        r"```\n(.*?)```",    # Code block without language
        r"```(.*?)```"        # Most flexible
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            code = match.group(1).strip()
            if code:  # Verify we got actual code
                return code
    
    print("❌ No valid code block found in response")
    print("Debug: First 200 chars of response:")
    print(response[:200])
    exit(1)

def write_fixed_code(code: str):
    """Write corrected C code to the fixes folder."""
    os.makedirs("fixes", exist_ok=True)
    with open(FIXED_FILE, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"✅ Fixed code saved to: {FIXED_FILE}")

def generate_test_file():
    os.makedirs("tests", exist_ok=True)
    with open(TEST_FILE, "w") as f:
        f.write('#include <assert.h>\n')
        f.write('// Include only specific functions, not the entire file\n')
        f.write('int add(int a, int b); // Forward declaration\n\n')
        f.write('int test_main() {\n')  # Renamed from main()
        f.write('    assert(add(2, 3) == 5);\n')
        f.write('    assert(add(-1, 1) == 0);\n')
        f.write('    return 0;\n')
        f.write('}\n\n')
        f.write('int main() { return test_main(); }')  # Wrapper

def compile_and_run_tests() -> bool:
    """Compile and execute the test file."""
    print("🛠️ Compiling tests...")
    try:
        # Compile both files together
        compile_result = subprocess.run(
            ["gcc", TEST_FILE, FIXED_FILE, "-o", EXECUTABLE_FILE],
            stderr=subprocess.PIPE,
            text=True,
            timeout=30  # Added timeout
        )
        if compile_result.returncode != 0:
            print(f"❌ Compilation failed:\n{compile_result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Compilation error: {str(e)}")
        return False

    print("🚀 Running tests...")
    try:
        result = subprocess.run(
            [EXECUTABLE_FILE],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print(f"❌ Tests failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return False

def main():
    print("\n" + "="*50)
    print("🛠️ C Code Debugger Agent")
    print("="*50 + "\n")

    # 1. Analysis Phase
    print("\n=== PHASE 1: CODE ANALYSIS ===")
    c_code = read_code()
    cppcheck_output = run_cppcheck(C_CODE_FILE)
    gcc_output = run_gcc_syntax_check(C_CODE_FILE)
    
    if not cppcheck_output and not gcc_output:
        print("✅ No issues found by static analysis")
    else:
        print(f"⚠️  Analysis found issues:\n"
              f"Cppcheck: {len(cppcheck_output)} chars\n"
              f"GCC: {len(gcc_output)} chars")

    # 2. Fixing Phase
    print("\n=== PHASE 2: AI CODE FIXING ===")
    mistral_response = send_to_mistral(c_code, cppcheck_output, gcc_output)
    fixed_code = extract_fixed_code(mistral_response)
    write_fixed_code(fixed_code)

    # 3. Testing Phase
    print("\n=== PHASE 3: VALIDATION ===")
    generate_test_file()
    tests_passed = compile_and_run_tests()

    # Final Report
    print("\n" + "="*50)
    print("📋 FINAL REPORT")
    print("="*50)
    print(f"Static analysis issues: {'Yes' if cppcheck_output or gcc_output else 'No'}")
    print(f"AI fix generated: ✅ Success")
    print(f"Unit tests: {'✅ Passed' if tests_passed else '❌ Failed'}")
    print(f"\nFixed code location: {os.path.abspath(FIXED_FILE)}")

if __name__ == "__main__":
    main()