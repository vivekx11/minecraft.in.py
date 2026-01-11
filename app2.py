from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
from random import randint, choice
from math import sin, cos

app = Ursina()

# Performance settings
window.fps_counter.enabled = True
window.borderless = False
window.fullscreen = False

# Game state
game_state = {
    'selected_block': 'grass',
    'inventory': {'grass': 100, 'stone': 50, 'wood': 30, 'sand': 40, 'gold': 20},
    'mode': 'build',
    'time_of_day': 0,
    'render_distance': 25  # Reduced for performance
}

# Block types with different properties - VIBRANT COLORS
BLOCK_TYPES = {
    'grass': {'color': color.green, 'texture': None},
    'stone': {'color': color.red, 'texture': None},
    'wood': {'color': color.blue, 'texture': None},
    'sand': {'color': color.yellow, 'texture': None},
    'gold': {'color': color.violet, 'texture': None}
}

# Optimized voxel with LOD
class Voxel(Button):
    def __init__(self, position=(0, 0, 0), block_type='grass'):
        self.block_type = block_type
        block_props = BLOCK_TYPES[block_type]
        
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            color=block_props['color'],
            scale=1,
            collider='box',
            highlight_color=color.light_gray
        )

    def input(self, key):
        if self.hovered:
            if key == 'left mouse down':
                if game_state['inventory'][game_state['selected_block']] > 0:
                    new_pos = self.position + mouse.normal
                    Voxel(position=new_pos, block_type=game_state['selected_block'])
                    game_state['inventory'][game_state['selected_block']] -= 1
                    update_ui()
                    
            if key == 'right mouse down':
                if self.position.y > 0:
                    game_state['inventory'][self.block_type] += 1
                    destroy(self)
                    update_ui()

# Optimized terrain generation - brown ground
def generate_terrain():
    size = game_state['render_distance']
    for z in range(size):
        for x in range(size):
            # Brown ground only
            Voxel(position=(x, 0, z), block_type='grass')
            
            # Add random trees (less frequent)
            if randint(1, 30) == 1:
                create_tree(x, 1, z)

def create_tree(x, y, z):
    # Smaller tree for performance
    for i in range(3):
        Voxel(position=(x, y + i, z), block_type='wood')
    
    # Compact leaves
    for lx in range(-1, 2):
        for lz in range(-1, 2):
            if not (lx == 0 and lz == 0):
                Voxel(position=(x + lx, y + 3, z + lz), block_type='grass')

# ===== MODERN UI DESIGN =====

# Main UI container with glassmorphism effect
ui_container = Entity(parent=camera.ui, model='quad', 
                      scale=(1.9, 0.16), 
                      position=(0, 0.46),
                      color=color.rgba(30, 30, 60, 200))

# Hotbar background with gradient effect
hotbar_bg = Entity(parent=camera.ui, model='quad',
                   scale=(0.55, 0.09),
                   position=(0, -0.43),
                   color=color.rgba(45, 25, 60, 220))

# Title text with shadow
title_shadow = Text(parent=camera.ui, text='VOXEL BUILDER', 
                    position=(-0.72, 0.481), scale=2.2, 
                    color=color.rgba(0, 0, 0, 200), font='VeraMono.ttf')

title_text = Text(parent=camera.ui, text='VOXEL BUILDER', 
                  position=(-0.72, 0.485), scale=2.2, 
                  color=color.orange, font='VeraMono.ttf')

# Inventory display with icons
inventory_panel = Entity(parent=camera.ui, model='quad',
                         scale=(0.7, 0.08),
                         position=(-0.3, 0.46),
                         color=color.rgba(40, 80, 120, 180))

inventory_text = Text(parent=camera.ui, position=(-0.62, 0.465), 
                      text='', scale=1.3, origin=(0, 0), 
                      color=color.yellow)

# Mode indicator with icon
mode_bg = Entity(parent=camera.ui, model='quad',
                 scale=(0.18, 0.06),
                 position=(0.72, 0.46),
                 color=color.rgba(50, 180, 100, 220))

mode_text = Text(parent=camera.ui, position=(0.64, 0.465), 
                 text='BUILD', scale=1.6, origin=(0, 0),
                 color=color.cyan)

# Hotbar slots
hotbar_slots = []
slot_indicators = []
for i in range(5):
    # Slot background
    slot = Entity(parent=camera.ui, model='quad',
                  scale=(0.08, 0.08),
                  position=(-0.2 + i * 0.1, -0.43),
                  color=color.rgba(60, 40, 80, 240))
    
    # Slot number
    Text(parent=camera.ui, text=str(i + 1),
         position=(-0.235 + i * 0.1, -0.385),
         scale=1.2, color=color.orange)
    
    hotbar_slots.append(slot)
    
    # Block preview in slot
    block_names = list(BLOCK_TYPES.keys())
    if i < len(block_names):
        block = Entity(parent=camera.ui, model='cube',
                      scale=0.04,
                      position=(-0.2 + i * 0.1, -0.43),
                      color=BLOCK_TYPES[block_names[i]]['color'],
                      rotation=(20, 45, 0))
        slot_indicators.append(block)

