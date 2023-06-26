from matplotlib.colors import ColorConverter

__all__ = ['alpha_blend_colors']

COLOR_CONVERTER = ColorConverter()


def alpha_blend_colors(colors, additional_alpha=1.0):
    """
    Given a sequence of colors, return the alpha blended color.

    This assumes the last color is the one in front.
    """

    srcr, srcg, srcb, srca = COLOR_CONVERTER.to_rgba(colors[0])
    srca *= additional_alpha

    for color in colors[1:]:
        dstr, dstg, dstb, dsta = COLOR_CONVERTER.to_rgba(color)
        dsta *= additional_alpha
        outa = srca + dsta * (1 - srca)
        outr = (srcr * srca + dstr * dsta * (1 - srca)) / outa
        outg = (srcg * srca + dstg * dsta * (1 - srca)) / outa
        outb = (srcb * srca + dstb * dsta * (1 - srca)) / outa
        srca, srcr, srcg, srcb = outa, outr, outg, outb

    return srcr, srcg, srcb, srca


def rgb_string(color, alpha=False):
    """
    Given a QColor, return an RGB/RGBA string representing
    that color.
    """

    prefix = "rgba" if alpha else "rgb"
    components = [color.red(), color.green(), color.blue()]
    if alpha:
        components.append(color.alpha())
    components = [str(c) for c in components]
    return f"{prefix}({', '.join(components)})"
