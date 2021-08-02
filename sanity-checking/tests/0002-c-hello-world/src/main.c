#include <stdio.h>
#include <stdlib.h>
#include <string.h>

__attribute__((constructor))
static void init () {
  printf ("Constructor says \"Hi!\"\n");
}

__attribute__((destructor))
static void deinit () {
  printf ("Destructor says \"Hi!\"\n");
}

int main (int argc, char **argv) {
  char *hello = (char *)malloc(15);
  strncpy(hello, "Hello, there!\n", 15);
  printf ("%s", hello);

  if (argv[argc] != NULL) {
      printf ("Error: argv[argc] != NULL\n");
  }

  printf ("argv[0]: '%s'\n", argv[0]);

  /* argv strings should be writable */
  argv[0][0] = 't';
  argv[0][1] = 'e';
  argv[0][2] = 's';
  argv[0][3] = 't';
  printf ("modified argv[0]: '%s'\n", argv[0]);

  for (int j = 1; j < argc; j++) {
    printf (" ... arg: %s\n", argv[j]);
  }

  return 0;
}
