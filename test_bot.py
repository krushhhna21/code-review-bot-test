# Intentionally bad code to trigger the Code Review Bot

foo = "x" * 200  # super long line (>120)

def bad_func(a, b):  # missing docstring
	return a + b  # uses a tab for indentation (PEP8 violation)

# Fake secret patterns
AWS_SECRET_KEY = "AKIA1234567890ABCDE"
API_KEY = "api_key=abcdefghijklmnop1234"

def very_complex(n):  # missing docstring + complexity > default threshold
    total = 0
    for i in range(n):
        if i % 2 == 0:
            total += i
        else:
            total -= i
        if i % 3 == 0:
            total *= 2
        if i % 5 == 0:
            total //= 2
        if i % 7 == 0:
            total += 7
        if i % 11 == 0:
            total -= 11
    return total
