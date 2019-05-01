import pygame
from pygame import *
import time
import copy
from math import tan, atan, pi
from random import randint

class Enemy():
    def __init__(self, enemytype, gridloc, wave, order):
        self.alive = True
        self.wave = wave
        self.order = order
        self.Sprite = Sprite(enemytype)
        self.enemytype = enemytype
        self.ongrid = False
        self.forming = True
        self.gridloc = gridloc
        self.togrid = False
        self.dieonhit = True
        self.speed = 10#.8 #need to update as level progress TODOlvl
        self.attacking = False #not sure how I'll use this one --> Now I know yay
        self.dest = (0,0)
        self.route = -1
        self.path = []
        self.x = -50
        self.y = -50
        self.following = False #used by moths when patrolling w/ bats
        self.points = 0
        self.lastshot = time.time() - 20
        self.cooldown = 20#find a way to change this on level increment
        self.splitting = False
        self.capturing = False

    #resets boolean switches to start values, as well as clearing other information
    #used when spawning in enemies after they are killed (also at start, but it doesn't/shouldn't(!) change anything)
    #without this enemy behaviour might be odd after re-spawning
    def spawn(self):
        global level
        self.alive = True
        self.ongrid = False
        self.forming = True
        self.togrid = False
        self.dieonhit = True
        if self.enemytype == "Bat2":
            self.dieonhit = False
        self.attacking = False
        self.following = False
        self.path= []
        self.cooldown = 20 - ((level-1)/16)
        self.lastshot = time.time() - self.cooldown + 2
        self.speed = 10 + ((level-1)/20)

    #Handles enemy movement
    #Called every loop that the enemy is alive for
    #Not responsible for making decisions
    #Will warp enemies from below the screen to above the screen
    def move(self):
        if self.ongrid: #or following: moth movement will be decided in part by bat movement??? not sure
            self.set_grid_coords()
        elif self.capturing and len(self.path) == 0:
            self.capture()
        else:
            if self.y >= 600 and not self.following:
                #ATT put a check here to det enemy behaviour based on ememies left
                self.warp_to_top()
                if self.enemytype == "Bat2":
                    for follower in self.followers:
                        follower.warp_to_top()
                    self.release_moths()

            self.shoot()#enemy has a random chance of firing a bullet
            self.ongrid = False #Unnecessary
            atdest = self.move_direct() #atdest doubles as a number showing how much unused speed the enemy has
            while atdest:
                self.next_dest(1)
                atdest = self.move_direct(atdest)

    def next_dest(self, go = 0):
        if len(self.path) == 0 and go == 1:
            self.togrid = True
        if self.splitting and self.togrid:
            self.dest = (gx, gy + 80)
            self.splitting = False
        elif self.togrid:
            self.dest = self.get_grid_coords()
        elif go == 1:
            self.dest = self.path[0]
            self.path.pop(0)
        self.face_dest()

    #turns the sprite towards its destination
    #needs tweaking b/c of quandrants etc
    def face_dest(self):
        x = self.x
        y = self.y
        (destx,desty) = self.dest
        deltax = destx-x
        deltay = desty-y
        
        if deltay == 0: #Divide by zero error avoidance
            return False
        angle = (atan(deltax/deltay) /pi) * 180
        if deltay > 0: #awful
            angle += 180
        if self.ongrid: #TEMPish
            angle = 0
        if self.enemytype == "Bat2":
            self.okSprite.rotate_to(angle)
        self.Sprite.rotate_to(angle)


    def face_up(self):
        if self.enemytype == "Bat2":
            self.okSprite.rotate_to(0)
        self.Sprite.rotate_to(0)
        

    #disgusting, but works
    #moves to enemy directly towards its next destination
    #if the enemy makes it to it's destination, tries to save remaining speed
    #This is actually STUPID (not self-demeaning this time) b/c the speed is split up into x & y,
    #which makes it difficult
    def move_direct(self, remainingspeed = 0): #returns remaining distance.
        speed = self.speed
        if remainingspeed > 0:
            speed = remainingspeed
        dest = self.dest
        (destx,desty) = dest
        (rx,ry) = (0,0)
        xdist = destx-self.x
        ydist = desty-self.y
        n = (xdist**2 + ydist**2)**.5
        if n == 0:
            return True
        unitx = xdist/n
        unity = ydist/n
        deltax = unitx*speed
        deltay = unity*speed
        #this next bit is prob. unnessesary
        if abs(deltax) > abs(xdist):
            self.x = destx
            rx = abs(deltax-xdist)
        else:
            self.x += deltax
        if abs(deltay) > abs(ydist):
            self.y = desty
            ry = abs(deltay-ydist)
        else:
            self.y += deltay
        #print('ha')
        (x,y) = self.get_grid_coords()
        if x == self.x and y == self.y:
            self.ongrid = True
            self.attacking = False
            self.face_up()
            return False
        else:
            self.ongrid = False
        if rx > 0 and ry > 0:
            return (rx**2 + ry**2)**.5 #True
        return False

    def warp_to_top(self):
        self.y -= 700
        self.path = []
        self.togrid = True
        self.next_dest()

    def path_from_spot(self, pathnum, spot):
        newpath = copy.copy(pathlists[pathnum])
        (spotx,spoty) = spot
        for point in newpath:
            (x,y) = point
            x += spotx
            y += spoty
            self.path.append((x,y))

    def path_from_loc(self, pathnum, extray = 0):
        spot = (self.x, self.y+extray)
        self.path_from_spot(pathnum, spot)
        #DELETE
        '''
        newpath = copy.copy(pathlists[pathnum])
        for i in newpath:
            (x,y) = i
            x += self.x
            y += self.y + extray
            self.path.append((x,y))
        '''

    def set_grid_coords(self):
        (x,y) = self.get_grid_coords()
        self.x = x
        self.y = y

    def get_grid_coords(self):
        (x,y) = self.gridloc
        x*= 48 +gridspacing
        x += gridx
        y*= 50
        y += gridy
        return (x,y)

    def draw(self):
        global gridx,gridy, screen, gridspacing
        if self.dieonhit == False:
            sprite = self.okSprite.pic
        else:
            sprite = self.Sprite.pic
        if self.ongrid:
            self.set_grid_coords()
        screen.blit(sprite, (self.x,self.y))


    #to be overridden
    def attack(self, omnidir = False, diroverride = -1):
        self.ongrid = False
        self.togrid = False
        self.attacking = True
        if omnidir and diroverride == -1: #Bats can veer off of the grid to either side
            nowdir = randint(0,1)
            if nowdir == 0:
                self.path_from_loc(4)
            else:
                self.path_from_loc(5)
            return nowdir
        else:
            (x,y) = self.gridloc
            if (x >= 5 and diroverride == -1) or diroverride == 1:
                self.path_from_loc(5)
                return 1
            else:
                self.path_from_loc(4)
                return 0

    def shoot(self):
        global level
        chance = randint(1, 10000)
        if chance <= level and time.time() - self.lastshot > self.cooldown:
            ebullets.append(Bullet(False,(self.x+20,self.y+48)))
            self.lastshot = time.time()
        

    def get_points(self):
        if not self.ongrid:
            return int(self.points *2)
        return self.points

    def destroy(self):
        if self.enemytype == "Bat2":
            self.release_moths()
            if not self.dieonhit:
                self.dieonhit = True
                return False
            else:
                self.alive = False
                if self.capturing:
                    self.capturing = False
                    capturing = False
        else:
            self.alive = False
        return True

