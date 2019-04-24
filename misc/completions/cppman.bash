_cppman ()
{
	if [ "${#COMP_WORDS[@]}" -gt 2 ]; then
		return
	fi
	if [ -z "${COMP_WORDS[1]}" ]; then
		return
	fi
	P=${COMP_LINE[0]}
	W=${COMP_WORDS[1]}

	PERLP=$(printf 'if (m/^(.*?) - (.*)$/) { print "$1$/"; }' $W)

	params="$($P -f "$W" | perl -ne "$PERLP" | sort -u | xargs -d '\n' printf '%q ')"
	echo $params > test.log

	COMPREPLY=($(compgen -W "$params" "$W"))

}
complete -F _cppman cppman
