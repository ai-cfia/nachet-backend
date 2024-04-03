"""
Contains the colors palettes uses to colors the boxes.
"""

class FormatWarning(UserWarning):
    pass


SET1 = [
    (0.89411764705882357, 0.10196078431372549, 0.10980392156862745),
    (0.21568627450980393, 0.49411764705882355, 0.72156862745098038),
    (0.30196078431372547, 0.68627450980392157, 0.29019607843137257),
    (0.59607843137254901, 0.30588235294117649, 0.63921568627450975),
    (1.0,                 0.49803921568627452, 0.0                ),
    (1.0,                 1.0,                 0.2                ),
    (0.65098039215686276, 0.33725490196078434, 0.15686274509803921),
    (0.96862745098039216, 0.50588235294117645, 0.74901960784313726),
    (0.6,                 0.6,                 0.6)
]


SET2 = [
    (0.4,                 0.76078431372549016, 0.6470588235294118 ),
    (0.9882352941176471,  0.55294117647058827, 0.3843137254901961 ),
    (0.55294117647058827, 0.62745098039215685, 0.79607843137254897),
    (0.90588235294117647, 0.54117647058823526, 0.76470588235294112),
    (0.65098039215686276, 0.84705882352941175, 0.32941176470588235),
    (1.0,                 0.85098039215686272, 0.18431372549019609),
    (0.89803921568627454, 0.7686274509803922,  0.58039215686274515),
    (0.70196078431372544, 0.70196078431372544, 0.70196078431372544)
]


def get_color_palettes(set_: str = "set1", format_: str = "hex") -> list:
    """
    Get color palettes based on the specified set and format.

    Args:
        set_ (str, optional): The color set to use. Defaults to "set1".
        format_ (str, optional): The format of the color values. Defaults to "hex".

    Returns:
        list: The color palettes in the specified format.

    Raises:
        FormatWarning: If an invalid format is selected.
    """
    hex = ""
    colors = []

    if set_ == "set1":
        color_set = SET1

    if set_ == "set2":
        color_set = SET2

    match format_:
        case "hex":
            for color in color_set:
                for v in color:
                    hex += "{:02X}".format(int(v * 255))
                    colors.append(f"#{hex}")
        case "rgb":
            for color in color_set:
                r, g, b = color
                colors.append((r*255, g*255, b*255))

        case _:
            colors = color_set
            raise FormatWarning(f"no valid format selected {format_}")

    return colors