class Bat(Enemy):
    def __init__(self, gridloc, wave, order):
        Enemy.__init__(self, "Bat2", gridloc, wave, order)
        self.points = 200
        self.dieonhit = False
        self.okSprite = Sprite("Bat1")
        self.moths = []
        self.followers = []
        self.capturing = False
        self.hasship = False
        self.netstage = 0
        self.netwait = 1.5 #does not change with level
        self.netupdate = -1

    def attack(self):
        global capturing, secondship
        direction = super(Bat, self).attack(True)
        choice = randint(0,4)
        if choice == 1 and not capturing and not secondship: #maybe make sure no other bats are capturing? #TODO get rid of 'not' in this conditional. It is only there to test capturing behaviour
            x = int((randint(5,30)*4)*((randint(0,1)*2)-1))
            self.path += [(self.x+x, 370),(self.x+x,610)]
            self.capturing = True
            capturing = True
        else:
            self.path_from_loc(12+direction)
            self.next_dest(1)
            if choice >= 2:
                self.take_moths(direction)
            

    def set_moths(self):
        (x,y) = self.gridloc
        #On the left moth priority goes centre, left, right
        #On the right moth priority goes centre, right, left
        if x == 3:
            self.moths = [E[6],E[5],E[7]]
        elif x == 4:
            self.moths = [E[7],E[6],E[8]]
        elif x == 5:
            self.moths = [E[8],E[9],E[7]]
        elif x == 6:
            self.moths = [E[9],E[10],E[8]]

    #TODO: make it so the number of moths taken is different (1, 2, or 3, not just 3 all the time)
    def take_moths(self, direction):
        nummoths = int(randint(1,10)**.5)
        for moth in self.moths:
            if moth.ongrid and nummoths > 0:
                moth.ongrid = False
                moth.following = True
                super(Moth, moth).attack(False, direction)
                moth.path_from_loc(12+direction)
                moth.next_dest(1)
                self.followers.append(moth)
                nummoths -= 1

    def release_moths(self):
        for moth in self.followers:
            moth.togrid = True
            moth.following = False
        self.followers = []

    def capture(self):
        global capturing, Net
        if self.netupdate == -1:
            self.netupdate = time.time()
            self.Sprite.rotate_to(180)
            self.okSprite.rotate_to(180)
            #create capture area for gameloop
        elif time.time() - self.netupdate > self.netwait:
            self.netstage += 1
            self.netupdate = time.time()
            if self.netstage == 3:
                Net = (self, self.x-55, self.x+55)  
        if self.netstage == 4:
            self.netupdate = -1
            self.netstage = 0
            self.capturing = False
            capturing = False
            Net = -1

    def draw(self):
        super(Bat, self).draw()
        if self.netstage == 1:
            screen.blit(netSm,(self.x-24, self.y + 50))
        elif self.netstage == 2:
            screen.blit(netMed,(self.x-24, self.y + 50))
        elif self.netstage == 3:
            screen.blit(netLrg,(self.x-24, self.y + 50))
        if self.hasship:
            screen.blit(netCap, (self.x-1, self.y - 57))
        

class Moth(Enemy):
    def __init__(self, gridloc, wave, order):
        Enemy.__init__(self, "Moth", gridloc, wave, order)
        self.points = 80
        self.turnlist = [250, 400, 550]
        self.minlimits = [30, 50, 10]
        self.maxlimits = [60, 100, 20]

    def attack(self):#moth should turn at 250, 400, 550
        direction = super(Moth, self).attack()
        #remember: 0 is left, 1 is right
        direction = (direction*-2)+1 #0 --> 1, 1 --> -1

        for i in range(0,3):
            lastspot = self.path[-1]
            nextturn = randint(self.minlimits[i],self.maxlimits[i]) * 4 #make this different for last turn
            (nextx,nexty) = lastspot
            nextx += (nextturn * direction)
            if nextx < -40:
                nextx = -40
            elif nextx > 590:
                nextx = 590
            nexty = self.turnlist[i]
            self.path_from_spot(6+int((direction+1)/2), (nextx,nexty))
            direction *= -1

        self.next_dest(1)
        

