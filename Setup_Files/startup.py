import subprocess
import time
import psutil

print("Starting Stretch_robot_home.py...")

# Step 1: Run homing (blocking)
p1 = subprocess.Popen([
    "python3",
    "/home/hello-robot/stretch_body/tools/bin/stretch_robot_home.py"])
p1.wait()
print("Homing complete. Launching navigation...")

# Launches the neavigation
p2 = subprocess.Popen([
    "ros2", "launch", "stretch_nav2", "navigation.launch.py",
    "map:=/home/hello-robot/stretch_user/maps/finalized_map.yaml"
])

# Wait for Nav2 to initialize (will remain on the entire time)
print("Waiting for navigation stack to initialize...")
time.sleep(10)

print("Publishing initial pose...")

# Runs the initial pose location
p3 = subprocess.Popen([
    "ros2", "run", "stretch_init_pose", "initial_pose"
])

p3.wait()

print("Initial pose published.")
