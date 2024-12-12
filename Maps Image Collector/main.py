import pygame
import pygame.display
import win32api
import win32con
import win32gui
import os

import ctypes
from ctypes import wintypes 

import pyautogui

from pynput import keyboard
import threading
import clipboard

import xml.etree.ElementTree as ET

pygame.init()
pygame.font.init()

font1 = pygame.font.SysFont("Arial", 20)

# get screen size
w, h = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

wn = pygame.display.set_mode((w, h), pygame.NOFRAME)

transparent = (255, 0, 128)  # transparency color


# create layered window
hwnd = pygame.display.get_wm_info()["window"]
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                       win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)

win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*transparent), 0, win32con.LWA_COLORKEY)
win32gui.SetLayeredWindowAttributes(hwnd, 0, int(255 * 0.5), win32con.LWA_ALPHA)
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*transparent), int(255 * 0.8), win32con.LWA_COLORKEY | win32con.LWA_ALPHA)



# pin window on top
user32 = ctypes.WinDLL("user32")
user32.SetWindowPos.restype = wintypes.HWND
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.UINT]
user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001)



def create_xml_file(file_name):
    if not os.path.exists(file_name):
        root = ET.Element("data")
        
        tree = ET.ElementTree(root)
        
        tree.write(file_name, encoding="utf-8", xml_declaration=True)


def add_entry_to_xml(file_name, unique_id, latitude, longitude, zoom, heading, tilt):
    create_xml_file(file_name)
    

    tree = ET.parse(file_name)
    root = tree.getroot()


    new_entry = ET.Element("entry", attrib={"id": str(unique_id)})
    

    ET.SubElement(new_entry, "latitude").text = str(longitude)
    ET.SubElement(new_entry, "longitude").text = str(latitude)
    ET.SubElement(new_entry, "zoom").text = str(zoom)
    ET.SubElement(new_entry, "heading").text = str(heading)
    ET.SubElement(new_entry, "tilt").text = str(tilt)


    root.append(new_entry)


    tree.write(file_name, encoding="utf-8", xml_declaration=True)