class Wasp(Enemy):
    def __init__(self, gridloc, wave, order):
        Enemy.__init__(self, "Wasp", gridloc, wave, order)
        self.points = 50

    def attack(self):
        super(Wasp, self).attack()
        (x,y) = self.gridloc
        extray = 0
        if y == 4:
            extray = 50
        pathnum = 8
        if x >= 5:
            pathnum += 1
        self.path_from_loc(pathnum, extray)
        self.next_dest(1)

class Sprite(): #TODO: expand for bullets & player
    def __init__(self, imagetype):
        self.imagetype = imagetype
        self.pic = ""
        if self.imagetype == "Bat1":
            self.pic = bat
        elif self.imagetype == "Bat2":
            self.pic = bathurt
        elif self.imagetype == "Moth":
            self.pic = moth
        elif self.imagetype == "Wasp":
            self.pic = wasp
        elif self.imagetype == "goodbullet":
            self.pic = pbullet
        elif self.imagetype == "enemybullet":
            self.pic = ebullet
        self.origpic = self.pic
        self.rotation = 0

    #changes rotation by a given deltadegree
    def rotate(self, rot):
        self.rotation += rot
        self.pic = transform.rotate(self.origpic, self.rotation)

    #sets rotaion to an angle
    def rotate_to(self, rot):
        self.rotation = rot
        self.pic = transform.rotate(self.origpic, self.rotation)

class Bullet():
    def __init__(self, good, pos):
        self.good = good
        self.Sprite = ""
        self.speed = 0
        if self.good:
            self.Sprite = Sprite("goodbullet")
            self.speed = 20
        else:
            self.Sprite = Sprite("enemybullet")
            self.speed = 5
        self.pos = pos

    def move(self):
        (x,y) = self.pos
        if self.good:
            y -= self.speed
        else:
            y += self.speed
        self.pos = (x,y)

    def draw(self):
        screen.blit(self.Sprite.pic, (self.pos))

class Splat():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pics = [splatSm, splatMed, splatLrg]
        self.picnum = 0
        self.expiretime = time.time()
        self.expirestep = .2

    def draw(self):
        if time.time() - self.expiretime > self.expirestep:
            self.picnum += 1
            self.expiretime = time.time()
        if self.picnum >= 3:
            return True
        else:
            screen.blit(self.pics[self.picnum], (self.x,self.y))
            return False
        

def update_sprites(): #OBSOLETE?
    for s in range(len(sprites)):
        screen.blit(sprites[s], spritepos[s])

def update_background():
    global backgroundmid, bgmidy
    global backgroundtop, bgtopy
    global backgroundbot, bgboty
    
    screen.blit(backgroundbot, (0, bgboty))
    screen.blit(backgroundbot, (0, bgboty - 800))
    bgboty += .25
    if bgboty >= 800:
        bgboty -= 800
    
    screen.blit(backgroundmid, (0, bgmidy))
    screen.blit(backgroundmid, (0, bgmidy - 800))
    bgmidy += .5
    if bgmidy >= 800:
        bgmidy -= 800
    
    screen.blit(backgroundtop, (0, bgtopy))
    screen.blit(backgroundtop, (0, bgtopy - 800))
    bgtopy += 1
    if bgtopy >= 800:
        bgtopy -= 800

def handle_event(e):
    etype = e.type
    if etype == 2:
        if e.key == 276: #leftdown
            toggle_move("ld")
        elif e.key == 275: #rightdown
            toggle_move("rd")
        elif e.key == 122: #z
            shoot()
    #    elif e.key == 32: #TEMP
    #        print(pathpoints) #TEMP
    elif etype == 3:
        if e.key == 276: #leftup
            toggle_move("lu")
        elif e.key == 275: #rightup
            toggle_move("ru")
    #elif etype == 5: #TEMP
    #    print(e.pos) #TEMP
    #    pathpoints.append(e.pos) #TEMP
    #    #pathlists[8].append(e.pos) #TEMP
    elif etype == 12:
        pygame.quit()

def shoot():
    global alive, reclaiming, levelcomplete
    global bullets, bulletsfired
    '''
    #global cooldown, lastshot
    if alive and not reclaiming and not levelcomplete and time.time() - lastshot > cooldown:
        bullets.append(Bullet(True,(gx+21,gy+12)))
        if secondship:
            bullets.append(Bullet(True,(gx2+21,gy2+12)))
            bulletsfired += 1
        bulletsfired += 1
        lastshot = time.time()
    '''
    if alive and not reclaiming and not levelcomplete and len(bullets) < 2:
        bullets.append(Bullet(True,(gx+21,gy+12)))
        if secondship:
            bullets.append(Bullet(True,(gx2+21,gy2+12)))
            bulletsfired += 1
        bulletsfired += 1



def add_points(pts):
    global points, highscore, oneupbase, nextoneup, lives
    points += pts
    if points > highscore:
        highscore = points
    while points >= nextoneup:
        if lives < 104:
            lives += 1
            nextoneup += oneupbase
        else:
            break
        
            
def toggle_move(option):
    global moveleft,moveright
    if option == "ld":
        moveleft = True
    elif option == "lu":
        moveleft = False
    elif option == "rd":
        moveright = True
    elif option == "ru":
        moveright = False

def spawn(enemy, route):
    CE.append(enemy)
    enemy.spawn()
    if route == 0:
        enemy.x = 225
        enemy.y = -50
        enemy.route = 0
    elif route == 1:
        enemy.x = 325
        enemy.y = -50
        enemy.route = 1
    elif route == 2:
        enemy.x = -50
        enemy.y = 450
        enemy.route = 2
    elif route == 3:
        enemy.x = 600
        enemy.y = 450
        enemy.route = 3
    enemy.path = copy.copy(pathlists[enemy.route])
    if enemy.splitting:
        if enemy.route == 0 or enemy.route == 3: #hopefully I picked these right. Enemy should curve outward
            enemy.path_from_spot(5, enemy.path[-1])
        else:
            enemy.path_from_spot(4, enemy.path[-1])
            
    enemy.next_dest(1)


