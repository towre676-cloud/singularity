#define _GNU_SOURCE
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <dlfcn.h>
ssize_t readlink(const char *path,char *buf,size_t size){
 const char *p=getenv("LEAN_EXECUTABLE_PATH");
 if(p && strncmp(path,"/proc/",6)==0 && strlen(path)>10 && strcmp(path+strlen(path)-4,"/exe")==0){size_t n=strlen(p);if(n>size)n=size;memcpy(buf,p,n);return n;}
 ssize_t (*f)(const char*,char*,size_t)=dlsym(RTLD_NEXT,"readlink");return f(path,buf,size);
}
