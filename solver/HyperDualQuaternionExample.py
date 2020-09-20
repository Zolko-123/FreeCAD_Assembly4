from HyperDual import HyperDualQuaternion


q0 = HyperDualQuaternion(-0.007596123493895969, 0.08682408883346517,  0.08682408883346515, 0.9924038765061041)
q2 = HyperDualQuaternion(10, 0, 0, 0)
q1 = q0@q2@q0**-1

print(q1)
print(q0**-1@q1@q0 - q2)