#kills the player's ship.
#shipid 0: normalship
#shipid 1: secondship
#awful awful nested if statements
    #(almost enough to call it an AI)
def kill(shipid):
    global immortal, alive, secondship
    global gx, gy, gpos
    global gx2,gy2,gpos2
    if not immortal:
        if shipid == 0:
            if secondship: #move the regular ship to where the secondship is, and remove the second ship
                secondship = False
                gx = gx2
                gy = gy2
                gpos = (gx,gy)
                gx2 = -100
                gy2 = -100
                gpos2 = (gx2,gy2)
            else:
                alive = False
        elif shipid == 1:
            secondship = False
            gx2 = -100
            gy2 = -100
            gpos2 = (gx2, gy2)
    
'''
routes:
        
ltop: w0moths, w4 (250,-50) '0'
rtop: w0wasps, w3 (350,-50) #TODO change these '1'
lbot: w1 (-50, 450) '2'
rbot: w2 (600, 450) '3'
'''

def gameloop():
    global gx,gy,gpos
    global gridx,gridy
    global moveleft, moveright
    global gridspacing,gridspacinggrowth,gridupdatetime,gridupdatelength, gridposchange
    global waves
    global bulletsfired, hittargets
    global points
    global alive, lives
    global level, levelcomplete
    global Net, capturing, captured
    global gx2,gy2,gpos2,secondship
    level = 0
    lastspawn = time.time()
    spawning = False#True
    forming = False#True
    attacking = False
    levelcomplete = True
    nextlevel = False
    reclaiming = False
    reclaimstage = 0
    reclaimstart = -1
    currentwave = 0
    currentorder = 0
    enemytowatch = 0
    attackwait = 5 #TEMP? 5 #time b/w calling enemies to attack #gets worse over time
    lastattack = time.time()
    Sidebar = Rect(600,-10, 220,620)
    hitlist_e = []
    hitlist_b = []
    hitlist_eb = []
    hitlist_s = []
    splats = []
    deathcooldown = 10
    deathtime = -1
    gameover = False
    levelcooldown = 5
    levelend = time.time()
    while True:
        #Order:
        #Draw, Attack, Collisions, Movement, Spawning, Deletion, Death, Gameover, Reclaimation, ~Levelup~, Events, Grid
        #need to handle: ~death~, ~gameover~, ~levelup~, reclaimation, capture
        #(capture is handled like death)
        #levelup is handled throughout code
        if nextlevel: #sets up level 
            lastspawn = time.time()
            spawning = True
            forming = True
            attacking = False
            #captured stays on as long as the player has not reclaimed their ship, even across levels
            capturing = False
            if captured and not secondship:
                capturing = True
            currentwave = 0
            currentorder = 0
            enemytowatch = 0
            lastattack = time.time()
            #update attackwait starts at 5, lowest should be 1, so 5 - int(level/64) CHECK. WHo cares about int? its time to double is fine
            attackwait = 5 - (level/64)
            #update enemies speed #Enemy().spawn() CHECK
            #assign enemies to split off CHECK
            #update enemies'  chance to shoot (may be done in Enemy() code) CHECK
            #update enemies' cooldowns CHECK
            #update num that can split off CHECK
            enemiessplitoff = randint(int(level/16),int((level+15)/16)*2)
            while enemiessplitoff > 0:
                enemy = randint(0,39)
                if not E[enemy].splitting:
                    E[enemy].splitting = True
                    enemiessplitoff -= 1
            level += 1
            nextlevel = False

        #DRAW
        #Handle sprites, bg etc
        screen.fill((255,255,255))
        update_background()

        if not gameover:
            for enemy in CE:
                enemy.draw()

            if alive:
                screen.blit(gyragia, (gx,gy))
                if reclaiming or secondship:
                    screen.blit(gyragia, (gx2,gy2))
        
            #draw bullets
            for bullet in bullets:
                bullet.draw()
            for ebullet in ebullets:
                ebullet.draw()

            for splat in splats:
                killsplat = splat.draw()
                if killsplat:
                    hitlist_s.append(splat)

        #update_sidebar
        draw.rect(screen,(255,198,64), Sidebar) #maybe change colour later. Orange maybe?  #8,100,50 was neat, but didn't work

        #display points, lives
        highscoretext = myfont40.render("High Score", 1, (0, 0, 0)) #(0,255,255) works somehow
        screen.blit(highscoretext,(600,50))
    
        highscorevalue = myfont40.render(str(highscore), 1, (0,0,0))
        screen.blit(highscorevalue, (620, 80))

        pointstext = myfont40.render("Points", 1, (0,0,0))
        screen.blit(pointstext, (600, 150))

        pointsvalue = myfont40.render(str(points), 1, (0,0,0))
        screen.blit(pointsvalue, (620, 180))

        livestext = myfont40.render("Lives", 1, (0,0,0))
        screen.blit(livestext, (600, 300))

        if lives >= 5:
            livesshown = 5
        else:
            livesshown = lives
        if lives > 5:
            livesvalue = lives - 5
        else:
            livesvalue = 0

        livesadjust = 0

        for i in range(0,livesshown):
            ii = i
            if i >= 3:
                livesadjust = 50
                ii = i-3
            screen.blit(gyragia, (600 + (50*ii),330 + livesadjust))
        if livesvalue > 0:
            livesvaluetext = myfont40.render("+" + str(livesvalue), 1, (0,0,0))
            screen.blit(livesvaluetext, (700,380))

        if level > 0:
            leveltext = myfont40.render("Level", 1, (0,0,0))
            screen.blit(leveltext, (600, 470))
    
            levelvalue = myfont40.render(str(level), 1, (0,0,0))
            screen.blit(levelvalue, (620, 500))

        if gameover:
            gameovertext = myfont40.render("GAMEOVER", 1, (0,0,0))
            screen.blit(gameovertext, (200,200))
            resettext = myfont30.render("Reset to play another game", 1, (0,0,0))
            screen.blit(resettext, (150,230))
            resulttext = myfont40.render("Result:", 1, (0,0,0))
            screen.blit(resulttext, (200, 300))
            firedtext = myfont40.render("Shots Fired: " + str(bulletsfired), 1, (0,0,0))
            screen.blit(firedtext, (220, 330))
            hittext = myfont40.render("Targets Hit: " + str(hittargets), 1, (0,0,0))
            screen.blit(hittext, (220, 360))
            if bulletsfired == 0:
                hitmiss = "0.0"
            else:
                hitmiss = str(int((hittargets*1000)/bulletsfired)/10)
            hitmisstext = myfont40.render("Hit/Miss Ratio: " + hitmiss + "%", 1, (0,0,0))
            screen.blit(hitmisstext, (220, 390))
            

        #display next level text:
        if levelcomplete:
            if time.time() - levelend <= levelcooldown - 1:
                nextleveltext = myfont40.render("LEVEL " + str(level+1), 1, (0,0,0))
                screen.blit(nextleveltext, (200,200))
            if time.time() - levelend > levelcooldown:
                levelcomplete = False
                nextlevel = True

        for point in pathpoints:
            draw.circle(screen, (128,128,128), point, 4)

        #TEMP just neat
        if showpaths:
            for e in CE:
                colour = (128,128,128)
                if e.enemytype == "Bat2":
                    colour = (0,0,0)
                elif e.enemytype == "Wasp":
                    colour = (0,162,232)
                elif e.enemytype == "Moth": #I could just do type(e) lol whatever
                    colour = (237,28,36)
            
                for point in e.path:
                    (plotx,ploty) = point
                    point = (int(plotx),int(ploty))
                    draw.circle(screen, colour, point, 4)
                
        
        #TEMP for plotting new points
        #
        #newpath = copy.copy(pathlists[4])
        #(x,y) = E[1].get_grid_coords()
        #for i in newpath:
        #    (x2,y2) = i
        #    x2+=x
        #    y2+=y
        #    draw.circle(screen, (0,0,0), (x2,y2), 4)
        #ENDTEMP    

        #display changes
        display.flip()
        
        #ATTACK
        #enemy attacks
        #TEMP #ATT: add this section back in
        
        if attacking and alive and not reclaiming and time.time() - lastattack >= attackwait:
            if len(CE) > 0:
                randenemy = CE[randint(0,len(CE)-1)]
                if not randenemy.attacking:
                    randenemy.attack()
                    lastattack = time.time()
            else:
                attacking = False
                levelcomplete = True
                levelend = time.time()
        
        #END #TEMP #ATT

        #Only to test bat attack--> comment in prev section also to use
        #if E[1].ongrid == True:
        #    E[1].attack()
        #if E[0].ongrid:
        #    E[0].attack()
        #if E[2].ongrid:
        #    E[2].attack()
        #if E[3].ongrid:
        #    E[3].attack()
            
        #COLLISIONS
        #Check all enemies & ebullets against player
        #Then check all enemies against pbullets
        if not reclaiming:
            for enemy in CE:
                x = enemy.x
                y = enemy.y
                distance = int(((x-gx)**2 + (y-gy)**2)**.5)
                if distance < 45:
                    hitlist_e.append(enemy)
                    kill(0)
                    break
                if secondship:
                    distance = int(((x-gx2)**2 + (y-gy2)**2)**.5)
                    if distance < 45:
                        hitlist_e.append(enemy)
                        kill(1)
                        break
                    
            if alive:
                for ebullet in ebullets:
                    distance = int(((x-gx)**2 + (y-gy)**2)**.5)
                    if distance < 45:
                        hitlist_e.append(enemy)
                        kill(0)
                        break
                    if secondship:
                        distance = int(((x-gx2)**2 + (y-gy2)**2)**.5)
                        if distance < 45:
                            hitlist_e.append(enemy)
                            kill(1)
                            break

        for bullet in bullets:
            (bx,by) = bullet.pos
            bx += 3
            by += 6
            for enemy in CE:
                x = enemy.x + 24
                y = enemy.y + 24
                distance = ((x-bx)**2 + (y-by)**2)**.5
                distance = int(distance)
                if distance < 20:
                    hittargets += 1
                    hitlist_e.append(enemy)
                    hitlist_b.append(bullet)
                    break

        if Net != -1:
            (bat,x1,x2) = Net
            if gx >= x1 and gx <= x2:
                Net = -1
                #capturing = False Actually we're keeping this as True, b/c then no more bats will attack
                bat.capturing = False
                bat.netstage = 0
                if not immortal:
                    captured = True
                    alive = False
                bat.hasship = True
        

        #MOVEMENT
        #enemy movement
        for enemy in CE:
            enemy.move()
        if not enemytowatch in CE and not type(enemytowatch) == int:
            enemytowatch.move()

        #bullet movement
        for bullet in bullets:
            bullet.move()
            (x,y) = bullet.pos
            if y <= -10 and bullet not in hitlist_b:
                hitlist_b.append(bullet)
                
        #bullet movement, but for enemies
        for ebullet in ebullets:
            ebullet.move()
            (x,y) = ebullet.pos
            if y >= 600 and ebullet not in hitlist_eb:
                hitlist_eb.append(ebullet)

        #player movement
        if alive and not reclaiming: #secondship hastily added at 12:46 am when I'm supposed to be asleep. Not the best code organizationally, but it /should/ work no problem
            if moveleft:
                gx -= shipspeed
                if secondship:
                    gx2 -= shipspeed
            if moveright:
                gx += shipspeed
                if secondship:
                    gx2 += shipspeed
            if gx < 0:
                gx = 0
                if secondship:
                    gx2 = 50
            elif gx > 550:
                gx = 550
            elif secondship and gx > 500:
                gx = 500
                gx2 = 550
            gpos = (gx,gy)
            gpos2 = (gx2,gy2)
        #else: #not sure why this is here, it should not be
        #    gpos = (300,530)
            
        #SPAWNING
        #enemy formation
        if forming and not spawning:
            if enemytowatch.ongrid == True:
                spawning = True
                lastspawn = time.time() + .5 #not true, but gives time buffer
            
        if forming and spawning and time.time() - lastspawn > .3:
            #if nextwave == currentwave:
            #    nextwave += 1
            if currentwave == 0:
                enemy = waves[currentwave][currentorder]
                spawn(enemy, 0)
                enemy = waves[currentwave][currentorder+4]
                spawn(enemy, 1)
            elif currentwave == 1:
                enemy = waves[currentwave][currentorder]
                spawn(enemy, 2)
            elif currentwave == 2:
                enemy = waves[currentwave][currentorder]
                spawn(enemy, 3)
            elif currentwave == 3:
                enemy = waves[currentwave][currentorder]
                spawn(enemy, 1)
            elif currentwave == 4:
                enemy = waves[currentwave][currentorder]
                spawn(enemy, 0)
            currentorder += 1
            if currentwave == 5:
                forming = False
                currentwave = 0
                nextwave = 0
                enemytowatch = 0
            if (currentwave == 0 and currentorder == 4) or (currentorder == 8):
                currentwave += 1
                currentorder = 0
                enemytowatch = enemy
                spawning = False
            
            lastspawn = time.time()


        #DELETION
        #streamline this. use classes or something, you should've have to repeat yourself to find collisions like this
        #find a non-trash way of detecting collisions...
        #I added the try-except b/c the game was trying to delete enemies twice, and this is the laziest way to deal with it
        for e in hitlist_e:
            try:
                died = e.destroy()
                if died: #bats should still be alive after one hit
                    add_points(e.get_points())
                    CE.pop(CE.index(e))
                    if e.enemytype == "Bat2" and e.hasship:
                        e.hasship = False
                        reclaiming = True
                        gx2 = e.x
                        gy2 = e.y-57
                    splats.append(Splat(e.x,e.y))
            except:
                pass
        hitlist_e = []
        for eb in hitlist_eb:
            try:
                ebullets.pop(ebullets.index(eb))
            except:
                pass
        hitlist_eb = []
        for b in hitlist_b:
            try:
                bullets.pop(bullets.index(b))
            except:
                pass
        hitlist_b = []
        for s in hitlist_s:
            try:
                splats.pop(splats.index(s))
            except:
                pass
        hitlist_s = []


        
        #DEATH
        if not alive and deathtime == -1:
            lives -= 1
            gpos = (-100,-100)
            (gx,gy) = gpos
            #for enemy in CE:
            #    enemy.togrid = True
                #enemy.path = []
            splats.append(Splat(gx,gy))
            deathtime = time.time()
        elif not alive:
            if time.time() - deathtime >= deathcooldown:
                alive = True
                gpos = (300,530)
                (gx,gy) = gpos
                deathtime = -1


        #GAMEOVER
        if lives < 0:
            gameover = True
            
        #RECLAIM
        if reclaiming: #most of this code could be in a function b/c it is repetitive but ehhhh
            if reclaimstage == 0: #just turn the capture bools off
                capturing = False
                captured = False
                reclaimstage += 1
            elif reclaimstage == 1: #move main ship to (250,550) on the screen slowly
                if abs(gx-250) <= 5:
                    gx = 250
                    reclaimstage += 1
                elif gx > 250:
                    gx -= 5
                elif gx < 250:
                    gx += 5
            elif reclaimstage == 2: #move secondship up/down to a spot (300,350) on the screen
                if abs(gy2-350) <= 5:
                    gy2 = 350
                    reclaimstage += 1
                elif gy2 > 350:
                    gy2 -= 5
                elif gy2 < 350:
                    gy2 += 5
            elif reclaimstage == 3: #move secondship left/right to a spot (300,350) on the screen
                if abs(gx2-300) <= 5:
                    gx2 = 300
                    reclaimstage += 1
                elif gx2 > 300:
                    gx2 -= 5
                elif gx2 < 300:
                    gx2 += 5
            elif reclaimstage == 4: #wait a bit
                if reclaimstart == -1:
                    reclaimstart = time.time()
                if time.time() - reclaimstart >= 5:
                    reclaimstart = -1
                    reclaimstage += 1
            elif reclaimstage == 5: #move secondship left/right to a final spot (300,550) on the screen
                if abs(gy2-530) <= 5:
                    gy2 = 530
                    reclaimstage += 1
                elif gy2 > 530:
                    gy2 -= 5
                elif gy2 < 530:
                    gy2 += 5
            elif reclaimstage == 6:
                reclaiming = False
                secondship = True
                gx2 = gx+50
                gy2 = gy
                reclaimstage = 0
            #move g1 to centre bottom, while moving g2 next to g1. Once (use if) both ships are in position, set reclaiming to False, secondship to True

        #LEVELUP
        #Not here oops


        #EVENTS
        #Handle Events
        events = event.get()
        for e in events:
            handle_event(e)

        #GRID
        #grid shrinking/expanding
        if time.time()-gridupdatetime >= gridupdatelength:
            if not attacking:
                gridx += gridposchange
                if gridx == 70 or gridx == 30:
                    gridposchange *= -1
                gridupdatetime = time.time()
                if not forming and gridx == 50:
                    attacking = True
                    for e in CE:
                        e.forming = False
            else:
                #TEMP!! put code back in later
                gridspacing += gridspacinggrowth
                gridx -= (gridspacinggrowth * 5)
                if gridspacing == 5:
                    gridspacinggrowth = -1
                elif gridspacing == 1:
                    gridspacinggrowth = 1
                gridupdatetime = time.time()
    



