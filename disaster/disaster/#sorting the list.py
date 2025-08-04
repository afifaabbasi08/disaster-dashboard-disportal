#sorting the list 
import bisect
mylist = [2, 4, 5, 8, 1, 10]
mylist.sort()
print(mylist)
#inserting 6 in the sorted manner bisect uses the concept of bst to place 6 whilde minating the ascending nature of the list 
bisect.insort(mylist, 6)
print(mylist)
#find pairs whose sum is equals to 10 
i=0
j=len(mylist)-1
while i<j:
    s=mylist[i]+mylist[j]
    if s==10:
        print({mylist[i]},{mylist[j]})
        i+=1
        j-=1
    elif s>10:
        j-=1
    else:
        i+=1
