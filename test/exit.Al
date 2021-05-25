PrintLine "In five seconds this program will exit with exit code 1..."

Assign count = 5
While count > 0 Repeat
    PrintLine count
    Assign count = count - 1
    Sleep 1
EndWhile

Exit 1