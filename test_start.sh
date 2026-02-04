#!/usr/bin/env bash
set -u

cmd=(python Tautulli.py --datadir ./TEST)
startup_grace=${STARTUP_GRACE_SECONDS:-50}
shutdown_timeout=${SHUTDOWN_TIMEOUT_SECONDS:-120}

"${cmd[@]}" &
pid=$!

end=$((SECONDS + startup_grace))
while kill -0 "$pid" 2>/dev/null && [ "$SECONDS" -lt "$end" ]; do
  sleep 0.2
done

if kill -0 "$pid" 2>/dev/null; then
  echo "SUCCESS: app started, shutting down test process."
  kill "$pid" 2>/dev/null || true
  timeout_end=$((SECONDS + shutdown_timeout))
  while kill -0 "$pid" 2>/dev/null && [ "$SECONDS" -lt "$timeout_end" ]; do
    sleep 0.2
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  else
    wait "$pid" 2>/dev/null || true
  fi
  exit 0
fi

wait "$pid"
exit_code=$?
echo "FAIL: app exited early with code $exit_code."
if [ "$exit_code" -eq 0 ]; then
  exit 1
fi
exit "$exit_code"
