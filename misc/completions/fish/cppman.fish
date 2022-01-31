set -l progname cppman

complete -c $progname -f

complete -c $progname -s s -l source -a "cppreference.com cplusplus.com" -d "Select source"
complete -c $progname -s c -l cache-all -d "Cache all available man pages from cppreference.com and cplusplus.com to enable offline browsing"
complete -c $progname -s C -l clear-cache -d "Clear all cached files"
complete -c $progname -s f -l find-page -d "Find man page"
complete -c $progname -s o -l force-update -d "Force cppman to update existing cache when '--cache-all' or browsing man pages that were already cached"
complete -c $progname -s m -l use-mandb -a "true false" -d "If true, cppman adds manpage path to mandb so that you can view C++ manpages with 'man' command"
complete -c $progname -s p -l pager -a "vim nvim less system" -d "Select pager to use"
complete -c $progname -s r -l rebuild-index -d "rebuild index database for the selected source"
complete -c $progname -s v -l version -d "Show version information"
complete -c $progname -l force-columns -d "Force terminal columns"
complete -c $progname -s h -l help -d "Show help message and exit"
