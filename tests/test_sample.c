#include <assert.h>
#include "../fixes/sample_fixed.c"

int main() {
    assert(add(2, 3) == 5);
    assert(add(0, 0) == 0);
    return 0;
}
