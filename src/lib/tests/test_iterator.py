# # global imports
# import sys
#
# # sys.path.insert(0, '../src')
# # sys.path.insert(0, '../src/lib')

# local imports
from lib.helper import clear_debug_window
clear_debug_window()

from lib.helper import IteratorWithPushback

def test_iter1():

    test_list = ['a', 'bb', 'c', 'ddd', 'ee']
    test_iter = IteratorWithPushback(test_list)
    result = []
    while True:
        try:
            x = next(test_iter)
            result.append(x)
            if x == 'c':
                test_iter.push_back(x)
                x = next(test_iter)
                result.append(x)
        except StopIteration:
            break

    assert not result == test_list      # Should fail, as 'c' was pushed back
    assert result == ['a', 'bb', 'c', 'c', 'ddd', 'ee']