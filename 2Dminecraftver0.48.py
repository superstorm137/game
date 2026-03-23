# paper minecraft ver. 0.45
# by chatgpt and me
# made in the beautiful land of amurica
# play the damn game already
import pygame, random, math

# --- Mining ---
DEFAULT_MINING_TIME = 30

block_mining_time = {
    "dirt": 10,
    "grass": 10,
    "stone": 40,
    "coal_ore": 45,
    "copper_ore": 50,
    "iron_ore": 60,
    "gold_ore": 80,
    "diamond_ore": 120,
    "wood": 20,
    "leaves": 5,
}

mining_progress = 0
mining_block = None

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
TILE_SIZE = 40
GRAVITY = 0.5
MAX_FALL_SPEED = 12
JUMP_STRENGTH = -10
PLAYER_SPEED = 5
VISIBILITY_RANGE = 10

# --- Initialize ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Paper Minecraft Survival + Recipe Book")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)

# --- World ---
WORLD_WIDTH, WORLD_HEIGHT = 150, 80
world = [["air" for _ in range(WORLD_HEIGHT)] for _ in range(WORLD_WIDTH)]

# --- Terrain ---
def generate_terrain():
    base_height = WORLD_HEIGHT // 2
    height_map = []
    for x in range(WORLD_WIDTH):
        hill = int(base_height + math.sin(x/5)*5 + random.randint(-2,2))
        height_map.append(hill)
        for y in range(hill, WORLD_HEIGHT):
            if y == hill:
                world[x][y] = "grass"
            elif y < hill + 5:
                world[x][y] = "dirt"
            else:
                world[x][y] = "stone"
    return height_map

height_map = generate_terrain()

