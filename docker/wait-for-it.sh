#!/bin/sh
# wait-for-it.sh

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "Redis is unavailable - sleeping"
  sleep 1
done

>&2 echo "Redis is up - executing command"
exec $cmd