class ButtonUI:
    def __init__(self, x, y, w, h, text, color):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.color = color

    def is_over(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

class CursorUI:
    def __init__(self, x, y, cursor_sprite, locked_sprite, unlocked_sprite):
        self.x = x
        self.y = y
        self.cursor_sprite = cursor_sprite
        self.locked_sprite = locked_sprite
        self.unlocked_sprite = unlocked_sprite

        self.dragging = False
        self.locked = True

    def step(self, mx, my, left_down, left_released, FigSizeUI):
        if left_released or self.locked:
            was_dragging = self.dragging
            self.dragging = False
            return was_dragging


        if left_down and not FigSizeUI.dragging:
            if self.x - self.cursor_sprite.get_width() // 2 < mx < self.x + self.cursor_sprite.get_width() // 2 and self.y - self.cursor_sprite.get_height() // 2 < my < self.y + self.cursor_sprite.get_height() // 2:
                self.dragging = True
        
        if self.dragging:
            self.x = mx
            self.y = my

    def draw(self, surf):
        if self.locked:
            surf.blit(self.locked_sprite, (self.x - self.locked_sprite.get_width() // 2 - 20, self.y - self.locked_sprite.get_height() // 2 - 20))
        surf.blit(self.cursor_sprite, (self.x - self.cursor_sprite.get_width() // 2, self.y - self.cursor_sprite.get_height() // 2))

class FigSizeUI:
    def __init__(self, x, y, corner_sprite, locked_sprite, unlocked_sprite, size = 200):
        self.size = size
        
        self.top_left = [x, y]
        self.bottom_right = [x + size, y + size]

        self.corner_sprite = corner_sprite
        self.corner_sprite2 = pygame.transform.flip(corner_sprite, True, True)
        self.locked_sprite = locked_sprite
        self.unlocked_sprite = unlocked_sprite

        self.dragging = None
        self.other = None
        self.other_relative_pos = None

        self.locked = True

    def is_over(self, mx, my, corner):
        if not corner: # check top left corner
            return self.top_left[0] < mx < self.top_left[0] + self.corner_sprite.get_width() and self.top_left[1] < my < self.top_left[1] + self.corner_sprite.get_height()

        return self.bottom_right[0] - self.corner_sprite.get_width() < mx < self.bottom_right[0] and self.bottom_right[1] - self.corner_sprite.get_height() < my < self.bottom_right[1]
            

    def step(self, mx, my, left_down, left_released):
        if left_released or self.locked:
            was_dragging = self.dragging
            self.dragging = None
            return was_dragging
        
        
        if left_down:
            if self.is_over(mx, my, False):
                self.dragging = self.top_left
                self.other = self.bottom_right
                self.other_relative_pos = [self.bottom_right[0] - self.top_left[0], self.bottom_right[1] - self.top_left[1]]
            elif self.is_over(mx, my, True):
                self.dragging = self.bottom_right
                self.other = self.top_left
                self.other_relative_pos = [self.top_left[0] - self.bottom_right[0], self.top_left[1] - self.bottom_right[1]]


        if self.dragging:
            

            if self.dragging == self.top_left:
                self.dragging[0] = mx - self.corner_sprite.get_width() // 2
                self.dragging[1] = my - self.corner_sprite.get_height() // 2

                self.other[0] = self.dragging[0] + self.other_relative_pos[0]
                self.other[1] = self.dragging[1] + self.other_relative_pos[1]
            
            else:
                other_pos = [self.other[0] + self.other_relative_pos[0], self.other[1] + self.other_relative_pos[1]]
                d = max(other_pos[0] - mx, other_pos[1] - my)

                self.dragging[0] = other_pos[0] - d
                self.dragging[1] = other_pos[1] - d

                if self.dragging[0] < self.other[0] + 200:
                    self.dragging[0] = self.other[0] + 200
                if self.dragging[1] < self.other[1] + 200:
                    self.dragging[1] = self.other[1] + 200

    def draw(self, surf):
        pygame.draw.rect(surf, (125, 125, 125), (self.top_left[0] + 4, self.top_left[1] + 4, self.bottom_right[0] - self.top_left[0] - 9, self.bottom_right[1] - self.top_left[1]- 9), 10)
        surf.blit(self.corner_sprite, self.top_left)
        surf.blit(self.corner_sprite2, (self.bottom_right[0] - self.corner_sprite.get_width(), self.bottom_right[1] - self.corner_sprite.get_height()))

        if self.dragging == self.bottom_right:
            text = font1.render(f"{self.bottom_right[0] - self.top_left[0]}x{self.bottom_right[1] - self.top_left[1]}", False, (255, 255, 255))
            surf.blit(text, (self.bottom_right[0] - text.get_width() - 15, self.bottom_right[1] - text.get_height() - 15))

        if self.locked:
            surf.blit(self.locked_sprite, (self.top_left[0] - self.locked_sprite.get_width() // 2 - 20, self.top_left[1] - self.locked_sprite.get_height() // 2 - 20))




def on_press(key):
    global space_press, l_press

    try:
        if key.name == "space":
            space_press = True
    except:
        pass

    try:
        if key.char == 'l':
            l_press = True
    except:
        pass
    
    
    
    return True

def start_key_listener():
    with keyboard.Listener(on_press=on_press) as listener:
            listener.join()


space_press = False
l_press = False

listener_thread = threading.Thread(target=start_key_listener)
listener_thread.start()




create_xml_file("data/coordinates.xml")


def main():
    global space_press, l_press

    clock = pygame.time.Clock()
    state_left = win32api.GetKeyState(0x01)

    corner_sprite = pygame.image.load("drawables/corner.png").convert_alpha()
    cursor_sprite = pygame.image.load("drawables/cursor.png").convert_alpha()
    locked_sprite = pygame.image.load("drawables/locked.png").convert_alpha()
    unlocked_sprite = pygame.image.load("drawables/unlocked.png").convert_alpha()

    
    # load progressive_index, fx, fy, s, cx, cy from file
    try:
        with open("data/data.txt", "r") as f:
            progressive_index = int(f.readline().strip())
            fx, fy = f.readline().strip().split(",")
            fx, fy = int(fx), int(fy)
            s = int(f.readline().strip())
            cx, cy = f.readline().strip().split(",")
            cx, cy = int(cx), int(cy)
    except:
        progressive_index = 0
        fx, fy = w//2 - 100, 300
        s = 200
        cx, cy = w//2, 100


    figsize_ui = FigSizeUI(fx, fy, corner_sprite, locked_sprite, unlocked_sprite, size = s)
    cursor_ui = CursorUI(cx, cy, cursor_sprite, locked_sprite, unlocked_sprite)
    

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:

                pygame.quit()
                return
        
        mx, my = win32api.GetCursorPos()
        state = win32api.GetKeyState(0x01)

        left_down = False
        left_released = False

        if state != state_left:
            state_left = state
            if state < 0:
                left_down = True
            else:
                left_released = True


        was_dragging = figsize_ui.step(mx, my, left_down, left_released)
        was_dragging2 = cursor_ui.step(mx, my, left_down, left_released, figsize_ui)

        if was_dragging or was_dragging2:
            # save stuff
            print("saving")
            with open("data/data.txt", "w") as f:
                f.write(str(progressive_index) + "\n")
                f.write(str(figsize_ui.top_left[0]) + "," + str(figsize_ui.top_left[1]) + "\n")
                f.write(str(figsize_ui.bottom_right[0] - figsize_ui.top_left[0]) + "\n")
                
                f.write(str(cursor_ui.x) + "," + str(cursor_ui.y) + "\n")


        if space_press:
            space_press = False
            wn.fill(transparent)
            pygame.display.flip()

            # copy to clipboard a random string, so a error will be raised if the user exploits the macro
            clipboard.copy("a" * 100)

            screenshot = pyautogui.screenshot(region=(figsize_ui.top_left[0], figsize_ui.top_left[1], figsize_ui.bottom_right[0] - figsize_ui.top_left[0], figsize_ui.bottom_right[1] - figsize_ui.top_left[1]))

            import time
            old_pos = mx, my
            pyautogui.moveTo(cursor_ui.x, cursor_ui.y)
            pyautogui.click()
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'c')
            pyautogui.moveTo(old_pos[0], old_pos[1])
            pyautogui.press('esc')

            # get clipboard data
            data = str(clipboard.paste())
            
            split = data.split("/")
            print("split", split)
            assert split[3] == "maps" 
            data = split[4][1:].split(",")

            data.pop(2) # remove y
            data[2] = data[2].replace("y", "")
            data[3] = data[3].replace("h", "")
            data[4] = data[4].replace("t", "")




            screenshot.save("images/" + str(progressive_index) + ".png")
            add_entry_to_xml("data/coordinates.xml", progressive_index, *data)
            progressive_index += 1

            # save stuff
            with open("data/data.txt", "w") as f:
                print("saving")
                f.write(str(progressive_index) + "\n")
                f.write(str(figsize_ui.top_left[0]) + "," + str(figsize_ui.top_left[1]) + "\n")
                f.write(str(figsize_ui.bottom_right[0] - figsize_ui.top_left[0]) + "\n")
                
                f.write(str(cursor_ui.x) + "," + str(cursor_ui.y) + "\n")

            
        
        if l_press:
            l_press = False
            cursor_ui.locked = not cursor_ui.locked
            figsize_ui.locked = not figsize_ui.locked
       
 

        
        wn.fill(transparent)
        figsize_ui.draw(wn)
        cursor_ui.draw(wn)

        pygame.display.flip()
        clock.tick()


if __name__ == "__main__":
    main()
    quit()
        
