import pygame, sys, math, random

pygame.init()
CS = 40
COLS, ROWS = 15, 10
W, H = COLS*CS, ROWS*CS + 50
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Tower Defense")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 14)
big_font = pygame.font.SysFont("monospace", 26)

PATH = [(0,4),(1,4),(2,4),(3,4),(3,3),(3,2),(4,2),(5,2),(6,2),(6,3),(6,4),
        (6,5),(6,6),(7,6),(8,6),(9,6),(9,5),(9,4),(9,3),(9,2),(10,2),(11,2),
        (12,2),(12,3),(12,4),(12,5),(12,6),(12,7),(12,8),(13,8),(14,8)]
PATH_SET = set(PATH)

TOWERS = [
    {"name":"Arrow", "cost":50,  "color":(96,165,250), "range":80,  "damage":15,"rate":45,"splash":0,  "slow":0},
    {"name":"Cannon","cost":100, "color":(249,115,22), "range":100, "damage":50,"rate":90,"splash":35, "slow":0},
    {"name":"Freeze","cost":75,  "color":(167,139,250),"range":90,  "damage":5, "rate":60,"splash":0,  "slow":60},
    {"name":"Laser", "cost":150, "color":(74,222,128), "range":120, "damage":8, "rate":8, "splash":0,  "slow":0},
]

