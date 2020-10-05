from PIL import Image, ImageDraw, ImageFont
import logging
import time

class OmniaUI:

    default_font = ImageFont.truetype("Arial.ttf", 20)

    def __init__(self, display_dimensions, click_callback=None, click_bias=0, background_color=(255,255,255), background_image=None, font=None, debug=False):

        # Dimensions
        self.width = display_dimensions[0]
        self.height = display_dimensions[1]

        # Touch
        self.touch_x = 0
        self.touch_y = 0
        self.bias = click_bias
        self.click_callback = click_callback

        # Image utilities
        self.image = Image.new("RGBA", (self.width, self.height), background_color)
        self.draw = ImageDraw.Draw(self.image)

        # Colors
        self.background_color = background_color

        # Background Image
        self.background_image = background_image

        # Font
        self.font = self.default_font
        if font:
            self.font = font

        # Elements
        self.buttons = {}
        self.labels = {}
        
        # Debug
        self.debug = debug
        self.debug_point = None
        self.debug_point_time = time.time()

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)
        self.log = logging.getLogger('OmniaUI')
        ### --- ###
    
    def _draw_debug_point(self):
        self.draw.ellipse(self.debug_point, fill=(255,0,0))

    def click(self, coordinates):
        x = coordinates[0]
        y = coordinates[1]
        if (0 <= x <= self.width) and (0 <= y <= self.height):
            self.touch_x = x
            self.touch_y = y

            # draw a red point of radius = r and center = (x,y)
            if self.debug:
                r = 5
                self.debug_point = [(x-r, y-r), (x+r, y+r)]
                #self._draw_debug_point()
            
            for button_id in self.buttons:
                button = self.buttons[button_id]

                if button.isClicked(coordinates, self.bias):
                    self.log.debug("Element '{}' clicked".format(button.id))
                    
                    if self.click_callback:
                        self.click_callback(button)
                        break
                    else:
                        return button
        else:
            #raise ValueError("Click coordinates '{}' outside image".format((x,y)))
            self.log.error("Click coordinates '{}' outside image".format((x,y)))
    
    ### BUTTONS ###

    def _draw_element(self, element):
        if element.image:
            self.image.paste(element.image, element.box[0], mask=element.image)
        else:
            self.draw.rectangle(element.box, fill=element.background_color, outline=element.outline_color)
            self.draw.text(( element.x0 + element.padding, element.y0 + element.padding ), element.text, fill=element.text_color, font=element.font)

    def addElement(self, element):
        element_id = element.id
        element_type = element.type

        if element_type == "button":
            
            if not element_id in self.buttons:
                # register button
                self.buttons[element_id] = element

                # draw button
                self._draw_element(element)
            
            else:
                #raise ValueError("Button with id '{}' already exists".format(element_id))
                self.log.error("Button with id '{}' already exists".format(element_id))
        
        if element_type == "label":
            
            if not element_id in self.labels:
                # register label
                self.labels[element_id] = element

                # draw label
                self._draw_element(element)
        
            else:
                #raise ValueError("Label with id '{}' already exists".format(element_id))
                self.log.error("Label with id '{}' already exists".format(element_id))

    def removeElement(self, element_id):
        if element_id in self.buttons:
            self.buttons.pop(element_id)
            self.refresh_image()
        elif element_id in self.labels:
            self.labels.pop(element_id)
            self.refresh_image()
        else:
            #raise ValueError("Element with id '{}' does not exists".format(element_id))
            self.log.error("Element with id '{}' does not exists".format(element_id))
    
    ### --- ###

    ### LABELS ###

    ### --- ###

    ### IMAGE ###

    def refresh_image(self):
        self.clear_image()
        for button_id in self.buttons:
            self._draw_element(self.buttons[button_id])
        
        for label_id in self.labels:
            self._draw_element(self.labels[label_id])
        
        if self.debug:
            if self.debug_point:
                self._draw_debug_point()

    def show_image(self):
        self.image.show()
    
    def clear_image(self, box=None):
        if not box:
            box = [0,0,self.width,self.height]
        
        if self.background_image:
            self.image.paste(self.background_image, box)
        else:
            self.image.paste(self.background_color, box)
    
    def get_image(self):
        return self.image.copy()
    
    ### --- ###

    ### COLORS ###

    def setBackgroundImage(self, image):
        image = image.resize((self.width, self.height))

        self.background_image = image
        self.refresh_image()
    
    def setBackgroundColor(self, color):
        self.background_color = color
        self.refresh_image()

    ### --- ###

class OmniaUIElement:

    padding = 5
    default_font = ImageFont.truetype("Arial.ttf", 20)

    def __init__(self, id, element_type, position, text, image=None, clickable=False, dimensions=(70,30), text_color=(0,0,0), text_font=None, background_color=(230, 230, 230), outline_color=(166, 166, 166)):

        # Id
        self.id = id

        # Type
        self.type = element_type
        
        # Font
        self.font = self.default_font
        if text_font:
            self.font = text_font
        
        # Text
        self.text = text

        # Coordinates and box
        self.dimensions = dimensions

        if text != '':
            text_size = self.font.getsize(text)
            self.dimensions = ( text_size[0], text_size[1] )
        
        self.x0 = position[0]
        self.y0 = position[1]

        self.x1 = 0
        self.y1 = 0

        self.box = []

        # Colors
        self.text_color = text_color
        self.background_color = background_color
        self.outline_color = outline_color

        # Image
        self.image = image
        if self.image:
            self.dimensions = self.image.size
        
        # Click
        self.clickable = clickable

        # set initial box
        self._update_box()
    
    def isClicked(self, coordinates, bias):
        x = coordinates[0]
        y = coordinates[1]

        if (self.x0 - bias <= x <= self.x1 + bias) and (self.y0 - bias <= y <= self.y1 + bias) and self.clickable:
            return True
        else:
            return False

    def _update_box(self):
        self.x1 = self.x0 + self.dimensions[0]
        self.y1 = self.y0 + self.dimensions[1]

        # add margin for text
        if not self.image:
            self.x1 += 2*self.padding
            self.y1 += 2*self.padding
        
        self.box = [( self.x0, self.y0 ), ( self.x1, self.y1 )]

    def setText(self, text):
        self.text = text
        text_size = self.font.getsize(text)
        self.dimensions = ( text_size[0], text_size[1] )

        self._update_box()
    
    def setPosition(self, position):
        self.x0 = position[0]
        self.y0 = position[1]

        self._update_box()
    
    def setDimensions(self, dimensions):
        self.dimensions = dimensions

        self._update_box()
    
    def setBackgroundColor(self, color):
        self.background_color = color

    def setOutlineColor(self, color):
        self.outline_color = color
    
    def setTextColor(self, color):
        self.text_color = color
    
    def addImage(self, image):
        self.dimensions = image.size
        self.image = image

        self._update_box()

    def removeImage(self):
        self.image = None
