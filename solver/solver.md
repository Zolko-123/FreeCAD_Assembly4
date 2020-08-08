# Hyper Dual Numbers
I mostly followed this [paper](http://adl.stanford.edu/hyperdual/Fike_AIAA-2011-886.pdf) to implement hyper dual numbers. I made some modifications in order to be able to get the gradient and the hessian using numpy arrays. I am not sure if the modifications I made are the most efficient or even if they work on all cases; however, so far the optimization algorithms seem to work well using my implementation of hyper dual numbers. *HyperDualExample.py*  is a small test I made comparing hyper dual numbers with discrete gradient and hessian functions. The examples follow scipy.optimize [page](https://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html#sequential-least-squares-programming-slsqp-algorithm-method-slsqp). The results I got is that using hyper dual numbers is around 2 times slower than using discrete functions. 

In order to be able to use dual numbers and scipy.minimize I used objects instead of functions. In essence, the object has 2 properties and 3 methods. The first property is an array of hyper dual numbers that represent each variable. The second property is an hyper dual number representing the evaluation of the function. The first method, is an evaluation of the function that has as input a numpy array. This method first assigns the values of each element in the input array into the real values of each hyper dual number in the object's property. Then, it evaluates the function, puts the result on the corresponding property and finally returns the real value of the resulting hyper dual number. While the function is evaluated, we obtain the gradient and the hessian automatically, they are stored in the object's property containing the value of the function. The other two methods just return the gradient and the hessian matrices when they are called since their values are already known. Here is an example of the class:

```python

class Function:
    def __init__(self, hyper_dual_array):
        self.hp = hyper_dual_array
        self.val = None
   
   def function(self, x):
        # Assings the values of input array into array of hyper duals
        for i in range(x.shape[0]):
            self.hp[i].real = x[i]
        # Function is evaluated (here we sum the squares of all the variables)
        self.val = sum(self.hp**2)
        return self.val.real
        
    def grad(self, x):
        # Returns the gradient 
        # x is a dummy variable since we don't need it, 
        # but the minimize function expects us to use it 
        return self.val.grad
        
    def hess(self, x):
        # Same than with the grad method
        return self.val.hess
            
```

The next problem is to get the vector x which represents all the placement components in the assembly (position coordinates and rotation angles). The components in the vector x have to be unique placement components. For example, the x-component of the placement of a part can't be twice in the vector x. So the first step is to use a set to get the unique variables. And then to construct 3 lists based with the number of independent variables. The first list contains constriant functions. The second list contains all the independent variables in hyperdual form. And the last list is similar to the second, but it contains the names of all the variables so we can set the variables values in the FreeCAD document once the optimize function returns the results. In other words, the last list is a sort of "id" for all the variables.
