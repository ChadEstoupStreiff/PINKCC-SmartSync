import os
import time
import argparse
from tqdm import tqdm

def test_speed(folder_path, file_size_mb=100, iterations=3):
    file_path = os.path.join(folder_path, "speed_test.tmp")
    data = os.urandom(1024 * 1024) 
    
    write_speeds = []
    read_speeds = []

    print(f"--- Testing folder: {folder_path} ({iterations} passes) ---")

    for i in tqdm(range(iterations), desc="Testing Progress"):
        # 1. Test Write Speed
        start_time = time.time()
        with open(file_path, 'wb') as f:
            for _ in range(file_size_mb):
                f.write(data)
            os.fsync(f.fileno())
        write_duration = time.time() - start_time
        write_speeds.append(file_size_mb / write_duration)

        # 2. Test Read Speed
        start_time = time.time()
        with open(file_path, 'rb') as f:
            while f.read(1024 * 1024):
                pass
        read_duration = time.time() - start_time
        read_speeds.append(file_size_mb / read_duration)

        # Cleanup after each pass to ensure fresh writes
        if os.path.exists(file_path):
            os.remove(file_path)

    # Calculate Averages
    avg_write = sum(write_speeds) / len(write_speeds)
    avg_read = sum(read_speeds) / len(read_speeds)

    print("\n--- Results ---")
    print(f"Average Write Speed: {avg_write:.2f} MB/s")
    print(f"Average Read Speed:  {avg_read:.2f} MB/s")
    print("---------------------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Folder Speed Test Tool")
    parser.add_argument("folder", type=str, help="Path to the folder to test.")
    parser.add_argument("--size", type=int, default=100, help="Size of the test file in MB.")
    parser.add_argument("--n", type=int, default=3, help="Number of iterations.")
    
    args = parser.parse_args()
    
    # Check if folder exists before running
    if os.path.isdir(args.folder):
        test_speed(args.folder, file_size_mb=args.size, iterations=args.n)
    else:
        print(f"Error: {args.folder} is not a valid directory.")