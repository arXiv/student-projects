#!/usr/bin/env bash
#
# Backfill stats-aggregate-hourly-downloads for hours that failed with a
# NoRetryError (logged, not retried by pubsub) between START_TIME and END_TIME.
#
# It finds the failed hours by reading "A NoRetry exception has been raised"
# log lines from Cloud Logging and working backwards from each failure's log
# timestamp: scheduled invocations process (invocation_time - hour_delay),
# truncated to the hour (see config.hour_delay / validate_cloud_event in
# stats-functions/aggregate_hourly_downloads/src/main.py). hour_delay is 3
# unless the function's config has been changed.
#
# Usage:
#   ./backfill_hourly_downloads.sh [--dry-run] [--yes] [--sleep-seconds N] [START_TIME] [END_TIME]
#
# Env vars (all optional, shown with defaults):
#   PROJECT=arxiv-production
#   TOPIC=stats-aggregate-hourly-downloads
#   SERVICE_NAME=stats-aggregate-hourly-downloads
#   HOUR_DELAY=3
#   SLEEP_SECONDS=600   (also settable via --sleep-seconds)
#   START_TIME=2026-08-05T00:00:00Z
#   END_TIME=<today at 00:00 UTC>   (i.e. through the end of yesterday)
#
# Examples:
#   ./backfill_hourly_downloads.sh --dry-run
#   ./backfill_hourly_downloads.sh --yes
#   ./backfill_hourly_downloads.sh --yes --sleep-seconds 120
#   ./backfill_hourly_downloads.sh --yes 2026-08-05T00:00:00Z 2026-08-09T00:00:00Z

set -euo pipefail

PROJECT="${PROJECT:-arxiv-production}"
TOPIC="${TOPIC:-stats-aggregate-hourly-downloads}"
SERVICE_NAME="${SERVICE_NAME:-stats-aggregate-hourly-downloads}"
HOUR_DELAY="${HOUR_DELAY:-3}"
SLEEP_SECONDS="${SLEEP_SECONDS:-600}"
START_TIME="${START_TIME:-2026-08-05T00:00:00Z}"
END_TIME="${END_TIME:-$(date -u +%Y-%m-%dT00:00:00Z)}"

DRY_RUN=false
ASSUME_YES=false
POSITIONAL=()

# split flags from positional args (START_TIME/END_TIME) so either order works
# using a while/shift loop (rather than `for`) since --sleep-seconds consumes
# an extra argument for its value
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --yes|-y) ASSUME_YES=true; shift ;;
    --sleep-seconds=*) SLEEP_SECONDS="${1#*=}"; shift ;;
    --sleep-seconds) SLEEP_SECONDS="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,34p' "$0"
      exit 0
      ;;
    *) POSITIONAL+=("$1"); shift ;;
  esac
done

if [[ "${#POSITIONAL[@]}" -ge 1 ]]; then START_TIME="${POSITIONAL[0]}"; fi
if [[ "${#POSITIONAL[@]}" -ge 2 ]]; then END_TIME="${POSITIONAL[1]}"; fi

echo "Project:       $PROJECT"
echo "Topic:         $TOPIC"
echo "Service:       $SERVICE_NAME"
echo "Window:        [$START_TIME, $END_TIME)"
echo "Hour delay:    $HOUR_DELAY"
echo "Sleep between: ${SLEEP_SECONDS}s"
echo "Dry run:       $DRY_RUN"
echo

echo "Fetching NoRetry error logs..."
LOG_FILTER="resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND textPayload=~\"A NoRetry exception has been raised\" AND timestamp>=\"${START_TIME}\" AND timestamp<\"${END_TIME}\""

# one timestamp per failed invocation, oldest first
RAW_TIMESTAMPS="$(gcloud logging read "$LOG_FILTER" \
  --project="$PROJECT" \
  --format="value(timestamp)" \
  --order=asc \
  --limit=5000)"

if [[ -z "$RAW_TIMESTAMPS" ]]; then
  echo "No NoRetry errors found in that window. Nothing to backfill."
  exit 0
fi

FAILURE_COUNT="$(printf '%s\n' "$RAW_TIMESTAMPS" | grep -c .)"
echo "Found $FAILURE_COUNT NoRetry error log entries."

# Convert each failure's log timestamp into the data-hour it was trying to
# process (invocation_time - hour_delay, truncated to the hour), and dedupe.
# Done in python rather than `date` since GNU/BSD date flags aren't portable.
TMP_PY="$(mktemp)"
trap 'rm -f "$TMP_PY"' EXIT

cat > "$TMP_PY" <<'PYEOF'
import sys
from datetime import datetime, timedelta

hour_delay = int(sys.argv[1])
seen = set()
hours = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    ts = datetime.fromisoformat(line.replace("Z", "+00:00"))
    # scheduled (cron) invocations have no explicit "hour" attribute, so
    # validate_cloud_event() derives the target hour from the event's own
    # timestamp minus hour_delay - mirror that here to recover which hour
    # each failure was trying to process.
    failed_hour = (ts - timedelta(hours=hour_delay)).replace(minute=0, second=0, microsecond=0)
    key = failed_hour.strftime("%Y-%m-%d%H")  # matches validate_hour()'s expected format
    if key not in seen:
        seen.add(key)
        hours.append(key)

for h in sorted(hours):
    print(h)
PYEOF

HOURS="$(printf '%s\n' "$RAW_TIMESTAMPS" | python3 "$TMP_PY" "$HOUR_DELAY")"
HOUR_COUNT="$(printf '%s\n' "$HOURS" | grep -c .)"

echo
echo "Inferred $HOUR_COUNT distinct failed hour(s) to backfill:"
printf '  %s\n' $HOURS
echo
ESTIMATED_MINUTES=$(( (HOUR_COUNT - 1 > 0 ? HOUR_COUNT - 1 : 0) * SLEEP_SECONDS / 60 ))
echo "This will take roughly ${ESTIMATED_MINUTES} minutes to run (waits ${SLEEP_SECONDS}s between each publish)."

if [[ "$DRY_RUN" == true ]]; then
  echo
  echo "Dry run - not publishing anything."
  exit 0
fi

# safety gate before triggering a long, production-impacting replay run
if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "Proceed and publish $HOUR_COUNT backfill message(s) to '$TOPIC' in project '$PROJECT'? [y/N] " CONFIRM
  if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
  fi
fi

# publish one hour at a time with attribute "hour=<hour>" - this is what
# validate_hour() reads to know which hour to (re)aggregate. Sleeping between
# each publish keeps the DB from getting hit with overlapping bulk writes.
INDEX=0
for HOUR in $HOURS; do
  INDEX=$((INDEX + 1))
  echo "[$INDEX/$HOUR_COUNT] $(date -u +%Y-%m-%dT%H:%M:%SZ) publishing hour=$HOUR"
  gcloud pubsub topics publish "$TOPIC" \
    --project="$PROJECT" \
    --message="" \
    --attribute="hour=$HOUR"

  if [[ "$INDEX" -lt "$HOUR_COUNT" ]]; then
    echo "  sleeping ${SLEEP_SECONDS}s before next publish..."
    sleep "$SLEEP_SECONDS"
  fi
done

echo
echo "Done. Published $HOUR_COUNT backfill message(s)."
echo "Check logs again in a few minutes to confirm each hour processed successfully:"
echo "  gcloud logging read '${LOG_FILTER}' --project=$PROJECT --order=asc"
