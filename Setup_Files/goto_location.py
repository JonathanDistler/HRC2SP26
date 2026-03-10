import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from ament_index_python.packages import get_package_share_directory

import yaml
import sys
import os


class GoToLocation(Node):

    def __init__(self, location_name):
        super().__init__('goto_location')

        self.publisher = self.create_publisher(PoseStamped, '/goal_pose', 10)

        package_path = get_package_share_directory('stretch_init_pose')
        yaml_path = os.path.join(package_path, 'config', 'locations.yaml')

        with open(yaml_path, 'r') as f:
            locations = yaml.safe_load(f)

        if location_name not in locations:
            self.get_logger().error(f"Location '{location_name}' not found")
            self.get_logger().info(f"Available locations: {list(locations.keys())}")
            rclpy.shutdown()
            return

        loc = locations[location_name]

        goal = PoseStamped()

        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()

        goal.pose.position.x = loc["x"]
        goal.pose.position.y = loc["y"]
        goal.pose.position.z = loc["z"]

        goal.pose.orientation.x = loc["qx"]
        goal.pose.orientation.y = loc["qy"]
        goal.pose.orientation.z = loc["qz"]
        goal.pose.orientation.w = loc["qw"]

        self.goal = goal
        self.timer = self.create_timer(1.0, self.publish_goal)

        self.get_logger().info(f"Navigating to {location_name}")

        self.create_timer(1.0, self.shutdown)

    def publish_goal(self):
       self.goal.header.stamp = self.get_clock().now().to_msg()
       self.publisher.publish(self.goal)
       self.get_logger().info("Publishing navigation goal...")
    def shutdown(self):
        rclpy.shutdown()


def main():

    rclpy.init()

    if len(sys.argv) < 2:
        print("Usage: ros2 run stretch_init_pose goto_location <location>")
        return

    location = sys.argv[1]

    node = GoToLocation(location)

    rclpy.spin(node)


if __name__ == '__main__':
    main()
