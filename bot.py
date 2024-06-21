from mcpi.minecraft import Minecraft
import time

# Connect to Minecraft
mc = Minecraft.create(address='127.0.0.1', port=25565)

# Log in a player (assumes you are already logged in via Minecraft client)

# Function to remove blocks
def remove_blocks(x, y, z, width, height, depth):
    for dx in range(width):
        for dy in range(height):
            for dz in range(depth):
                mc.setBlock(x + dx, y + dy, z + dz, 0)  # 0 is the ID for air, effectively removing the block

# Main function
def main():
    # Get player position
    pos = mc.player.getTilePos()
    
    # Coordinates to start removing blocks (e.g., start from player's position)
    start_x = pos.x
    start_y = pos.y
    start_z = pos.z

    # Define the dimensions of the area to clear
    width = 10  # Blocks along the X-axis
    height = 10 # Blocks along the Y-axis
    depth = 10  # Blocks along the Z-axis

    # Call the function to remove blocks
    remove_blocks(start_x, start_y, start_z, width, height, depth)

    # Inform player that blocks are being removed
    mc.postToChat("Removing blocks...")

    # Optional: Wait for a bit to see the changes
    time.sleep(5)

    # Inform player that the task is done
    mc.postToChat("Blocks removed!")

if __name__ == "__main__":
    main()
