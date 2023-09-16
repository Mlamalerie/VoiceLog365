from glob import glob
import os
from datetime import datetime
from pydub import AudioSegment
import calendar
from tqdm import tqdm
from typing import List
import pandas as pd
import matplotlib.pyplot as plt


# vocals directory
WHATSAPPS_VOCALS_DIR_PATH = "data/Mlamali à Pau"
PODCAST_OUTPUT_DIR_PATH = "output"

def extract_date_from_filename(filename : str) -> datetime:
    return datetime.strptime(filename.split('-')[1], DATE_FORMAT)


def analyze_audio_files(audio_files: List[str], merged_dir: str) -> None:
    """
    Analyze audio files and display information such as duration, size, and count by month.
    """

    df = pd.DataFrame()
    df['filename'] = audio_files
    df['date'] = df['filename'].apply(extract_date_from_filename)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df['month'] = df['date'].dt.month
    df['month_abbr'] = df['month'].apply(lambda x: calendar.month_abbr[x])
    df['year'] = df['date'].dt.year
    df['size'] = df['filename'].apply(lambda x: os.path.getsize(x))
    df['size'] = df['size'] / 1024 / 1024  # Convert size to MB

    # Display aggregated info by month
    df_grouped = df.groupby(['year', 'month']).agg({'filename': 'count', 'size': 'sum'})

    # Save plot visualizing the information
    fig, ax = plt.subplots(figsize=(15, 7))
    df_grouped.plot(kind='bar', ax=ax)
    plt.title(f"Number of audios by month ({os.path.basename(merged_dir)})")
    plt.xlabel("Month")
    plt.ylabel("Number of audios")
    plt.savefig(os.path.join(merged_dir, "audios_by_month.png"))


def remove_noise(audio):
    """
    Votre fonction pour enlever le bruit d'un segment audio.
    Modifiez cette fonction selon votre besoin.
    """
    # Ici, vous pourriez intégrer un code pour traiter l'audio et enlever le bruit.
    # Pour l'instant, elle retourne juste l'audio original.
    return audio


DATE_FORMAT = "%Y%m%d"
ISO_WEEK_FORMAT = "%Y%U"


def create_and_export_podcast(current_audio : AudioSegment, interval : str, start_date : datetime, merged_dir : str, output_format : str) -> str:
    """Create and export a podcast."""
    if interval == "weekly":
        iso_date_str = "".join([str(i) for i in datetime.isocalendar(start_date)[:2]])
        start_date_str = start_date.strftime(DATE_FORMAT)
        output_filename = os.path.join(merged_dir, f"Podcast_Week_{iso_date_str} (start_date={start_date_str}).{output_format}")
    else:
        output_filename = os.path.join(merged_dir, f"Podcast_Month_{start_date.strftime('%Y%m')}.{output_format}")
    current_audio.export(output_filename, format=output_format)
    return output_filename


def assemble_audio_podcasts(audio_files : List[str], merged_dir : str, interval : str = "monthly", pause_duration_ms : int = 1000, output_format : str = "mp3") -> List[str]:
    """Merge audio files into weekly or monthly podcasts."""
    if not audio_files:
        raise ValueError("The list of audio files is empty.")

    audio_files.sort()
    merged_files = []
    pause = AudioSegment.silent(duration=pause_duration_ms)

    current_audio = None
    start_date = extract_date_from_filename(audio_files[0])

    for filename in tqdm(audio_files, desc="Creating podcasts...", total=len(audio_files)):
        date_obj = extract_date_from_filename(filename)
        clean_audio = remove_noise(AudioSegment.from_file(filename))

        if interval == "weekly" and datetime.isocalendar(date_obj)[:2] != datetime.isocalendar(start_date)[:2]:
            merged_files.append(create_and_export_podcast(current_audio, interval, start_date, merged_dir, output_format))
            start_date = date_obj
            current_audio = None

        elif interval == "monthly" and date_obj.strftime('%Y%m') != start_date.strftime('%Y%m'):
            merged_files.append(create_and_export_podcast(current_audio, interval, start_date, merged_dir, output_format))
            start_date = date_obj
            current_audio = None

        current_audio = (current_audio + pause if current_audio else AudioSegment.empty()) + clean_audio

    if current_audio:
        merged_files.append(create_and_export_podcast(current_audio, interval, start_date, merged_dir, output_format))

    return merged_files


def main():
    # List audio files
    wa_vocals_files = glob(f'{WHATSAPPS_VOCALS_DIR_PATH}/*.opus')
    print("> Number of vocals: ", len(wa_vocals_files))
    print(wa_vocals_files[:5])

    # Create a directory for merged audios
    merged_dir_name = f"{os.path.basename(WHATSAPPS_VOCALS_DIR_PATH)} ({datetime.now().strftime('%Y%m%d_%H')})"
    merged_dir = os.path.join(PODCAST_OUTPUT_DIR_PATH, merged_dir_name)
    os.makedirs(merged_dir, exist_ok=True)

    # Analyze and then merge audio files
    analyze_audio_files(wa_vocals_files, merged_dir)
    PAUSE_SEC = 1.5
    merged_files = assemble_audio_podcasts(wa_vocals_files, merged_dir, interval="weekly", pause_duration_ms=PAUSE_SEC * 1000)
    print("> Number of files generated: ", len(merged_files))
    print(merged_files)



if __name__ == '__main__':
    main()


