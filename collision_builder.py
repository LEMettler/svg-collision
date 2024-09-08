#
# Created on:  Tue Sep 03 2024
# By:  Lukas Mettler (lukas.mettler@student.kit.edu)
# https://github.com/LEMettler
#


import numpy as np
import matplotlib.pyplot as plt
import os, sys
import webbrowser
import json
import time

np.random.seed(int(time.time()))



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



def reflect(pos, wall, width, height):
    wall = wall.strip()
    if wall == 'A':
        return [pos[0], -pos[1]]
    if wall == 'C':
        return [pos[0], 2*height - pos[1]]
    if wall == 'B':
        return [2*width - pos[0], pos[1]]
    if wall == 'D':
        return [-pos[0], pos[1]]
    print('Error')

def calculateAngle(A, Bstar):
    return np.rad2deg(2*np.pi + np.arctan2(Bstar[1]-A[1], Bstar[0]-A[0])) % 360 # [0,360)



def calculatePathLength(coordinates):
    
    coords = np.array(coordinates)
    deltas = np.diff(coords, axis=1)
    
    distances = np.sqrt(np.sum(deltas**2, axis=0))
    
    return np.sum(distances)
    

def array2d_string(path_arr, inverse_direction=True):

    x_arr = np.array(path_arr[0])
    y_arr = np.array(path_arr[1])

    if inverse_direction:
        x_arr = x_arr[::-1]
        y_arr = y_arr[::-1]

    content = f'M{x_arr[0]},{y_arr[0]}'
    for px, py in zip(x_arr[1:], y_arr[1:]):
        content += f' L{px:.3f},{py:.3f}'
        
    return content


def line2svgPath(d, identifier, color='#ffffff', stroke_width=2, begin=0, dur=3, stroke_max=1000, fill='none', animate=True):
    line = f'<path d="{d}"\n  stroke="{color}" stroke-width="{stroke_width}" fill="{fill}"'

    if animate:
        #growing animation
        line += f'\n  stroke-dasharray="{stroke_max}" stroke-dashoffset="{stroke_max}">    \n  \n  <animate \n  id="{identifier}grow" \n  attributeName="stroke-dashoffset" \n    from="{stroke_max}" \n    to="0" \n    begin="{begin}s"\n    dur="{dur}s" \n    fill="freeze"/> \n'
    else:
        line += f'> \n\n'
        
    line += f'</path>'

    return line



def primary2Path(d, color='#ffffff', stroke_width=2, begin=0, dur=3, dur_fade= 1.0, stroke_max=1000, fill='none', animate=True):
    line = f'<path d="{d}"\n  stroke="{color}" stroke-width="{stroke_width}" fill="{fill}"'

    if animate:
        #growing animation
        line += f'\n  stroke-dasharray="{stroke_max}" stroke-dashoffset="{stroke_max}">    \n  \n' 
        line += f'<animate \n  id="primarygrow" \n  attributeName="stroke-dashoffset" \n    from="{stroke_max}" \n    to="0" \n    begin="{begin}s;secondaryfade.end"\n    dur="{dur}s" \n    fill="freeze"/> \n'

        # opacity fade
        line += f'\n <animate id="primaryfade" \n attributeName="opacity" \n from="1" \n to="0" \n begin="primarygrow.end" \n  dur="{dur_fade}s" \n fill="freeze" /> \n '

        # reset values
        line += f'\n<set attributeName="stroke-dashoffset" to="{stroke_max}" begin="secondaryfade.end-0.001s"/>\n'
        line += f'<set attributeName="opacity" to="1" begin="secondaryfade.end-0.001s"/>\n'

    else:
        line += f'> \n\n'
        
    line += f'</path>'

    return line


def secondary2Path(d, color='#00c666', stroke_width=2, dur=3, dur_fade= 1.0, dur_freeze=1.5, stroke_max=1000, fill='none', animate=True):
    line = f'<path d="{d}"\n  stroke="{color}" stroke-width="{stroke_width}" fill="{fill}"'

    if animate:
        #growing animation
        line += f'\n  stroke-dasharray="{stroke_max}" stroke-dashoffset="{stroke_max}">    \n  \n' 
        line += f'<animate \n  id="secondarygrow" \n  attributeName="stroke-dashoffset" \n    from="{stroke_max}" \n    to="0" \n    begin="primarygrow.end"\n    dur="{dur}s" \n    fill="freeze"/> \n'

        # opacity fade
        line += f'\n <animate id="secondaryfade" \n attributeName="opacity" \n from="1" \n to="0" \n begin="primarygrow.end+{dur_freeze}s" \n  dur="{dur_fade}s" \n fill="freeze" /> \n '

        # reset values
        line += f'\n<set attributeName="stroke-dashoffset" to="{stroke_max}" begin="secondaryfade.end-0.001s"/>\n'
        line += f'<set attributeName="opacity" to="1" begin="secondaryfade.end-0.001s"/>\n'

    else:
        line += f'> \n\n'
        
    line += f'</path>'

    return line




