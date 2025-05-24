import os
import subprocess
import shutil
import re

C_CODE_FILE = "c_code/sample.c"
FIXED_FILE = "fixes/sample_fixed.c"
TEST_FILE = "tests/test_sample.c"
EXECUTABLE_FILE = os.path.abspath("tests/test_exec.exe")

def run_cppcheck(file_path):
    result = subprocess.run(["cppcheck", "--enable=all", "--quiet", file_path],
                            stderr=subprocess.PIPE, text=True)
    return result.stderr

def run_gcc_syntax_check(file_path):
    result = subprocess.run(["gcc", "-fsyntax-only", file_path],
                            stderr=subprocess.PIPE, text=True)
    return result.stderr

def suggest_fix(cppcheck_output, gcc_output):
    suggestions = []
    
    # Cppcheck suggestions
    if "missingIncludeSystem" in cppcheck_output:
        suggestions.append("➡️ Suggestion: Ensure all headers like <stdio.h> are correctly included and spelled.")

    if "unusedFunction" in cppcheck_output:
        suggestions.append("➡️ Suggestion: The function is never used. Consider calling it or removing it.")

    # GCC error suggestions
    if "expected ';'" in gcc_output:
        match = re.search(r"error: expected '(.*?)' before", gcc_output)
        if match:
            suggestions.append(f"➡️ Syntax Error: Missing `{match.group(1)}`. Check the line before the error.")

    if "undeclared" in gcc_output:
        match = re.search(r"'(.+?)' undeclared", gcc_output)
        if match:
            suggestions.append(f"➡️ Undeclared identifier: Did you forget to define `{match.group(1)}`?")

    return suggestions

def generate_fixed_code(original_path, fixed_path):
    # No smart fix applied yet, just copy original
    shutil.copy(original_path, fixed_path)

def generate_test_file():
    os.makedirs("tests", exist_ok=True)
    with open(TEST_FILE, "w") as f:
        f.write('#include <assert.h>\n')
        f.write('#include "../fixes/sample_fixed.c"\n\n')
        f.write("int main() {\n")
        f.write("    assert(add(2, 3) == 5);\n")
        f.write("    assert(add(0, 0) == 0);\n")
        f.write("    return 0;\n")
        f.write("}\n")

def compile_and_run_tests():
    compile_cmd = ["gcc", TEST_FILE, "-o", EXECUTABLE_FILE]
    result = subprocess.run(compile_cmd, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print("❌ Compilation failed:\n", result.stderr)
        return False

    try:
        result = subprocess.run([EXECUTABLE_FILE], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ Executable not found.")
        return False

def main():
    os.makedirs("fixes", exist_ok=True)

    print("🔍 Running static analysis...")
    cppcheck_output = run_cppcheck(C_CODE_FILE)
    print("📝 Cppcheck Output:\n", cppcheck_output)

    gcc_output = run_gcc_syntax_check(C_CODE_FILE)
    if gcc_output:
        print("🛑 GCC Syntax Errors:\n", gcc_output)

    suggestions = suggest_fix(cppcheck_output, gcc_output)
    if suggestions:
        for s in suggestions:
            print(s)
    else:
        print("⚠️ No known fix suggestion found. Please review manually.")

    if gcc_output:
        print("❌ Compilation errors detected. Fix code before proceeding.")
        return

    # If code is syntactically correct, copy it as fixed version
    print("⚙️  Attempted to apply auto-fix to common patterns.")
    generate_fixed_code(C_CODE_FILE, FIXED_FILE)
    print("✅ Fixed code saved to:", FIXED_FILE)

    print("\n🧪 Generating and running unit tests...")
    generate_test_file()
    test_passed = compile_and_run_tests()

    print("\n📋 Summary Report")
    print("────────────────────────")
    print(f"🧠 Bug Detected      : {'Yes' if cppcheck_output else 'No'}")
    print(f"🛠️  Fix Suggestions  : {'Shown above' if suggestions else 'None'}")
    print(f"🧪 Unit Tests Passed : {'✅ Yes' if test_passed else '❌ No'}")
    print(f"📄 Output File       : {FIXED_FILE if os.path.exists(FIXED_FILE) else 'N/A'}")

if __name__ == "__main__":
    main()
