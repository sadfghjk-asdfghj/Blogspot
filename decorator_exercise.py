import random
import time

list=[1, 2, 3, 4, 5]
number=random.choice(list)
print(number)

def admin_only(function):
    def wrapper_function():
        if number==1:
            function()
    return wrapper_function

def delay(function):
    def wrapper_function():
            time.sleep(10)
            function()
    return wrapper_function




@admin_only
@delay
def say_hello():
    print("How are you doing?")
say_hello()