pygame.init()
font.init()
myfont40 = font.Font(None, 40)
myfont30 = font.Font(None, 30)

screen = display.set_mode((800,600))

#TEMP
pathpoints = []#[(110, 341), (170, 371), (339, 378), (362, 383), (383, 394), (399, 404), (414, 417), (425, 439), (430, 467), (429, 498), (427, 533), (422, 558), (402, 585), (384, 593), (356, 596), (315, 594), (282, 592), (262, 577), (254, 561), (250, 540)]

alive = True
gx = 300
gy = 530
gpos = (gx,gy)
gx2 = -100
gy2 = -100
gpos2 = (gx2,gy2) #used for the second ship
secondship = False
moveleft = False
moveright = False

shipspeed = 7.5

(gridx,gridy) = (50,10)
gridspacing = 3
gridspacinggrowth = 1
gridposchange = 5
gridupdatelength = 1
gridupdatetime = time.time()

bulletsfired = 0
hittargets = 0
lastshot = -1
cooldown = .75

gyragia = image.load('Gyragia.png')
gyragia = transform.scale(gyragia, (48,48))
moth = image.load("badmoth.png")
moth = transform.scale(moth, (48,48))
wasp = image.load("badwasp.png")
wasp = transform.scale(wasp, (48,48))
bat = image.load("badbat.png")
bat = transform.scale(bat, (48,48))
bathurt = image.load("badbathurt.png")
bathurt = transform.scale(bathurt, (48,48))
pbullet = image.load("badbullet.png")
pbullet = transform.scale(pbullet, (8,16))
ebullet = image.load("ebullet.png")
ebullet = transform.scale(ebullet, (6,12))

