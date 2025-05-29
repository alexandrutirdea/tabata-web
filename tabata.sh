#!/bin/bash

# Usage: ./tabata.sh WORK REST ROUNDS [PREPARE]
# Example: ./tabata.sh 20 10 8 20

WORK=$1
REST=$2
ROUNDS=$3
PREPARE=${4:-20}

TOPIC="tabata"

#This is optional, only if you want notifications on your fitness bracelet or smartwatch during your workouts
send_notification() {
    MESSAGE="$1"
    curl -s -H "Title: Tabata" -d "$MESSAGE" "ntfy_server/$TOPIC" > /dev/null
}

format_time() {
    local TOTAL=$1
    local MIN=$((TOTAL / 60))
    local SEC=$((TOTAL % 60))
    printf "%02d:%02d" "$MIN" "$SEC"
}

countdown() {
    local SECONDS=$1
    local LABEL=$2
    local -n REMAINING=$3  # Use nameref to update remaining time

    for (( t=SECONDS; t>0; t-- )); do
        ((REMAINING--))
        printf "\r%-10s %2ds remaining | Total left: %s" "$LABEL" "$t" "$(format_time $REMAINING)"
        sleep 1
    done
    echo ""
}

# Calculate total workout time in seconds
TOTAL_TIME=$((PREPARE + (WORK + REST) * ROUNDS - REST))  # No rest after final round
TOTAL_REMAINING=$TOTAL_TIME

# Convert total time to minutes (round up to nearest minute)
PLAYLIST_MINUTES=$(( (TOTAL_TIME + 59) / 60 ))  # Ceiling division

echo "Total workout time: $(format_time $TOTAL_TIME)"
echo "Prepare: $PREPARE seconds"
send_notification "Get Ready!"
countdown "$PREPARE" "Prepare" TOTAL_REMAINING

for (( i=1; i<=$ROUNDS; i++ ))
do
    echo "Round $i: Work for $WORK seconds"
    send_notification "Round $i: WORK!"
    countdown "$WORK" "Work" TOTAL_REMAINING

    if (( i < ROUNDS )); then
        echo "Round $i: Rest for $REST seconds"
        send_notification "Round $i: REST"
        countdown "$REST" "Rest" TOTAL_REMAINING
    fi
done

send_notification "Workout complete!"
echo "Workout complete!"
