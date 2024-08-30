#define LOG_GLOBAL_ENABLE

#define LL_DEBUG 0
#define LL_INFO 1
#define LL_WARN 2
#define LL_ERROR 3
#define LL_NONE 4

// default log level
#ifndef LOG_LEVEL
// #define LOG_LEVEL LL_DEBUG
// #define LOG_LEVEL LL_ERROR
#define LOG_LEVEL LL_NONE
#endif

#define _LOG_PRINTF(fmt, level, ...) printf( "%s[%s:%s(%d)] " fmt "\n", level, __FILE__, __FUNCTION__, __LINE__, ##__VA_>

#if defined(LOG_GLOBAL_ENABLE) && LOG_LEVEL <= LL_DEBUG
#define LOG_DEBUG(fmt, ...) _LOG_PRINTF(fmt, "Debug", ##__VA_ARGS__)
#else
#define LOG_DEBUG(fmt, ...)
#endif

#if defined(LOG_GLOBAL_ENABLE) && LOG_LEVEL <= LL_ERROR
#define LOG_ERROR(fmt, ...) _LOG_PRINTF(fmt, "Error", ##__VA_ARGS__)
#else
#define LOG_ERROR(fmt, ...)
#endif