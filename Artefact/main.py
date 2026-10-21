# -*- coding: utf-8 -*-
"""
Created on Tue Feb  3 19:53:42 2026

@author: School
"""
import pygame
import matplotlib as mpl
import numpy as np
import math

pygame.init()
pygame.display.set_caption('359510 Wildfire Spread')

screen = pygame.display.set_mode((1280,720))

clock = pygame.time.Clock()

EMBEDDED_SYSTEM_DATA = ((301.53, 0, 7), (901.80, 0, 71)) #at 901.80 milliseconds my embedded system recorded these values from my flower pot.


FPS = 120 # max fps, usually for me the fps sits at 40.
TILE_D = 32
GRID_D = 20
MAX_HEIGHT = 1000
MAX_TEMP = 1000
TRUCK_SPEED = 1.2
MAX_FIRETRUCKS = 8
MASTER_COLORS= ("#F8F95F", "#800020") 
FIRETRUCK = pygame.image.load("imgs/firetruck.png")
RAIN_IMG = pygame.image.load("imgs/rain.png")

ALARM_IMGS = [pygame.image.load("imgs/f_alarm/tile"+str(x)+".png") for x in range(10)]

GRID_IMGS = (pygame.image.load("imgs/grass.png"), pygame.image.load("imgs/tall_grass.png"),\
             pygame.image.load("imgs/bush.png"), pygame.image.load("imgs/tree.png"), pygame.image.load("imgs/fire.png"), pygame.image.load("imgs/firedepartment.png"))

BUTTONS = (pygame.image.load("imgs/button0.png"), pygame.image.load("imgs/button1.png"), pygame.image.load("imgs/button2.png"), \
           pygame.image.load("imgs/pause0.png"), pygame.image.load("imgs/pause1.png"), pygame.image.load("imgs/pause2.png"), \
           pygame.image.load("imgs/pause3.png"), pygame.image.load("imgs/pause4.png"), pygame.image.load("imgs/pause5.png")) #decreases load on the cpu because i need to load default image every frame, instead
            # i save a constant with that image and just refer to it
THE_TEXT_LOL='This computer model was made by exam.no 359510--This is a sandbox where you can investigate how different--\
terrains and environmet variables affect the spread of wildfire.--\
You can use "brushes", see buttons on the right->--\
The way to use the brushes is first to make sure you are--in the brush mode by clicking on the play button. You will--\
see it will switch inbetween simulation and brush modes.--Then press on the desired type of attribute button you--\
want to change e.g. dryness and hold down left mouse or--right mouse btns(press once for vegetation)--while hovering over the tile you would like to change.--\
I was inspired to make this computer model--through pygame module and in this style because--I have been playing games since I was a\
little kid.--Pixelated games always stood out for me, they had--something simple but beautiful in them.--After terraforming the grid in any way you like you can ignite--\
a tile using the button on the right and place a firedepartment.--You can adjust how many tiles burning can cause an alarm.--After you have drawn as much as want you can--\
start the simulation and pause at any time.'

button_padding = 10
line_sep = 2

vegetation_types = {
    0: "nothing",
    1: "grass",
    2: "tall_grass",
    3: "bush",
    4: "tree",
    5: "firedepartment" #special type of tile, will send out alarms and trucks (as long as there are less trucks on the map than MAX_FIRETRUCKS constant)
}

modes = {
    0: "vegetation type change",
    1: "dryness",
    2: "altitude",
    3: "ignite",
    4: "placing fire stations"
}


z = 675
b = 9200
c = 50

cooling_const = 0.035 # how fast does a tile cool down
        # for example grass heats up fast but also cools down faster
heating_const = 5 # how fast does an object heat up when burning
air_temp = 20

def dist(pos1, pos2):
    '''Finding distance between two points - pos1 and pos2'''
    return ((pos1[0]-pos2[0])**2+(pos1[1]-pos2[1])**2)**0.5

def altitude_heating_diff(x, n):#fire spreads faster uphill so this function would model how much faster the fire would spread uphill
    '''Quadratic function that returns a number that affects how fast a tile should heat up given x, n its altitude and neighbours alititude respectively.'''
    return float((-(x-n-z)**2)/b+c)

def color_fade(color1,color2,mix=0):    #fade from color 1 (mix=0) to color 2 (mix=1)
    start=np.array(mpl.colors.to_rgb(color1))
    end=np.array(mpl.colors.to_rgb(color2))
    
    return mpl.colors.to_hex((1-mix)*start + mix*end)


