from autoalpha.tools.code_execute import execute_code


code = """
import random
print(random.randint(1,3))
"""
run_code, run_results, _ = execute_code(code)