# Selection highlight
selection_highlight = Entity(parent=camera.ui, model='quad',
                             scale=(0.09, 0.09),
                             position=(-0.2, -0.43),
                             color=color.rgba(255, 150, 0, 0),
                             z=0.01)

# Crosshair - modern design
crosshair_h = Entity(parent=camera.ui, model='quad', scale=(0.015, 0.002), 
                     color=color.lime, z=-1)
crosshair_v = Entity(parent=camera.ui, model='quad', scale=(0.002, 0.015), 
                     color=color.lime, z=-1)
crosshair_center = Entity(parent=camera.ui, model='circle', scale=0.003,
                         color=color.red, z=-1)

# Help panel (toggleable)
help_panel = Entity(parent=camera.ui, model='quad',
                    scale=(0.5, 0.35),
                    position=(0.6, 0),
                    color=color.rgba(25, 15, 45, 240),
                    enabled=False)

help_title = Text(parent=help_panel, text='CONTROLS', 
                  position=(0, 0.14), scale=2, 
                  color=color.orange)

help_content = Text(parent=help_panel, 
                    text='1-5  Select Block\nLMB  Place Block\nRMB  Break Block\nE    Quick Build\nQ    Dig Down\nF    Fly Mode\nH    Toggle Help\nESC  Exit',
                    position=(0, 0), scale=1.3, 
                    color=color.cyan, origin=(0, 0))

# FPS counter styling
fps_text = Text(parent=camera.ui, position=(0.8, 0.48),
                text='', scale=1.2, color=color.lime)

# Smooth UI update with animation
def update_ui():
    selected = game_state['selected_block']
    block_list = list(BLOCK_TYPES.keys())
    
    # Update inventory text
    inv_str = ""
    for i, (block, count) in enumerate(game_state['inventory'].items()):
        if block == selected:
            inv_str += f"[{block.upper()}: {count}]  "
        else:
            inv_str += f"{block.upper()}: {count}  "
    
    inventory_text.text = inv_str
    
    # Update mode
    if game_state['mode'] == 'build':
        mode_text.text = '⚒ BUILD'
        mode_bg.color = color.rgba(50, 180, 100, 220)
    else:
        mode_text.text = '⛏ DESTROY'
        mode_bg.color = color.rgba(255, 80, 80, 220)
    
    # Animate selection highlight
    selected_idx = block_list.index(selected)
    target_x = -0.2 + selected_idx * 0.1
    selection_highlight.animate_position((target_x, -0.43), duration=0.15, curve=curve.out_expo)
    selection_highlight.color = color.orange

# Advanced features
def quick_build_platform():
    forward = player.forward
    base_pos = player.position + forward * 3
    
    for x in range(-1, 2):
        for z in range(-1, 2):
            pos = Vec3(int(base_pos.x) + x, int(base_pos.y), int(base_pos.z) + z)
            if game_state['inventory'][game_state['selected_block']] > 0:
                Voxel(position=pos, block_type=game_state['selected_block'])
                game_state['inventory'][game_state['selected_block']] -= 1
    update_ui()

def dig_down():
    pos = Vec3(int(player.position.x), int(player.position.y) - 1, int(player.position.z))
    for entity in scene.entities:
        if isinstance(entity, Voxel) and entity.position == pos:
            game_state['inventory'][entity.block_type] += 1
            destroy(entity)
            update_ui()
            break

# Lighting - Night mode
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))
sun.color = color.rgb(50, 50, 80)  # Dark bluish light
AmbientLight(color=color.rgba(20, 20, 40, 0.5))  # Very dark ambient

# Smooth update loop
def update():
    # FPS display
    fps_text.text = f'FPS: {int(1/time.dt)}' if time.dt > 0 else 'FPS: --'
    
    # Smooth crosshair pulse
    pulse = abs(sin(time.time() * 2)) * 0.001 + 0.003
    crosshair_center.scale = pulse

# Input handling
def input(key):
    block_list = list(BLOCK_TYPES.keys())
    
    if key in '12345':
        idx = int(key) - 1
        if idx < len(block_list):
            game_state['selected_block'] = block_list[idx]
            update_ui()
    
    if key == 'tab':
        game_state['mode'] = 'destroy' if game_state['mode'] == 'build' else 'build'
        update_ui()
    
    if key == 'e':
        quick_build_platform()
    
    if key == 'q':
        dig_down()
    
    if key == 'f':
        player.gravity = 0 if player.gravity else 1
    
    if key == 'h':
        help_panel.enabled = not help_panel.enabled
    
    if key == 'escape':
        application.quit()

# Sky with night mode - dark blue to black gradient
Sky(color=color.rgb(10, 10, 30))  # Very dark blue, almost black

# Generate terrain
print("Generating terrain...")
generate_terrain()
print("Terrain generated!")

# Create player with optimized settings
player = FirstPersonController(position=(12, 3, 12))
player.cursor.visible = False
player.speed = 6
player.jump_height = 2

# Initial UI update
update_ui()

print("\n=== VOXEL BUILDER ===")
print("Press H for controls")
print("Optimized for smooth gameplay!\n")

app.run()
