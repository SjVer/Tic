# Compute average of given values.

Let a = 0
While a < 1 Repeat
    Print "Enter number of scores: "
    Input a
Endwhile

Let b = 0
Let s = 0
Print "Enter one value at a time: "
While b < a Repeat
    Input c
    Let s = s + c
    Let b = b + 1
Endwhile

Print "Average: "
Print s / a
