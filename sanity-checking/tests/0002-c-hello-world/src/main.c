#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libgen.h>

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

  printf ("argv[0]: %s\n", basename(argv[0]));

  /* argv strings should be writable */
  const int len = strlen(argv[0]);
  argv[0][len - 4] = 't';
  argv[0][len - 3] = 'e';
  argv[0][len - 2] = 's';
  argv[0][len - 1] = 't';
  printf ("modified argv[0]: %s\n", basename(argv[0]));

  for (int j = 1; j < argc; j++) {
    printf (" ... arg: %s\n", argv[j]);
  }

  return 0;
}
