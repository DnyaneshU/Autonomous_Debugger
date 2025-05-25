import os
import subprocess
import shutil
import re
from typing import List, Optional

# Define file paths as constants
C_CODE_FILE = "c_code/sample.c"
FIXED_FILE = "fixes/sample_fixed.c"
TEST_FILE = "tests/test_sample.c"
EXECUTABLE_FILE = os.path.abspath("tests/test_exec.exe")


def run_cppcheck(file_path: str) -> str:
    """
    Run cppcheck static analyzer on the given C source file.
    
    Args:
        file_path (str): Path to the C source file.
        
    Returns:
        str: The stderr output from cppcheck containing warnings/errors.
    """
    result = subprocess.run(
        ["cppcheck", "--enable=all", "--quiet", file_path],
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    return result.stderr


def run_gcc_syntax_check(file_path: str) -> str:
    """
    Run GCC compiler syntax check on the given C source file.
    
    Args:
        file_path (str): Path to the C source file.
        
    Returns:
        str: The stderr output from GCC containing syntax errors.
    """
    result = subprocess.run(
        ["gcc", "-fsyntax-only", file_path],
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    return result.stderr


def suggest_fix(cppcheck_output: str, gcc_output: str) -> List[str]:
    """
    Generate fix suggestions based on cppcheck and gcc outputs.
    
    Args:
        cppcheck_output (str): Output from cppcheck static analysis.
        gcc_output (str): Output from gcc syntax check.
        
    Returns:
        List[str]: List of human-readable suggestions.
    """
    suggestions = []

    # Cppcheck suggestions
    if "missingIncludeSystem" in cppcheck_output:
        suggestions.append("➡️ Suggestion: Ensure all system headers like <stdio.h> are included and correctly spelled.")

    if "unusedFunction" in cppcheck_output:
        suggestions.append("➡️ Suggestion: Function defined but never used; consider removing or invoking it.")

    # GCC error suggestions
    if "expected ';'" in gcc_output:
        match = re.search(r"error: expected '(.*?)' before", gcc_output)
        if match:
            suggestions.append(f"➡️ Syntax Error: Missing `{match.group(1)}`; check preceding line for missing delimiter.")

    if "undeclared" in gcc_output:
        match = re.search(r"'(.+?)' undeclared", gcc_output)
        if match:
            suggestions.append(f"➡️ Undeclared identifier: `{match.group(1)}` might be undefined or missing a declaration.")

    return suggestions


def generate_fixed_code(original_path: str, fixed_path: str) -> None:
    """
    Copy original source code to fixed code path.
    Placeholder for future smart fix implementation.
    
    Args:
        original_path (str): Path to original source code.
        fixed_path (str): Destination path for fixed code.
    """
    shutil.copyfile(original_path, fixed_path)


def generate_test_file() -> None:
    """
    Generate a simple unit test file for the fixed source code.
    Creates the tests directory if it does not exist.
    """
    os.makedirs("tests", exist_ok=True)
    with open(TEST_FILE, "w") as f:
        f.write('#include <assert.h>\n')
        f.write('#include "../fixes/sample_fixed.c"\n\n')
        f.write("int main() {\n")
        f.write("    assert(add(2, 3) == 5);\n")
        f.write("    assert(add(0, 0) == 0);\n")
        f.write("    return 0;\n")
        f.write("}\n")


def compile_and_run_tests() -> bool:
    """
    Compile the generated test file and run the resulting executable.
    
    Returns:
        bool: True if tests pass (exit code 0), False otherwise.
    """
    compile_cmd = ["gcc", TEST_FILE, "-o", EXECUTABLE_FILE]
    compile_result = subprocess.run(compile_cmd, stderr=subprocess.PIPE, text=True)

    if compile_result.returncode != 0:
        print(f"❌ Compilation failed:\n{compile_result.stderr}")
        return False

    try:
        test_result = subprocess.run([EXECUTABLE_FILE], capture_output=True)
        return test_result.returncode == 0
    except FileNotFoundError:
        print("❌ Executable not found. Test run aborted.")
        return False


def main() -> None:
    """
    Main workflow: runs static analysis, suggests fixes, attempts basic auto-fix,
    generates and runs unit tests, then summarizes results.
    """
    os.makedirs("fixes", exist_ok=True)

    print("🔍 Running static analysis with cppcheck...")
    cppcheck_output = run_cppcheck(C_CODE_FILE)
    if cppcheck_output:
        print("📝 Cppcheck output:\n", cppcheck_output)
    else:
        print("✅ No issues found by cppcheck.")

    print("🔍 Running GCC syntax check...")
    gcc_output = run_gcc_syntax_check(C_CODE_FILE)
    if gcc_output:
        print("🛑 GCC syntax errors:\n", gcc_output)
    else:
        print("✅ GCC syntax check passed without errors.")

    suggestions = suggest_fix(cppcheck_output, gcc_output)
    if suggestions:
        print("\n💡 Suggested fixes:")
        for suggestion in suggestions:
            print(suggestion)
    else:
        print("\n⚠️ No fix suggestions generated. Manual review recommended.")

    if gcc_output:
        print("\n❌ Compilation errors detected. Please fix errors before proceeding.")
        return

    print("\n⚙️ Applying auto-fix (currently copies original code)...")
    generate_fixed_code(C_CODE_FILE, FIXED_FILE)
    print(f"✅ Fixed code saved to: {FIXED_FILE}")

    print("\n🧪 Generating and running unit tests...")
    generate_test_file()
    tests_passed = compile_and_run_tests()

    print("\n📋 Summary Report")
    print("────────────────────────")
    print(f"🧠 Bugs detected       : {'Yes' if cppcheck_output else 'No'}")
    print(f"🛠️ Fix suggestions     : {'Available' if suggestions else 'None'}")
    print(f"🧪 Unit tests passed   : {'✅ Yes' if tests_passed else '❌ No'}")
    print(f"📄 Fixed code location : {FIXED_FILE if os.path.exists(FIXED_FILE) else 'N/A'}")


if __name__ == "__main__":
    main()
