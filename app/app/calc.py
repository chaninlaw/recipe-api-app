"""
Calculator functions
"""

def add(x: int, y: int):
  """Add two numbers together."""
  if (type(x) != int) or (type(y) != int):
    print("Warning: Both arguments must be integers.")
    return 0
  
  return x + y


def subtract(x: int, y: int,):
  """Subtract two numbers together."""
  if (type(x) != int) or (type(y) != int):
    print("Warning: Both arguments must be integers.")
    return 0
  
  return x - y