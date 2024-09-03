#
# Created on:  Tue Sep 03 2024
# By:  Lukas Mettler (lukas.mettler@student.kit.edu)
#
# https://github.com/LEMettler
#


import numpy as np
import matplotlib.pyplot as plt
import os
import webbrowser



def line(x, a, b):
    return x*a + b

def angle2line(x, x0, y0, alpha0):
    return np.tan(np.deg2rad(alpha0))*(x-x0) + y0

def inv_angle2line(y, x0, y0, alpha0):
    return (y-y0)/np.tan(np.deg2rad(alpha0)) + x0
    


def newCollsionPoint(x, y, alpha, width, height):
    yleft = angle2line(0, x, y, alpha)
    yright = angle2line(width, x, y, alpha)
    xbottom = inv_angle2line(0, x, y, alpha)
    xtop = inv_angle2line(height, x, y, alpha)

    if alpha < 90: # collision top-right
        if xtop > width:
            return (width, yright, 180-alpha) # collision right vertical
        else: 
            return (xtop, height, 360-alpha) # collision top horizontal
        
    if alpha < 180: # collsion top left
        if yleft > height:
            return (xtop, height, 360-alpha) # collision top horizontal

        else:
            return (0, yleft, 180-alpha) # collision left vertical


    if alpha < 270: # collsion bottom left
        if xbottom < 0:
            return (0, yleft, 540-alpha) # collision left vertical
        else:
            return (xbottom, 0, 360-alpha) # collision bottom horizontal
        
    # collision bottom right
    if xbottom > width:
        return (width, yright, 540-alpha) # collision right vertical
    else:
        return (xbottom, 0, 360-alpha) # collision bottom horizontal
    
    


def secondaryPaths(n, x0, y0, alpha1, alpha2, alpha_std=30, length_mean=50, length_std=10):
    alpha_mean = (alpha1 + alpha2)/2
    alpha_mean -= 180 #flip

    sec_alphas = alpha_mean + alpha_std*np.random.randn(n)
    sec_alphas[sec_alphas > 360] -= 360


    sec_lengths = length_mean + length_std*np.random.randn(n)

    sec_paths = []
    for s_a, s_l in zip(sec_alphas, sec_lengths):
        y1 = y0 + np.sin(np.deg2rad(s_a)) * s_l
        x1 = x0 + np.cos(np.deg2rad(s_a)) * s_l
        
        new_path = [[x0, x1], [y0, y1]]
        sec_paths.append(new_path)

    return sec_paths



def calculatePathLength(coordinates):
    
    coords = np.array(coordinates)
    deltas = np.diff(coords, axis=1)
    
    distances = np.sqrt(np.sum(deltas**2, axis=0))
    
    return np.sum(distances)
    

def array2d_string(path_arr, secondary=False):

    x_arr = np.array(path_arr[0])[::-1] # inverse direction
    y_arr = np.array(path_arr[1])[::-1] # inverse direction

    if secondary:
        x_arr = x_arr[::-1]
        y_arr = y_arr[::-1]

    content = f'M{x_arr[0]},{y_arr[0]}'
    for px, py in zip(x_arr[1:], y_arr[1:]):
        content += f' L{px:.3f},{py:.3f}'
        
    return content


def line2svgPath(d, identifier, color='#ffffff', stroke_width=2, begin=0, dur=3, stroke_max=1000, fill='none', animate=True, reverse=True):
    line = f'<path id="{identifier}"\n  d="{d}"\n  stroke="{color}" stroke-width="{stroke_width}" fill="{fill}"'

    if animate:
        if reverse:
            line += f'\n  stroke-dasharray="{stroke_max}" stroke-dashoffset="{stroke_max}">    \n  \n  <animate \n    attributeName="stroke-dashoffset" \n    from="0" \n    to="{stroke_max}" \n    begin="{begin}s"\n    dur="{dur}s" \n    fill="freeze"/> \n'
        else:
            line += f'\n  stroke-dasharray="{stroke_max}" stroke-dashoffset="{stroke_max}">    \n  \n  <animate \n    attributeName="stroke-dashoffset" \n    from="{stroke_max}" \n    to="0" \n    begin="{begin}s"\n    dur="{dur}s" \n    fill="freeze"/> \n'
    else:
        line += f'> \n\n'
        
    line += f'</path>'

    return line



