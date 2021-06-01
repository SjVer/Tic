# Compute average of given values.

Declare a = 0
Print "Enter number of scores: "
Input a

Declare s = 0
PrintLine "Enter one value at a time: "
For b, 0, a - 1, 1 Do
    Declare c = 1
    Input c
    Set s = s + c
EndFor

Print "Average: "
PrintLine s / a