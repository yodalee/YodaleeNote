import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
import sympy as sp

# define polynomial
# coefficients for 1 - 2x - 3x^2 + x^3
poly = np.polynomial.Polynomial([2, -2, -3, 1])
print(poly)

# generate x range for smooth curve
x = np.linspace(-2, 3, 400)
y = poly(x)

# points to highlight
points_x = np.array([-1, 0, 1, 2])
points_y = poly(points_x)

# create plot
plt.figure(figsize=(6, 4))
plt.plot(x, y, label=f"f(x) = {poly}")
plt.scatter(points_x, points_y, zorder=5)

# annotate points
for px, py in zip(points_x, points_y):
    print(f"({px}, {py})", end=" ")
    plt.annotate(f"({px}, {py})", (px, py),
                 textcoords="offset points",
                 xytext=(5, 5))
print()

# labels and grid
plt.xlabel("x")
plt.ylabel("f(x)")
plt.axhline(y=0, linewidth=2, color='black')  # x-axis
plt.axvline(x=0, linewidth=2, color='black')  # y-axis
plt.grid(True)
plt.legend()

# save to png
plt.savefig("function_plot.png", dpi=300, bbox_inches="tight")

# First example
points_x = [-1, 0, 1, 2, 3, 4]
print([(x, int(poly(x))) for x in points_x])

print("=========================================")

# Print the combination of received code
# Note that we modify the points 
l = [(-1, 0), (0, 2), (1, -2), (2, 1), (3, -4), (4, 10)]
for p in combinations(l, 4):
    c0, c1, c2, c3 = sp.symbols('c0 c1 c2 c3')
    # 建立方程式
    eqs = [
        c0 + c1*p[i][0] + c2*p[i][0]**2 + c3*p[i][0]**3 - p[i][1]
        for i in range(4)
    ]
    sol = sp.solve(eqs, (c0, c1, c2, c3))
    print(f"{p} -> {sol}")

print("=========================================")

p = [(-1,2),(0,-2),(1,-3),(2,1)]
c0, c1, c2, c3 = sp.symbols('c0 c1 c2 c3')
eqs = [
    c0 + c1*p[i][0] + c2*p[i][0]**2 + c3*p[i][0]**3 - p[i][1]
    for i in range(4)
]
sol = sp.solve(eqs, (c0, c1, c2, c3))
print(f"{p} -> {sol}")
poly = np.polynomial.Polynomial([sol[c0], sol[c1], sol[c2], sol[c3]])
print(f"poly(3) = {poly(3)}")
print(f"poly(4) = {poly(4)}")

print("=========================================")

# multiply by x^2
nom = np.polynomial.Polynomial([0, 0, 2, -2, -3, 1])
denom = np.polynomial.Polynomial([2, -3, 1])

quatient = nom // denom
remainder = nom % denom
print(f"Quotient: {quatient}")
print(f"Remainder: {remainder}")