class CollisionBuider:
    def __init__(self, width, height, point_of_contact, incoming_angles=[], relative_margin=0.05):
        self.width = width
        self.height = height 
        self.point_of_contact = point_of_contact
        self.incoming_angles = incoming_angles
        self.relative_margin = relative_margin

        self.primary_paths = []
        self.secondary_paths = []


    def setStyle(self, collision_index, primary_color='#ffffff', secondary_color='#00c666',
                primary_stroke_width=2, secondary_stroke_width=1,
                  primary_duration=2, secondary_duration=1, primary_begin=0, 
                  dur_fade_primary=1.0, dur_fade_secondary=0.5, dur_freeze_secondary=1.0,
                  background_color='#dc7474', box_color='#3c3c3c'):
        self.collision_index = collision_index
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.primary_stroke_width = primary_stroke_width
        self.secondary_stroke_width = secondary_stroke_width
        self.primary_duration = primary_duration
        self.secondary_duration = secondary_duration
        self.primary_begin = primary_begin
        self.background_color = background_color
        self.box_color = box_color
        self.dur_fade_primary = dur_fade_primary
        self.dur_fade_secondary = dur_fade_secondary
        self.dur_freeze_secondary = dur_freeze_secondary



    def calculatePrimaryPaths(self, n_bounces):
        if type(n_bounces) == int:
            n_bounces = [n_bounces]* len(self.incoming_angles)
        
        for n, alpha in zip(n_bounces, self.incoming_angles):
            x_path, y_path = [self.point_of_contact[0]], [self.point_of_contact[1]]
            
            for i in range(int(n)):
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


    def addPrimaryFrom(self, start_pos, wall_collisions):
        '''
        - start_pos: a (x, y)
        - wall collisions: Combination of "A", "B", "C", "D" [[path1], [path2], ...] (in time-forward order)
        ---------------------------------------
        Calculate and Save the path(s) to be taken from start_pos (a) -> point_of_collision (b)
        '''

        n_bounces = []
        # allow multiple paths to be computed
        for this_wall_collision_path in wall_collisions:

            # calculate virtual endpoint
            virtual_end_pos = start_pos.copy()
            for coll in this_wall_collision_path[::-1]:
                virtual_end_pos = reflect(virtual_end_pos, coll, self.width, self.height)


            # calculate angle going out from a, aimed at virtual b
            start_alpha = calculateAngle(self.point_of_contact, virtual_end_pos)

            self.incoming_angles.append(start_alpha)
            n_bounces.append(len(this_wall_collision_path))


        # compute the paths of collision
        self.calculatePrimaryPaths(n_bounces)

        # need to add a last point: b
        for i in range(len(self.primary_paths)):
            self.primary_paths[i][0].append(start_pos[0])
            self.primary_paths[i][1].append(start_pos[1])




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
                  primary_duration=2, secondary_duration=1, primary_begin=0, 
                  dur_fade_primary=1.0, dur_fade_secondary=0.5, dur_freeze_secondary=1.0,
                  background_color='#dc7474', box_color='#3c3c3c'):
        
        
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
            d_string = array2d_string(primary_path, inverse_direction=True)
            total_length = calculatePathLength(primary_path)

            if primary_color == '0':
                col = hsl_to_hex(np.random.rand(), 1, 0.5)
            else:
                col = primary_color
            
            path_string = primary2Path(d=d_string,
                                       color=col, stroke_width=primary_stroke_width,
                                       begin=primary_begin, dur=primary_duration, stroke_max=total_length,
                                         animate=True, dur_fade=dur_fade_primary)
            
            total_string += path_string + '\n\n\n'


        # loop over secondary paths
        for secondary_path in self.secondary_paths:
            # this is the path as a string of Mx,y Lx,y ...
            d_string = array2d_string(secondary_path, inverse_direction=False)
            total_length = calculatePathLength(secondary_path)




            if secondary_color == '0':
                col = hsl_to_hex(np.random.rand(), 1, 0.5)
            else:
                col = secondary_color
            

            path_string = secondary2Path(d=d_string, 
                                       color=col, stroke_width=secondary_stroke_width,
                                       dur=secondary_duration,stroke_max=total_length,
                                    animate=True, dur_fade=dur_fade_secondary, dur_freeze=dur_freeze_secondary)
            
            total_string += path_string + '\n\n'


        #end the string
        total_string += '</g>\n\n</svg>'

        # write
        with open(name, 'w') as file:
            file.write(total_string)
        
        print(f'Writen to {name}!')


    #########################################################################
    def prepare_for_multi_svg(self, template_path, last_collision_index=-1):
        with open(template_path) as template_file:
            template_string = template_file.read()


        def insertParameters(path, length, color, width,
                            stroke_id, stroke_begin, stroke_duration, stroke_reset_begin,
                            opacity_id, opacity_begin, opacity_duration, opacity_reset_begin):
            path_string = template_string
            
            path_string = path_string.replace('_PATH_', path)
            path_string = path_string.replace('_LENGTH_', length)
            path_string = path_string.replace('_COLOR_', color)
            path_string = path_string.replace('_WIDTH_', width)
            path_string = path_string.replace('_STROKE-ID_', stroke_id)
            path_string = path_string.replace('_STROKE-BEGIN_', stroke_begin)
            path_string = path_string.replace('_STROKE-DURATION_', stroke_duration)
            path_string = path_string.replace('_OPACITY-ID_', opacity_id)
            path_string = path_string.replace('_OPACITY-BEGIN_', opacity_begin)
            path_string = path_string.replace('_OPACITY-DURATION_', opacity_duration)
            path_string = path_string.replace('_STROKE-RESET-BEGIN_', stroke_reset_begin)
            path_string = path_string.replace('_OPACITY-RESET-BEGIN_', opacity_reset_begin)

            return path_string + '\n\n'
        


        this_collision_string = ''


        if self.collision_index > 0:
            last_collision_index = self.collision_index - 1

        # loop over the primaries

        primary_stroke_id = f'primary{self.collision_index}_stroke'
        primary_opacity_id = f'primary{self.collision_index}_opacity'

        primary_stroke_begin = f'primary{last_collision_index}_stroke.end'
        if self.collision_index == 0:
            primary_stroke_begin += ';0s'
        primary_stroke_reset = f'primary{last_collision_index}_stroke.end-0.001s'
        
        primary_opacity_begin = f'primary{self.collision_index}_stroke.end'
        primary_opacity_reset = f'primary{last_collision_index}_stroke.end-0.001s'


        for path_array in self.primary_paths:
            d_string = array2d_string(path_array, inverse_direction=True)
            total_length = calculatePathLength(path_array)

            this_collision_string += insertParameters(path=d_string, length=str(total_length),
                                            color=self.primary_color,
                                            width=f'{self.primary_stroke_width}',
                                            stroke_id=primary_stroke_id,
                                            stroke_begin=primary_stroke_begin,
                                            stroke_duration=f'{self.primary_duration}s',
                                            stroke_reset_begin=primary_stroke_reset,
                                            opacity_id=primary_opacity_id,
                                            opacity_begin=primary_opacity_begin,
                                            opacity_duration=f'{self.dur_fade_primary}s',
                                            opacity_reset_begin=primary_opacity_reset)
            



        # loop over the secondaries

        secondary_stroke_id = f'secondary{self.collision_index}_stroke'
        secondary_opacity_id = f'secondary{self.collision_index}_opacity'
        
        secondary_stroke_begin = f'primary{self.collision_index}_stroke.end'
        secondary_stroke_reset = f'primary{last_collision_index}_stroke.end-0.001s'

        secondary_opacity_begin = f'primary{self.collision_index}_stroke.end+{self.dur_freeze_secondary}s'
        secondary_opacity_reset = f'primary{last_collision_index}_stroke.end-0.001s'



        for path_array in self.secondary_paths:
            d_string = array2d_string(path_array, inverse_direction=False)
            total_length = calculatePathLength(path_array)

            this_collision_string += insertParameters(path=d_string, length=str(total_length),
                                            color=self.secondary_color,
                                            width=f'{self.primary_stroke_width}',
                                            stroke_id=secondary_stroke_id,
                                            stroke_begin=secondary_stroke_begin,
                                            stroke_duration=f'{self.secondary_duration}s',
                                            stroke_reset_begin=secondary_stroke_reset,
                                            opacity_id=secondary_opacity_id,
                                            opacity_begin=secondary_opacity_begin,
                                            opacity_duration=f'{self.dur_fade_secondary}s',
                                            opacity_reset_begin=secondary_opacity_reset)
            
        return this_collision_string
            
            
            

            
            

        



    #########################################################################



