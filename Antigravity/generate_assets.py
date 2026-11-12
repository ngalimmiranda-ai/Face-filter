"""
Script to generate transparent PNG filter assets (Dog and Cat filters)
using pure Python standard library (zlib + struct) without external dependencies.
"""

import os
import math
import struct
import zlib

def create_png(width, height, rgba_data, filepath):
    """Writes an RGBA byte buffer to a valid PNG file."""
    # PNG signature
    png = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr_crc = struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)
    png += struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + ihdr_crc
    
    # IDAT chunk
    raw_scanlines = bytearray()
    for y in range(height):
        raw_scanlines.append(0)  # Filter byte: None
        start = y * width * 4
        raw_scanlines.extend(rgba_data[start:start + width * 4])
        
    compressed = zlib.compress(bytes(raw_scanlines), level=9)
    idat_crc = struct.pack('>I', zlib.crc32(b'IDAT' + compressed) & 0xffffffff)
    png += struct.pack('>I', len(compressed)) + b'IDAT' + compressed + idat_crc
    
    # IEND chunk
    iend_crc = struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)
    png += struct.pack('>I', 0) + b'IEND' + iend_crc
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(png)
    print(f"Generated: {filepath} ({width}x{height})")


class Canvas:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        # Initialize transparent RGBA buffer
        self.buffer = bytearray(width * height * 4)

    def set_pixel(self, x, y, r, g, b, a):
        if 0 <= x < self.w and 0 <= y < self.h:
            idx = (y * self.w + x) * 4
            # Alpha blend over existing pixel
            existing_a = self.buffer[idx + 3] / 255.0
            new_a = a / 255.0
            out_a = new_a + existing_a * (1.0 - new_a)
            if out_a > 0:
                out_r = (r * new_a + self.buffer[idx] * existing_a * (1.0 - new_a)) / out_a
                out_g = (g * new_a + self.buffer[idx + 1] * existing_a * (1.0 - new_a)) / out_a
                out_b = (b * new_a + self.buffer[idx + 2] * existing_a * (1.0 - new_a)) / out_a
                self.buffer[idx] = int(min(255, max(0, out_r)))
                self.buffer[idx + 1] = int(min(255, max(0, out_g)))
                self.buffer[idx + 2] = int(min(255, max(0, out_b)))
                self.buffer[idx + 3] = int(min(255, max(0, out_a * 255)))

    def fill_circle(self, cx, cy, radius, r, g, b, a=255):
        r_sq = radius * radius
        for y in range(int(cy - radius - 1), int(cy + radius + 2)):
            for x in range(int(cx - radius - 1), int(cx + radius + 2)):
                dist_sq = (x - cx) ** 2 + (y - cy) ** 2
                if dist_sq <= r_sq:
                    # Antialiasing edge
                    dist = math.sqrt(dist_sq)
                    edge = radius - dist
                    alpha = a if edge >= 1.0 else int(a * max(0.0, edge))
                    self.set_pixel(x, y, r, g, b, alpha)

    def fill_ellipse(self, cx, cy, rx, ry, r, g, b, a=255, angle_deg=0):
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        max_r = max(rx, ry) + 2
        for y in range(int(cy - max_r), int(cy + max_r + 1)):
            for x in range(int(cx - max_r), int(cx + max_r + 1)):
                dx = x - cx
                dy = y - cy
                # Rotate point back
                tx = dx * cos_a + dy * sin_a
                ty = -dx * sin_a + dy * cos_a
                norm_sq = (tx / rx) ** 2 + (ty / ry) ** 2
                if norm_sq <= 1.0:
                    norm = math.sqrt(norm_sq)
                    edge = (1.0 - norm) * min(rx, ry)
                    alpha = a if edge >= 1.0 else int(a * max(0.0, edge))
                    self.set_pixel(x, y, r, g, b, alpha)

    def draw_line(self, x0, y0, x1, y1, r, g, b, a=255, thickness=3):
        # Draw thick line with antialiased circles along path
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        steps = max(1, int(dist * 2))
        for step in range(steps + 1):
            t = step / steps
            cx = x0 + dx * t
            cy = y0 + dy * t
            self.fill_circle(cx, cy, thickness / 2.0, r, g, b, a)

    def draw_curve(self, points, r, g, b, a=255, thickness=3):
        for i in range(len(points) - 1):
            self.draw_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], r, g, b, a, thickness)

    def save(self, filepath):
        create_png(self.w, self.h, self.buffer, filepath)


