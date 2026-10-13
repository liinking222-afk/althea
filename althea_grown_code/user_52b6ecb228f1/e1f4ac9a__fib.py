def fibonacci(n):
    """Generate and print the first n Fibonacci numbers."""
    if n <= 0:
        return
    
    a, b = 0, 1
    for i in range(n):
        print(a)
        a, b = b, a + b

if __name__ == "__main__":
    fibonacci(10)