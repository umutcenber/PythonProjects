from moviepy import VideoFileClip
import os

print("=" * 40)
print("     VIDEO TO GIF CONVERTER")
print("=" * 40)

video_path = input("Enter video path: ").strip()

if not os.path.exists(video_path):
    print("❌ Video not found.")
    exit()

try:
    start = float(input("Start time (seconds): "))
    end = float(input("End time (seconds): "))
    fps = int(input("GIF FPS (recommended 10-15): "))

    if start < 0 or end <= start:
        print("❌ Invalid time range.")
        exit()

except ValueError:
    print("❌ Invalid input.")
    exit()

try:
    clip = VideoFileClip(video_path)

    duration = clip.duration

    if end > duration:
        end = duration

    gif = clip.subclipped(start, end)

    output_name = os.path.splitext(video_path)[0] + ".gif"

    gif.write_gif(output_name, fps=fps)

    clip.close()
    gif.close()

    print("\n✅ GIF created successfully!")
    print(output_name)

except Exception as e:
    print(f"\n❌ Error: {e}")