netSm = image.load("NetSm.png")
netSm = transform.scale(netSm, (96,144))
netMed = image.load("NetMed.png")
netMed = transform.scale(netMed, (96,144))
netLrg = image.load("NetLrg.png")
netLrg = transform.scale(netLrg, (96,144))
netCap = image.load("NetCap.png")
netCap = transform.scale(netCap, (50,50))

splatSm = image.load("SplatSm.png")
splatSm = transform.scale(splatSm, (48,48))
splatMed = image.load("SplatMed.png")
splatMed = transform.scale(splatMed, (48,48))
splatLrg = image.load("SplatLrg.png")
splatLrg = transform.scale(splatLrg, (48,48))
splats = []
hitlist_s = []


backgroundtop = image.load("HighClouds.png")
backgroundtop = transform.scale(backgroundtop, (600,800))
backgroundmid = image.load("LowClouds.png")
backgroundmid = transform.scale(backgroundmid, (600,800))
backgroundbot = image.load("land.png")
backgroundbot = transform.scale(backgroundbot, (600,800))

bgtopy = -100
bgmidy = -100
bgboty = -100

level = 0
levelcomplete = True

lives = 3
points = 0
highscore = 30000 #later get this from a file
oneupbase = 30000
nextoneup = 30000

capturing = False
captured = False
Net = -1
reclaiming = False


