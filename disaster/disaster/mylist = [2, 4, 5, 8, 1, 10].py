mylist = [2, 4, 5, 8, 1, 10]
mylist.sort()
print(mylist)
x = 6
for i in range(len(mylist)):
    if mylist[i] > x:
        mylist.insert(i, x)
        break 
print( mylist)
