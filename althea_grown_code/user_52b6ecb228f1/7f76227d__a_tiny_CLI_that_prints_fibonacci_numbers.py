#!/usr/bin/env python3
import sys

def fibonacci(n):
    """Generate the first n Fibonacci numbers."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fibs = [0, 1]
    for i in range(2, n):
        fibs.append(fibs[-1] + fibs[-2])
    return fibs

def main():
    if len(sys.argv) < 2:
        print("Usage: python fibonacci_cli.py <count>")
        print("Example: python fibonacci_cli.py 10")
        sys.exit(1)
    
    try:
        count = int(sys.argv[1])
        if count < 0:
            print("Error: Please provide a non-negative integer")
            sys.exit(1)
        
        numbers = fibonacci(count)
        
        print(f"First {count} Fibonacci number(s):")
        for i, num in enumerate(numbers):
            print(f"F({i}) = {num}")
            
    except ValueError:
        print("Error: Please provide a valid integer")
        sys.exit(1)

if __name__ == "__main__":
    main()