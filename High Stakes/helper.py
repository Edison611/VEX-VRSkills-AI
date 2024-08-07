import math 

def convert_coord(grid_size, coord):
    center_x, center_y = grid_size[0] // 2, grid_size[1] // 2

    adjusted_x = center_x + coord[0]
    adjusted_y = center_y - coord[1]

    return adjusted_x, adjusted_y

def calculate_front_position(position, heading, bot_width):
    # Calculate the front position based on the heading
    angle_rad = math.radians(heading)
    front_x = position[0] + (bot_width / 2 * math.sin(angle_rad)) 
    front_y = position[1] + (bot_width / 2 * math.cos(angle_rad))
    return front_x, front_y


def calculate_back_position(position, heading, bot_height):
    # Calculate the back position based on the heading
    angle_rad = math.radians(heading)
    back_x = position[0] - (bot_height / 2 * math.sin(angle_rad)) 
    back_y = position[1] - (bot_height / 2 * math.cos(angle_rad))
    return back_x, back_y

