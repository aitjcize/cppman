_cppman ()
{
	P=cppman
	if [ ${#words[@]} -gt 2 ]; then
		return
	fi
	W=$(eval echo ${words[@]:1})
	if [ -z "$W" ]; then
		return
	fi
	PERLP=$(printf 'if (m/^(.*?) - (.*)$/) { print "$1$/"; }' $W)
	params="$($P -f "$W" | perl -ne "$PERLP" | sort -u | xargs -d '\n' printf '%q ')"

	eval "compadd -X "%USuggestions%u" -- $params"
}
compdef _cppman -P cppman -N
