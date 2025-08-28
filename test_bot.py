"x = 'A' * 200" 
# Long line (style check will trigger)
foo = "x" * 200

# Function without docstring (docs check will trigger)
def my_function(x, y):
    return x + y

# Fake secret (security check will trigger)
AWS_SECRET_KEY = "AKIA1234567890ABCDE"
