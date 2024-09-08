#
# Created on:  Sun Sep 08 2024
# By:  Lukas Mettler (lukas.mettler@student.kit.edu)
# https://github.com/LEMettler
#


import numpy as np
import matplotlib.pyplot as plt 
from collision_builder import *


class ConsecutiveCollisionBuilder:
    def __init__(self, width, height, inital_point, relative_margin=0.05):
        self.points_of_collision = [inital_point]
        self.collisions = []
        self.relative_margin = relative_margin
        self.width = width
        self.height = height

        self.default_config = {
            'n_secondaries': 40,
            'alpha_std': 50,
            'length_mean': 200,
            'length_std': 100,
            'primary_color': '#eb6e21',
            'secondary_color': '#c9801a',
            'box_color': '#3c3c3c',
            'background_color': '#a6480f',
            'primary_stroke_width': 3.5,
            'secondary_stroke_width': 3.5,
            'primary_begin': 0,
            'secondary_duration': 0.4,
            'primary_duration': 5,
            'dur_fade_primary': 0.5,
            'dur_fade_secondary': 0.5,
            'dur_freeze_secondary': 0
            }

    def addCollision(self, new_point_of_collision, border_collisions, **kwargs):
        
        config = self.default_config.copy()
        config.update(kwargs)

        new_collision = CollisionBuider(self.width, self.height, new_point_of_collision,
                                        incoming_angles=[], relative_margin=self.relative_margin)
        
        new_collision.addPrimaryFrom(self.points_of_collision[-1], border_collisions)

        new_collision.calculateSecondaryPaths(n_secondaries=config['n_secondaries'],
                                            alpha_std=config['alpha_std'],
                                            length_mean=config['length_mean'],
                                            length_std=config['length_std'])


        style_dict = {k: v for k, v in config.items() if k not in ['n_secondaries', 'alpha_std', 'length_mean', 'length_std']}
        new_collision.setStyle(collision_index=len(self.collisions), **style_dict)

        self.points_of_collision.append(new_point_of_collision)
        self.collisions.append(new_collision)


    def to_svg(self, file_name):
        # closing the loop
        #self.addCollision(self.points_of_collision[0], [['A'], ['B', 'C']])
        

        #begin the string
        total_string = f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">\n\n'


        # background box
        d_box = f'M0,0 L{self.width},0 L{self.width},{self.height} L0,{self.height} Z'
        box_string = line2svgPath(d=d_box, identifier='box',
                                  color=self.default_config['background_color'],
                                  stroke_width=0, animate=False, fill=self.default_config['background_color'])
        total_string += box_string + '\n\n'   


        # rescaling and translation to center
        scale_w = 1 - self.relative_margin
        scale_h = round(1 - self.width * self.relative_margin / self.height, 3)
        translation = self.relative_margin*self.width/2
        total_string += f'<g transform="scale({scale_w},{scale_h}) translate({translation}, {translation})"> \n\n'


        # surrounding box
        d_box = f'M0,0 L{self.width},0 L{self.width},{self.height} L0,{self.height} Z'
        box_string = line2svgPath(d=d_box, identifier='box',
                                  color=self.default_config['box_color'], stroke_width=0.5, animate=False, fill=self.default_config['box_color'])
        total_string += box_string + '\n\n'   

        # for each collision add the paths
        for coll in self.collisions:
            total_string += coll.prepare_for_multi_svg('templates/path_template.txt', len(self.collisions)-1)



        #end the string
        total_string += '\n\n</g>\n\n</svg>'

        # write
        with open(file_name, 'w') as file:
            file.write(total_string)
        
        print(f'Writen to {file_name}!')





###############################################################

# execution

    
if __name__ == "__main__":
    

    ccb = ConsecutiveCollisionBuilder(800, 400, [300, 100])
    ccb.addCollision([402, 230], [['C', 'D', 'C'], ['B', 'A', 'D', 'A']], primary_duration=2)
    ccb.addCollision([5, 10], [['C', 'D', 'C'], ['C', 'A']], primary_duration=2)
    ccb.addCollision([751, 190], [['A', 'D', 'C'], ['B']], primary_duration=2)
    ccb.addCollision([81, 320], [['B', 'D', 'A', 'C'], ['A', 'D']], primary_duration=2)
    ccb.addCollision([300, 100], [['A', 'D', 'A'], ['B', 'C', 'A']], primary_duration=2)
    ccb.to_svg('unicolor.svg')
    
    # display the new animation
    webbrowser.open('unicolor.svg')
    