class CollisionBuider:
    def __init__(self, width, height, point_of_contact, incoming_angles, relative_margin=0.05):
        self.width = width
        self.height = height 
        self.point_of_contact = point_of_contact
        self.incoming_angles = incoming_angles
        self.relative_margin = relative_margin

        self.primary_paths = []
        self.secondary_paths = []


    def calculatePrimaryPaths(self, n_bounces):
        if type(n_bounces) == int:
            n_bounces = [n_bounces]* len(self.incoming_angles)
        
        for n, alpha in zip(n_bounces, self.incoming_angles):
            x_path, y_path = [self.point_of_contact[0]], [self.point_of_contact[1]]
            
            for i in range(n):
                xi, yi, alpha = newCollsionPoint(x_path[-1], y_path[-1], alpha, self.width, self.height)
                x_path.append(xi)
                y_path.append(yi)
            self.primary_paths.append([x_path, y_path])


    def calculateSecondaryPaths(self, n_secondaries, alpha_std=30, length_mean=10, length_std=2):
        
        alpha_mean = np.mean(self.incoming_angles) + 180
        sec_alphas = alpha_mean + alpha_std*np.random.randn(n_secondaries)
        sec_alphas[sec_alphas > 360] -= 360

        sec_lengths = length_mean + length_std*np.random.randn(n_secondaries)

        for s_a, s_l in zip(sec_alphas, sec_lengths):
            x1 = self.point_of_contact[0] + np.cos(np.deg2rad(s_a)) * s_l
            y1 = self.point_of_contact[1] + np.sin(np.deg2rad(s_a)) * s_l
            
            new_path = [[self.point_of_contact[0], x1], [self.point_of_contact[1], y1]]
            self.secondary_paths.append(new_path)


    def plotResult(self):
        plt.figure(figsize=(10, self.height/self.width*10))
        plt.plot([0, self.width, self.width, 0, 0], [0, 0, self.height, self.height, 0], color='k')
        for primary_path in self.primary_paths:
            plt.plot(*primary_path, color='blue', linewidth=2)

        for secondary_path in self.secondary_paths:
            plt.plot(*secondary_path, color='orange', linewidth=1)

        plt.show()

        

    def to_svg(self, name, primary_color='#ffffff', secondary_color='#00c666',
                primary_stroke_width=2, secondary_stroke_width=1,
                  primary_duration=2, secondary_duration=1, primary_begin=0, background_color='#dc7474', box_color='#3c3c3c'):
        
        secondary_begin = (primary_duration + primary_begin)

        #begin the string
        total_string = f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">\n\n'



        # background box
        d_box = f'M0,0 L{self.width},0 L{self.width},{self.height} L0,{self.height} Z'
        box_string = line2svgPath(d=d_box, identifier='box',
                                  color=background_color, stroke_width=0, animate=False, fill=background_color)
        total_string += box_string + '\n\n'   


        # rescaling and translation to center
        scale_w = 1 - self.relative_margin
        scale_h = round(1 - self.width * self.relative_margin / self.height, 3)
        translation = self.relative_margin*self.width/2
        total_string += f'<g transform="scale({scale_w},{scale_h}) translate({translation}, {translation})"> \n\n'


        # surrounding box
        d_box = f'M0,0 L{self.width},0 L{self.width},{self.height} L0,{self.height} Z'
        box_string = line2svgPath(d=d_box, identifier='box',
                                  color=box_color, stroke_width=0.5, animate=False, fill=box_color)
        total_string += box_string + '\n\n'   



        # loop over primary paths
        for primary_path in self.primary_paths:
            # this is the path as a string of Mx,y Lx,y ...
            d_string = array2d_string(primary_path)
            total_length = calculatePathLength(primary_path)
            
            path_string = line2svgPath(d=d_string, identifier='primary-path',
                                       color=primary_color, stroke_width=primary_stroke_width,
                                       begin=primary_begin, dur=primary_duration, stroke_max=total_length,
                                         animate=True, reverse=False)
            
            total_string += path_string + '\n\n\n'


        # loop over secondary paths
        for secondary_path in self.secondary_paths:
            # this is the path as a string of Mx,y Lx,y ...
            d_string = array2d_string(secondary_path, secondary=True)
            total_length = calculatePathLength(secondary_path)
            path_string = line2svgPath(d=d_string, identifier='secondary-path',
                                       color=secondary_color, stroke_width=secondary_stroke_width,
                                       begin=secondary_begin, dur=secondary_duration,stroke_max=total_length,
                                       animate=True, reverse=False)
            
            total_string += path_string + '\n\n'


        #end the string
        total_string += '</g>\n\n</svg>'

        # write
        with open(name, 'w') as file:
            file.write(total_string)
        
        print(f'Writen to {name}!')



