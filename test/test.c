#include <stdio.h>
#include <math.h>
#include <string.h>



float a;


//funcs:

void MyFunc(void *x){
printf("\n\n%i", x);printf("parameter: ");
printf("\n");
}

//wraps:

void MyFunc_wrapper(float randvarjEhyF){
MyFunc(&randvarjEhyF);}


//code:

int main(void){
a = 
1
+
1
;
MyFunc_wrapper(
a
);


return 0;
}


