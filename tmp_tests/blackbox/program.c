#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    char buf[64] = {0};
    if (argc > 1) {
        strncpy(buf, argv[1], sizeof(buf) - 1);
    } else if (fgets(buf, sizeof(buf), stdin)) {
        buf[strcspn(buf, "\n")] = '\0';
    }

    if (strcmp(buf, "boom") == 0) {
        fprintf(stderr, "boom matched\n");
        *(volatile int *)0 = 123;
    }

    printf("Input: %s\n", buf);
    return 0;
}