def hsl_to_hex(h, s, l):
    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

    r, g, b = [int(x * 255) for x in (r, g, b)]
    return f'#{r:02x}{g:02x}{b:02x}'


##################################################################

def clear_terminal():
    #For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    #For Unix/Linux/MacOS
    else:
        _ = os.system('clear')

def get_random_point(width, height):
    return (np.random.uniform(0, width), np.random.uniform(0, height))

def get_random_angles(n):
    return list(np.random.uniform(0, 360, size=n))



def print_parameters(params):
    print(f"Primary and secondary colors can be randomized with: 0")
    print("\nCurrent Parameters:\n")
    for i, (key, value) in enumerate(params.items(), 1):
        print(f"{i}. {key}: {value}")

    print(f'\n{len(params)+1}. Load parameters from file')
    print(f"\n0. Continue")


def get_user_choice(params):
    while True:
        try:
            choice = int(input("\nEnter the number of the parameter you want to modify (or Continue): "))
            if 0 <= choice <= len(params) + 1:
                return choice
            else:
                print("Invalid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")



def modify_parameter(params, choice):
    key = list(params.keys())[choice - 1]
    current_value = params[key]

    print(f"\nCurrent {key}: {current_value}")

    # Is listed parameter
    if isinstance(current_value, (list, tuple, np.ndarray)):
        new_list = []

        if key == 'point_of_contact':
            km = 2
        else:
            km = params['n_primaries']
        for k in range(km):
            new_value = float(input(f"New ({k+1}/{km}): "))
            new_list.append(new_value)
        params[key] = new_list
        return
            
    # Non-List parameter
    new_value = input(f"New {key}: ")
    
    # Convert the input to the appropriate type
    if  isinstance(current_value, int):
        params[key] = int(new_value)
    elif isinstance(current_value, float):
        params[key] = float(new_value)
    elif isinstance(current_value, bool):
        params[key] = bool(new_value)
    else:
        params[key] = new_value

    # Some changes demand other recalculations
    if key == 'n_primaries':
        params['incoming_angles'] = get_random_angles(int(new_value))
        params['n_border_collisions'] = int(new_value)*[int(np.mean(params['n_border_collisions']))]
    



