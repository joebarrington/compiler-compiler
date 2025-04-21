import os
import sys
import time
from pathlib import Path
import psutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated_parser import GeneratedParser

ERROR_FILES = [
    "EofInComment", "EofInStr", "IllegalSymbol", "NewLineInStr", "OnlyComments", "Empty"
]

def test_parser(file_path, expect_error=False):
    parser_creation_time = 0
    parsing_time = 0
    
    try:
        with open(file_path, 'r') as file:
            code = file.read()
        
        print(f"Testing file: {file_path}")
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / (1024 * 1024)
        
        parser_start_time = time.time()
        parser = GeneratedParser(code)
        parser_end_time = time.time()
        parser_creation_time = parser_end_time - parser_start_time
        
        parsing_start_time = time.time()
        result = parser.parse()
        parsing_end_time = time.time()
        parsing_time = parsing_end_time - parsing_start_time
        
        memory_after = process.memory_info().rss / (1024 * 1024)
        memory_used = memory_after - memory_before
        
        print(f"Parser creation time: {parser_creation_time:.4f} seconds")
        print(f"Parsing time: {parsing_time:.4f} seconds")
        print(f"Memory usage: {memory_used:.2f} MB")
        
        if expect_error:
            print(f"UNEXPECTED SUCCESS: File {file_path} was expected to fail but parsed successfully")
            return False, parser_creation_time, parsing_time, memory_used
        else:
            print(f"SUCCESS: File {file_path} parsed as expected")
            return True, parser_creation_time, parsing_time, memory_used
            
    except Exception as e:
        try:
            memory_after = process.memory_info().rss / (1024 * 1024)
            memory_used = memory_after - memory_before
        except:
            memory_used = 0.0
            
        error_message = str(e)
        is_syntax_error = isinstance(e, SyntaxError)
        
        print(f"{'Parsing' if parsing_time > 0 else 'Setup'} time until error: {parser_creation_time:.4f} seconds")
        print(f"Memory usage: {memory_used:.2f} MB")
        
        if expect_error:
            print(f"SUCCESS: File {file_path} failed with expected {'syntax ' if is_syntax_error else ''}error: {error_message[:100]}...")
            return True, parser_creation_time, parsing_time, memory_used
        else:
            print(f"UNEXPECTED FAILURE: File {file_path} failed with {'syntax ' if is_syntax_error else ''}error: {error_message[:100]}...")
            return False, parser_creation_time, parsing_time, memory_used

def test_all_files(directory):
    results = {
        "expected_success_correct": 0,
        "expected_success_wrong": 0,
        "expected_error_correct": 0,
        "expected_error_wrong": 0
    }
    
    performance_data = {
        "parser_creation_times": [],
        "parsing_times": [],
        "memory_usage": []
    }
    
    jack_files = list(Path(directory).glob('**/*.jack'))
    
    print(f"Found {len(jack_files)} Jack files to test")
    print("-" * 60)
    
    for file_path in jack_files:
        file_name = file_path.stem
        expect_error = any(error_pattern in file_name for error_pattern in ERROR_FILES)
        
        success, parser_time, parsing_time, memory = test_parser(file_path, expect_error)
        
        performance_data["parser_creation_times"].append(parser_time)
        performance_data["parsing_times"].append(parsing_time)
        performance_data["memory_usage"].append(memory)
        
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
    
    print("\nPERFORMANCE METRICS:")
    print(f"Average parser creation time: {sum(performance_data['parser_creation_times'])/len(performance_data['parser_creation_times']):.4f} seconds")
    print(f"Average parsing time: {sum(performance_data['parsing_times'])/len(performance_data['parsing_times']):.4f} seconds")
    print(f"Average memory usage: {sum(performance_data['memory_usage'])/len(performance_data['memory_usage']):.2f} MB")
    print(f"Maximum memory usage: {max(performance_data['memory_usage']):.2f} MB")
    
    return results, performance_data

if __name__ == "__main__":
    test_dir = sys.argv[1] if len(sys.argv) > 1 else "test_files"
    test_all_files(test_dir)