waveorder =                   [[1,0],[1,2],[1,4],[1,6],
                   [2,1],[2,3],[1,1],[0,0],[0,1],[1,3],[2,0],[2,2],
                   [2,5],[2,7],[1,5],[0,2],[0,3],[1,7],[2,4],[2,6],
             [4,0],[4,2],[3,1],[3,3],[0,4],[0,5],[3,0],[3,2],[4,1],[4,3],
             [4,4],[4,6],[3,5],[3,7],[0,6],[0,7],[3,4],[3,6],[4,5],[4,7]]
waves = [[],[],[],[],[]]

for wave in waves:
    for i in range(8):
        wave.append(0)
        
pathlists = [[(204, 4), (211, 40), (220, 65), (236, 81), (261, 92), (306, 110), (365, 136), (421, 156), (465, 179), (492, 200), (509, 219), (517, 239), (527, 263), (529, 287), (524, 309), (512, 331), (500, 347), (476, 371), (455, 386), (430, 396), (396, 400), (364, 393), (331, 376), (305, 360)],#, (277, 340)],
             [(346, 4), (339, 40), (330, 65), (314, 81), (289, 92), (244, 110), (185, 136), (129, 156), (85, 179), (58, 200), (41, 219), (33, 239), (23, 263), (21, 287), (26, 309), (38, 331), (50, 347), (74, 371), (95, 386), (120, 396), (154, 400), (186, 393), (219, 376), (245, 360)],# (273, 340)],
             [(0, 469), (40, 464), (68, 461), (104, 452), (126, 446), (156, 436), (180, 425), (192, 415), (202, 399), (211, 379), (212, 357), (212, 333), (204, 314), (194, 298), (182, 285), (166, 272), (148, 264), (128, 260), (104, 257), (78, 258), (59, 270), (50, 287), (43, 305), (37, 325), (40, 347), (50, 367), (68, 378), (87, 390), (110, 399), (134, 404), (157, 408), (175, 410), (201, 410), (220, 405), (240, 392), (252, 379)],
             [(550, 469), (510, 464), (482, 461), (446, 452), (424, 446), (394, 436), (370, 425), (358, 415), (348, 399), (339, 379), (338, 357), (338, 333), (346, 314), (356, 298), (368, 285), (384, 272), (402, 264), (422, 260), (446, 257), (472, 258), (491, 270), (500, 287), (507, 305), (513, 325), (510, 347), (500, 367), (482, 378), (463, 390), (440, 399), (416, 404), (393, 408), (375, 410), (349, 410), (330, 405), (310, 392), (298, 379)],
             [(0,0),(0,-20),(-33,-34),(-49,-31),(-56,-18)],
             [(0,0),(0,-20),(33,-34),(49,-31),(56,-18)],
             [(0, 0), (-23, 9), (-34, 24), (-40, 44), (-33, 62), (-17, 72), (-1, 77)],#[(206, 113), (183, 122), (172, 137), (166, 157), (173, 175), (189, 185), (205, 190)],
             [(0, 0), (23, 9), (34, 24), (40, 44), (33, 62), (17, 72), (1, 77)],
             [(-42, 81), (18, 111), (187, 118), (210, 123), (231, 134), (247, 144), (262, 157), (273, 179), (278, 207), (277, 238), (275, 273), (270, 298), (250, 325), (232, 333), (204, 336), (163, 334), (130, 332), (110, 317), (102, 301), (98, 280)],#[(110, 341), (170, 371), (339, 378), (362, 383), (383, 394), (399, 404), (414, 417), (425, 439), (430, 467), (429, 498), (427, 533), (422, 558), (402, 585), (384, 593), (356, 596), (315, 594), (282, 592), (262, 577), (254, 561), (250, 540)], #adjusted from (152, 260)
             [(42, 81), (-18, 111), (-187, 118), (-210, 123), (-231, 134), (-247, 144), (-262, 157), (-273, 179), (-278, 207), (-277, 238), (-275, 273), (-270, 298), (-250, 325), (-232, 333), (-204, 336), (-163, 334), (-130, 332), (-110, 317), (-102, 301), (-98, 280)],
             [],
             [],
             [(-56, 13), (-57, 51), (-52, 102), (-48, 150), (-35, 190), (-25, 206), (-16, 219), (-3, 229), (13, 237), (29, 234), (46, 229), (64, 217), (73, 204), (78, 191), (83, 169), (81, 153), (78, 138), (70, 128), (62, 117), (50, 111), (27, 104), (6, 109), (-9, 118), (-20, 136), (-30, 151), (-34, 170), (-37, 184), (-34, 201), (-25, 221), (-15, 234), (-5, 243), (14, 257), (28, 265), (44, 275), (54, 284), (67, 296), (77, 306), (84, 317), (94, 330), (100, 343), (113, 362), (119, 377), (124, 390), (128, 408), (131, 419), (138, 440), (139, 456), (140, 470), (140, 489), (141, 503), (141, 520), (141, 533), (141, 540)],#[(198, 73), (197, 111), (202, 162), (206, 210), (219, 250), (229, 266), (238, 279), (251, 289), (267, 297), (283, 294), (300, 289), (318, 277), (327, 264), (332, 251), (337, 229), (335, 213), (332, 198), (324, 188), (316, 177), (304, 171), (281, 164), (260, 169), (245, 178), (234, 196), (224, 211), (220, 230), (217, 244), (220, 261), (229, 281), (239, 294), (249, 303), (268, 317), (282, 325), (298, 335), (308, 344), (321, 356), (331, 366), (338, 377), (348, 390), (354, 403), (367, 422), (373, 437), (378, 450), (382, 468), (385, 479), (392, 500), (393, 516), (394, 530), (394, 549), (395, 563), (395, 580), (395, 593), (395, 600)] #adjust above to (254, 60)
             [(56, 13), (57, 51), (52, 102), (48, 150), (35, 190), (25, 206), (16, 219), (3, 229), (-13, 237), (-29, 234), (-46, 229), (-64, 217), (-73, 204), (-78, 191), (-83, 169), (-81, 153), (-78, 138), (-70, 128), (-62, 117), (-50, 111), (-27, 104), (-6, 109), (9, 118), (20, 136), (30, 151), (34, 170), (37, 184), (34, 201), (25, 221), (15, 234), (5, 243), (-14, 257), (-28, 265), (-44, 275), (-54, 284), (-67, 296), (-77, 306), (-84, 317), (-94, 330), (-100, 343), (-113, 362), (-119, 377), (-124, 390), (-128, 408), (-131, 419), (-138, 440), (-139, 456), (-140, 470), (-140, 489), (-141, 503), (-141, 520), (-141, 533), (-141, 540)]]