def generate_dog_ears():
    c = Canvas(600, 360)
    # Left Ear (Floppy dog ear)
    # Outer dark brown ear
    c.fill_ellipse(130, 200, 65, 140, 150, 95, 50, a=255, angle_deg=18)
    c.fill_ellipse(135, 200, 55, 120, 185, 120, 70, a=255, angle_deg=18)
    # Inner pinkish fold
    c.fill_ellipse(140, 230, 32, 75, 230, 150, 150, a=240, angle_deg=15)
    
    # Right Ear (Floppy dog ear)
    c.fill_ellipse(470, 200, 65, 140, 150, 95, 50, a=255, angle_deg=-18)
    c.fill_ellipse(465, 200, 55, 120, 185, 120, 70, a=255, angle_deg=-18)
    c.fill_ellipse(460, 230, 32, 75, 230, 150, 150, a=240, angle_deg=-15)

    c.save("assets/dog_ears.png")


def generate_dog_nose():
    c = Canvas(400, 340)
    # Cute pink dog tongue sticking out
    c.fill_ellipse(200, 220, 48, 75, 245, 115, 140, a=255)
    c.fill_ellipse(200, 230, 42, 60, 255, 140, 165, a=255)
    # Tongue center groove line
    c.draw_line(200, 175, 200, 255, 210, 80, 110, a=220, thickness=4)

    # Black shiny dog nose
    c.fill_ellipse(200, 120, 75, 52, 35, 35, 40, a=255)
    # Nostrils
    c.fill_ellipse(165, 130, 18, 12, 15, 15, 18, a=255, angle_deg=-15)
    c.fill_ellipse(235, 130, 18, 12, 15, 15, 18, a=255, angle_deg=15)
    # Specular white highlights on nose
    c.fill_ellipse(175, 105, 16, 9, 255, 255, 255, a=200, angle_deg=-20)
    c.fill_circle(215, 108, 6, 255, 255, 255, a=160)

    # Mouth line
    c.draw_line(200, 145, 200, 175, 30, 30, 30, a=255, thickness=4)
    # Whiskers / whisker spots
    for dx in [-75, -55, -35]:
        c.fill_circle(200 + dx, 160 + abs(dx)//5, 4, 60, 60, 60, a=200)
    for dx in [35, 55, 75]:
        c.fill_circle(200 + dx, 160 + abs(dx)//5, 4, 60, 60, 60, a=200)

    c.save("assets/dog_nose.png")


def generate_cat_ears():
    c = Canvas(600, 320)
    # Triangular / Pointy Cat Ears
    def draw_triangle(c, p1, p2, p3, r, g, b, a=255):
        # Fill polygon bounding box
        min_x = int(min(p1[0], p2[0], p3[0]))
        max_x = int(max(p1[0], p2[0], p3[0]))
        min_y = int(min(p1[1], p2[1], p3[1]))
        max_y = int(max(p1[1], p2[1], p3[1]))
        
        # Barycentric test
        def sign(p, a, b):
            return (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                d1 = sign((x, y), p1, p2)
                d2 = sign((x, y), p2, p3)
                d3 = sign((x, y), p3, p1)
                has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
                has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
                if not (has_neg and has_pos):
                    c.set_pixel(x, y, r, g, b, a)

    # Left Cat Ear
    # Outer white/cream fluffy base
    draw_triangle(c, (60, 270), (160, 40), (240, 270), 245, 240, 235, 255)
    c.fill_ellipse(150, 160, 60, 110, 245, 240, 235, 255, angle_deg=-15)
    # Inner pink ear
    draw_triangle(c, (95, 255), (160, 85), (215, 255), 255, 165, 185, 245)
    c.fill_ellipse(155, 175, 38, 75, 255, 165, 185, 245, angle_deg=-15)
    # Soft inner shadow
    draw_triangle(c, (115, 250), (160, 120), (195, 250), 245, 130, 155, 180)

    # Right Cat Ear
    draw_triangle(c, (360, 270), (440, 40), (540, 270), 245, 240, 235, 255)
    c.fill_ellipse(450, 160, 60, 110, 245, 240, 235, 255, angle_deg=15)
    # Inner pink ear
    draw_triangle(c, (385, 255), (440, 85), (505, 255), 255, 165, 185, 245)
    c.fill_ellipse(445, 175, 38, 75, 255, 165, 185, 245, angle_deg=15)
    draw_triangle(c, (405, 250), (440, 120), (485, 250), 245, 130, 155, 180)

    # Add fluffy ear tufts at the base
    for x, y, dx in [(100, 260, 15), (130, 265, 20), (470, 265, -20), (500, 260, -15)]:
        c.fill_circle(x, y, 16, 255, 255, 255, 230)

    c.save("assets/cat_ears.png")


def generate_cat_nose():
    c = Canvas(460, 260)
    # Whiskers (Left 3 whiskers)
    c.draw_line(150, 120, 20, 80, 240, 240, 245, a=240, thickness=3)
    c.draw_line(145, 130, 15, 130, 240, 240, 245, a=240, thickness=3)
    c.draw_line(150, 140, 25, 175, 240, 240, 245, a=240, thickness=3)

    # Whiskers (Right 3 whiskers)
    c.draw_line(310, 120, 440, 80, 240, 240, 245, a=240, thickness=3)
    c.draw_line(315, 130, 445, 130, 240, 240, 245, a=240, thickness=3)
    c.draw_line(310, 140, 435, 175, 240, 240, 245, a=240, thickness=3)

    # Muzzle pads (cute cheeks)
    c.fill_ellipse(210, 140, 32, 22, 255, 255, 255, a=220)
    c.fill_ellipse(250, 140, 32, 22, 255, 255, 255, a=220)

    # Small pink triangular cat nose
    def draw_triangle(c, p1, p2, p3, r, g, b, a=255):
        min_x = int(min(p1[0], p2[0], p3[0]))
        max_x = int(max(p1[0], p2[0], p3[0]))
        min_y = int(min(p1[1], p2[1], p3[1]))
        max_y = int(max(p1[1], p2[1], p3[1]))
        def sign(p, a, b):
            return (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                d1 = sign((x, y), p1, p2)
                d2 = sign((x, y), p2, p3)
                d3 = sign((x, y), p3, p1)
                if not (((d1 < 0) or (d2 < 0) or (d3 < 0)) and ((d1 > 0) or (d2 > 0) or (d3 > 0))):
                    c.set_pixel(x, y, r, g, b, a)

    draw_triangle(c, (205, 110), (255, 110), (230, 135), 255, 135, 160, 255)
    c.fill_circle(205, 110, 6, 255, 135, 160, 255)
    c.fill_circle(255, 110, 6, 255, 135, 160, 255)
    c.fill_circle(230, 135, 6, 255, 135, 160, 255)
    # Highlight
    c.fill_circle(225, 114, 3, 255, 220, 230, 220)

    # Cute cat mouth (W shape)
    c.draw_line(230, 136, 230, 146, 120, 70, 90, a=230, thickness=3)
    # Left curl
    for deg in range(0, 150, 10):
        rad = math.radians(deg)
        x = 215 + math.cos(rad) * 15
        y = 146 + math.sin(rad) * 12
        c.fill_circle(x, y, 2, 120, 70, 90, a=230)
    # Right curl
    for deg in range(30, 180, 10):
        rad = math.radians(deg)
        x = 245 - math.cos(rad) * 15
        y = 146 + math.sin(rad) * 12
        c.fill_circle(x, y, 2, 120, 70, 90, a=230)

    c.save("assets/cat_nose.png")


if __name__ == "__main__":
    print("Generating transparent filter assets...")
    generate_dog_ears()
    generate_dog_nose()
    generate_cat_ears()
    generate_cat_nose()
    print("All filter assets generated successfully!")
