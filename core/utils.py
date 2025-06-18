import colorsys
import re


class ColorThemeGenerator:
    """Generate complete color themes from primary colors"""

    def __init__(self, primary_color, secondary_color):
        self.primary = primary_color
        self.secondary = secondary_color

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB values"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])

        try:
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
        except ValueError:
            return "27, 94, 32"  # Fallback to default primary

    def rgb_to_hex(self, r, g, b):
        """Convert RGB values to hex color"""
        return f"#{r:02x}{g:02x}{b:02x}"

    def hex_to_hsl(self, hex_color):
        """Convert hex color to HSL"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])

        try:
            r, g, b = [int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4)]
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            return h * 360, s * 100, l * 100
        except ValueError:
            return 120, 60, 25  # Fallback HSL

    def hsl_to_hex(self, h, s, l):
        """Convert HSL to hex color"""
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0

        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return self.rgb_to_hex(int(r * 255), int(g * 255), int(b * 255))

    def lighten_color(self, hex_color, amount=0.1):
        """Lighten a color by increasing lightness"""
        h, s, l = self.hex_to_hsl(hex_color)
        l = min(100, l + (amount * 100))
        return self.hsl_to_hex(h, s, l)

    def darken_color(self, hex_color, amount=0.1):
        """Darken a color by decreasing lightness"""
        h, s, l = self.hex_to_hsl(hex_color)
        l = max(0, l - (amount * 100))
        return self.hsl_to_hex(h, s, l)

    def adjust_saturation(self, hex_color, amount=0.1):
        """Adjust color saturation"""
        h, s, l = self.hex_to_hsl(hex_color)
        s = max(0, min(100, s + (amount * 100)))
        return self.hsl_to_hex(h, s, l)

    def generate_success_color(self, primary_color):
        """Generate success color based on primary"""
        h, s, l = self.hex_to_hsl(primary_color)
        # Shift towards green
        h = 120  # Green hue
        s = max(50, s)
        return self.hsl_to_hex(h, s, l)

    def generate_info_color(self, primary_color):
        """Generate info color based on primary"""
        h, s, l = self.hex_to_hsl(primary_color)
        # Shift towards blue
        h = 210  # Blue hue
        return self.hsl_to_hex(h, s, l)

    def generate_warning_color(self, primary_color):
        """Generate warning color based on primary"""
        h, s, l = self.hex_to_hsl(primary_color)
        # Shift towards orange
        h = 35  # Orange hue
        s = max(70, s)
        return self.hsl_to_hex(h, s, l)

    def generate_danger_color(self, primary_color):
        """Generate danger color based on primary"""
        h, s, l = self.hex_to_hsl(primary_color)
        # Shift towards red
        h = 0  # Red hue
        s = max(60, s)
        return self.hsl_to_hex(h, s, l)

    def generate_accent_color(self, primary_color, secondary_color):
        """Generate accent color from primary and secondary"""
        h1, s1, l1 = self.hex_to_hsl(primary_color)
        h2, s2, l2 = self.hex_to_hsl(secondary_color)

        # Create complementary color
        h_accent = (h1 + 180) % 360
        s_accent = (s1 + s2) / 2
        l_accent = (l1 + l2) / 2

        return self.hsl_to_hex(h_accent, s_accent, l_accent)

    def is_dark_color(self, hex_color):
        """Check if color is dark (for determining text color)"""
        h, s, l = self.hex_to_hsl(hex_color)
        return l < 50

    def get_contrast_color(self, hex_color):
        """Get contrasting text color (white or black)"""
        return "#ffffff" if self.is_dark_color(hex_color) else "#000000"
