import numpy as np

arr = np.array([[[0, 1, 531], [0, 45, 61]], [[22, 1, 5], [0, 415, 6]], [[0, 132, 5], [0, 420, 6]]])
arr_copy = arr[:, :, 2]
print(arr_copy)
for i in range(len(arr_copy)):
    max = np.nanmax(arr_copy)
    print(max)
    index = np.where(arr_copy == max)
    print(index[1][0])
    if arr_copy[index[0][0]][index[1][0]] == max:
        arr_copy[index[0][0]][index[1][0]] = 0
print(arr_copy)