#a different helpful tool
'''
(primex,primey) = (254, 60)
for i in range(len(pathlists[12])):
    (x,y) = pathlists[12][i]
    x = x-primex
    y = y-primey
    pathlists[12][i] = (x,y)
print(pathlists[12])


for i in pathlists[12]:
    (x,y) = i
    pathlists[13].append((-x,y))
for i in pathlists:
    print(i)
'''
#paths:
#0 left top
#1 right top
#2 left bot
#3 right bot
#4 left spinout
#5 right spinout
#6 left curve (used by moths)
#7 right curve (used by moths)
#8 left-right j-hook (used by wasps)
#9 right-left j-hook (used by wasps)
#10 left-right j-swoopdown (used by wasps)
#11 right-left j-swoopdown (used by wasps)
#12 loop* (used by bats)
#13 loop*
#tool for flipping pathlists around
'''
for i in pathlists[2]:
    (x,y) = i
    rem = x - 275
    x = 275 - rem
    pathlists[3].append((x,y))

print(pathlists[3])
'''



#Debugging
showpaths = False #Highlights the Enemies flight paths with dots. Default False
immortal = False #Makes the player unable to die. Default False

#DebuggingEnd

E = []
CE = []
bullets = []
ebullets = []

#should make the enemy objects eventually
#bats
w = 0
spot = 3
for i in range(4):
    #enemies.append([bat, (i+spot,1)])
    wave = waveorder[w][0]
    order = waveorder[w][1]
    E.append(Bat((i+spot,1),wave,order))
    waves[wave][order] = E[-1]
    w+=1
spot = 1
for row in range(2):
    for i in range(8):
        #enemies.append([moth, (i+spot,row+2)])
        wave = waveorder[w][0]
        order = waveorder[w][1]
        E.append(Moth((i+spot,row+2),wave,order))
        waves[wave][order] = E[-1]
        w+=1
for row in range(2):
    for i in range(10):
        #enemies.append([wasp, (i, row+ 4)])
        wave = waveorder[w][0]
        order = waveorder[w][1]
        E.append(Wasp((i,row+4),wave,order))
        waves[wave][order] = E[-1]
        w+=1

for i in range(0,4):
    E[i].set_moths() #gives the bats a list of moths each that they can call to attack with them

    


#sprites.append(gyragia)
#spritepos.append(gpos)

#screen.blit(gyragia, gpos)
#display.flip()

gameloop()
