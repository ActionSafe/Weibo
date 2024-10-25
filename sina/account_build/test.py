# -*- encoding: utf-8 -*-
"""
@File    : test.py
@Time    : 2020/3/30 22:09
@Author  : ActionSafe
@Email   : actionsafe@163.com
"""

if __name__ == '__main__':
    n_rows = 13
    result = [[1]]
    while len(result) < n_rows:
        newRow = [sum(x) for x in zip([0] + result[-1], result[-1] + [0])]
        result.append(newRow)
    for item in result:
        print("\t".join(map(str, item)))


