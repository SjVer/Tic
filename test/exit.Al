PrintLine "In five seconds this program will exit with exit code 1..."

Assign count = 5

# the while loops are pretty straight forward
While count > 0 Repeat
    PrintLine count
    Assign count = count - 1
    Sleep 1
EndWhile

Exit 1