cppman()
{
    command cppman ${1//\//::}
}
_cppman()
{ 
    local W params IFS=$' \t\n'
    if [ -z "${COMP_WORDS[1]}" ]; then
        return
    fi
    W=${COMP_WORDS[1]}
    W=${W//\//::}; W=${W//\*/\\*}; W=${W//[/\\[}
    params="$(
        command cppman -f "$W" |
        perl -ne 'if (m/^(.*?) - (.*)$/) { print "$1$/"; }' |
        sed -n 's/([^)]\+)//g; /^'"${W}"'/p'
    )"
    IFS=$'\n'
    params=${params//::/\/}
    COMPREPLY=( $(compgen -W "$params" -- ${COMP_WORDS[1]}) )
}

complete -F _cppman cppman