def get_path_pos(idx):
    c,r = PATH[idx]
    return (c*CS+CS//2, r*CS+CS//2)

def can_place(col,row,towers):
    return ((col,row) not in PATH_SET and 0<=col<COLS and 0<=row<ROWS
            and not any(t["col"]==col and t["row"]==row for t in towers))

def spawn_enemy(wave, etype=0):
    types = [
        {"hp":80, "speed":1.0,"reward":10,"color":(239,68,68), "r":10},
        {"hp":200,"speed":0.6,"reward":25,"color":(249,115,22),"r":13},
        {"hp":50, "speed":1.8,"reward":15,"color":(251,191,36),"r":8},
        {"hp":500,"speed":0.5,"reward":60,"color":(124,58,237),"r":18},
    ]
    t = types[etype]
    bonus = max(0,(wave-1))*20
    px,py = get_path_pos(0)
    return {"x":float(px),"y":float(py),"pathIdx":0,"progress":0.0,
            "hp":t["hp"]+bonus,"maxHp":t["hp"]+bonus,
            "speed":t["speed"],"baseSpeed":t["speed"],
            "reward":t["reward"],"color":t["color"],"r":t["r"],
            "slow":0,"hit":0,"id":random.random()}

def build_wave(wave):
    q = []
    count = 5 + wave*2
    for i in range(count):
        etype = 0
        if wave>2 and random.random()<0.3: etype=2
        if wave>4 and random.random()<0.2: etype=1
        if wave%5==0 and i==count//2: etype=3
        q.append(etype)
    return q

def spawn_particles(x,y,color,n,particles):
    for _ in range(n):
        a=random.uniform(0,math.pi*2); s=random.uniform(1,3)
        particles.append({"x":x,"y":y,"vx":math.cos(a)*s,"vy":math.sin(a)*s,
                          "life":1.0,"color":color,"size":random.randint(1,3)})

gold=150; lives=20; wave=0; state="prep"
selected=0; towers=[]; enemies=[]; bullets=[]; particles=[]
spawn_queue=[]; spawn_timer=0; frame=0
hover_col=hover_row=-1

running=True
while running:
    clock.tick(60)
    mx,my = pygame.mouse.get_pos()
    hover_col = mx//CS; hover_row = my//CS

    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE and state=="prep":
                wave+=1; spawn_queue=build_wave(wave); spawn_timer=0; state="spawning"
            if event.key==pygame.K_SPACE and state=="dead":
                gold=150;lives=20;wave=0;state="prep";selected=0
                towers=[];enemies=[];bullets=[];particles=[];spawn_queue=[]
            for i,k in enumerate([pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4]):
                if event.key==k: selected=i
        if event.type==pygame.MOUSEBUTTONDOWN:
            if my>ROWS*CS:
                idx=(mx-10)//130
                if 0<=idx<len(TOWERS): selected=idx
            elif state in ("prep","spawning"):
                col,row=mx//CS,my//CS
                if can_place(col,row,towers) and gold>=TOWERS[selected]["cost"]:
                    gold-=TOWERS[selected]["cost"]
                    t=dict(TOWERS[selected])
                    t.update({"col":col,"row":row,"x":col*CS+CS//2,"y":row*CS+CS//2,
                               "cooldown":0,"angle":0})
                    towers.append(t)

    if state=="spawning":
        frame+=1; spawn_timer+=1
        if spawn_timer>=40 and spawn_queue:
            enemies.append(spawn_enemy(wave,spawn_queue.pop(0)))
            spawn_timer=0
        if not spawn_queue and not enemies:
            state="prep"; gold+=20+wave*5

    if state in ("spawning","prep"):
        for e in enemies:
            spd=e["baseSpeed"]*0.4 if e["slow"]>0 else e["baseSpeed"]
            e["progress"]+=spd
            if e["slow"]>0: e["slow"]-=1
            if e["hit"]>0: e["hit"]-=1
            while e["progress"]>=CS and e["pathIdx"]<len(PATH)-1:
                e["progress"]-=CS; e["pathIdx"]+=1
            if e["pathIdx"]>=len(PATH)-1:
                lives-=1; e["hp"]=0
                if lives<=0: state="dead"
            else:
                cx,cy=get_path_pos(e["pathIdx"])
                nx,ny=get_path_pos(min(e["pathIdx"]+1,len(PATH)-1))
                t=e["progress"]/CS
                e["x"]=cx+(nx-cx)*t; e["y"]=cy+(ny-cy)*t

        for t in towers:
            if t["cooldown"]>0: t["cooldown"]-=1; continue
            best=None; best_d=t["range"]
            for e in enemies:
                d=math.sqrt((e["x"]-t["x"])**2+(e["y"]-t["y"])**2)
                if d<best_d: best_d=d; best=e
            if not best: continue
            t["angle"]=math.atan2(best["y"]-t["y"],best["x"]-t["x"]); t["cooldown"]=t["rate"]
            bullets.append({"x":float(t["x"]),"y":float(t["y"]),
                "vx":math.cos(t["angle"])*6,"vy":math.sin(t["angle"])*6,
                "damage":t["damage"],"color":t["color"],"r":4,"life":120,
                "splash":t["splash"],"slow":t["slow"]})

        new_bullets=[]
        for b in bullets:
            b["x"]+=b["vx"]; b["y"]+=b["vy"]; b["life"]-=1
            hit=next((e for e in enemies if math.sqrt((b["x"]-e["x"])**2+(b["y"]-e["y"])**2)<e["r"]+b["r"]),None)
            if hit:
                if b["splash"]>0:
                    for e in enemies:
                        if math.sqrt((hit["x"]-e["x"])**2+(hit["y"]-e["y"])**2)<b["splash"]:
                            e["hp"]-=b["damage"]; e["hit"]=8
                    spawn_particles(hit["x"],hit["y"],(249,115,22),8,particles)
                else:
                    hit["hp"]-=b["damage"]; hit["hit"]=6
                    if b["slow"]: hit["slow"]=60
                    spawn_particles(b["x"],b["y"],b["color"],3,particles)
            else:
                if b["life"]>0: new_bullets.append(b)
        bullets=new_bullets

        for e in [e for e in enemies if e["hp"]<=0]:
            gold+=e["reward"]; spawn_particles(e["x"],e["y"],(251,191,36),8,particles)
        enemies=[e for e in enemies if e["hp"]>0]

        for p in particles: p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["vy"]+=0.05; p["life"]-=0.04
        particles=[p for p in particles if p["life"]>0]

    # Draw
    for c in range(COLS):
        for r in range(ROWS):
            col_c = (139,92,46) if (c,r) in PATH_SET else ((22,101,52) if (c+r)%2==0 else (21,128,61))
            pygame.draw.rect(screen,col_c,(c*CS,r*CS,CS,CS))

    # Range preview
    if 0<=hover_col<COLS and 0<=hover_row<ROWS and can_place(hover_col,hover_row,towers):
        t=TOWERS[selected]; cx=hover_col*CS+CS//2; cy=hover_row*CS+CS//2
        s=pygame.Surface((W,ROWS*CS),pygame.SRCALPHA)
        pygame.draw.circle(s,(*t["color"],40),(cx,cy),t["range"])
        pygame.draw.circle(s,(*t["color"],120),(cx,cy),t["range"],1)
        screen.blit(s,(0,0))

    for t in towers:
        pygame.draw.circle(screen,t["color"],(t["x"],t["y"]),14)
        ex=t["x"]+int(math.cos(t["angle"])*14)
        ey=t["y"]+int(math.sin(t["angle"])*14)
        pygame.draw.line(screen,(255,255,255),(t["x"],t["y"]),(ex,ey),4)

    for e in enemies:
        c=e["color"] if e["hit"]==0 else (255,255,255)
        if e["slow"]>0: c=(167,139,250)
        pygame.draw.circle(screen,c,(int(e["x"]),int(e["y"])),e["r"])
        hw=e["r"]*2
        pygame.draw.rect(screen,(69,10,10),(int(e["x"])-e["r"],int(e["y"])-e["r"]-10,hw,5))
        pygame.draw.rect(screen,(74,222,128),(int(e["x"])-e["r"],int(e["y"])-e["r"]-10,int(hw*(e["hp"]/e["maxHp"])),5))

    for b in bullets:
        pygame.draw.circle(screen,b["color"],(int(b["x"]),int(b["y"])),b["r"])

    for p in particles:
        pygame.draw.circle(screen,p["color"],(int(p["x"]),int(p["y"])),max(1,p["size"]))

    # HUD
    pygame.draw.rect(screen,(0,0,0),(0,ROWS*CS,W,50))
    for i,t in enumerate(TOWERS):
        x=10+i*130; y=ROWS*CS+8; sel=i==selected
        c=(40,40,60) if sel else (25,25,35)
        pygame.draw.rect(screen,c,(x,y,120,34),border_radius=4)
        if sel: pygame.draw.rect(screen,t["color"],(x,y,120,34),2,border_radius=4)
        pygame.draw.circle(screen,t["color"],(x+14,y+17),8)
        screen.blit(font.render(f"{i+1}:{t['name']} ${t['cost']}",True,(255,255,255)),(x+26,y+10))
    screen.blit(font.render(f"Gold:{gold}  Lives:{lives}  Wave:{wave}  SPACE=start wave",True,(255,255,255)),(530,ROWS*CS+16))

    if state=="dead":
        msg=big_font.render(f"Game Over! Wave {wave}",True,(239,68,68))
        sub=font.render("Press SPACE to restart",True,(180,180,180))
        screen.blit(msg,(W//2-msg.get_width()//2,ROWS*CS//2-20))
        screen.blit(sub,(W//2-sub.get_width()//2,ROWS*CS//2+20))
    elif state=="prep":
        msg=font.render(f"Wave {wave} cleared! +{20+wave*5} gold  |  Press SPACE for wave {wave+1}",True,(251,191,36))
        screen.blit(msg,(W//2-msg.get_width()//2,ROWS*CS//2))

    pygame.display.flip()

pygame.quit()
sys.exit()