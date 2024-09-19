import os
import sys
import ffmpeg

def process_video(input_file, output_dir):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get video information
    probe = ffmpeg.probe(input_file)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    
    # Calculate the output framerate (assuming input is 30 fps)
    input_fps = float(video_info['r_frame_rate'].split('/')[0]) / float(video_info['r_frame_rate'].split('/')[1])
    output_fps = min(input_fps, 30)

    try:
        # Process the video
        (
            ffmpeg
            .input(input_file)
            .filter('scale', 640, 360)
            .filter('fps', fps=output_fps)
            .output(os.path.join(output_dir, 'frame_%05d.png'), video_bitrate='64k', start_number=0)
            .global_args('-an')  # Remove audio
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"Video processed successfully. Frames saved in {output_dir}")
    except ffmpeg.Error as e:
        print(f"An error occurred: {e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_video_file> <output_directory>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    process_video(input_file, output_dir)

