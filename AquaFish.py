#!/usr/bin/env python

import random, os.path

#import basic pygame modules
import pygame
import time

from pygame.locals import *

#see if we can load more than standard BMP
if not pygame.image.get_extended():
    raise SystemExit("Sorry, extended image module required")


#game constants
ALIEN_ODDS     = 22    #chances a new alien appears
BOMB_ODDS      = 60    #chances a new bomb will drop
MAX_FISHES     = 10    #frames between new aliens
SCREENRECT     = Rect(0, 0, 640, 357)
SCORE          = 0

main_dir = os.path.split(os.path.abspath(__file__))[0]

def load_image(file):
    "loads an image, prepares it for play"
    file = os.path.join(main_dir, 'data', 'img', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s'%(file, pygame.get_error()))
    return surface.convert()

def load_images(*files):
    imgs = []
    for file in files:
        imgs.append(load_image(file))
    return imgs


class dummysound:
    def play(self): pass

def load_sound(file):
    if not pygame.mixer: return dummysound()
    file = os.path.join(main_dir, 'data', 'music', file)
    try:
        sound = pygame.mixer.Sound(file)
        return sound
    except pygame.error:
        print ('Warning, unable to load, %s' % file)
    return dummysound()



# each type of game object gets an init and an
# update function. the update function is called
# once per frame, and it is when each object should
# change it's current position and state. the Player
# object actually gets a "move" function instead of
# update, since it is passed extra information about
# the keyboard


class Player(pygame.sprite.Sprite):
    speed = 10
    bounce = 24
    gun_offset = -11
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = 0
        self.origtop = self.rect.top
        self.facing = -1

    def move(self, direction):
        if direction: self.facing = direction
        self.rect.move_ip(direction*self.speed, 0)
        self.rect = self.rect.clamp(SCREENRECT)
        if direction < 0:
            self.image = self.images[0]
        elif direction > 0:
            self.image = self.images[1]
        self.rect.top = self.origtop - (self.rect.left//self.bounce%2)

    def gunpos(self):
        pos = self.facing*self.gun_offset + self.rect.centerx
        return pos, self.rect.top


class Fish(pygame.sprite.Sprite):
    speed = [1, 5]
    images = []
    current_speed = 0
    last_speed_change = 0
    last_deep_change = 0
    last_facing_change = 0

    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.facing = self.get_speed(force=1)
        self.frame = 0
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def get_speed(self, force=0):
        if time.time() > self.last_speed_change + 2 and random.choice((0,1)) or force:
            self.facing = random.choice((-1,1)) * random.randrange(self.speed[0], self.speed[1], 1)
            self.last_speed_change = time.time()
        # print(time.time(), self.last_speed_change + 0.2)

        return self.facing

    def update(self):
        self.facing = self.get_speed()
        self.rect.move_ip(self.facing, 0)

        if not SCREENRECT.contains(self.rect) or random.choice((0,1)):
            if not SCREENRECT.contains(self.rect) or random.choice((0,1)) and self.last_facing_change + 10 < time.time() :
                self.facing = -self.facing;
                self.last_facing_change = time.time()
                if random.choice((0,1)) and time.time() > self.last_deep_change + 2 :
                    self.last_deep_change = time.time()
                    if random.choice((0,1)) : 
                        self.rect.top = self.rect.bottom + 1
                    else :
                        self.rect.bottom = self.rect.top - 1


                self.rect = self.rect.clamp(SCREENRECT)

        self.frame = self.frame + 1
        if self.facing < 0:
                self.image = self.images[0]
        elif self.facing > 0:
            self.image = self.images[1]


class Explosion(pygame.sprite.Sprite):
    defaultlife = 12
    animcycle = 3
    images = []
    def __init__(self, actor):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.life = self.defaultlife

    def update(self):
        self.life = self.life - 1
        self.image = self.images[self.life//self.animcycle%2]
        if self.life <= 0: self.kill()


class Shot(pygame.sprite.Sprite):
    speed = -11
    images = []
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.top <= 0:
            self.kill()


class Bomb(pygame.sprite.Sprite):
    speed = 9
    images = []
    def __init__(self, alien):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=
                    alien.rect.move(0,5).midbottom)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.bottom >= 470:
            Explosion(self)
            self.kill()


class Score(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 20)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 340)

    def update(self):
        if SCORE != self.lastscore:
            self.lastscore = SCORE
            msg = "[SPACE] -- create new fish | [R] -- delete fish | [LSHIFT+R]  -- delete all fishes | Total fishes: %d of %d" % (SCORE, MAX_FISHES)
            self.image = self.font.render(msg, 0, self.color)



def main(winstyle = 0):
    # Initialize pygame
    pygame.init()
    if pygame.mixer and not pygame.mixer.get_init():
        print ('Warning, no sound')
        pygame.mixer = None

    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    #Load images, assign to sprite classes
    #(do this before the classes are used, after screen setup)
    img = load_image('f_gold.png')
    img = load_image('f_gold.png')
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]

    img = load_image('f_gold.png')
    Fish.images =  [img, pygame.transform.flip(img, 1, 0)]

    #decorate the game window
    icon = pygame.transform.scale(Fish.images[0], (32, 32))
    pygame.display.set_icon(icon)
    pygame.display.set_caption('Pygame Fishs')
    pygame.mouse.set_visible(0)

    #create the background, tile the bgd image
    bgdtile = load_image('ocean.jpg')
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    #load the sound effects
    boom_sound = load_sound('boom.wav')
    shoot_sound = load_sound('car_door.wav')
    if pygame.mixer:
        music = os.path.join(main_dir, 'data', 'music', 'Aqua.wav')
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1)

    # Initialize Game Groups
    fishes = pygame.sprite.Group()
    all = pygame.sprite.RenderUpdates()

    #assign default groups to each sprite class
    Fish.containers = fishes, all
    Explosion.containers = all
    Score.containers = all

    #Create Some Starting Values
    # global score
    clock = pygame.time.Clock()

    #initialize our starting sprites
    global SCORE

    # Fish() #note, this 'lives' because it goes into a sprite group
    if pygame.font:
        all.add(Score())

    last_created_time = 0

    while 1:

        #get input
        for event in pygame.event.get():
            if event.type == QUIT or \
                (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return

        #to avoid fast fist creating
        if last_created_time + 0.15 < time.time() :
            last_created_time = time.time()
            keystate = pygame.key.get_pressed()

            # Create new fish
            if keystate[K_SPACE] and (len(fishes) < MAX_FISHES):
                SCORE += 1
                fishes.add(Fish())
            # Deleting fish
            if keystate[K_r] :
                fish_sprites = fishes.sprites()
                if keystate[K_LSHIFT] :
                    for f in fish_sprites :
                        f.kill()
                    SCORE = 0
                elif len(fish_sprites) > 0:
                    fish_sprites[0].kill()
                    SCORE -= 1

        # clear/erase the last drawn sprites
        all.clear(screen, background)

        #update all the sprites
        all.update()

        # # Detect collisions
        # for alien in pygame.sprite.spritecollide(player, fishes, 1):
        #     boom_sound.play()
        #     Explosion(alien)
        #     Explosion(player)
        #     SCORE = SCORE + 1
        #     player.kill()

        #draw the scene
        dirty = all.draw(screen)
        pygame.display.update(dirty)

        #cap the framerate
        clock.tick(40)

    if pygame.mixer:
        pygame.mixer.music.fadeout(1000)
    pygame.time.wait(1000)
    pygame.quit()



#call the "main" function if running this script
if __name__ == '__main__': main()

