KW = {
    'a': (1, 1),
    'b': (9, 2),
    'c': (5, 5),
    'd': (2, 3),
    'e': (8, 8),
}

# Extract thresholds

# first_elements = [v[0] for v in KW.values()]
# second_elements = [v[1] for v in KW.values()]

# first_threshold = sorted(first_elements)[len(first_elements) // 2]  # Middle of first elements
# second_threshold = sorted(second_elements)[len(second_elements) // 2]  # Middle of second elements

# print(f"First threshold: {first_threshold}")
# print(f"Second threshold: {second_threshold}")

# sorted_scores = dict(sorted(KW.items(), key=lambda x: (
# not (x[1][0] < first_threshold and x[1][1] < second_threshold), 
#     x[1][1],  #the first element
#     x[1][0]  #second element
# ), reverse=True))
import numpy as np

sorted_scores = dict(sorted(
    KW.items(),
    key=lambda x: np.sqrt(x[1][0] * x[1][1]),
    reverse=True
))

print(sorted_scores)