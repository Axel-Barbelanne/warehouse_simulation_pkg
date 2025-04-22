import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, LogInfo
from launch_ros.actions import Node

def generate_launch_description():
    # Get the package directory
    pkg_dir = get_package_share_directory('warehouse_simulation_pkg')
    
    # Construct model and world paths
    models_path = os.path.join(pkg_dir, 'models')
    world_file = os.path.join(pkg_dir, 'worlds', 'new_warehouse.sdf')
    
    # Print debug information
    log_paths = LogInfo(msg=f"Using models path: {models_path}")
    log_world = LogInfo(msg=f"Loading world file: {world_file}")
    
    # Launch Gazebo with our world
    gazebo = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', world_file],
        output='screen',
        additional_env={
            'IGN_GAZEBO_RESOURCE_PATH': models_path,
            'IGN_VERBOSE': '4'
        }
    )
    
    return LaunchDescription([
        log_paths,
        log_world,
        gazebo,
    ])