def generate_ores():
    for x in range(WORLD_WIDTH):
        for y in range(WORLD_HEIGHT//2, WORLD_HEIGHT):
            if world[x][y] == "stone":
                r = random.random()
                if r < 0.002:
                    world[x][y] = "diamond_ore"
                elif r < 0.006:
                    world[x][y] = "gold_ore"
                elif r < 0.012:
                    world[x][y] = "iron_ore"
                elif r < 0.020:
                    world[x][y] = "copper_ore"
                elif r < 0.035:
                    world[x][y] = "coal_ore"

generate_ores()


# --- Trees ---
def generate_trees():
    for x in range(2, WORLD_WIDTH-2, 2):
        if random.random() < 0.1:
            gy = height_map[x]
            for i in range(3):
                if gy-i-1>0:
                    world[x][gy-i-1]="wood"
            for lx in range(-1,2):
                for ly in range(-3,0):
                    nx, ny = x+lx, gy+ly-1
                    if 0<=nx<WORLD_WIDTH and 0<=ny<WORLD_HEIGHT and world[nx][ny]=="air":
                        world[nx][ny]="leaves"
generate_trees()

# --- Textures ---
def draw_block_texture(surface, block, rect):
    if block == "grass":
        pygame.draw.rect(surface, (34,139,34),
                         (rect.x, rect.y, rect.width, rect.height//2))
        pygame.draw.rect(surface, (139,69,19),
                         (rect.x, rect.y+rect.height//2, rect.width, rect.height//2))

    elif block == "dirt":
        pygame.draw.rect(surface, (139,69,19), rect)

    elif block == "stone":
        pygame.draw.rect(surface, (128,128,128), rect)

    elif block == "coal_ore":
        pygame.draw.rect(surface, (90,90,90), rect)
        pygame.draw.circle(surface, (20,20,20), rect.center, 5)

    elif block == "iron_ore":
        pygame.draw.rect(surface, (120,120,120), rect)
        pygame.draw.circle(surface, (200,200,200), rect.center, 5)

    elif block == "copper_ore":
        pygame.draw.rect(surface, (120,100,80), rect)
        pygame.draw.circle(surface, (184,115,51), rect.center, 5)

    elif block == "gold_ore":
        pygame.draw.rect(surface, (120,120,120), rect)
        pygame.draw.circle(surface, (255,215,0), rect.center, 5)

    elif block == "diamond_ore":
        pygame.draw.rect(surface, (100,100,100), rect)
        pygame.draw.circle(surface, (0,255,255), rect.center, 5)

    elif block == "wood":
        pygame.draw.rect(surface, (101,67,33), rect)

    elif block == "leaves":
        pygame.draw.rect(surface, (34,139,34), rect)

    elif block == "planks":
        pygame.draw.rect(surface, (205,133,63), rect)

    elif block == "crafting_table":
        pygame.draw.rect(surface, (139,69,19), rect)
        pygame.draw.rect(surface, (200,150,100),
                         (rect.x+5, rect.y+5, rect.width-10, rect.height-10))
# --- Mining cracks ---
def draw_cracks(surface, rect, progress, required_time):
    alpha = min(255, int((progress / required_time) * 255))
    crack = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

    pygame.draw.line(crack, (0, 0, 0, alpha), (0, 0), (rect.width, rect.height), 2)
    pygame.draw.line(crack, (0, 0, 0, alpha), (rect.width, 0), (0, rect.height), 2)

    surface.blit(crack, rect.topleft)

# --- Item Textures ---
def draw_item_texture(surface, item, rect):
    if item == "coal":
        pygame.draw.circle(surface, (20,20,20), rect.center, rect.width//3)

    elif item == "iron_ingot":
        pygame.draw.rect(surface, (200,200,200),
                         rect.inflate(-rect.width//4, -rect.height//2))

    elif item == "copper_ingot":
        pygame.draw.rect(surface, (184,115,51),
                         rect.inflate(-rect.width//4, -rect.height//2))

    elif item == "gold_ingot":
        pygame.draw.rect(surface, (255,215,0),
                         rect.inflate(-rect.width//4, -rect.height//2))

    elif item == "diamond":
        points = [
            (rect.centerx, rect.top),
            (rect.right, rect.centery),
            (rect.centerx, rect.bottom),
            (rect.left, rect.centery)
        ]
        pygame.draw.polygon(surface, (0,255,255), points)

# --- Player ---
player = pygame.Rect(100,100,TILE_SIZE//2,TILE_SIZE)
vel_x, vel_y = 0,0
on_ground = False

# --- Camera ---
camera_x, camera_y = 0,0

# --- Inventory / Hotbar ---
inventory_slots = [
    "dirt","stone","grass","wood","leaves",
    "planks","crafting_table",
    "coal","iron_ingot","copper_ingot","gold_ingot","diamond"
]

inventory = {block:0 for block in inventory_slots}

# --- Item-only definitions ---
item_only = {
    "coal", "iron_ingot", "copper_ingot", "gold_ingot", "diamond"
}

# --- Ore drops (block -> item) ---
ore_drops = {
    "coal_ore": "coal",
    "iron_ore": "iron_ingot",
    "copper_ore": "copper_ingot",
    "gold_ore": "gold_ingot",
    "diamond_ore": "diamond"
}

inventory = {block: 0 for block in inventory_slots}
hotbar_size = 9
hotbar_slots = [""] * hotbar_size
selected_index = 0

# --- Crafting grids ---
personal_crafting = [["" for _ in range(2)] for _ in range(2)]  # 2x2 grid
crafting_table_grid = [["" for _ in range(3)] for _ in range(3)]  # 3x3 grid
personal_result = ""
table_result = ""

# --- Crafting recipes (Minecraft-style) ---
# Each recipe is a dict with 'grid' and 'result'
personal_recipes = [
    {"grid": [["wood"]],  # 1 wood anywhere in grid → 4 planks
     "result": "planks"},
    
    {"grid": [["planks","planks"],
              ["planks","planks"]],  # 2x2 planks → crafting table
     "result": "crafting_table"}
]

table_recipes = [
    {"grid": [["wood","",""],
              ["","",""],
              ["","",""]],
     "result": "planks"},

    {"grid": [["planks","planks",""],
              ["planks","planks",""],
              ["","",""]],
     "result": "crafting_table"}
]

# Combine recipes for recipe book
all_recipes = personal_recipes + table_recipes

# --- GUI ---
inventory_open = False
crafting_table_open = False
crafting_table_pos = None
dragging_item = None  # (item_name, source_type, source_coords)

# --- HELPER FUNCTIONS FOR CRAFTING RESULTS & RECIPE BOOK ---
def grid_to_str(grid):
    """Convert a recipe grid into a readable string for the recipe book."""
    return " | ".join(["".join([c if c else " " for c in row]) for row in grid])

def update_personal_result():
    global personal_result
    personal_result = ""
    grid = trim_grid(personal_crafting)
    if not grid: return
    for recipe in personal_recipes:
        if grids_match(grid, recipe["grid"]):
            counts = count_recipe_items(recipe["grid"])
            if all(inventory.get(k,0) >= counts[k] for k in counts):
                personal_result = recipe["result"]
                return

def update_table_result():
    global table_result
    table_result = ""
    grid = trim_grid(crafting_table_grid)
    if not grid: return
    for recipe in table_recipes:
        if grids_match(grid, recipe["grid"]):
            counts = count_recipe_items(recipe["grid"])
            if all(inventory.get(k,0) >= counts[k] for k in counts):
                table_result = recipe["result"]
                return

def draw_result_slot(surface, result, rect, recipes):
    """Draw the crafting result icon + amount."""
    if result == "": return
    recipe = next(r for r in recipes if r["result"] == result)
    amount = recipe.get("amount", 1)
    if result in item_only:
        draw_item_texture(surface, result, rect.inflate(-20,-20))
    else:
        draw_block_texture(surface, result, rect.inflate(-5,-5))
    text_amount = font.render(str(amount), True, (255,255,255))
    surface.blit(text_amount, (rect.right-15, rect.bottom-20))

def draw_recipe_book(surface, recipes, x, y):
    pygame.draw.rect(surface, (100,100,150), (x, y, 150, 250))
    for idx, recipe in enumerate(recipes):
        key = recipe["grid"]
        val = recipe["result"]
        y_pos = y + idx*30
        counts = count_recipe_items(key)
        has_all = all(inventory.get(k,0) >= counts[k] for k in counts)
        color = (0,255,0) if has_all else (255,255,255)
        text = font.render(f"{val}: {grid_to_str(key)}", True, color)
        surface.blit(text, (x+5, y_pos))

# --- Helper ---
def get_block(x,y):
    if 0<=x<WORLD_WIDTH and 0<=y<WORLD_HEIGHT: return world[x][y]
    return "stone"

def check_collision(rect):
    collisions=[]
    px,py=rect.x//TILE_SIZE,rect.y//TILE_SIZE
    for x in range(max(0,px-VISIBILITY_RANGE),min(WORLD_WIDTH,px+VISIBILITY_RANGE+1)):
        for y in range(max(0,py-VISIBILITY_RANGE),min(WORLD_HEIGHT,py+VISIBILITY_RANGE+1)):
            b=get_block(x,y)
            if b!="air":
                block_rect=pygame.Rect(x*TILE_SIZE,y*TILE_SIZE,TILE_SIZE,TILE_SIZE)
                if rect.colliderect(block_rect): collisions.append(block_rect)
    return collisions

def trim_grid(grid):
    """Trim empty rows/columns from edges."""
    rows = [row[:] for row in grid]
    while rows and all(cell=="" for cell in rows[0]): rows.pop(0)
    while rows and all(cell=="" for cell in rows[-1]): rows.pop(-1)
    if not rows: return []
    while all(row[0]=="" for row in rows): 
        for row in rows: row.pop(0)
    while all(row[-1]=="" for row in rows):
        for row in rows: row.pop(-1)
    return rows

def grids_match(grid, recipe_grid):
    gh, gw = len(grid), len(grid[0])
    rh, rw = len(recipe_grid), len(recipe_grid[0])
    for y_off in range(gh - rh + 1):
        for x_off in range(gw - rw + 1):
            match = True
            for y in range(rh):
                for x in range(rw):
                    if recipe_grid[y][x] == "": continue
                    if grid[y+y_off][x+x_off] != recipe_grid[y][x]:
                        match = False
                        break
                if not match: break
            if match: return True
    return False

def count_recipe_items(recipe_grid):
    counts = {}
    for row in recipe_grid:
        for cell in row:
            if cell != "":
                counts[cell] = counts.get(cell,0)+1
    return counts

def update_personal_result():
    global personal_result
    personal_result = ""
    grid = trim_grid(personal_crafting)
    if not grid: return
    for recipe in personal_recipes:
        if grids_match(grid, recipe["grid"]):
            counts = count_recipe_items(recipe["grid"])
            if all(inventory.get(k,0) >= counts[k] for k in counts):
                personal_result = recipe["result"]
                return

def update_table_result():
    global table_result
    table_result = ""
    grid = trim_grid(crafting_table_grid)
    if not grid: return
    for recipe in table_recipes:
        if grids_match(grid, recipe["grid"]):
            counts = count_recipe_items(recipe["grid"])
            if all(inventory.get(k,0) >= counts[k] for k in counts):
                table_result = recipe["result"]
                return

def fill_crafting_grid(grid_type, recipe_grid):
    """Auto-fill the crafting grid with a recipe, consuming items if available."""
    counts = count_recipe_items(recipe_grid)
    if not all(inventory.get(k,0) >= counts[k] for k in counts):
        return  # Not enough materials

    if grid_type == "personal":
        for y in range(2):
            for x in range(2):
                if y < len(recipe_grid) and x < len(recipe_grid[0]):
                    item = recipe_grid[y][x]
                    personal_crafting[y][x] = item if item!="" else ""
                    if item != "":
                        inventory[item]-=1
        update_personal_result()
    elif grid_type == "table":
        for y in range(3):
            for x in range(3):
                if y < len(recipe_grid) and x < len(recipe_grid[0]):
                    item = recipe_grid[y][x]
                    crafting_table_grid[y][x] = item if item!="" else ""
                    if item != "":
                        inventory[item]-=1
        update_table_result()

# --- Main Loop ---
running=True
while running:
    screen.fill((135,206,235))
    mx,my=pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False

        # Toggle inventory
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_e:
                inventory_open=not inventory_open
                crafting_table_open=False
            elif pygame.K_1<=event.key<=pygame.K_9 and not inventory_open and not crafting_table_open:
                selected_index=event.key-pygame.K_1

        # Mouse click events
        if event.type==pygame.MOUSEBUTTONDOWN:
            if not inventory_open and not crafting_table_open:
                tx,ty=(mx+camera_x)//TILE_SIZE,(my+camera_y)//TILE_SIZE
                block=get_block(tx,ty)
                selected_block = hotbar_slots[selected_index]
                if event.button == 1 and block != "air":
                    player_center = player.center
                    block_center = (tx*TILE_SIZE + TILE_SIZE//2, ty*TILE_SIZE + TILE_SIZE//2)
                    distance = math.hypot(block_center[0]-player_center[0],
                                          block_center[1]-player_center[1])
                    if distance <= 4 * TILE_SIZE:
                        mining_block = (tx, ty)
                        mining_progress = 0
                elif event.button==3:
                    if block=="air" and selected_block!="" and inventory[selected_block]>0:
                        world[tx][ty]=selected_block
                        inventory[selected_block]-=1
                    elif block=="crafting_table":
                        crafting_table_open=True
                        crafting_table_pos=(tx,ty)

            # --- Inventory / GUI Drag Start ---
            if inventory_open:
                # Personal crafting 2x2
                for y in range(2):
                    for x in range(2):
                        rect=pygame.Rect(200+x*50,200+y*50,50,50)
                        if rect.collidepoint(mx,my) and personal_crafting[y][x]!="":
                            dragging_item=("personal", (x,y), personal_crafting[y][x])
                            personal_crafting[y][x]=""
                            update_personal_result()
                # Output slot draggable
                rect_out=pygame.Rect(310,210,50,50)
                if rect_out.collidepoint(mx,my) and personal_result!="":
                    dragging_item=("personal_output", None, personal_result)
                # Inventory slots
                for i,item in enumerate(inventory_slots):
                    rect=pygame.Rect(200+(i%5)*50,300+(i//5)*50,40,40)
                    if rect.collidepoint(mx,my) and inventory[item]>0:
                        dragging_item=("inventory", i, item)
                        inventory[item]-=1
            # Crafting table GUI
            if crafting_table_open:
                for y in range(3):
                    for x in range(3):
                        rect=pygame.Rect(180+x*50,180+y*50,50,50)
                        if rect.collidepoint(mx,my) and crafting_table_grid[y][x]!="":
                            dragging_item=("table", (x,y), crafting_table_grid[y][x])
                            crafting_table_grid[y][x]=""
                            update_table_result()
                rect_out=pygame.Rect(350,220,50,50)
                if rect_out.collidepoint(mx,my) and table_result!="":
                    dragging_item=("table_output", None, table_result)
            # Recipe book click
            recipe_book_rect = pygame.Rect(500,200,150,250) if inventory_open else pygame.Rect(550,180,150,250)
            if (inventory_open or crafting_table_open) and recipe_book_rect.collidepoint(mx,my):
                idx = (my - recipe_book_rect.y) // 30
                if 0 <= idx < len(all_recipes):
                    recipe = all_recipes[idx]
                    grid = recipe["grid"]
                    if inventory_open:  # fill 2x2 personal crafting
                        for y in range(2):
                            for x in range(2):
                                if y < len(grid) and x < len(grid[y]):
                                    item = grid[y][x]
                                    if item and inventory.get(item,0) > 0:
                                        personal_crafting[y][x] = item
                                        inventory[item] -= 1
                        update_personal_result()
                    elif crafting_table_open:  # fill 3x3 crafting table
                        for y in range(3):
                            for x in range(3):
                                if y < len(grid) and x < len(grid[y]):
                                    item = grid[y][x]
                                    if item and inventory.get(item,0) > 0:
                                        crafting_table_grid[y][x] = item
                                        inventory[item] -= 1
                        update_table_result()


        # --- Drag End / Drop ---
        if event.type==pygame.MOUSEBUTTONUP and dragging_item:
            x,y = mx,my
            dtype,dcoord,item = dragging_item
            # Inventory GUI drop
            if inventory_open and 150<x<650 and 150<y<450:
                gx,gy = (x-200)//50,(y-200)//50
                if 0<=gx<2 and 0<=gy<2 and personal_crafting[gy][gx]=="":
                    personal_crafting[gy][gx]=item
                    update_personal_result()
                else:
                    # Inventory slots
                    for i in range(len(inventory_slots)):
                        rect=pygame.Rect(200+(i%5)*50,300+(i//5)*50,40,40)
                        if rect.collidepoint(mx,my):
                            inventory[item]+=1
                            if dtype=="personal_output":
                                for yy in range(2):
                                    for xx in range(2): personal_crafting[yy][xx]=""
                                update_personal_result()
                            break
                    else:
                        if dtype=="personal": personal_crafting[dcoord[1]][dcoord[0]]=item; update_personal_result()
                        elif dtype=="inventory": inventory[item]+=1
            # Crafting table GUI drop
            elif crafting_table_open and 150<x<550 and 150<y<550:
                gx,gy=(x-180)//50,(y-180)//50
                if 0<=gx<3 and 0<=gy<3 and crafting_table_grid[gy][gx]=="":
                    crafting_table_grid[gy][gx]=item
                    update_table_result()
                else:
                    inventory[item]+=1
                    if dtype=="table_output":
                        for yy in range(3):
                            for xx in range(3): crafting_table_grid[yy][xx]=""
                        update_table_result()
            else:
                inventory[item]+=1
                if dtype=="personal_output":
                    for yy in range(2):
                        for xx in range(2): personal_crafting[yy][xx]=""
                    update_personal_result()
                elif dtype=="table_output":
                    for yy in range(3):
                        for xx in range(3): crafting_table_grid[yy][xx]=""
                    update_table_result()
            dragging_item=None

    # --- Player movement ---
    if not inventory_open and not crafting_table_open:
        keys=pygame.key.get_pressed()
        vel_x=0
        if keys[pygame.K_a]: vel_x=-PLAYER_SPEED
        if keys[pygame.K_d]: vel_x=PLAYER_SPEED
        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and on_ground:
            vel_y=JUMP_STRENGTH
            on_ground=False
        vel_y+=GRAVITY
        if vel_y>MAX_FALL_SPEED: vel_y=MAX_FALL_SPEED
        # collisions
        player.x+=vel_x
        for b in check_collision(player):
            if vel_x>0: player.right=b.left
            elif vel_x<0: player.left=b.right
        player.y+=vel_y
        on_ground=False
        for b in check_collision(player):
            if vel_y>0: player.bottom=b.top; vel_y=0; on_ground=True
            elif vel_y<0: player.top=b.bottom; vel_y=0
        camera_x=player.centerx-SCREEN_WIDTH//2
        camera_y=player.centery-SCREEN_HEIGHT//2
        camera_x=max(0,min(camera_x,WORLD_WIDTH*TILE_SIZE-SCREEN_WIDTH))
        camera_y=max(0,min(camera_y,WORLD_HEIGHT*TILE_SIZE-SCREEN_HEIGHT))
        
        if pygame.mouse.get_pressed()[0] and mining_block:
            tx, ty = mining_block
            if get_block(tx, ty) != "air":
                mining_progress += 1
        
                block = get_block(tx, ty)
                required_time = block_mining_time.get(block, DEFAULT_MINING_TIME)
                
                if mining_progress >= required_time:
                    block = get_block(tx, ty)
                    if block in ore_drops:
                        drop = ore_drops[block]
                        inventory[drop] += 1
                    elif block in inventory:
                        inventory[block] += 1
        
                    # decide what actually goes into the hotbar
                    if block in ore_drops:
                        hotbar_item = ore_drops[block]
                    else:
                        hotbar_item = block
                    
                    if hotbar_item not in hotbar_slots:
                        for i in range(hotbar_size):
                            if hotbar_slots[i] == "":
                                hotbar_slots[i] = hotbar_item
                                break
        
                    world[tx][ty] = "air"
                    mining_block = None
                    mining_progress = 0
            else:
                mining_block = None
                mining_progress = 0
        else:
            mining_block = None
            mining_progress = 0

    # --- Draw world ---
    start_x=max(0,(camera_x//TILE_SIZE)-1)
    end_x=min(WORLD_WIDTH,((camera_x+SCREEN_WIDTH)//TILE_SIZE)+2)
    start_y=max(0,(camera_y//TILE_SIZE)-1)
    end_y=min(WORLD_HEIGHT,((camera_y+SCREEN_HEIGHT)//TILE_SIZE)+2)
    for x in range(start_x,end_x):
        for y in range(start_y,end_y):
            b=get_block(x,y)
            if b!="air": draw_block_texture(screen,b,pygame.Rect(x*TILE_SIZE-camera_x,y*TILE_SIZE-camera_y,TILE_SIZE,TILE_SIZE))
    pygame.draw.rect(screen,(255,0,0),(player.x-camera_x,player.y-camera_y,player.width,player.height))
    # --- Draw mining cracks ---
    if mining_block:
        tx, ty = mining_block
        block = get_block(tx, ty)
        required_time = block_mining_time.get(block, DEFAULT_MINING_TIME)
    
        draw_cracks(
            screen,
            pygame.Rect(
                tx * TILE_SIZE - camera_x,
                ty * TILE_SIZE - camera_y,
                TILE_SIZE,
                TILE_SIZE
            ),
            mining_progress,
            required_time
        )

    # --- Hotbar ---
    hotbar_width = hotbar_size * 50
    start_x = (SCREEN_WIDTH - hotbar_width) // 2
    
    for i, item in enumerate(hotbar_slots):
        rect = pygame.Rect(start_x + i * 50, SCREEN_HEIGHT - 60, 50, 50)
        pygame.draw.rect(screen, (80, 80, 80), rect)  # slot background
    
        if item != "":  # only draw something if the slot has an item/block
            if item in item_only:  # draw item texture
                draw_item_texture(screen, item, rect.inflate(-20, -20))
            else:  # draw block texture
                draw_block_texture(screen, item, rect.inflate(-10, -10))
    
            # draw item/block count
            count_text = font.render(str(inventory.get(item, 0)), True, (255,255,255))
            screen.blit(count_text, (rect.right - 15, rect.bottom - 20))
    
        # highlight selected slot
        if i == selected_index:
            pygame.draw.rect(screen, (255, 255, 0), rect, 3)

    # --- Inventory GUI ---
    if inventory_open:
        pygame.draw.rect(screen,(50,50,50),(150,150,500,300))
        # 2x2 crafting
        for y in range(2):
            for x in range(2):
                rect=pygame.Rect(200+x*50,200+y*50,50,50)
                pygame.draw.rect(screen,(100,100,100),rect)
                item=personal_crafting[y][x]
                if item!="": 
                  if item in item_only:
                      draw_item_texture(screen, item, rect.inflate(-20,-20))
                  else:
                      draw_block_texture(screen, item, rect.inflate(-10,-10))

        # Output (personal crafting result)
        rect_out = pygame.Rect(310, 210, 50, 50)
        pygame.draw.rect(screen, (150,150,150), rect_out)
        draw_result_slot(screen, personal_result, rect_out, personal_recipes)

        # Inventory slots
        for i,item in enumerate(inventory_slots):
            rect=pygame.Rect(200+(i%5)*50,300+(i//5)*50,40,40)
            pygame.draw.rect(screen,(120,120,120),rect)
            if inventory[item] > 0:
                if item in item_only:
                    draw_item_texture(screen, item, rect.inflate(-20,-20))
                else:
                    draw_block_texture(screen, item, rect.inflate(-10,-10))
            if inventory[item] > 0:
                count_text=font.render(str(inventory[item]),True,(255,255,255))
                screen.blit(count_text,(rect.x+20,rect.y+15))
        # Recipe book (properly indented!)
        draw_recipe_book(screen, personal_recipes, 500, 200)

    # --- Crafting Table GUI ---
    if crafting_table_open:
      pygame.draw.rect(screen,(70,70,70),(150,150,400,400))
      # draw crafting table slots...
      rect_out = pygame.Rect(350, 220, 50, 50)
      pygame.draw.rect(screen, (180,180,180), rect_out)
      draw_result_slot(screen, table_result, rect_out, table_recipes)

      # Recipe book
      draw_recipe_book(screen, table_recipes, 550, 180)


    # --- Draw dragging item ---
    if dragging_item:
        item_name = dragging_item[2]
        rect = pygame.Rect(mx-20, my-20, 40, 40)
        if item_name in item_only:
            draw_item_texture(screen, item_name, rect)
        else:
            draw_block_texture(screen, item_name, rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()