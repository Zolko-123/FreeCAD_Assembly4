# Hyper Dual Numbers
I mostly followed this [paper](http://adl.stanford.edu/hyperdual/Fike_AIAA-2011-886.pdf) to implement hyper dual numbers. I made some modifications in order to be able to get the gradient and the hessian using numpy arrays. I am not sure if the modifications I made are the most efficient or even if they work on all cases; however, so far the optimization algorithms seem to work well using my implementation of hyper dual numbers. *HyperDualExample.py*  is a small test I made comparing hyper dual numbers with discrete gradient and hessian functions. The examples follow scipy.optimize [page](https://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html#sequential-least-squares-programming-slsqp-algorithm-method-slsqp). The results I got is that using hyper dual numbers is around 2 times slower than using discrete functions. 


The way I use hyper dual numbers is a little bit different to the way they are presented in the paper. In the paper they are shown as 4-dimensional numbers with 1 real and 3 imaginary parts. My implementation of hyper dual numbers consist of a real element, a "gradient" and a "hessian". The real element is just a real number. The gradient is a numpy array of size **nx1**. And the hessian is a numpy array of size **nxn**. Here **n** is the number of hyper dual numbers being used. The initial gradient of the hyper dual number is an array of zeros with only one element having the value of **1.** And the initial hessian is filled with zeros. Each hyper dual number can be thought to be a different variable in the system (**x0**, **x1**, **...**, **xn**). And the element of the gradient having a value of **1** is in the same position as the postion of the hyper dual. That is, the element of value **1** in the gradient of hyper dual **xi** is in the postion **i**. 


This implementation of hyper duals is a little bit complicated; however, it has the benefit that once a function of multiple variables is evaluated, the output (an hyper dual number) will already contain gradient and hessian matrices which can easily be used by the optimization algorithms.


Before beginning to work with the hyper duals, we need to know how many different numbers we will be using since the size of their gradients and hessians depend on the number of hyper duals being used. That is, when the solver is called and given a set of constraints and variables, it first checks all the different variables being used. Here, the variables represent elements of the placement of objects. Note that each hyper dual number represents an unique variable. 


In order to be able to use dual numbers and scipy.minimize I had to encapsulate the function evaluation inside an object because scipy.minimize only utilizes numpy arrays of real values. The object is used as a way to store the list of hyper dual values and to evaluate the function. The object has 2 properties and 3 methods. The first property is an array of hyper dual numbers that represent each variable. The second property is an hyper dual number representing the evaluation of the function. The first method, is an evaluation of the function that has as input a numpy array. This method first assigns the values of each element in the input array into the real values of each hyper dual number in the object's property. Then, it evaluates the function, puts the result on the corresponding property and finally returns the real value of the resulting hyper dual number. While the function is evaluated, we obtain the gradient and the hessian automatically, they are stored in the object's property containing the value of the function. The other two methods just return the gradient and the hessian matrices when they are called since their values are already known. Here is an example of the object:

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

# Constraints
Now I will talk about the constraints implemented.
