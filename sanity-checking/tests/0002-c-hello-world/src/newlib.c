#ifndef TEST_BOARD_NATIVE

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#ifdef TEST_BOARD_HIFIVE1

ssize_t
write (int fd, const void *buf, size_t nbytes)
{
  char volatile *uart_data = (char *)0x10013000;

  if (fd == STDOUT_FILENO || fd == STDERR_FILENO) {
    for (int i = 0; i < nbytes; i++) {
      while ((*uart_data & 0x80000000) != 0) {
        /* Waiting for TX FIFO to be empty */
        continue;
      }

      *uart_data = ((char *)buf)[i];
    }
    return nbytes;
  } else {
    return 0;
  }
}

void
_exit (int status)
{
  uint32_t volatile *test_device= (uint32_t *)0x100000;

  /* Write to the SiFive Test device on QEMU to shutdown */
  *test_device = 0x5555;

  while (1) {
  }
}

#endif  /* TEST_BOARD_HIFIVE1 */

/* Assume that all fd are a tty.  */
int
isatty (int fd)
{
  return 1;
}

int
close (int fd)
{
  return 0;
}

int
fstat (int fd, struct stat*buf)
{
  return -1;
}

off_t
lseek (int fd, off_t offset, int whence)
{
  return -1;
}

ssize_t
read (int fmd, void *buf, size_t count)
{
  return 0;
}

int
getpid (void)
{
  return 1;
}

int
kill (int pid, int sig)
{
  errno = EINVAL;
  return -1; /* Always fails */
}

/* Provide the .init function, and register the exception frame from there. */

void _init() __attribute__((section(".init")));
extern void __register_frame_info (const void *, void *);
extern void __deregister_frame_info (const void *);
extern const char __EH_FRAME__[];

void _init()
{
  /* This structure must approximately match that in unwind-dw2-fde.h.
     In particular it must be no smaller, and no less aligned.  */
  static struct object {
    void *pc_begin; void *tbase; void *dbase; void *u;
    unsigned long b; void *fde_end; struct object *next;
  } object;

  __register_frame_info (__EH_FRAME__, &object);
}

void _fini() __attribute__((section(".init")));

void _fini()
{
  __deregister_frame_info (__EH_FRAME__);
}

void
abort ()
{
  _exit(-1);
}

/* __heap_start and __heap_end are defined in the commands script for the
   linker. They define the space of RAM that has not been allocated
   for code or data. */

extern void *__heap_start;
extern void *__heap_end;

void *
sbrk (ptrdiff_t nbytes)
{
  static void *heap_ptr = (void *)&__heap_start;
  void *base;

  if (((uintptr_t)&__heap_end - (uintptr_t)heap_ptr) >= nbytes)
    {
      base = heap_ptr;
      heap_ptr += nbytes;
      return base;
    }
  else
    {
      return (void *)-1;
    }
}
#endif  /* TEST_BOARD_NATIVE */
