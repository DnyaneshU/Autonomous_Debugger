#include <assert.h>
#include "../fixes/sample_fixed.c"

void test_multiply() {
    assert(multiply(2, 3) == 6);
    assert(multiply(5, 0) == 0);
    assert(multiply(-1, 4) == -4);
}

int main() {
    test_multiply();
    return 0;
}
