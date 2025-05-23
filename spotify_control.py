from pynput.keyboard import Controller, Key

keyboard = Controller()

def start_spotify_song():
    # Play/Pause Spotify
    keyboard.press(Key.media_play_pause)
    keyboard.release(Key.media_play_pause)

def next_spotify_song():
    # Next track in Spotify
    keyboard.press(Key.media_next)
    keyboard.release(Key.media_next)

def stop_spotify_song():
    # Stop Spotify (Pause)
    keyboard.press(Key.media_play_pause)
    keyboard.release(Key.media_play_pause)