##################################################################

def clear_terminal():
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For Unix/Linux/MacOS
    else:
        _ = os.system('clear')

def get_random_point(width, height):
    return (np.random.uniform(0, width), np.random.uniform(0, height))

def get_random_angles(n):
    return np.random.uniform(0, 360, size=n)

def print_parameters(params):
    print("\nCurrent Parameters:\n")
    for i, (key, value) in enumerate(params.items(), 1):
        print(f"{i}. {key}: {value}")
    print(f"\n{len(params) + 1}. Continue")


def get_user_choice(params):
    while True:
        try:
            choice = int(input("\nEnter the number of the parameter you want to modify (or Continue): "))
            if 1 <= choice <= len(params) + 1:
                return choice
            else:
                print("Invalid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")



def modify_parameter(params, choice):
    key = list(params.keys())[choice - 1]
    current_value = params[key]
    
    print(f"\nCurrent {key}: {current_value}")
    new_value = input(f"New {key}: ")
    
    # Convert the input to the appropriate type
    if isinstance(current_value, int):
        params[key] = int(new_value)
    elif isinstance(current_value, float):
        params[key] = float(new_value)
    elif isinstance(current_value, tuple):
        params[key] = tuple(map(float, new_value.strip('()').split(',')))
    elif isinstance(current_value, list):
        params[key] = list(map(float, new_value.strip('[]').split(',')))
    else:
        params[key] = new_value


    # Some changes demand other recalculations
    if key == 'n_primaries':
        params['incoming_angles'] = get_random_angles(int(new_value))
        params['n_border_collisions'] = int(new_value)*[int(np.mean(params['n_border_collisions']))]
    



def input_mask(params):
    clear_terminal()
    while True:
        print_parameters(params)
        choice = get_user_choice(params)
        
        if choice == len(params) + 1:
            break
        else:
            modify_parameter(params, choice)
            clear_terminal()

    clear_terminal()
    print("\nParameters:")
    for key, value in params.items():
        print(f"{key}: {value}")

    return params


##################################################################
##################################################################
##################################################################


def main():
    params = {
        'width': 200,
        'height': 100,
        'name': 'anim.svg',
        'point_of_contact': get_random_point(200, 100),
        'incoming_angles': get_random_angles(2),
        'n_border_collisions': [4, 4],
        'n_primaries': 2,
        'primary_begin': 0,
        'primary_stroke_width': 1,
        'primary_duration': 1.,
        'primary_color': '#ffffff',
        'n_secondaries': 20,
        'alpha_std': 30.,
        'length_mean': 50.,
        'length_std': 30.,
        'secondary_stroke_width': 0.4,
        'secondary_duration': 0.3,
        'secondary_color': '#00c666',
        'box_color': '#3c3c3c',
        'background_color': '#dc7474',
        'relative_margin': 0.05,
    }

    params = input_mask(params)

    collision = CollisionBuider(width=params['width'],
                                height=params['height'],
                                point_of_contact=params['point_of_contact'],
                                incoming_angles=params['incoming_angles'],
                                relative_margin=params['relative_margin']
                                )
    collision.calculatePrimaryPaths(params['n_border_collisions'])
    collision.calculateSecondaryPaths(n_secondaries=params['n_secondaries'],
                                      alpha_std=params['alpha_std'],
                                      length_mean=params['length_mean'],
                                      length_std=params['length_std'])
    

    #collision.plotResult()
    
    collision.to_svg(name=params['name'],
                     primary_color=params['primary_color'],
                     secondary_color=params['secondary_color'],
                     primary_stroke_width=params['primary_stroke_width'],
                     secondary_stroke_width=params['secondary_stroke_width'],
                     primary_duration=params['primary_duration'],
                     secondary_duration=params['secondary_duration'],
                     primary_begin=params['primary_begin'],
                     background_color=params['background_color'],
                     box_color=params['box_color'])
    
    # display the new animation
    webbrowser.open(params['name'])

    
if __name__ == "__main__":
    main()