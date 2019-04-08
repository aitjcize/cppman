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

	PERLP=$(printf 'if (m/^(.*?%q[^:]*)(::)?.*$/) { print "$1$2$/"; }' $W)

	params="$($P -f "$W" | perl -ne "$PERLP" \
		| perl -ne '/^([^\[]*)(\W\[.*\].*)?$/; print "$1\n"' \
		| perl -ne '/^((?:std::)?)(.*)$/; print "$2\n$1$2\n"' \
		| sort -u | xargs -d '\n' printf '%q ')"

	COMPREPLY=($(compgen -W "$params" "$W"))

}
complete -F _cppman cppman
