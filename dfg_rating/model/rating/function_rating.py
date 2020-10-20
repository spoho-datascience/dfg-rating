import numpy as np


class FunctionRating:
    """Rating based on function generation
    Functions follow standard NumPy names and args
    https://numpy.org/doc/stable/reference/random/generator.html

    Attributes:
        distribution (str): Function name
    """
    def __init__(self, distribution: str, *args):
        try:
            self.distribution_method = getattr(np.random.default_rng(), distribution)
        except AttributeError as attribute_error:
            self.distribution_method = None
        self.arguments = []
        for arg in args:
            self.arguments.append(arg)

        pass

    def compute(self):
        """Compute single rating"""
        if self.distribution_method is not None:
            s = self.distribution_method(*self.arguments)
            return s

    def compute_array(self, length):
        """Compute array of ratings"""
        if self.distribution_method is not None:
            s = self.distribution_method(*self.arguments, length)
            return s




if __name__ == '__main__':
    for i in range(0, 1):
        FunctionRating('normal', 10, 1).compute()
    print('Season distribution')
    FunctionRating('normal', 10, 1).compute_array(5)
