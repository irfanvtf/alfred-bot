#!/bin/sh
# wait-for-it.sh

set -e

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <host> <port> -- <command> [args...]" >&2
  exit 1
fi

host="$1"
port="$2"
shift 2

# Check if the next argument is '--'
if [ "$1" = "--" ]; then
  shift # Remove the '--'
else
  >&2 echo "Error: Expected '--' before command arguments."
  exit 1
fi

# Now, "$@" contains the actual command and its arguments correctly.
# No need for cmd="$@"

>&2 echo "Waiting for host $host to be resolvable..."
until /usr/bin/dig +short "$host"; do
  >&2 echo "Host $host is not resolvable - sleeping"
  sleep 1
done
>&2 echo "Host $host is resolvable."

>&2 echo "Waiting for port $port on $host to be open..."
until nc -z "$host" "$port"; do
  >&2 echo "Port $port on $host is unavailable - sleeping"
  sleep 1
done
>&2 echo "Port $port on $host is open."

>&2 echo "Service is up - executing command"
exec "$@" # Execute the remaining arguments as the command and its arguments
