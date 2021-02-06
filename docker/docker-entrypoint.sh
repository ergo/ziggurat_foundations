#!/bin/bash
set -e

# change the app uid to ones set from environment
if [ -n "${USER_UID}" ]; then
  usermod -u $USER_UID application
fi
if [ -n "${USER_GID}" ]; then
  groupmod -g $USER_GID application
fi

process_init_files() {
	local f
	for f; do
		case "$f" in
			*.sh)
				# https://github.com/docker-library/postgres/issues/450#issuecomment-393167936
				# https://github.com/docker-library/postgres/pull/452
				if [ -x "$f" ]; then
					echo "$0: running $f"
					"$f"
				else
					echo "$0: sourcing $f"
					. "$f"
				fi
				;;
			*)        echo "$0: ignoring $f" ;;
		esac
	done
}

process_init_files /opt/entrypoint.d/*

gosu application "$@"
