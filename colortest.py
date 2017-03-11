'''
    Outputs an HTML webpage to stdout to visualize a set of colors
'''


def mkColor(name, color):
    ''' Converts a `name` and `rgb` (any CSS format) to a few CSS lines '''
    return '.color-{} {{\n\tcolor: {}\n}}\n'.format(name, color)


CSS_COLORS = {
    'white': 'Beige',
    'black': 'DarkSlateGrey',
    'blue': 'DarkSlateBlue',
    'green': 'ForestGreen',
    'lightred': 'Tomato',
    'red': 'Crimson',
    'magenta': 'MediumVioletRed',
    'brown': 'Chocolate',
    'yellow': 'GoldenRod',
    'lightgreen': 'LightGreen',
    'cyan': 'LightSeaGreen',
    'lightcyan': 'LightSkyBlue',
    'lightblue': 'RoyalBlue',
    'lightmagenta': 'HotPink',
    'darkgray': 'DimGrey',
    'gray': 'LightSlateGrey',
}


css = ''
for color in CSS_COLORS:
    css += mkColor(color, CSS_COLORS[color])
css += '''
table {
    width: 40%;
    padding: 30px;
}
'''

content = ''
for color in CSS_COLORS:
    content += ('<tr><td>{}</td><td class="color-{}">{}</td>' +
                '<td style="background-color: {}; padding-left:200px;">' +
                '</td></tr>\n').format(
                    color, color, color, CSS_COLORS[color])

content = '''<table style="background-color: white; color: black; float: left">
{}
</table>
<table style="background-color: black; color: white;">
{}
</table>
'''.format(content, content)

page = '''
<html>
  <head>
    <style>
''' + css + '''
    </style>
  </head>
  <body>
''' + content + '''
</html>'''

print(page)
