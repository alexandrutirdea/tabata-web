#!/usr/bin/env python3
import sys
import random
from datetime import datetime, timedelta
from plexapi.server import PlexServer
from plexapi.playqueue import PlayQueue

# === CONFIGURATION ===
PLEX_URL = 'http://server_ip:32400'
PLEX_TOKEN = 'YOURTOKEN'
TIME_MARGIN = 1  # Allow up to +1 minute over target
ARTIST_REPEAT_BUFFER = 30  # Number of tracks between same artist
# =====================

def track_played_recently(track, cutoff):
    if not track.lastViewedAt:
        return False
    return track.lastViewedAt >= cutoff

def select_tracks(source_tracks, target_minutes, cooldown_days, attempts=1000):
    cutoff = datetime.now() - timedelta(days=cooldown_days)
    eligible = [t for t in source_tracks if not track_played_recently(t, cutoff)]
    print(f"[INFO] {len(eligible)} eligible tracks (not played in last {cooldown_days} days)")

    min_ms = target_minutes * 60_000
    max_ms = (target_minutes + TIME_MARGIN) * 60_000

    for attempt in range(attempts):
        random.shuffle(eligible)
        selected = []
        artist_buffer = []
        total_ms = 0

        for track in eligible:
            artist_name = track.artist().title.strip().lower()

            if len(selected) <= ARTIST_REPEAT_BUFFER:
                if artist_name in artist_buffer:
                    continue
            else:
                if artist_name in artist_buffer[-ARTIST_REPEAT_BUFFER:]:
                    continue

            if total_ms + track.duration > max_ms:
                continue

            selected.append(track)
            artist_buffer.append(artist_name)
            total_ms += track.duration

            if total_ms >= min_ms:
                break

        if min_ms <= total_ms <= max_ms:
            return selected, total_ms

    return [], 0

def main():
    if len(sys.argv) != 5:
        print("Usage: play_mix.py \"Playlist Name\" <minutes> <cooldown_days> \"Player Name\"")
        sys.exit(1)

    playlist_name = sys.argv[1]
    target_minutes = int(sys.argv[2])
    cooldown_days = int(sys.argv[3])
    player_name = sys.argv[4]

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    print(f"[INFO] Fetching playlist: {playlist_name}")
    playlist = plex.playlist(playlist_name)
    all_tracks = playlist.items()

    selected_tracks, total_ms = select_tracks(all_tracks, target_minutes, cooldown_days)
    total_sec = total_ms // 1000

    if not selected_tracks:
        print("[ERROR] No valid track combination found.")
        sys.exit(1)

    title = f"{playlist_name} - {target_minutes}min Mix"
    print(f"[INFO] Creating playlist '{title}' with {len(selected_tracks)} tracks, total {total_sec // 60}m {total_sec % 60}s")

    mix = plex.createPlaylist(title, items=selected_tracks)
    print(f"[SUCCESS] Created temporary playlist: {title}")

    player = None
    for client in plex.clients():
        if client.title.strip().lower() == player_name.strip().lower():
            player = client
            break

    if not player:
        print(f"[ERROR] Player '{player_name}' not found. Make sure it's active and visible to Plex.")
        return

    print(f"[INFO] Starting playback on: {player_name}")
    pq = PlayQueue.create(plex, selected_tracks)
    player.playMedia(pq)
    print(f"[SUCCESS] Playing now on {player_name}.")

    # Delete playlist after playback starts
    try:
        print(f"[INFO] Deleting temporary playlist: {title}")
        mix.delete()
        print(f"[INFO] Playlist deleted successfully.")
    except Exception as e:
        print(f"[WARN] Failed to delete playlist: {e}")

if __name__ == "__main__":
    main()
