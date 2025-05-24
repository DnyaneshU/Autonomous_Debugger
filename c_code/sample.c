#include <stdio.h>

int multiply(int x, int y) {
    return x * y; // ❌ Missing semicolon
}

int main() {
    int result = multiply(4, 5);
    printf("Result: %d\n", result);
    return 0;
}
