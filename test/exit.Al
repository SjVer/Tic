PRINT "In five seconds this program will exit with exit code 1..."

LET count = 5
WHILE count > 0 REPEAT
    PRINT count
    LET count = count - 1
    SLEEP 1
ENDWHILE

EXIT 1