class Control:
    '''
    Control is basically a class that manages general functions like time mangament, turning on and off the simulation and changing brush modes and stuff like that.

    I dont know why I put firetrucks and alarms in here because it should have just been done in the grid class.
    Now that I am reviewing my code it was a stupid decision to put the firetrucks and fire stations logic in here
    The direct interaction with tiles and their managment is literally what grid class is made for.
    I recognise that this is inefficient and bad coding, if I would have had more time I would have fixed this.
    '''
    def __init__(self, mode = 0, alarm_btw_frame_time = 0.1):
        self.time = 0                           #time of the simulation
        self.mode = mode                        #brush mode
        self.sim = False                        #is the simulation on?
        self.number_fire_stations = 0
        self.fire_stations = []
        self.last_frame_time = 0
        self.curr_frame = 0
        self.frame_timing = alarm_btw_frame_time
        self.firetrucks = []
        self.alarm_up = False
        
    def change_mode(self, desired_mode: int):
        '''Changes the modes of the brushes. '''
        self.mode = desired_mode 
    
    def change_simulation(self):
        '''Turns the simulation on and off'''
        self.sim = not(self.sim)
    
    def show_time(self, prnt = False, font_size: int = 14):
        '''Displays the time of the simulation (how long the simulation have been on) on the screen'''
        text_font = pygame.font.SysFont("pxlDigivolve.otf", int(font_size))
        img = text_font.render("The timestamp of the simulation is "+str(round(self.time, 2)), True, "#000000")
        
        screen.blit(img, (TILE_D*GRID_D-self.time//10-14*font_size, GRID_D*TILE_D+2))
        if prnt:
            print("The timestamp of the simulation is "+str(self.time))
    
    def draw_text(self, text, pos, font_size):
        '''Displays whatever text you want it at any position with any font size'''
        text_font = pygame.font.SysFont("pxlDigivolve.otf", int(font_size))
        
        text = text.split("--")# double dash would mean new line. I implemented this because I didnt want to call this method multiple times, or hard code it so 
        # I just decided that double dashed would mean a new line in my code.
        
        for i in range(len(text)): # for each double dash I would step down line_sep + i*font_size pixels allowing me to make a new line.
            img = text_font.render(text[i], True, "#000000")
            
            screen.blit(img, (pos[0], pos[1]+i*font_size+line_sep))
    
    def alarm(self):
        '''plays the alarm animation at all fire stations. This really should have been done in the grid class.'''
        if self.number_fire_stations > 0:
            if (self.time-self.last_frame_time) > self.frame_timing:
                self.curr_frame+=1
                self.last_frame_time = self.time
            if self.curr_frame >= len(ALARM_IMGS):
                self.curr_frame = 0
            
            self.image = ALARM_IMGS[self.curr_frame]
            for fire_station in self.fire_stations:
                self.rect = pygame.Rect(*fire_station, 17, 17)
                screen.blit(self.image, self.rect)
        self.alarm_up = True
                
    def send_firetruck(self, target, tile):
        '''Sends a firetruck to a target tile. Firetruck is nothing more than a list. I dont actually create a class or anything.
            All of the logic for the firetrucks is done by the control class, specifically move_firetrucks and draw_firetrucks mehtods
            They take this list self.firetrucks with a list of the firetrucks' current positions their targets and tiles and governs their
            behaviour. 
        '''
        if self.alarm_up and self.number_fire_stations > 0 and len(self.firetrucks) < MAX_FIRETRUCKS:
            minimal_dist = -1
            best_fire_station = (-1, -1)
            for fire_station in self.fire_stations:
                if minimal_dist == -1:
                    best_fire_station = fire_station
                    minimal_dist = dist(fire_station, target)
                elif minimal_dist > dist(fire_station, target):
                    best_fire_station = fire_station
                    minimal_dist = dist(fire_station, target)
            
            if tile.burning:
                self.firetrucks.append([best_fire_station, target, tile, False])
            else:
                return -1
            return True
        else:
            return 0

    def move_firetrucks(self):
        '''Using subdivision of the segment between the current position of the firetruck and the target positon 
        The current positon is translated along the line joining the current postion and target, accoridng to the TRUCK_SPEED constant.
        If the truck reached the destination it will water the tiles around the fire.
        '''
        if self.sim:
            if len(self.firetrucks) == 0:
                return -1
            for index in range(len(self.firetrucks)):
                x, y= self.firetrucks[index][0]
                x1, y1 = self.firetrucks[index][1]
                if dist((x,y), (x1, y1)) > TILE_D*1.5:
                    v = TRUCK_SPEED*TILE_D/clock.get_fps()# adjust for the delta time
                    self.firetrucks[index][0] = ((v*x1+(dist((x,y), (x1, y1))-v)*x)/dist((x,y), (x1, y1)), \
                                              (v*y1+(dist((x,y), (x1, y1))-v)*y)/dist((x,y), (x1, y1))) 
                    # translate the pos of the firetruck towards the target according to the speed of the firetruck.
                else:
                    self.firetrucks[index][3] = True
                    for neighbour in self.firetrucks[index][2].neighbours:
                        neighbour.dryness = 1 
                
    def draw_firetrucks(self):
        '''Drawing the firetrucks at their current postion'''
        pop_queue = []
        moved = self.move_firetrucks()
        
        if moved != -1:
            for index in range(len(self.firetrucks)):
                if not self.firetrucks[index][2].burning: 
                    pop_queue.append(self.firetrucks[index])
                elif self.firetrucks[index][3]:
                    pass #start the watering here
                image = FIRETRUCK
                rect = pygame.Rect(self.firetrucks[index][0][0]+FIRETRUCK.get_width()//2, self.firetrucks[index][0][1]+FIRETRUCK.get_height()//2, FIRETRUCK.get_width(), FIRETRUCK.get_height())
                screen.blit(image, rect)
            for firetruck in pop_queue:
                self.firetrucks.remove(firetruck)
                
              
class Wind:
    '''This class governs wind'''
    def __init__(self, centre, rad):
        self.pos = centre
        self.rad = rad
        self.wind = (self.pos[0],self.pos[1]-20)
    
    def wind_speed(self):
        return dist(self.pos, self.wind)
    
    def wind_adjusted(self):
        return (self.wind[0]-self.pos[0], -self.wind[1]+self.pos[1])
    
    def wind_angle(self):
        if self.wind == self.pos:
            return None
        return math.atan((self.pos[1]-self.wind[1])/(self.pos[0]-self.wind[0]))
    
    def draw(self): #draw the circle and the direction of the wind
        pygame.draw.rect(screen, "#000000", pygame.Rect(self.pos[0], self.pos[1], 1, 1))    #drawing the centre of the circle
        pygame.draw.circle(screen, "#f0f0f0", self.pos, self.rad)                           #drawing the circle
        pygame.draw.line(screen, "#000000", self.pos, self.wind)
    
    def mouse_event(self): #check if the user is trying to change the wind speed
        x, y = pygame.mouse.get_pos()
        if dist((x,y), self.pos) < self.rad and pygame.mouse.get_pressed()[0]:
            self.wind = (x,y)


class Grid:
    '''Governs interaction with the tiles, the display of the grid and other functions related to changing the grid.'''
    def __init__(self, ctrl: Control, d:int = 3):
        self.the_d = d # the dimensions of the grid, it is square
        self.the_grid = [[str(x)+str(y) for x in range(self.the_d)] for y in range(self.the_d)]
        self.dealt_fire_grid = [[False for x in range(self.the_d)] for y in range(self.the_d)]
        self.ctrl = ctrl
        
    def check_key(self, key): #checks if the postition of the tile exists in the grid.
        if key[0] < 0 or key[1] < 0:
            raise IndexError('This point'+str(key)+' out of range')
        elif key[0] >= self.the_d or key[1] >= self.the_d:
            raise IndexError('This point'+str(key)+' out of range')
    
    def __getitem__(self, key):
        '''uses normal day to day cartesian point system instead of top to bottom, left to right [y][x] system in 2D arrays'''
        self.check_key(key)
        
        return self.the_grid[key[1]][key[0]]

    def __setitem__ (self, key, val):
        '''makes it easier to interact with the grid outside of the class'''
        self.check_key(key)
        
        self.the_grid[key[1]][key[0]] = val
    
    def fill(self, **args):
        '''fills the grid with the same tile using the args provided'''
        for x in range(self.the_d):
            for y in range(self.the_d):
                self.the_grid[y][x] = Tile(**args)
        self.ctrl.time = 0
    
    def draw(self):
        ''''draw the grid on the screen
            I also check if the tiles that are burning were "dealt with" - the fire truck was sent to them
        '''
        for y in range(self.the_d):
            for x in range(self.the_d):
                self.the_grid[x][y].draw((x*TILE_D,y*TILE_D))
                if not(self.dealt_fire_grid[x][y]) and self.the_grid[x][y].burning:
                    if self.ctrl.send_firetruck((x*TILE_D, y*TILE_D), self.the_grid[x][y]):
                        self.dealt_fire_grid[x][y] = self.the_grid[x][y].burning                
        
    def rain(self):
        '''makes it rain. sets all the tiles's dryness to 1 - or full humidity'''
        for y in range(self.the_d):
            for x in range(self.the_d):
                self.the_grid[x][y].n_dryness = 1
    
    def no_of_burning_tiles(self):
        '''retruns number of burning tiles currently in the grid'''
        counter = 0
        for y in range(self.the_d):
            for x in range(self.the_d):
                if self.the_grid[x][y].burning:
                    counter += 1
        return counter
    
    
class Tile:
    ''' stores information about the agent in the model.
        Performs "ticks" and updates which simulate the behaviour of the agent according to its neighbours
    '''
    def __init__(self, v_type:int = 1, dryness:float = 0.5, altitude:int = 0, temp:int = 20):
        self.v_type = v_type            #type of vegetation, types of vegetation are listed out in the dictionary at the start of the code
        self.dryness = dryness          #how moist a tile is, the name is a little deceiving, 0 is dry, 1 is wet
        self.alt = altitude             #how high the tile is relative to the sea level
        self.temp = temp                #temperature of the tile
        self.max_fuel = self.v_type*10  #how much fuel does the tile has the potential to store, the bigger the vegetation type the more fuel can a tile store, e.g. a tree would burn longer than a bush
        self.fuel = self.v_type*10      #current amount of fuel a tile has
        self.burnt = False              #if the tile has burned out
        self.burning = False            #is the tile burning?
        
        #temporary values that are used in the simulation
        self.n_burning = self.burning
        self.n_dryness = self.dryness
        self.n_fuel = self.fuel
        self.n_temperature = self.temp
        self.neighbours = None
        self.n_v_type = self.v_type
    
    def update(self):
        '''After all the ticks of all the tiles, update method must be called 
        to actually update the tiles fot the next tick.
        '''
        if self.n_v_type != self.v_type:
            self.v_type = self.n_v_type
            if self.v_type != 0:
                self.fuel = self.v_type*10*(self.fuel/self.max_fuel) # adjusts fuel to the new v_type
                self.max_fuel = (self.v_type*10+1)
        self.dryness = self.n_dryness
        self.temp = self.n_temperature
        self.fuel = self.n_fuel
        self.burning = self.n_burning
        
    def tick(self, neighbours:list, wind: Wind):
        '''Supply neighbours in the list in the following order - (N neighbour, E neigbour, S neighbour, W neighbour)
        i.e. in the clockwise direction starting with north. 
        The tick method itself doesnt change any tile's parameters, it only makes a "prediction" of what tile should be for the next frame/tick. 
        This approach avoids bugs were the behaviour of tiles is affected by the order in which the tiles' tick methods are called. 
        If the tick method changed the parameters directly the following tiles after the previous one would be affected 
        by the tick functions previously called therefore the order of calls would matter.
        This is eliminated by n_parameter variables where n_ refers to "new" or "next tick".'''
        self.neighbours = neighbours
        if self.v_type == 5:
            return None #immidiately returns None if the tile is a fire station,
         
        self.n_dryness = self.dryness
        self.n_temperature = self.temp
        self.n_fuel = self.fuel
        self.n_burning = self.burning
        self.neighbours=neighbours
        #cleaning the variables after previous tick
        
        if self.fuel <= 0:
            self.n_v_type = 0
            self.burnt = True
            self.n_burning = False
        
        if self.temp >= 100 and self.v_type != 0 and not self.burnt:
            self.n_dryness -= 0.02/clock.get_fps()

        if not self.burning and self.temp >= 300 and not self.burnt and self.v_type != 0:
            if self.dryness <= 0:
                self.n_burning = True 
            else:
                self.n_dryness -= 0.5*(self.temp-300)/MAX_TEMP/clock.get_fps()
        
        if self.burning:
            self.n_dryness = 0
            if self.temp < 300:
                self.temp = 300
            if self.fuel > 0:    
                self.n_fuel = self.n_fuel - 1/clock.get_fps()
                self.n_temperature = self.temp + (heating_const*(self.v_type+1)+6*self.fuel/self.max_fuel)/clock.get_fps() 
                # when a bush is burnign it tends to burn faster but gives off less heat then a tree
                                                                            
        for direction in range(4):
            if neighbours[direction] == None:
                continue
            if neighbours[direction].v_type != 0:
                if neighbours[direction].temp > self.temp: # some of the numbers like 0.5 are kind of random, most of the constants like heating constant 
                    #aren't tied to any real life value but rather were tweaked to make the simulation appear somewhat close to real life
                    self.n_temperature += (neighbours[direction].temp-self.temp)*0.9/(math.sqrt(self.v_type)+1)/clock.get_fps()+\
                    min(max(altitude_heating_diff(self.alt, neighbours[direction].alt), -100), 100)/clock.get_fps() # limits the altitude difference heat transfer to just 50 Celcius per sec
                    
                    if direction == 0:  #checks north direction
                        self.n_temperature -= wind.wind_adjusted()[1]*0.02/clock.get_fps()
                    elif direction == 1:#checks east
                        self.n_temperature -= wind.wind_adjusted()[0]*0.02/clock.get_fps()
                    elif direction == 2:#checks south
                        self.n_temperature += wind.wind_adjusted()[1]*0.02/clock.get_fps()
                    elif direction == 3:#check west
                        self.n_temperature += wind.wind_adjusted()[0]*0.02/clock.get_fps()
                    
                if self.n_temperature > MAX_TEMP:
                    self.n_temperature = MAX_TEMP
                
        if self.temp > air_temp: # cooling down
           self.n_temperature -= ((self.n_temperature-air_temp)*cooling_const)/clock.get_fps()
            
        if self.v_type == 0:
            self.burning = False
        
    def draw(self, pos):
        '''draws the tile on the screen, given its position'''
        self.pos = pos
        def draw_fire():
            self.fire_image = GRID_IMGS[4]
            self.fire_image.set_alpha(255//2)
            self.fire_rect = pygame.Rect(self.pos[0], self.pos[1], TILE_D, TILE_D) 
            screen.blit(self.fire_image, self.fire_rect)
            
        def draw_humidity():
            h_rect = pygame.Rect(self.pos[0], self.pos[1]+TILE_D-4, int(TILE_D*self.dryness), 4)
            pygame.draw.rect(screen, "#0000F0", h_rect)
        
        def draw_temperature():
            t_rect = pygame.Rect(self.pos[0], self.pos[1]+TILE_D-8, int(TILE_D*self.temp//MAX_TEMP), 4)
            pygame.draw.rect(screen, "#F00000", t_rect)
        
        if self.v_type != 5:
            self.bg_rect = pygame.Rect(self.pos[0], self.pos[1], TILE_D, TILE_D)
            pygame.draw.rect(screen, color_fade(MASTER_COLORS[0], MASTER_COLORS[1], self.alt/MAX_HEIGHT), self.bg_rect)
            
            if self.v_type != 0:
                self.v_image = GRID_IMGS[self.v_type-1]
                self.v_rect = pygame.Rect(self.pos[0], self.pos[1], TILE_D, TILE_D) 
                screen.blit(self.v_image, self.v_rect)
            draw_humidity()
            draw_temperature()
            if self.burning:
                draw_fire()
        
        elif self.v_type == 5:
            self.firedepo_image = GRID_IMGS[5]
            self.v_rect = pygame.Rect(self.pos[0], self.pos[1], TILE_D, TILE_D) 
            screen.blit(self.firedepo_image, self.v_rect)


class Slider:
    def __init__(self, ctrl: Control, x, y, width, val_range, height = 10):
        self.pos = (x,y)
        self.val = val_range[0]
        self.val_range = val_range
        self.width = width
        self.height = height
        self.rect = pygame.Rect(*(self.pos[0], self.pos[1]-2), width+4, height+4)
        self.ctrl = ctrl
    
    def draw(self):
        m_pos = pygame.mouse.get_pos()
        
        if self.rect.collidepoint(m_pos) and pygame.mouse.get_pressed()[0] == 1:
            self.val = int(((m_pos[0]-self.pos[0])/self.width)*(self.val_range[1]-self.val_range[0]))
        
        self.ctrl.draw_text(str(self.val), (self.pos[0]+self.width*self.val/(self.val_range[1]-self.val_range[0])-2, self.pos[1]-14), 14)    
        pygame.draw.line(screen, "#696969", (self.pos[0], self.pos[1]+self.height//2), (self.pos[0]+self.width, self.pos[1]+self.height//2), self.height)
        
        pygame.draw.circle(screen, "#000000", (self.width*self.val/(self.val_range[1]-self.val_range[0])+self.pos[0], self.pos[1]+self.height//2+1), 5)
      
        
class Button:
    def __init__(self, x, y, func: Control.change_mode, scale:float = 1):
        self.scale = scale
        self.__new_buttons()
        self.rect = self.images[0].get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False
        self.func = func
        
    def __new_buttons(self):
        self.images = [pygame.transform.scale(BUTTONS[x], (int(BUTTONS[x].get_width()*self.scale), int(BUTTONS[x].get_height()*self.scale))) for x in range(3)]
    

class Mode(Button):
    def __init__(self,  x, y, text, func: Control.change_mode, args, text_pad:int = 20, left_text_pad:int = 0, scale:float = 1):
        super().__init__(x, y, func, scale)
        
        self.args = args
        self.text = text
        self.text_pad = text_pad
        self.left_text_pad = left_text_pad

    def __draw_text(self):
        text_font = pygame.font.SysFont("pxlDigivolve.otf", int(14*self.scale))
        img = text_font.render(self.text, True, "#000000")
        
        screen.blit(img, (self.rect.x+self.text_pad+self.left_text_pad, self.rect.y+self.text_pad))
        
    def draw(self):
        pos = pygame.mouse.get_pos()
        
        self.image = self.images[0]
        
        if self.rect.collidepoint(pos):
            self.image = self.images[1]
            
            if self.clicked:
                self.image = self.images[2]
            
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                self.clicked = True
                
            elif pygame.mouse.get_pressed()[0] == 0 and self.clicked == True:
                self.clicked = False
                if self.args != -1 and type(self.args) == dict:
                    self.func(**self.args)
                elif self.args != -1:
                    self.func(self.args)
                else:
                    self.func()
        else:
            self.clicked = False
        
        screen.blit(self.image, (self.rect.x, self.rect.y))
        self.__draw_text()


class Pause(Button):
    def __init__(self, x, y, func: Control.change_simulation, scale:float = 1):
        super().__init__(x, y, func, scale)
        self.__new_buttons()
        self.rect = self.images[0].get_rect()
        self.rect.topleft = (x, y)
        self.sim = False
    
    def __new_buttons(self):
        self.images = [pygame.transform.scale(BUTTONS[x], (int(BUTTONS[x].get_width()*self.scale), int(BUTTONS[x].get_height()*self.scale))) for x in range(3, 9)]
    
    def draw(self):
        pos = pygame.mouse.get_pos()
        
        self.image = self.images[0+3*self.sim]
        
        if self.rect.collidepoint(pos):
            self.image = self.images[1+3*self.sim]
            
            if self.clicked:
                self.image = self.images[2+3*self.sim]
            
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                self.clicked = True
                
            elif pygame.mouse.get_pressed()[0] == 0 and self.clicked == True:
                self.clicked = False
                self.sim = not self.sim
                self.func()
        else:
            self.clicked = False
        screen.blit(self.image, (self.rect.x, self.rect.y))


class Action_Button(Pause):
    def __init__(self, x, y, func, args = (), scale:float = 1):
        super().__init__(x, y, func)
        self.__new_buttons()
        del self.sim
        self.args = args
        
    def __new_buttons(self):
        self.images = [pygame.transform.scale(RAIN_IMG, (int(RAIN_IMG.get_width()*self.scale), int(RAIN_IMG.get_height()*self.scale)))]
    
    def draw(self):
        pos = pygame.mouse.get_pos()
        
        self.image = self.images[0]
        
        if self.rect.collidepoint(pos) and pygame.mouse.get_pressed()[0] == 1:
            self.func(*self.args)
        screen.blit(self.image, (self.rect.x, self.rect.y))


def main():
    ctrl = Control()
    
    grid = Grid(ctrl, GRID_D)
    grid.fill(dryness = int(EMBEDDED_SYSTEM_DATA[0][2])/100)
    
    running = True
    
    v_button = Mode(1280-128*2-button_padding, button_padding, "Change Vegetation Type", ctrl.change_mode, 0, scale = 2, left_text_pad=-10)
    d_button = Mode(1280-128*2-button_padding, button_padding*2+64, "Change Dryness", ctrl.change_mode, 1, scale=2)
    a_button = Mode(1280-128*2-button_padding, button_padding*3+64*2, "Change Altitude", ctrl.change_mode, 2, scale=2)
    f_button = Mode(1280-128*2-button_padding, button_padding*4+64*3, "Ignite Tile", ctrl.change_mode, 3, scale=2)
    fd_button = Mode(1280-128*2-button_padding, 720-64-button_padding, "Place a fire department", ctrl.change_mode, 4, scale=2)
    reset_button = Mode(1280-128*2-button_padding, button_padding*5+64*4, "Reset the tiles", grid.fill, {"dryness": int(EMBEDDED_SYSTEM_DATA[0][2])/100}, scale=2)
    rain_button = Action_Button(button_padding  , GRID_D*TILE_D+button_padding, grid.rain)
    sim_button = Pause(1280-128*2-64-button_padding, button_padding, ctrl.change_simulation, scale = 2)
    #buttons are initiated above
    wind = Wind((1280-128*2-button_padding+64, button_padding*7+64*6+32), 64)
    #wind initiated
    slider = Slider(ctrl, 1280-128*2-button_padding, 720-(64-button_padding)*2-10, 128*2, (1, 10))
    #slider initiated
    
    mouse_down_time = [0, 0] # how long was left or right mouse pressed
    
    while running:
        screen.fill((240,250,230))
        
        ctrl.show_time()
        grid.draw()
        ctrl.draw_firetrucks()
        
        v_button.draw()
        d_button.draw()
        a_button.draw()
        f_button.draw()
        fd_button.draw()
        reset_button.draw()
        sim_button.draw()
        wind.draw()
        rain_button.draw()
        slider.draw()
        
        ctrl.draw_text("Brush"*(not(ctrl.sim))+"Simulation"*ctrl.sim+" mode", (TILE_D*GRID_D+128, 32), 28)
        ctrl.draw_text("FPS: "+str(round(clock.get_fps(), 2)), (0,TILE_D*GRID_D), 14)
        ctrl.draw_text("Number of burning tiles are: "+str(grid.no_of_burning_tiles()), (64, TILE_D*GRID_D), 14)
        ctrl.draw_text("Number of available trucks (no more trucks will be sent out than this number): "+str(MAX_FIRETRUCKS), (64, TILE_D*GRID_D+14), 14)
        ctrl.draw_text("Wind control:", (1280-128*2-button_padding, button_padding*6+64*5), 28)
        ctrl.draw_text("N", (1280-128*2-button_padding+64-6, button_padding*7+64*6-42), 28)
        ctrl.draw_text("S", (1280-128*2-button_padding+64-6, button_padding*7+64*6+32+56), 28)
        ctrl.draw_text("W", (1280-128*2-button_padding-14, button_padding*7+64*6+27), 28)
        ctrl.draw_text("E", (1280-128*2-button_padding+128, button_padding*7+64*6+27), 28)
        ctrl.draw_text(THE_TEXT_LOL, (TILE_D*GRID_D+line_sep, 72), 18)
        ctrl.draw_text("How many burning tiles trigger an alram:", (1280-128*2-button_padding-4, 720-(64-button_padding)*2-40), 19)
        # all the drawing of on the screen happens between lines 308 and 317
        
        ctrl.alarm_up = False
        if grid.no_of_burning_tiles()>=slider.val:
            ctrl.alarm()
        
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if not ctrl.sim:
                if event.type == pygame.MOUSEMOTION:
                    wind.mouse_event()
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    col = x // TILE_D
                    row = y // TILE_D
                    wind.mouse_event()
                    
                    if ctrl.mode == 4 and not (row >=  GRID_D or col >=  GRID_D  or row < 0 or col < 0):
                        if pygame.mouse.get_pressed()[0] == True and grid[row, col].v_type != 5:
                            grid[row, col].n_v_type = 5
                            ctrl.fire_stations.append((col*TILE_D,row*TILE_D))
                            ctrl.number_fire_stations += 1
                        elif pygame.mouse.get_pressed()[2] == True and grid[row, col].v_type == 5:
                            grid[row, col].n_v_type = 0
                            ctrl.fire_stations.remove((col*TILE_D,row*TILE_D))
                            ctrl.number_fire_stations -= 1
                    elif ctrl.mode == 0 and not (row >=  GRID_D or col >=  GRID_D  or row < 0 or col < 0):
                        if grid[row, col].v_type == 5:
                            grid[row, col].n_v_type = 0  
                        elif pygame.mouse.get_pressed()[2] == True and grid[row, col].v_type > 0:
                            grid[row, col].n_v_type -= 1
                        elif pygame.mouse.get_pressed()[0] == True and grid[row, col].v_type < 4:
                            grid[row, col].n_v_type += 1
                        else:
                            grid[row, col].n_v_type = 0
                    elif ctrl.mode == 3 and not (row >=  GRID_D or col >=  GRID_D) and grid[row, col].v_type != 5:
                        if pygame.mouse.get_pressed()[0] == True:
                            grid[row, col].n_burning = True
                        elif pygame.mouse.get_pressed()[2] == True:
                            grid[row, col].n_burning = False
                      
                    
        if not ctrl.sim:        
            if pygame.mouse.get_pressed()[0] == True:
                mouse_down_time[0] += 1
                x, y = pygame.mouse.get_pos()
                col = x // TILE_D
                row = y // TILE_D
                
                if not (row >=  GRID_D or col >=  GRID_D or row < 0 or col < 0):                                
                    if ctrl.mode == 2:
                        if grid[row, col].alt < MAX_HEIGHT:
                            grid[row, col].alt += (100 + mouse_down_time[0]//10)//clock.get_fps()
                    elif ctrl.mode == 1 and grid[row, col].dryness < 1:
                        grid[row, col].n_dryness += (0.025*(mouse_down_time[0]/60) + 0.075)/clock.get_fps()
                        if grid[row, col].dryness > 1:
                            grid[row, col].n_dryness = 1
                        
            else:
                mouse_down_time[0] = 0
                
            if pygame.mouse.get_pressed()[2] == True:
                mouse_down_time[1] += 1
                x, y = pygame.mouse.get_pos()
                col = x // TILE_D
                row = y // TILE_D
                
                if not (row >=  GRID_D or col >=  GRID_D or row < 0 or col < 0):                                
                    if ctrl.mode == 2:
                        if grid[row, col].alt < MAX_HEIGHT:
                            grid[row, col].alt -= (15 + mouse_down_time[1]//10)//clock.get_fps()
                    elif ctrl.mode == 1 and grid[row, col].dryness > 0:
                        grid[row, col].n_dryness -= (0.025*(mouse_down_time[1]/60) + 0.075)/clock.get_fps()
                        if grid[row, col].dryness < 0:
                            grid[row, col].n_dryness = 0
                        
            elif pygame.mouse.get_pressed()[2] == False:
                mouse_down_time[1] = 0
        else:
            ctrl.time += 1/clock.get_fps()
            #first the special cases will be simulated than the all the other tiles,
            #the special tiles are those that dont have four neighbours like corner tiles
            #grid[y, x] where [0,0] top left
            #corners are "ticked" first
            grid[0,0].tick((None, grid[0,1], grid[1,0], None), wind)
            grid[GRID_D-1, GRID_D-1].tick((grid[GRID_D-2, GRID_D-1], None, None, grid[GRID_D-1, GRID_D-2]), wind)
            grid[GRID_D-1, 0].tick((grid[GRID_D-2, 0], grid[GRID_D-1, 1], None, None), wind)
            grid[0, GRID_D-1].tick((None, None, grid[1, GRID_D-1], grid[0, GRID_D-2]), wind)
            
            #top, bottom, sides 
            for i in range(1, GRID_D-1):
                grid[0, i].tick((None, grid[0, i+1], grid[1, i], grid[0, i-1]), wind)                                   #top row
                grid[i, GRID_D-1].tick((grid[i-1, GRID_D-1], None, grid[i+1, GRID_D-1], grid[i, GRID_D-2]), wind) #right column
                grid[GRID_D-1, i].tick((grid[GRID_D-2, i], grid[GRID_D-1, i+1], None, grid[GRID_D-1, i-1]), wind) #bottom row
                grid[i, 0].tick((grid[i-1, 0], grid[i, 1], grid[i+1, 0], None), wind)                             #left column
                for j in range(1, GRID_D-1):
                    grid[i, j].tick((grid[i-1, j], grid[i, j+1], grid[i+1, j], grid[i, j-1]), wind)
                
            
                
            
        #updating all tiles after each tick
        grid[0,0].update()
        grid[GRID_D-1, GRID_D-1].update()
        grid[GRID_D-1, 0].update()
        grid[0, GRID_D-1].update()
        
        for i in range(1, GRID_D-1):
            grid[i, 0].update()
            grid[i, GRID_D-1].update()
            grid[0, i].update()
            grid[GRID_D-1, i].update()
            for j in range(1, GRID_D-1):
                grid[i, j].update()
        
        pygame.display.flip()  # Refresh on-screen display
        clock.tick(FPS)
        
    pygame.quit()


if __name__ == "__main__":
    main()