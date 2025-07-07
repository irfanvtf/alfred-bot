#!/bin/sh
# wait-for-it.sh

set -e

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <host> <port> <command> [args...]" >&2
  exit 1
fi
host="$1"
port="$2"
shift 2

until nc -z "$host" "$port"; do
  >&2 echo "Redis is unavailable - sleeping"
  sleep 1
done

>&2 echo "Redis is up - executing command"
exec "$@"
