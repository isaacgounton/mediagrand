import os
import ffmpeg
import logging
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

def process_video_merge_with_audio(
    video_urls,
    audio_url,
    job_id=None
):
    """
    Merges multiple videos into one, overlays the provided audio (speech), and repeats the last video segment until the audio ends.
    The output video will end only after the audio finishes, with a small buffer at the end.
    """
    if not video_urls:
        raise ValueError("No video URLs provided for merging")
    if not audio_url:
        raise ValueError("No audio_url provided for merging")

    input_files = []
    downloaded_files = []
    output_filename = f"{job_id}_merged_with_audio.mp4"
    output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
    concat_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_concat_list.txt")

    try:
        logger.info(f"Job {job_id}: Starting video merge with audio for {len(video_urls)} videos")

        # Download all video files
        for i, video_url in enumerate(video_urls):
            if os.path.isfile(video_url):
                input_files.append(video_url)
            else:
                input_filename = download_file(video_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_video_{i}"))
                input_files.append(input_filename)
                downloaded_files.append(input_filename)

        # Download audio file
        if os.path.isfile(audio_url):
            speech_file = audio_url
        else:
            speech_file = download_file(audio_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_speech"))
            downloaded_files.append(speech_file)
        if not os.path.exists(speech_file):
            raise FileNotFoundError(f"Speech audio file does not exist: {speech_file}")

        # Get durations
        video_info = []
        total_video_duration = 0
        for i, input_file in enumerate(input_files):
            probe = ffmpeg.probe(input_file)
            duration = float(probe['format']['duration'])
            has_audio = any(stream['codec_type'] == 'audio' for stream in probe['streams'])
            video_info.append({
                'file': input_file,
                'duration': duration,
                'has_audio': has_audio
            })
            total_video_duration += duration

        speech_probe = ffmpeg.probe(speech_file)
        speech_duration = float(speech_probe['format']['duration'])
        logger.info(f"Job {job_id}: Speech audio duration: {speech_duration:.2f}s")

        # Calculate how many times to repeat the last video
        repeat_needed = speech_duration - total_video_duration
        repeat_needed = max(0, repeat_needed)
        last_video_file = input_files[-1]
        last_video_duration = video_info[-1]['duration']

        # Build concat list: all videos + repeat last as needed
        concat_files = input_files.copy()
        if repeat_needed > 0:
            repeat_count = int(repeat_needed // last_video_duration)
            remainder = repeat_needed % last_video_duration
            for _ in range(repeat_count):
                concat_files.append(last_video_file)
            if remainder > 0:
                # Cut the last segment to match the remainder
                cut_file = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_last_cut.mp4")
                (
                    ffmpeg
                    .input(last_video_file, ss=0, t=remainder + 0.2)  # add a small buffer
                    .output(cut_file, vcodec='copy', acodec='copy')
                    .overwrite_output()
                    .run(quiet=False)
                )
                concat_files.append(cut_file)
                downloaded_files.append(cut_file)

        # Write concat list file
        with open(concat_file_path, 'w', encoding='utf-8') as concat_file:
            for input_file in concat_files:
                abs_path = os.path.abspath(input_file).replace("'", "'\"'\"'")
                concat_file.write(f"file '{abs_path}'\n")

        # Concatenate all video segments
        temp_concat_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_temp_concat_with_audio.mp4")
        (
            ffmpeg.input(concat_file_path, format='concat', safe=0)
            .output(temp_concat_path, c='copy', avoid_negative_ts='make_zero')
            .run(overwrite_output=True, quiet=False)
        )

        # Overlay the speech audio, trim video to match audio length + buffer
        final_duration = speech_duration + 0.2
        video_input = ffmpeg.input(temp_concat_path)
        audio_input = ffmpeg.input(speech_file)
        output_args = {
            'vcodec': 'copy',
            'acodec': 'aac',
            'shortest': None
        }
        (
            ffmpeg
            .output(
                video_input['v'],
                audio_input['a'],
                output_path,
                **output_args,
                t=final_duration
            )
            .run(overwrite_output=True, quiet=False)
        )

        # Clean up temp files
        for f in downloaded_files + [concat_file_path, temp_concat_path]:
            if os.path.exists(f):
                os.remove(f)

        logger.info(f"Job {job_id}: Video merge with audio completed successfully: {output_path}")
        return output_path

    except Exception as e:
        for f in downloaded_files + [concat_file_path]:
            if os.path.exists(f):
                os.remove(f)
        logger.error(f"Job {job_id}: Video merge with audio failed: {str(e)}")
        raise