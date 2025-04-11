import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, FindExecutable
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Path configurations with error checking
    pkg_path = get_package_share_directory('warehouse_simulation_pkg')
    urdf_file = os.path.join(pkg_path, 'urdf', 'delivery_bot', 'husky.urdf.xacro')
    world_file = os.path.join(pkg_path, 'worlds', 'warehouse.world')
    
    # Verify files exist before launching
    if not os.path.exists(urdf_file):
        raise FileNotFoundError(f"URDF file not found at: {urdf_file}")
    if not os.path.exists(world_file):
        raise FileNotFoundError(f"World file not found at: {world_file}")
    
    # Set the GAZEBO_MODEL_PATH to include your package's models directory
    model_path = os.path.join(pkg_path, 'models')
    if 'GAZEBO_MODEL_PATH' in os.environ:
        os.environ['GAZEBO_MODEL_PATH'] += ":" + model_path
    else:
        os.environ['GAZEBO_MODEL_PATH'] = model_path
    
    # Disable online model fetching to prevent hangs
    os.environ['GAZEBO_MODEL_DATABASE_URI'] = ""
    
    # Declare launch arguments
    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    spawn_robot = DeclareLaunchArgument(
        'spawn_robot',
        default_value='true',
        description='Whether to spawn the robot'
    )
    use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Whether to launch RViz'
    )
    
    return LaunchDescription([
        use_sim_time,
        spawn_robot,
        use_rviz,
        
        # Kill any existing gazebo processes
        ExecuteProcess(
            cmd=['pkill', '-9', 'gzserver'],
            output='screen',
            shell=True
        ),
        
        # Launch Gazebo with custom parameters
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={
                'world': world_file,
                'extra_gazebo_args': '--verbose -s libgazebo_ros_init.so -s libgazebo_ros_factory.so',
                'gui': 'true'
            }.items()
        ),
        
        # Robot State Publisher with better parameter handling
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': Command(['xacro ', urdf_file]),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'publish_frequency': 30.0
            }]
        ),
        
        # Spawn Entity with conditional launching
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name='spawn_husky',
            arguments=[
                '-topic', 'robot_description',
                '-entity', 'husky',
                '-x', '0.0',
                '-y', '0.0',
                '-z', '0.1',
                '-R', '0.0',
                '-P', '0.0',
                '-Y', '0.0'
            ],
            output='screen',
            condition=IfCondition(LaunchConfiguration('spawn_robot'))
        ),
        
        # Optional: Launch RViz for visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', os.path.join(pkg_path, 'config', 'husky.rviz')],
            output='screen',
            condition=IfCondition(LaunchConfiguration('use_rviz'))
        )
    ])