def store_parameters(params, filename):
    with open(filename, 'w') as f:
        json.dump(params, f, indent=4)
    print(f"Parameters saved to {filename}")

def load_parameters(filename):
    try:
        with open(filename, 'r') as f:
            loaded_params = json.load(f)
        print(f"Parameters loaded from {filename}")
        return loaded_params
    except FileNotFoundError:
        print(f"File {filename} not found. Using default parameters.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding {filename}. Using default parameters.")
        return None



def input_mask(params):

    # Can pass a file to load when calling the file
    # python3 collision-builder.py file.json
    if len(sys.argv) > 1:
        filename = str(sys.argv[-1])
        loaded_params = load_parameters(filename)
        if loaded_params:
            params = loaded_params
            params['parameter_file'] = filename
            #return params
        else:
            print(f'Could not load file: {filename}!')


    while True:
        print_parameters(params)
        choice = get_user_choice(params)
        
        # Continue
        if choice == 0:
            break

        # Load Parameter from file
        elif choice == len(params) + 1: 
            clear_terminal()
            filename = input("Parameter file: ")
            loaded_params = load_parameters(filename)
            if loaded_params:
                params = loaded_params
            else:
                print(f'Could not load file: {filename}!')

        # Change Parameters
        else:
            modify_parameter(params, choice)
            clear_terminal()

    if params['store_parameters']:
        store_parameters(params, filename=params['parameter_file'])

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
        'width': 800,
        'height': 300,
        'n_primaries': 3,
        'n_secondaries': 30,
        'point_of_contact': get_random_point(800, 300),
        'incoming_angles': get_random_angles(3),
        'n_border_collisions': [15, 15, 15],
        'alpha_std': 40.,
        'length_mean': 200.,
        'length_std': 100.,
        'secondary_duration': 0.3,
        'primary_begin': 0,
        'primary_duration': 3.,
        'dur_fade_primary': 1.0,
        'dur_fade_secondary': 0.5,
        'dur_freeze_secondary': 1.5,
        'primary_stroke_width': 4.5,
        'secondary_stroke_width': 2.5,
        'primary_color': '#ffffff',
        'secondary_color': '#fff200',
        'background_color': '#c62100',
        'box_color': '#3c3c3c',
        'relative_margin': 0.05,
        'name': 'animations/test.svg',
        'parameter_file': 'configs/test.json',
        'store_parameters': 1,
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
                     box_color=params['box_color'],
                     dur_fade_primary=params['dur_fade_primary'],
                     dur_fade_secondary=params['dur_fade_secondary'],
                     dur_freeze_secondary=params['dur_freeze_secondary'])
    
    # display the new animation
    webbrowser.open(params['name'])

    
if __name__ == "__main__":
    main()