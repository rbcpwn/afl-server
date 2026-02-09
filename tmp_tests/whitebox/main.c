#include <stdio.h>
#include <string.h>

int main(void) {
    char buf[64];
    if (!fgets(buf, sizeof(buf), stdin)) {
        return 0;
    }

    if (strstr(buf, "crash")) {
        fprintf(stderr, "boom!\n");
        *(volatile int *)0 = 42;
    }

    printf("OK: %s\n", buf);
    return 0;
}
