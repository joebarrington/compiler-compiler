import os
import sys
import time
from pathlib import Path
from generated_parser.generated_parser import GeneratedParser


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ERROR_FILES = [
    "invalid_test"
]

def test_parser(file_path, expect_error=False):
    parsing_time = 0
    try:
        with open(file_path, 'r') as file:
            code = file.read()
        
        print(f"Testing file: {file_path}")
        parser = GeneratedParser(code)
        
        start_time = time.perf_counter()
        result = parser.parse()
        end_time = time.perf_counter()
        parsing_time = end_time - start_time
        
        print(f"Parsing time: {parsing_time:.4f} seconds")
        
        if expect_error:
            print(f"UNEXPECTED SUCCESS: File {file_path} was expected to fail but parsed successfully")
            return False, parsing_time
        else:
            print(f"SUCCESS: File {file_path} parsed as expected")
            return True, parsing_time
            
    except SyntaxError as e:
        if not 'start_time' in locals():
            parsing_time = 0
        else:
            end_time = time.perf_counter()
            parsing_time = end_time - start_time
            print(f"Parsing time until error: {parsing_time:.4f} seconds")
            
        if expect_error:
            print(f"SUCCESS: File {file_path} failed with expected syntax error: {str(e)[:100]}...")
            return True, parsing_time
        else:
            print(f"UNEXPECTED FAILURE: File {file_path} failed with syntax error: {str(e)[:100]}...")
            return False, parsing_time
            
    except Exception as e:
        if not 'start_time' in locals():
            parsing_time = 0
        else:
            end_time = time.perf_counter()
            parsing_time = end_time - start_time
            print(f"Parsing time until error: {parsing_time:.4f} seconds")
            
        if expect_error:
            print(f"SUCCESS: File {file_path} failed with expected error: {str(e)[:100]}...")
            return True, parsing_time
        else:
            print(f"UNEXPECTED FAILURE: File {file_path} failed with error: {str(e)[:100]}...")
            return False, parsing_time

def test_all_files(directory):
    results = {
        "expected_success_correct": 0,
        "expected_success_wrong": 0,
        "expected_error_correct": 0,
        "expected_error_wrong": 0
    }
    
    parsing_times = []
    
    test_files = list(Path(directory).glob('**/*.txt'))

    
    print(f"Found {len(test_files)} test files to test")
    print("-" * 60)
    
    for file_path in test_files:
        file_name = file_path.stem
        expect_error = any(error_pattern in file_name for error_pattern in ERROR_FILES)
        
        success, parsing_time = test_parser(file_path, expect_error)
        parsing_times.append(parsing_time)
        
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
    
    total = len(test_files)
    correct = results["expected_success_correct"] + results["expected_error_correct"]
    
    print("\nTEST SUMMARY:")
    print(f"Total files tested: {total}")
    print(f"Files expected to pass and did: {results['expected_success_correct']}")
    print(f"Files expected to pass but failed: {results['expected_success_wrong']}")
    print(f"Files expected to fail and did: {results['expected_error_correct']}")
    print(f"Files expected to fail but passed: {results['expected_error_wrong']}")
    
    if parsing_times:
        avg_parsing_time = sum(parsing_times) / len(parsing_times)
        max_parsing_time = max(parsing_times)
        min_parsing_time = min(parsing_times)
        print(f"Average parsing time: {avg_parsing_time:.7f} seconds")
        print(f"Maximum parsing time: {max_parsing_time:.7f} seconds")
        print(f"Minimum parsing time: {min_parsing_time:.7f} seconds")
    
    return results, parsing_times

if __name__ == "__main__":
    test_dir = sys.argv[1] if len(sys.argv) > 1 else "test_files"
    results, parsing_times = test_all_files(test_dir)