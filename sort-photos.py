import datetime
import sys
from pathlib import Path

import PIL
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
register_heif_opener()

image_extensions = ['.jpeg', '.jpg', '.png', '.heic', '.webp']

failed_files: list[Path] = []

def sort_image(file_path: Path, folder_path: Path) -> bool:
    stat = file_path.stat()

    try:
        with Image.open(file_path) as image:
            exif_data = image.getexif()
            time_taken_str: str = exif_data.get_ifd(ExifTags.IFD.Exif)[ExifTags.Base.DateTimeOriginal]
            time_taken = datetime.datetime.strptime(time_taken_str, "%Y:%m:%d %H:%M:%S")
    except (PIL.UnidentifiedImageError, KeyError, ValueError) as e:
        if isinstance(e, PIL.UnidentifiedImageError): print("PIL could not open file. Using image creation date. Error: " + str(e))
        if isinstance(e, KeyError): print("Image has no time taken metadata. Using image creation date.")
        if isinstance(e, ValueError): print(f"Could not parse EXIF time taken: {time_taken_str}. Using image creation date.")
        try:
            time_taken = stat.st_birthtime
        except AttributeError:
            time_taken = stat.st_mtime
            print("Could not find image creation date. Using date of last modification.")

    time_taken_timestamp = datetime.datetime.fromtimestamp(time_taken) if isinstance(time_taken, float) else time_taken
    year_taken = time_taken_timestamp.year
    month_taken = time_taken_timestamp.month

    new_file_path = folder_path / str(year_taken) / f"{month_taken:02d}"
    if not new_file_path.exists(): new_file_path.mkdir(parents=True)

    if not new_file_path.is_dir():
        print("ERROR: could not move file at " + str(file_path) + " into folder " + str(new_file_path) + ". "
              " A file exists at that location.")
        failed_files.append(file_path)
        return False

    dest = new_file_path / file_path.name
    if dest.exists():
        index = 0
        while dest.exists():
            dest = new_file_path / (file_path.stem + f"-{index}" + file_path.suffix)
            index += 1
        print("a file named \"" + file_path.name + "\" already exists. Renaming " + str(file_path) + " to " + str(dest.name))

    try:
        file_path.rename(dest)
    except Exception as e:
        print("ERROR moving file at " + str(file_path) + " to new path " + str(dest) + ". " + str(e))
        failed_files.append(file_path)
        return False

    print("Success: File at " + str(file_path) + " moved to path " + str(dest) + ".")
    return True


def sort_folder(given_path: Path) -> None:

    items_moved = 0

    for item in given_path.iterdir():
        if not item.is_file(): continue
        if item.suffix.lower() in image_extensions:
            try:
                if sort_image(item, given_path): items_moved += 1
            except Exception as e:
                print("ERROR: could not move file at " + str(item) + ". error: " + str(e))
                failed_files.append(item)

    print("folder " + str(given_path) + " sorted!\n"
          "Successfully moved " + str(items_moved) + " files.\n"
          "Failed to move " + str(len(failed_files)) + " files.\n")

    print(f"Failed to move: {', '.join(str(file) for file in failed_files)}")

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("A script to sort photos within a folder into sub-folders based on date taken.\n"
              "Usage: python sort-photos.py [directory to sort]")
        exit()

    path_str = sys.argv[1]
    path = Path(path_str)

    sort_folder(path)