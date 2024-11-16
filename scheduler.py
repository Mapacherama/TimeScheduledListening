from apscheduler.triggers.date import DateTrigger
from datetime import datetime

def schedule_playlist(scheduler, play_playlist, playlist_uri: str, play_time: str):
    now = datetime.now()
    play_time_obj = datetime.strptime(play_time, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    if play_time_obj < now:
        play_time_obj = play_time_obj.replace(day=now.day + 1)
    trigger = DateTrigger(run_date=play_time_obj)
    scheduler.add_job(play_playlist, trigger, args=[playlist_uri])
    return {
        "message": f"Playlist {playlist_uri} scheduled to play at {play_time_obj.strftime('%Y-%m-%d %H:%M:%S')}"
    }