import os
import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import the parser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your generated parser
from generated_parser import GeneratedParser

# Define which files are expected to have errors
ERROR_FILES = [
    "EofInComment", "EofInStr", "IllegalSymbol", "NewLineInStr", "OnlyComments", "Empty"
]

def test_parser(file_path, expect_error=False):
    """Test the parser on a file and check if the result matches expectations."""
    try:
        with open(file_path, 'r') as file:
            code = file.read()
        
        print(f"Testing file: {file_path}")
        parser = GeneratedParser(code)
        result = parser.parse()
        
        if expect_error:
            print(f"UNEXPECTED SUCCESS: File {file_path} was expected to fail but parsed successfully")
            return False
        else:
            print(f"SUCCESS: File {file_path} parsed as expected")
            return True
            
    except SyntaxError as e:
        if expect_error:
            print(f"SUCCESS: File {file_path} failed with expected syntax error: {str(e)[:100]}...")
            return True
        else:
            print(f"UNEXPECTED FAILURE: File {file_path} failed with syntax error: {str(e)[:100]}...")
            return False
            
    except Exception as e:
        if expect_error:
            print(f"SUCCESS: File {file_path} failed with expected error: {str(e)[:100]}...")
            return True
        else:
            print(f"UNEXPECTED FAILURE: File {file_path} failed with error: {str(e)[:100]}...")
            return False

def test_all_files(directory):
    """Test all .jack files in the specified directory."""
    results = {
        "expected_success_correct": 0,
        "expected_success_wrong": 0,
        "expected_error_correct": 0,
        "expected_error_wrong": 0
    }
    
    # Get all .jack files
    jack_files = list(Path(directory).glob('**/*.jack'))
    
    print(f"Found {len(jack_files)} Jack files to test")
    print("-" * 60)
    
    for file_path in jack_files:
        file_name = file_path.stem
        expect_error = any(error_pattern in file_name for error_pattern in ERROR_FILES)
        
        success = test_parser(file_path, expect_error)
        
        if expect_error:
            if success:
                results["expected_error_correct"] += 1
            else:
                results["expected_error_wrong"] += 1
        else:
            if success:
                results["expected_success_correct"] += 1
            else:
                results["expected_success_wrong"] += 1
                
        print("-" * 60)
    
    # Print summary
    total = len(jack_files)
    correct = results["expected_success_correct"] + results["expected_error_correct"]
    
    print("\nTEST SUMMARY:")
    print(f"Total files tested: {total}")
    print(f"Files that behaved as expected: {correct} ({correct/total*100:.1f}%)")
    print(f"Files that did not behave as expected: {total - correct} ({(total-correct)/total*100:.1f}%)")
    print("\nDETAILED RESULTS:")
    print(f"Files expected to pass and did: {results['expected_success_correct']}")
    print(f"Files expected to pass but failed: {results['expected_success_wrong']}")
    print(f"Files expected to fail and did: {results['expected_error_correct']}")
    print(f"Files expected to fail but passed: {results['expected_error_wrong']}")
    
    return results

if __name__ == "__main__":
    test_dir = sys.argv[1] if len(sys.argv) > 1 else "test_files"
    test_all_files(test_dir)