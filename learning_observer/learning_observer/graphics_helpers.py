'''
Helpers to make things look pretty.
'''

import colorsys
import hashlib
import svgwrite


φ = 1.61803


class ColorWheel:
    '''
    Returns colors circling around value, keeping hue and saturation fixed.

    We move by the golden ratio, which keeps an optimal distribution of distance
    between colors
    '''
    def __init__(self):
        self.h = 0
        self.s = 0.5
        self.v = 0.5

    def next_color(self):
        '''
        Move onto the next color
        '''
        self.h = self.h + φ
        self.h = self.h % 1

    def color_from_hash(self, s):
        '''
        Return a color from a string hash
        '''
        hash = int(hashlib.sha1(s.encode('utf-8')).hexdigest(), 16) % 2**16
        self.h = (hash * φ) % 1

    def rgb_format(self):
        '''
        Return a color in an RGB format, appropriate for plotly or css
        '''
        return 'rgb({0},{1},{2})'.format(*map(lambda x: int(x * 255), colorsys.hsv_to_rgb(self.h, self.s, self.v)))

    def hex_format(self):
        '''
        Return a color in an hex format
        '''
        return '#{0:02x}{1:02x}{2:02x}'.format(*map(lambda x: int(x * 255), colorsys.hsv_to_rgb(self.h, self.s, self.v)))


def default_user_icon(name):
    '''
    Get a default user icon as an SVG.

    Args:
        name (str): The name of the user.

    Returns:
        str: The default user icon.
    '''
    if name is None or name == "":
        name = 'Anonymous Anonymous'
    if len(name) <= 2:
        intials = name
    else:
        initials = name.split()[0][0].upper() + name.split()[-1][0].upper()
    d = svgwrite.Drawing(height=200, width=200)
    fill = ColorWheel()
    fill.color_from_hash(name)
    d.add(
        d.circle(
            center=(100, 100),
            r=100,
            fill=fill.hex_format()
        )
    )
    d.add(
        d.text(
            initials,
            insert=(100, 125),
            font_size=100,
            fill="white",
            text_anchor="middle",
            alignment_baseline="middle",
            font_family="sans-serif",
            font_weight="bold",
            text_rendering="optimizeLegibility",
            style="text-rendering: optimizeLegibility; font-family: sans-serif; font-weight: bold;",
        )
    )

    # Workaround for svgwrite bug. It ignores the height and width attributes
    # when rendering the SVG, and sets them to 100% instead.
    buggy_image = d.tostring()
    if "200px" in buggy_image:
        print("Huzza! svgwrite bug fixed!")
        print("Please remove the bug fix")
    else:
        fixed_image = buggy_image.replace('100%"', '200px"')
    return fixed_image


if __name__ == '__main__':
    print(default_user_icon("John Doe"))
    print(default_user_icon("Jim"))
    print(default_user_icon("李小龙"))  # Chinese support is a bit limited "李李" is not good
    print(default_user_icon("أحمد علي"))
    print(default_user_icon("Александр Пушкин"))
    print(default_user_icon("José Antonio"))
    print(default_user_icon("Janusz Zieliński"))
