# Compute average of given values.

Assign a = 0
While a < 1 Repeat
    Print "Enter number of scores: "
    Input a
Endwhile

Assign b = 0
Assign s = 0
Print "Enter one value at a time: "
While b < a Repeat
    Input c
    Assign s = s + c
    Assign b = b + 1
Endwhile

Print "Average: "
Print s / a
