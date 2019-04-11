_cppman ()
{
	P=cppman
	if [ ${#words[@]} -gt 2 ]; then
		return
	fi
	W=$(eval echo ${words[@]:1})
	PERLP=$(printf 'if (m/^(.*?%q[^:]*)(::)?.*$/) { print "$1$2$/"; }' $W)

	params="$($P -f "$W" | perl -ne "$PERLP" \
		| perl -ne '/^([^\[]*)(\W\[.*\].*)?$/; print "$1\n"' \
		| perl -ne '/^((?:std::)?)(.*)$/; print "$2\n$1$2\n"' \
		| sort -u | xargs -d '\n' printf '%q ')"


	eval "compadd -X "%USuggestions%u" -- $params"
}
compdef _cppman -P cppman -N
