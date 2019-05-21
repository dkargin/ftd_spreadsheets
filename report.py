from IPython.display import HTML, display
import math


def formatValue(key, value):
    """
    Formating value to be displayed in results table
    """
    if key == 'diameter':
        return '{:3}'.format(math.floor(value*1000))
    if key == 'damage':
        damage_data = []
        for dtype, damage in value.items():
            if isinstance(damage, tuple) and len(damage) == 2:
                damage_data.append('{0}={1:3d}:{2:3.1f}'.format(dtype, int(damage[0]), damage[1]))
            else:
                damage_data.append('{0}={1}'.format(dtype, str(damage)))
        return '</br>'.join(damage_data)
    if isinstance(value, float):
        return '{: 3.2f}'.format(value)

    return str(value)


def displayTable(results, columns=None):
    """
    Generates HTML table for results obtained from calcBestShells
    @param results - a list with results, obtained from calcBestShells
    @param columns:list - a list of column names to be displayed
    """
    if columns is None:
        columns = ["dps", "damage", "diameter", "velocity", "period", "blocks", "shell"]
    # Row start - caption
    # Column - output variant
    # html = <table><tr><td>Name</td><td>Data1</td></tr></table>
    caption = '<td>{}</td>'.format('</td><td>'.join('<b>{}</b>'.format(str(key).upper()) for key in columns))
    rows = []
    for row in results:
        line = '</td><td>'.join(formatValue(key, row[key]) for key in columns)
        rows.append('<td>{}</td>'.format(line))

    htmlData = '</tr><tr>'.join(rows)
    return display(HTML('<table><tr>' + caption + '</tr><tr>' + htmlData + '</tr></table>'))


def BBcode_formatValue(key, value):
    """
    Formating value to be displayed in results table
    """
    if key == 'diameter':
        return '{:3}'.format(math.floor(value*1000))
    if key == 'damage':
        damage_data = []
        for dtype, damage in value.items():
            if isinstance(damage, tuple) and len(damage) == 2:
                damage_data.append('{0}={1:3d}:{2:3.1f}'.format(dtype, int(damage[0]), damage[1]))
            else:
                damage_data.append('{0}={1}'.format(dtype, str(damage)))
        return ' '.join(damage_data)
    if isinstance(value, float):
        return '{: 3.2f}'.format(value)

    return str(value)


def BBcode_displayTable(results, columns=None):
    """
    Generates BBcode table for results obtained from calcBestShells
    @param results - a list with results, obtained from calcBestShells
    @param columns:list - a list of column names to be displayed
    """
    if columns is None:
        columns = ["dps", "damage", "diameter", "velocity", "period", "shell"]
    # Row start - caption
    # Column - output variant
    # html = <table><tr><td>Name</td><td>Data1</td></tr></table>
    caption = '[th]{}[/th]'.format('[/td][th]'.join('[b]{}[/b]'.format(str(key).upper()) for key in columns))
    rows = []
    for row in results:
        line = '[/td][td]'.join(BBcode_formatValue(key, row[key]) for key in columns)
        rows.append('[td]{}[/td]'.format(line))

    htmlData = '[/tr][tr]'.join(rows)
    return '[table][tr]' + caption + '[/tr][tr]' + htmlData + '[/tr][/table]'