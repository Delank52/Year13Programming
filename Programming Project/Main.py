import time
import pygame
import sys
import os
import math
import random
import webbrowser
from pathlib import Path

# Window and font
WINDOW_SIZE = (1280, 832)
FONT_NAME = "arial"
FONT_SIZE_TITLE = 36
FONT_SIZE_BUTTON = 28

pygame.init()
try:
    pygame.mixer.init()
    _mixer_ready = True
except pygame.error as exc:
    print(f"Audio init failed: {exc}")
    _mixer_ready = False
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Air Traffic Controller Simulator")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont(FONT_NAME, FONT_SIZE_TITLE)
font_button = pygame.font.SysFont(FONT_NAME, FONT_SIZE_BUTTON)

# Load background image 
background_menu = pygame.image.load("background.png")
background_menu = pygame.transform.scale(background_menu, WINDOW_SIZE)

background_generic = pygame.image.load("background.png")
background_generic = pygame.transform.scale(background_generic, WINDOW_SIZE)


# --- Simulation Scene ---
def simulation_screen():
    """Displays the blank radar simulation screen with airport at center and UI bars."""
    global current_scene
    # State variables for pause, command input
    paused = False
    command_text = ""
    game_over = False
    last_alert_time = 0
    alert_cooldown = 3.0  # seconds between alert sounds
    # --- Time scale for simulation speed ---
    time_scale = 1.0
    # For text input cursor blink (optional, not required)
    cursor_visible = True
    last_cursor_switch = time.time()
    cursor_interval = 0.5

    # --- Message log state ---
    messages = []  # list of (sender, text, timestamp)
    # Helper: append a message to the log
    def append_message(sender, text):
        messages.append((sender, text, time.time()))

    def resume_game():
        nonlocal paused
        paused = False

    def restart_level():
        nonlocal paused
        paused = False
        simulation_screen()

    zoom = 0.2
    ZOOM_MIN = 0.2
    ZOOM_MAX = 2.0
    ZOOM_STEP = 0.1

    base_radar_radius = (min(WINDOW_SIZE[0], WINDOW_SIZE[1]) / 2 - 60) * 0.75
    # Approximate physical scale: 5000 m runway spans ~300 px on screen
    METERS_PER_PIXEL = 5000 / 300
    PIXELS_PER_METER = 1 / METERS_PER_PIXEL
    PIXELS_PER_SECOND_PER_KNOT = 0.514444 * PIXELS_PER_METER
    PIXELS_PER_NM = 1852 * PIXELS_PER_METER

    aircrafts = []
    selected_aircraft = None
    spawn_timer = 0.0
    difficulty = SETTINGS.get("difficulty", "Normal")
    if difficulty == "Beginner":
        next_spawn_time = random.uniform(28.0, 36.0)
    elif difficulty == "Easy":
        next_spawn_time = random.uniform(14.0, 20.0)
    elif difficulty == "Normal":
        next_spawn_time = random.uniform(9.0, 16.0)
    elif difficulty == "Realistic":
        next_spawn_time = random.uniform(5.0, 10.0)
    else:
        next_spawn_time = random.uniform(9.0, 16.0)
    approach_target = pygame.Vector2(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2 - 20)

    screen_center = pygame.Vector2(WINDOW_SIZE[0] / 2, WINDOW_SIZE[1] / 2)

    def screen_to_world(point):
        vec = pygame.Vector2(point)
        return screen_center + (vec - screen_center) / max(zoom, 0.001)

    max_view_factor = 1.0 / ZOOM_MIN
    world_margin = 200
    world_left_limit = screen_center.x - screen_center.x * max_view_factor
    world_right_limit = screen_center.x + (WINDOW_SIZE[0] - screen_center.x) * max_view_factor
    world_top_limit = screen_center.y - screen_center.y * max_view_factor
    world_bottom_limit = screen_center.y + (WINDOW_SIZE[1] - screen_center.y) * max_view_factor
    world_bounds = pygame.Rect(
        world_left_limit - world_margin,
        world_top_limit - world_margin,
        (world_right_limit - world_left_limit) + 2 * world_margin,
        (world_bottom_limit - world_top_limit) + 2 * world_margin,
    )

    aircraft_label_font = pygame.font.SysFont(FONT_NAME, 18)
    airline_codes = ["BA", "QR", "LH", "EK", "AF", "DL", "VS", "QF", "KL", "TK"]
    aircraft_types = ["A320-251NX", "B777-300ER", "A380-800", "B787-8", "A350-900", "A321-200", "A330-800", "A220-200"]

    class Aircraft:
        def __init__(self, position, target, callsign, aircraft_type, speed_knots, altitude_ft):
            self.pos = pygame.Vector2(position)
            self.target = pygame.Vector2(target)
            self.callsign = callsign
            self.aircraft_type = aircraft_type
            self.speed_knots = float(speed_knots)
            self.altitude_ft = float(altitude_ft)
            self.selected = False
            self.speed_px = self.speed_knots * PIXELS_PER_SECOND_PER_KNOT
            direction_vec = (self.target - self.pos)
            if direction_vec.length_squared() == 0:
                direction_vec = pygame.Vector2(0, 1)
            else:
                direction_vec = direction_vec.normalize()
            self.direction = direction_vec
            self.heading_deg = (math.degrees(math.atan2(self.direction.x, -self.direction.y)) + 360) % 360

            self.target_heading = self.heading_deg
            self.target_speed = self.speed_knots
            self.target_altitude = self.altitude_ft
            self.turn_rate_deg = 2.5  # deg per second
            self.accel_knots_per_s = 3.0
            self.climb_rate_fps = 1500 / 60.0  # feet per second (~1500 fpm)

            base_radius = max(AIRCRAFT_IMAGE.get_width(), AIRCRAFT_IMAGE.get_height()) / 2 + 8 if AIRCRAFT_IMAGE else 20
            self.base_pick_radius = base_radius
            self.distance_to_target = (self.target - self.pos).length()
            self.range_nm = self.distance_to_target / PIXELS_PER_NM
            self.conflict = False

        def update(self, dt, target):
            # Adjust heading gradually
            heading_diff = (self.target_heading - self.heading_deg + 540) % 360 - 180
            max_turn = self.turn_rate_deg * dt
            if abs(heading_diff) > max_turn:
                self.heading_deg = (self.heading_deg + max_turn * (1 if heading_diff > 0 else -1)) % 360
            else:
                self.heading_deg = self.target_heading % 360

            rad = math.radians(self.heading_deg)
            self.direction = pygame.Vector2(math.sin(rad), -math.cos(rad))

            # Adjust speed gradually
            speed_diff = self.target_speed - self.speed_knots
            max_speed_change = self.accel_knots_per_s * dt
            if abs(speed_diff) > max_speed_change:
                self.speed_knots += max_speed_change * (1 if speed_diff > 0 else -1)
            else:
                self.speed_knots = self.target_speed
            self.speed_px = self.speed_knots * PIXELS_PER_SECOND_PER_KNOT

            # Adjust altitude gradually
            alt_diff = self.target_altitude - self.altitude_ft
            max_alt_change = self.climb_rate_fps * dt
            if abs(alt_diff) > max_alt_change:
                self.altitude_ft += max_alt_change * (1 if alt_diff > 0 else -1)
            else:
                self.altitude_ft = self.target_altitude

            self.pos += self.direction * self.speed_px * dt
            to_target = target - self.pos
            self.distance_to_target = to_target.length()
            self.range_nm = self.distance_to_target / PIXELS_PER_NM
            return None

        def apply_command(self, heading=None, speed=None, altitude=None):
            if heading is not None:
                self.target_heading = heading % 360
            if speed is not None:
                self.target_speed = float(speed)
            if altitude is not None:
                self.target_altitude = float(altitude)

        def draw(self, surface, zoom_level, transform_point):
            screen_vec = transform_point(self.pos)
            pos = (int(screen_vec.x), int(screen_vec.y))
            halo_radius = max(10, int(self.base_pick_radius * zoom_level * 1.1))
            if self.conflict:
                halo_color = (255, 60, 60)
            elif self.selected:
                halo_color = (255, 210, 40)
            else:
                halo_color = (60, 160, 245)
            halo_alpha = 110 if not self.selected else 180
            halo = pygame.Surface((halo_radius * 2, halo_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*halo_color, halo_alpha), (halo_radius, halo_radius), halo_radius)
            surface.blit(halo, (pos[0] - halo_radius, pos[1] - halo_radius))

            image_scale = max(0.3, min(1.5, zoom_level * 0.85))
            if AIRCRAFT_IMAGE:
                aircraft_sprite = pygame.transform.rotozoom(AIRCRAFT_IMAGE, self.heading_deg - 90, image_scale)
                sprite_rect = aircraft_sprite.get_rect(center=pos)
                surface.blit(aircraft_sprite, sprite_rect)
            else:
                marker_radius = max(6, int(12 * zoom_level))
                color = (255, 215, 0) if self.selected else (200, 220, 255)
                pygame.draw.circle(surface, color, pos, marker_radius)
                pygame.draw.circle(surface, (255, 255, 255), pos, marker_radius, 2)

            label = aircraft_label_font.render(self.callsign, True, (255, 255, 255))
            label_rect = label.get_rect(midtop=(pos[0], pos[1] + int(14 * zoom_level)))
            surface.blit(label, label_rect)

        def contains_point(self, point, zoom_level, transform_point):
            screen_vec = transform_point(self.pos)
            radius = self.base_pick_radius * zoom_level
            dx = point[0] - screen_vec.x
            dy = point[1] - screen_vec.y
            return dx * dx + dy * dy <= radius * radius

        def info_lines(self):
            return [
                f"Callsign: {self.callsign}",
                f"Type: {self.aircraft_type}",
                f"Speed: {int(self.speed_knots)} kts",
                f"Altitude: {int(self.altitude_ft)} ft",
                f"Heading: {int(self.heading_deg)}° | Range: {self.range_nm:.1f} NM",
            ]

    def generate_callsign():
        return f"{random.choice(airline_codes)}{random.randint(100, 999)}"

    def spawn_aircraft():
        nonlocal spawn_timer, next_spawn_time
        if game_over:
            return
        edge_name = random.choice(["left", "right", "top", "bottom"])
        if edge_name == "left":
            spawn_pos = screen_to_world((0.0, random.uniform(0.0, WINDOW_SIZE[1])))
        elif edge_name == "right":
            spawn_pos = screen_to_world((float(WINDOW_SIZE[0]), random.uniform(0.0, WINDOW_SIZE[1])))
        elif edge_name == "top":
            spawn_pos = screen_to_world((random.uniform(0.0, WINDOW_SIZE[0]), 0.0))
        else:
            spawn_pos = screen_to_world((random.uniform(0.0, WINDOW_SIZE[0]), float(WINDOW_SIZE[1])))
        callsign = generate_callsign()
        ac_type = random.choice(aircraft_types)
        speed = random.randint(160, 230)
        altitude = random.randint(4200, 9500)
        aircraft = Aircraft(spawn_pos, approach_target, callsign, ac_type, speed, altitude)
        aircrafts.append(aircraft)
        range_nm = ((pygame.Vector2(spawn_pos) - approach_target).length()) / PIXELS_PER_NM
        append_message(
            callsign,
            f"{callsign} {ac_type} inbound {edge_name}, {speed} kts, {altitude} ft, {range_nm:.1f} NM",
        )
        spawn_timer = 0.0
        difficulty = SETTINGS.get("difficulty", "Normal")
        if difficulty == "Beginner":
            next_spawn_time = random.uniform(28.0, 36.0)
        elif difficulty == "Easy":
            next_spawn_time = random.uniform(14.0, 20.0)
        elif difficulty == "Normal":
            next_spawn_time = random.uniform(9.0, 16.0)
        elif difficulty == "Realistic":
            next_spawn_time = random.uniform(5.0, 10.0)
        else:
            next_spawn_time = random.uniform(9.0, 16.0)

    def find_aircraft(callsign: str):
        callsign_upper = callsign.upper()
        for ac in aircrafts:
            if ac.callsign.upper() == callsign_upper:
                return ac
        return None

    # --- Runway entry points and headings ---
    runway_entry_points = {}
    runway_headings = {}

    # Helper: check landing clearance
    def check_landing_clearance(ac, entry_point, runway_heading):
        if (ac.pos - entry_point).length() > 10:
            return False, "Not at entry point"
        diff = (ac.heading_deg - runway_heading + 540) % 360 - 180
        if abs(diff) > 20:
            return False, "Not aligned with runway"
        if not (2000 <= ac.altitude_ft <= 3000):
            return False, "Not at landing altitude (FL20–30)"
        return True, "Clear to land"

    def process_command(command: str):
        tokens = command.strip().split()
        if len(tokens) < 4:
            append_message("Tower", "Message not transmitted, please try again.")
            return

        callsign = tokens[0]
        aircraft = find_aircraft(callsign)
        if not aircraft:
            append_message("Tower", f"Unknown aircraft {callsign}.")
            return


        # -- Landing clearance handling --
        if len(tokens) >= 5 and tokens[1].upper() == "CLEARED" and tokens[2].upper() == "TO" and tokens[3].upper() == "LAND":
            rw_label = tokens[4].upper().replace("RWY", "")
            if rw_label not in runway_entry_points:
                append_message("Tower", f"Runway {rw_label} not available")
                return
            entry_point = runway_entry_points[rw_label]
            runway_heading = runway_headings.get(rw_label)
            if not runway_heading:
                append_message("Tower", f"No heading info for {rw_label}")
                return
            ok, reason = check_landing_clearance(aircraft, entry_point, runway_heading)
            if ok:
                append_message(aircraft.callsign, f"{aircraft.callsign} landing clearance acknowledged runway {rw_label}")
                if aircraft in aircrafts:
                    aircrafts.remove(aircraft)
                    append_message(aircraft.callsign, f"{aircraft.callsign} landed successfully.")
            else:
                append_message("Tower", f"Landing clearance denied: {reason}")
            return

        heading = speed = altitude = None
        errors = []
        for tok in tokens[1:]:
            t = tok.upper()
            if t.startswith("HDG") and len(t) > 3:
                try:
                    heading_val = int(t[3:]) % 360
                    heading = heading_val
                except ValueError:
                    errors.append("Invalid heading")
            elif t.startswith("SPD") and len(t) > 3:
                try:
                    speed_val = max(40, min(400, int(t[3:])))
                    speed = speed_val
                except ValueError:
                    errors.append("Invalid speed")
            elif t.startswith("FL") and len(t) > 2:
                try:
                    altitude_val = int(t[2:]) * 100
                    altitude = altitude_val
                except ValueError:
                    errors.append("Invalid altitude")
            else:
                errors.append(f"Unknown token {tok}")

        if heading is None or speed is None or altitude is None:
            if not errors:
                errors.append("Missing HDG, SPD, or FL")

        if errors:
            append_message("Tower", "; ".join(errors))
            return

        aircraft.apply_command(heading=heading, speed=speed, altitude=altitude)
        append_message(
            aircraft.callsign,
            f"Turning HDG {heading:03d}, speed {speed} kts, altitude {altitude} ft",
        )

    # Font for chat log/messages
    chat_font = pygame.font.SysFont(FONT_NAME, 22)
    nonlocal_last_alert_time = [0]  # wrap in list to allow mutation
    while current_scene == "start":
        dt = (clock.get_time() / 1000.0) * time_scale
        # Fill background (dark blue)
        screen.fill((0, 44, 66))

        # Radar circles (concentric)
        center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        approach_target.update((screen_center.x, screen_center.y - 20))
        max_radius = max(40, int(base_radar_radius * zoom))
        circle_color = (40, 60, 80)
        circle_alpha = 150
        num_circles = 5
        center_vec = pygame.Vector2(center)

        def transform_point(world_point):
            vec = pygame.Vector2(world_point)
            return screen_center + (vec - screen_center) * zoom

        # Draw with alpha
        radar_surface = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        for i in range(1, num_circles + 1):
            radius = max_radius * i // num_circles
            pygame.draw.circle(radar_surface, (*circle_color, circle_alpha), center, radius, 2)
        # Draw crosshairs
        pygame.draw.line(radar_surface, (*circle_color, circle_alpha), (center[0], 60), (center[0], WINDOW_SIZE[1]-60), 1)
        pygame.draw.line(radar_surface, (*circle_color, circle_alpha), (60, center[1]), (WINDOW_SIZE[0]-60, center[1]), 1)
        screen.blit(radar_surface, (0, 0))

        # --- Draw runways ---
        def draw_runway(surface, center_point, length, width, heading_deg, label1, label2, color=(180, 180, 180)):
            """Draws a runway aligned with a true heading: 0° points north (up)."""
            rotation = 90 - heading_deg

            base_surface = pygame.Surface((length, width), pygame.SRCALPHA)
            pygame.draw.rect(base_surface, color, (0, 0, length, width))
            pygame.draw.rect(base_surface, (255, 255, 255), (0, 0, length, width), 2)
            runway_sprite = pygame.transform.rotozoom(base_surface, rotation, zoom)
            center_screen = transform_point(center_point)
            rect = runway_sprite.get_rect(center=(int(center_screen.x), int(center_screen.y)))
            surface.blit(runway_sprite, rect.topleft)

            import math

            rad = math.radians(heading_deg)
            dx_world = math.sin(rad)
            dy_world = math.cos(rad)
            dx = dx_world
            dy = -dy_world
            half_len = length // 2

            # Threshold positions
            end1 = (center_point[0] + dx * half_len, center_point[1] + dy * half_len)
            end2 = (center_point[0] - dx * half_len, center_point[1] - dy * half_len)

            offset = 40
            pos1 = (end1[0] + dx * offset, end1[1] + dy * offset)
            pos2 = (end2[0] - dx * offset, end2[1] - dy * offset)

            label_font = pygame.font.SysFont(FONT_NAME, 22, bold=True)

            def draw_label(text, pos, heading):
                text_surf = label_font.render(text, True, (255, 255, 255))
                text_rot = pygame.transform.rotozoom(text_surf, rotation, zoom)
                pos_screen = transform_point(pos)
                text_rect = text_rot.get_rect(center=(int(pos_screen.x), int(pos_screen.y)))
                surface.blit(text_rot, text_rect)

            draw_label(label1, pos1, heading_deg)
            draw_label(label2, pos2, heading_deg)

        def offset_perpendicular(base_center, heading_deg, distance):
            import math

            rad = math.radians(heading_deg)
            dx_world = math.sin(rad)
            dy_world = math.cos(rad)
            # perpendicular vector (positive to the left of heading) in world coordinates
            px_world = -dy_world
            py_world = dx_world
            px = px_world
            py = -py_world
            return (base_center[0] + px * distance, base_center[1] + py * distance)

        # Draw runways depending on airport
        airport = SETTINGS.get("Airport", "Heathrow")
        # --- Helper for drawing entry points (red dots) ---
        def draw_entry_points(center_point, length, heading_deg):
            import math
            # 5km in meters
            entry_dist_m = 5000
            entry_dist_px = entry_dist_m * PIXELS_PER_METER
            # Get heading vector (runway direction)
            rad = math.radians(heading_deg)
            dx = math.sin(rad)
            dy = -math.cos(rad)
            half_len = length // 2
            # World positions of runway thresholds
            end1 = (center_point[0] + dx * half_len, center_point[1] + dy * half_len)
            end2 = (center_point[0] - dx * half_len, center_point[1] - dy * half_len)
            # Entry points: 5 km further away from each threshold along the runway heading
            entry1 = (end1[0] + dx * entry_dist_px, end1[1] + dy * entry_dist_px)
            entry2 = (end2[0] - dx * entry_dist_px, end2[1] - dy * entry_dist_px)
            # Convert to screen
            pos1 = transform_point(entry1)
            pos2 = transform_point(entry2)
            pygame.draw.circle(screen, (255,0,0), (int(pos1.x), int(pos1.y)), 5)
            pygame.draw.circle(screen, (255,0,0), (int(pos2.x), int(pos2.y)), 5)
        def get_entry_points(center_point, length, heading_deg):
            import math
            entry_dist_m = 5000
            entry_dist_px = entry_dist_m * PIXELS_PER_METER
            rad = math.radians(heading_deg)
            dx = math.sin(rad)
            dy = -math.cos(rad)
            half_len = length // 2
            end1 = (center_point[0] + dx * half_len, center_point[1] + dy * half_len)
            end2 = (center_point[0] - dx * half_len, center_point[1] - dy * half_len)
            entry1 = (end1[0] + dx * entry_dist_px, end1[1] + dy * entry_dist_px)
            entry2 = (end2[0] - dx * entry_dist_px, end2[1] - dy * entry_dist_px)
            return [pygame.Vector2(entry1), pygame.Vector2(entry2)]

        # London Heathrow: two parallel east-west runways (09L/27R and 09R/27L)
        if airport.lower() in ["heathrow", "london heathrow"]:
            heading = 90
            r_length = 300
            r_width = 14
            spacing = 48
            upper_center = offset_perpendicular(center, heading, spacing)
            lower_center = offset_perpendicular(center, heading, -spacing)
            draw_runway(screen, upper_center, r_length, r_width, heading, "09L", "27R")
            draw_entry_points(upper_center, r_length, heading)
            points = get_entry_points(upper_center, r_length, heading)
            # Assign entry points and headings
            runway_entry_points["09L"] = points[0]
            runway_headings["09L"] = 90
            runway_entry_points["27R"] = points[1]
            runway_headings["27R"] = 270

            draw_runway(screen, lower_center, r_length, r_width, heading, "09R", "27L")
            draw_entry_points(lower_center, r_length, heading)
            points2 = get_entry_points(lower_center, r_length, heading)
            runway_entry_points["09R"] = points2[0]
            runway_headings["09R"] = 90
            runway_entry_points["27L"] = points2[1]
            runway_headings["27L"] = 270
        # Glasgow: two NE-SW runways (05/23), slightly separated
        elif airport.lower() == "glasgow":
            heading = 50
            r_length = 250
            r_width = 12
            draw_runway(screen, center, r_length, r_width, heading, "05", "23")
            draw_entry_points(center, r_length, heading)
            points = get_entry_points(center, r_length, heading)
            runway_entry_points["05"] = points[0]
            runway_headings["05"] = 50
            runway_entry_points["23"] = points[1]
            runway_headings["23"] = 230
        # Los Angeles: two parallel west-east runways (25L/07R and 25R/07L)
        elif airport.lower() in ["los angeles", "lax"]:
            heading = 250
            r_length = 320
            r_width = 16
            spacing = 56
            upper_center = offset_perpendicular(center, heading, spacing)
            lower_center = offset_perpendicular(center, heading, -spacing)
            draw_runway(screen, upper_center, r_length, r_width, heading, "25L", "07R")
            draw_entry_points(upper_center, r_length, heading)
            points = get_entry_points(upper_center, r_length, heading)
            runway_entry_points["25L"] = points[0]
            runway_headings["25L"] = 250
            runway_entry_points["07R"] = points[1]
            runway_headings["07R"] = 70

            draw_runway(screen, lower_center, r_length, r_width, heading, "25R", "07L")
            draw_entry_points(lower_center, r_length, heading)
            points2 = get_entry_points(lower_center, r_length, heading)
            runway_entry_points["25R"] = points2[0]
            runway_headings["25R"] = 250
            runway_entry_points["07L"] = points2[1]
            runway_headings["07L"] = 70

        # --- Dynamic Scale Bar (right side of screen) ---
        possible_scales = [1, 2, 4, 5, 10]  # candidate scales in NM
        scale_nm = 1
        for candidate in possible_scales:
            scale_px = int(candidate * PIXELS_PER_NM * zoom)
            if 60 < scale_px < 160:
                if candidate > 1:
                    scale_nm = candidate
                break
        scale_px = int(scale_nm * PIXELS_PER_NM * zoom)

        bar_x = WINDOW_SIZE[0] - 120   # further left from right edge
        bar_y_bottom = WINDOW_SIZE[1] - 100
        bar_y_top = bar_y_bottom - scale_px

        # Draw vertical line
        pygame.draw.line(screen, (255, 255, 255), (bar_x, bar_y_bottom), (bar_x, bar_y_top), 4)
        # End caps
        pygame.draw.line(screen, (255, 255, 255), (bar_x - 12, bar_y_bottom), (bar_x + 12, bar_y_bottom), 3)
        pygame.draw.line(screen, (255, 255, 255), (bar_x - 12, bar_y_top), (bar_x + 12, bar_y_top), 3)

        # Label in NM
        label = font_button.render(f"{scale_nm} NM", True, (255, 255, 255))
        label_rect = label.get_rect(midleft=(bar_x + 20, (bar_y_bottom + bar_y_top)//2))
        screen.blit(label, label_rect)

        removal_queue = []
        if not paused and not game_over:
            spawn_timer += dt
            if spawn_timer >= next_spawn_time and len(aircrafts) < 10:
                spawn_aircraft()
            for ac in list(aircrafts):
                outcome = ac.update(dt, approach_target)
                if outcome:
                    removal_queue.append((ac, outcome))

        if removal_queue:
            for ac, outcome in removal_queue:
                if ac in aircrafts:
                    aircrafts.remove(ac)
                if ac.selected:
                    ac.selected = False
                if selected_aircraft is ac:
                    selected_aircraft = None
                if outcome == "landed":
                    append_message(ac.callsign, f"{ac.callsign} landed successfully.")
        for ac in list(aircrafts):
            if not world_bounds.collidepoint(ac.pos.x, ac.pos.y):
                aircrafts.remove(ac)
                if ac.selected:
                    ac.selected = False
                if selected_aircraft is ac:
                    selected_aircraft = None
                append_message(ac.callsign, f"{ac.callsign} left airspace.")
                continue
            ac.draw(screen, zoom, transform_point)

        # --- Conflict detection ---
        # Reset conflicts
        for ac in aircrafts:
            ac.conflict = False
        any_conflict = False
        for i in range(len(aircrafts)):
            for j in range(i + 1, len(aircrafts)):
                ac1, ac2 = aircrafts[i], aircrafts[j]
                horiz_nm = (ac1.pos - ac2.pos).length() / PIXELS_PER_NM
                alt_diff = abs(ac1.altitude_ft - ac2.altitude_ft)
                if horiz_nm < 2.5 and alt_diff < 1000:
                    ac1.conflict = True
                    ac2.conflict = True
                    any_conflict = True

        # --- Halo overlap/game over detection ---
        if not game_over:
            for i in range(len(aircrafts)):
                for j in range(i + 1, len(aircrafts)):
                    ac1, ac2 = aircrafts[i], aircrafts[j]
                    # Convert to screen space
                    p1 = transform_point(ac1.pos)
                    p2 = transform_point(ac2.pos)
                    dist = (p1 - p2).length()
                    r1 = max(10, int(ac1.base_pick_radius * zoom * 1.1))
                    r2 = max(10, int(ac2.base_pick_radius * zoom * 1.1))
                    alt_diff = abs(ac1.altitude_ft - ac2.altitude_ft)
                    if dist < (r1 + r2) and alt_diff < 1000:
                        game_over = True
                        break
                if game_over:
                    break

        # --- Top Bar ---
        top_bar_height = 64
        pygame.draw.rect(screen, (0, 32, 48), (0, 0, WINDOW_SIZE[0], top_bar_height))
        pygame.draw.line(screen, (20, 80, 100), (0, top_bar_height), (WINDOW_SIZE[0], top_bar_height), 2)
        # Draw conflict alert after top bar is drawn
        if any_conflict:
            conflict_text = font_title.render("CONFLICT ALERT", True, (255, 60, 60))
            screen.blit(conflict_text, conflict_text.get_rect(center=(WINDOW_SIZE[0]//2, top_bar_height//2)))
            # Secondary info line on the bar too, slightly lower
            conflict_text2 = font_button.render("WARNING: Aircraft at risk of collision", True, (255, 180, 180))
            screen.blit(conflict_text2, conflict_text2.get_rect(center=(WINDOW_SIZE[0]//2, top_bar_height//2 + 26)))
            if CONFLICT_SOUND:
                CONFLICT_SOUND.play()
            if ALERT_SOUND:
                now_time = time.time()
                if now_time - last_alert_time >= alert_cooldown:
                    ALERT_SOUND.play()
                    last_alert_time = now_time

        # Top bar buttons (simple icons)
        icon_y = top_bar_height // 2
        icon_xs = [40, 110, 180]
        # Icon/text color (light yellow)
        icon_color = (255, 230, 0)
        # --- Fast-forward icon (double triangles) at icon_xs[0] ---
        ff_center = (icon_xs[0], icon_y)
        ff_size = 16
        # Left triangle
        pygame.draw.polygon(
            screen,
            icon_color,
            [
                (ff_center[0] - ff_size//2, ff_center[1] - ff_size//2),
                (ff_center[0], ff_center[1]),
                (ff_center[0] - ff_size//2, ff_center[1] + ff_size//2),
            ]
        )
        # Right triangle
        pygame.draw.polygon(
            screen,
            icon_color,
            [
                (ff_center[0], ff_center[1] - ff_size//2),
                (ff_center[0] + ff_size//2, ff_center[1]),
                (ff_center[0], ff_center[1] + ff_size//2),
            ]
        )
        # Draw speed text (e.g., "0.5x", "1x", "2x", "4x", "8x") near icon
        speed_str = f"{time_scale}x" if time_scale != int(time_scale) else f"{int(time_scale)}x"
        speed_font = pygame.font.SysFont(FONT_NAME, 16, bold=True)
        speed_surf = speed_font.render(speed_str, True, icon_color)
        speed_rect = speed_surf.get_rect(midleft=(icon_xs[0] + 22, icon_y))
        screen.blit(speed_surf, speed_rect)

        # Pause icon (2 bars)
        pygame.draw.rect(screen, icon_color, (icon_xs[1]-8, icon_y-14, 6, 28))
        pygame.draw.rect(screen, icon_color, (icon_xs[1]+8, icon_y-14, 6, 28))
        # Help icon (circle with ?)
        pygame.draw.circle(screen, icon_color, (icon_xs[2], icon_y), 16, 2)
        qfont = pygame.font.SysFont(FONT_NAME, 24)
        draw_text("?", qfont, icon_color, screen, icon_xs[2], icon_y)

        # Airport label in top-right
        label_text = SETTINGS.get("Airport", "Heathrow")
        label_surf = font_title.render(label_text, True, icon_color)
        label_rect = label_surf.get_rect(topright=(WINDOW_SIZE[0] - 32, 12))
        screen.blit(label_surf, label_rect)

        info_panel = pygame.Rect(WINDOW_SIZE[0] - 260, top_bar_height + 72, 228, 300)
        info_surface = pygame.Surface((info_panel.width, info_panel.height), pygame.SRCALPHA)
        info_surface.fill((0, 0, 0, 150))
        screen.blit(info_surface, info_panel.topleft)

        traffic_title = font_button.render("Traffic", True, icon_color)
        screen.blit(traffic_title, (info_panel.left + 12, info_panel.top + 12))

        list_y = info_panel.top + 56
        for ac in sorted(aircrafts, key=lambda a: a.distance_to_target)[:4]:
            text = f"{ac.callsign:<6} {ac.range_nm:>4.1f} NM"
            traffic_line = aircraft_label_font.render(text, True, (255, 255, 255))
            screen.blit(traffic_line, (info_panel.left + 12, list_y))
            list_y += 26

        detail_y = info_panel.top + 150
        if selected_aircraft:
            detail_title = aircraft_label_font.render("Selected", True, icon_color)
            screen.blit(detail_title, (info_panel.left + 12, detail_y))
            detail_y += 24
            for line in selected_aircraft.info_lines():
                info_line = aircraft_label_font.render(line, True, (255, 255, 255))
                screen.blit(info_line, (info_panel.left + 12, detail_y))
                detail_y += 24
        else:
            hint = aircraft_label_font.render("Click aircraft", True, (200, 200, 200))
            screen.blit(hint, (info_panel.left + 12, detail_y))

        # --- Chat/message log (top-left) ---
        now = time.time()
        chat_x = 24
        chat_y = top_bar_height + 12
        line_spacing = 8
        msg_y = chat_y
        # Only show recent messages (not faded out)
        for sender, text, timestamp in messages:
            dt = now - timestamp
            fade = min(dt / 8, 1.0)
            alpha = max(0, 255 - int(fade * 255))
            if alpha == 0:
                continue
            # Render sender label (yellow), then message text (white) next to it, both with alpha
            sender_label = f"{sender}:"
            sender_surf = chat_font.render(sender_label, True, (255, 230, 0))
            sender_surf.set_alpha(alpha)
            text_surf = chat_font.render(text, True, (255, 255, 255))
            text_surf.set_alpha(alpha)
            sender_rect = sender_surf.get_rect(topleft=(chat_x, msg_y))
            text_rect = text_surf.get_rect(topleft=(sender_rect.right + 8, msg_y))
            screen.blit(sender_surf, sender_rect)
            screen.blit(text_surf, text_rect)
            msg_y += max(sender_rect.height, text_rect.height) + line_spacing

        # --- Bottom Bar ---
        bottom_bar_height = 48
        pygame.draw.rect(screen, (0, 32, 48), (0, WINDOW_SIZE[1]-bottom_bar_height, WINDOW_SIZE[0], bottom_bar_height))
        pygame.draw.line(screen, (20, 80, 100), (0, WINDOW_SIZE[1]-bottom_bar_height), (WINDOW_SIZE[0], WINDOW_SIZE[1]-bottom_bar_height), 2)
        # Draw "Command Bar" label at left
        draw_text("Command Bar", font_button, (255, 230, 0), screen, 120, WINDOW_SIZE[1]-bottom_bar_height//2)
        # Draw input box (simple rectangle and text)
        input_box_x = 220
        input_box_y = WINDOW_SIZE[1] - bottom_bar_height + 8
        input_box_w = WINDOW_SIZE[0] - input_box_x - 32
        input_box_h = bottom_bar_height - 16
        input_rect = pygame.Rect(input_box_x, input_box_y, input_box_w, input_box_h)
        pygame.draw.rect(screen, (24, 48, 64), input_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 230, 0), input_rect, 2, border_radius=8)
        # Render the command text inside the input box
        txt_surf = font_button.render(command_text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(midleft=(input_rect.left + 12, input_rect.centery))
        screen.blit(txt_surf, txt_rect)
        # Draw blinking cursor if focused (always focused in this context)
        if now - last_cursor_switch > cursor_interval:
            cursor_visible = not cursor_visible
            last_cursor_switch = now
        if cursor_visible:
            cursor_x = txt_rect.right + 4
            cursor_y1 = txt_rect.top + 4
            cursor_y2 = txt_rect.bottom - 4
            pygame.draw.line(screen, (255, 255, 255), (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

        # Draw PAUSED overlay with pause menu if paused
        if paused:
            s = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            s.fill((0, 0, 0, 120))
            screen.blit(s, (0, 0))
            # Draw "PAUSED" text
            paused_center_x = WINDOW_SIZE[0] // 2
            paused_center_y = WINDOW_SIZE[1] // 2 - 90
            draw_text("PAUSED", font_title, (255, 230, 0), screen, paused_center_x, paused_center_y)

            # Define pause menu buttons, centered and vertically spaced below "PAUSED"
            button_spacing = 70
            btn_centers = [
                (paused_center_x, paused_center_y + 60),
                (paused_center_x, paused_center_y + 60 + button_spacing),
                (paused_center_x, paused_center_y + 60 + 2 * button_spacing),
                (paused_center_x, paused_center_y + 60 + 3 * button_spacing),
            ]
            pause_menu_buttons = [
                Button("Resume", btn_centers[0], resume_game),
                Button("Settings", btn_centers[1], lambda: change_scene("settings")),
                Button("Restart Level", btn_centers[2], restart_level),
                Button("Main Menu", btn_centers[3], lambda: change_scene("menu")),
            ]
            # Draw the buttons
            for b in pause_menu_buttons:
                b.draw(screen)

        # Draw GAME OVER overlay if game_over
        if game_over:
            s = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            s.fill((0, 0, 0, 160))
            screen.blit(s, (0, 0))
            draw_text("FAILED. An aircraft(s) has crashed.", font_title, (255, 60, 60), screen, WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2 - 60)

            # Draw Main Menu button centered below the message
            gameover_menu_btn = Button("Main Menu", (WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2 + 40), lambda: change_scene("menu"), width=240, height=60)
            gameover_menu_btn.draw(screen)

        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_scene("menu")
                    continue

                if event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS):
                    zoom = max(ZOOM_MIN, round(zoom - ZOOM_STEP, 2))
                    continue
                if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    zoom = min(ZOOM_MAX, round(zoom + ZOOM_STEP, 2))
                    continue

                # Only handle input if not paused or game_over
                if not paused and not game_over:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        cmd = command_text.strip()
                        if cmd:
                            append_message("You", cmd)
                            process_command(cmd)
                        command_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        command_text = command_text[:-1]
                    elif event.key == pygame.K_TAB:
                        pass  # ignore tab
                    elif event.unicode and len(event.unicode) == 1 and event.unicode.isprintable():
                        if len(command_text) < 100:
                            command_text += event.unicode
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    zoom = min(ZOOM_MAX, round(zoom + ZOOM_STEP * event.y, 2))
                elif event.y < 0:
                    zoom = max(ZOOM_MIN, round(zoom + ZOOM_STEP * event.y, 2))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if paused:
                    # Define pause menu buttons in the same way as above to check clicks
                    paused_center_x = WINDOW_SIZE[0] // 2
                    paused_center_y = WINDOW_SIZE[1] // 2 - 90
                    button_spacing = 70
                    btn_centers = [
                        (paused_center_x, paused_center_y + 60),
                        (paused_center_x, paused_center_y + 60 + button_spacing),
                        (paused_center_x, paused_center_y + 60 + 2 * button_spacing),
                        (paused_center_x, paused_center_y + 60 + 3 * button_spacing),
                    ]
                    pause_menu_buttons = [
                        Button("Resume", btn_centers[0], resume_game),
                        Button("Settings", btn_centers[1], lambda: change_scene("settings")),
                        Button("Restart Level", btn_centers[2], restart_level),
                        Button("Main Menu", btn_centers[3], lambda: change_scene("menu")),
                    ]
                    for b in pause_menu_buttons:
                        if b.is_clicked((mx, my)):
                            b.activate()
                            break
                elif game_over:
                    # Define the game over menu button in the same way as drawn above
                    gameover_menu_btn = Button("Main Menu", (WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2 + 40), lambda: change_scene("menu"), width=240, height=60)
                    if gameover_menu_btn.is_clicked((mx, my)):
                        gameover_menu_btn.activate()
                else:
                    clicked_ac = None
                    for ac in reversed(aircrafts):
                        if ac.contains_point((mx, my), zoom, transform_point):
                            clicked_ac = ac
                            break
                    if clicked_ac:
                        if selected_aircraft is clicked_ac:
                            clicked_ac.selected = False
                            selected_aircraft = None
                        else:
                            if selected_aircraft:
                                selected_aircraft.selected = False
                            clicked_ac.selected = True
                            selected_aircraft = clicked_ac
                            append_message(clicked_ac.callsign, f"{clicked_ac.callsign} selected.")
                        continue
                    # Fast-forward icon click (detect click on icon_xs[0])
                    ff_dist = math.hypot(mx - icon_xs[0], my - icon_y)
                    if ff_dist <= 24:
                        # Cycle time_scale between 0.5x, 1x, 2x, 4x, 8x
                        if time_scale == 0.5:
                            time_scale = 1.0
                        elif time_scale == 1.0:
                            time_scale = 2.0
                        elif time_scale == 2.0:
                            time_scale = 4.0
                        elif time_scale == 4.0:
                            time_scale = 8.0
                        else:
                            time_scale = 0.5
                        continue
                    # Pause icon click
                    pause_dist = math.hypot(mx - icon_xs[1], my - icon_y)
                    if pause_dist <= 24:
                        paused = not paused
                    # Help icon click
                    help_dist = math.hypot(mx - icon_xs[2], my - icon_y)
                    if help_dist <= 24:
                        change_scene("tutorial")

        pygame.display.flip()
        clock.tick(60)



def _load_button_sound():
    if not _mixer_ready:
        return None
    candidates = [
        "Soundeffect.wav",
        "Soundeffect.ogg",
        "Soundeffect.mp3",
        "Soundeffect",
    ]
    for name in candidates:
        path = Path(name)
        if path.exists():
            try:
                return pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                print(f"Failed to load button sound '{name}': {exc}")
    return None

def _load_conflict_sound():
    if not _mixer_ready:
        return None
    candidates = [
        "conflict.wav",
        "conflict.ogg",
        "conflict.mp3",
        "conflict",
    ]
    for name in candidates:
        path = Path(name)
        if path.exists():
            try:
                return pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                print(f"Failed to load conflict sound '{name}': {exc}")
    return None

def _load_alert_sound():
    if not _mixer_ready:
        return None
    candidates = [
        "alert.wav",
        "alert.ogg",
        "alert.mp3",
        "alert",
    ]
    for name in candidates:
        path = Path(name)
        if path.exists():
            try:
                return pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                print(f"Failed to load alert sound '{name}': {exc}")
    return None

BUTTON_SOUND = _load_button_sound()
CONFLICT_SOUND = _load_conflict_sound()
ALERT_SOUND = _load_alert_sound()   # <-- add this

BUTTON_SOUND = _load_button_sound()
CONFLICT_SOUND = _load_conflict_sound()


def play_button_sound():
    if not BUTTON_SOUND:
        print("No button sound loaded")
        return
    volume_setting = SETTINGS.get("master_volume", "Medium")
    print("Volume setting:", volume_setting)
    if volume_setting == "Off":
        print("Muted")
        return
    elif volume_setting == "Low":
        BUTTON_SOUND.set_volume(0.25)
    elif volume_setting == "Medium":
        BUTTON_SOUND.set_volume(0.6)
    elif volume_setting == "High":
        BUTTON_SOUND.set_volume(1.0)
    else:
        BUTTON_SOUND.set_volume(0.6)
    print("Playing sound at volume", BUTTON_SOUND.get_volume())
    BUTTON_SOUND.play()
    
# --- Helper functions ---
def draw_text(text, font, color, surface, x, y):
    """Draw text centered at (x, y)."""
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect(center=(x, y))
    surface.blit(text_obj, text_rect)
    return text_rect

def draw_text_multi_color(segments, font, surface, center_x, center_y):
    """Draw a single line with differently colored segments centered at (center_x, center_y).
    segments: list of (text, (r,g,b)) tuples
    """
    widths = [font.size(txt)[0] for txt, _ in segments]
    total_width = sum(widths)
    x = center_x - total_width // 2
    for (txt, color), w in zip(segments, widths):
        surf = font.render(txt, True, color)
        rect = surf.get_rect(midleft=(x, center_y))
        surface.blit(surf, rect)
        x += w

# --- Scene functions ---
def main_menu():
    buttons = [
        Button("Start simulation", (WINDOW_SIZE[0]//2, 200), lambda: change_scene("confirm_tutorial")),
        Button("Game settings", (WINDOW_SIZE[0]//2, 270), lambda: change_scene("settings")),
        Button("Tutorial", (WINDOW_SIZE[0]//2, 340), lambda: change_scene("tutorial")),
        Button("Credits", (WINDOW_SIZE[0]//2, 410), lambda: change_scene("credits")),
        Button("Exit", (80, WINDOW_SIZE[1]-40), lambda: pygame.quit() or sys.exit())
    ]

    while current_scene == "menu":
        # --- draw background image ---
        screen.blit(background_menu, (0, 0))

        draw_text("Air Traffic Controller Simulator", font_title, (255, 255, 255), screen, WINDOW_SIZE[0]//2, 80)
        for b in buttons:
            b.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b.is_clicked(event.pos):
                        b.activate()

        pygame.display.flip()
        clock.tick(60)
class Button:
    def __init__(self, text, center, action, width=300, height=60, play_sound=True):
        self.text = text
        self.center = center
        self.action = action
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center
        self.play_sound = play_sound

    def draw(self, surface):
        mouse = pygame.mouse.get_pos()

        # Change color if hovered
        if self.rect.collidepoint(mouse):
            color = (0, 130, 0)   # hover color (steel blue)
        else:
            color = (0, 149, 0)  # normal color (cornflower blue)

        # Draw button background (rounded corners)
        pygame.draw.rect(surface, color, self.rect, border_radius=12)

        # Draw button border
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=12)

        # Draw button text
        text_surf = font_button.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def activate(self):
        if self.play_sound:
            play_button_sound()
        if self.action:
            self.action()


# Scene manager
current_scene = "menu"
def change_scene(name):
    global current_scene
    current_scene = name

# Credits Page
def credits_screen():
    buttons = [Button("Back", (80, WINDOW_SIZE[1]-40), lambda: change_scene("menu"))]

    while current_scene == "credits":
        screen.blit(background_generic, (0, 0))

        # Darkened Background
        box_width, box_height = 800, 400
        box_x = (WINDOW_SIZE[0] - box_width) // 2
        box_y = (WINDOW_SIZE[1] - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)

        # Draw semi-transparent rectangle
        s = pygame.Surface((box_width, box_height))  
        s.set_alpha(180)  # 0 = fully transparent, 255 = opaque
        s.fill((0, 0, 0))  # black background
        screen.blit(s, (box_x, box_y))

        # Title 
        draw_text("Credits", font_title, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 40)

        # Credits text inside box 
        draw_text("Developed by: Delan Karim", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 120)
        draw_text("Inspired by real-world ATC operations", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 170)
        draw_text("Developed at Central foundation Boys School", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 220)

        # Draw buttons
        for b in buttons:
            b.draw(screen)

        # Handle events 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b.is_clicked(event.pos):
                        b.activate()

        pygame.display.flip()
        clock.tick(60)


# Settings Page
SETTINGS = {
    "master_volume": "Medium",   # Off/Low/Medium/High
    "difficulty": "Normal",      # Easy/Normal/Hard
    "gamemode": "Air",           # Ground/Air
    "Airport": "Heathrow",          # Low/Medium/High
}


class Dropdown:
    def __init__(self, label, center, width, options, selected_index=0, row_height=44):
        self.label = label
        self.center = center
        self.width = width
        self.options = options
        self.index = max(0, min(selected_index, len(options) - 1))
        self.row_height = row_height
        self.open = False
        self.rect = pygame.Rect(0, 0, width, row_height)
        self.rect.center = center

    @property
    def value(self):
        return self.options[self.index]

    def draw(self, surface):
        # Main box first
        pygame.draw.rect(surface, (30, 30, 30), self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)

        # Selected text inside the box
        sel_surf = font_button.render(self.value, True, (255, 255, 255))
        sel_rect = sel_surf.get_rect(midleft=(self.rect.left + 12, self.rect.centery))
        surface.blit(sel_surf, sel_rect)

        # Label above the box (drawn after so it isn't covered)
        label_text = f"{self.label}: {self.value}"
        text_surf = font_button.render(label_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(midbottom=(self.center[0], self.rect.top - 8))
        surface.blit(text_surf, text_rect)

        # Arrow
        ax = self.rect.right - 24
        ay = self.rect.centery
        arrow = [(ax - 8, ay - 4), (ax, ay - 4), (ax - 4, ay + 6)] if not self.open else [(ax - 8, ay + 4), (ax, ay + 4), (ax - 4, ay - 6)]
        pygame.draw.polygon(surface, (255, 255, 255), arrow)

        # Options list (open downwards below the box)
        if self.open:
            for i, opt in enumerate(self.options):
                r = pygame.Rect(
                    self.rect.left,
                    self.rect.bottom + i * self.row_height,
                    self.rect.width,
                    self.row_height,
                )
                bg = (60, 60, 60) if i != self.index else (0, 149, 0)
                pygame.draw.rect(surface, bg, r)
                pygame.draw.rect(surface, (255, 255, 255), r, 1)
                osurf = font_button.render(opt, True, (255, 255, 255))
                orect = osurf.get_rect(midleft=(r.left + 12, r.centery))
                surface.blit(osurf, orect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                self.open = not self.open
                return
            if self.open:
                # Check options list (opened downwards)
                for i, _ in enumerate(self.options):
                    r = pygame.Rect(
                        self.rect.left,
                        self.rect.bottom + i * self.row_height,
                        self.rect.width,
                        self.row_height,
                    )
                    if r.collidepoint(mx, my):
                        self.index = i
                        self.open = False
                        return
                # Click outside closes
                self.open = False


def settings_screen():
    # Panel layout similar to tutorial/credits
    panel_w, panel_h = 1000, 600
    panel_x = (WINDOW_SIZE[0] - panel_w) // 2
    panel_y = (WINDOW_SIZE[1] - panel_h) // 2

    # Controls (dropdowns only, no sliders)
    vol_levels = ["Off", "Low", "Medium", "High"]
    difficulties = ["Beginner", "Easy", "Normal", "Realistic"]
    gamemodes = ["Ground", "Air"]
    Airport = ["Los Angeles", "London Heathrow", "Glasgow"]

    dd_master_vol = Dropdown(
        "Master Volume",
        (panel_x + panel_w // 2, panel_y + 200),
        360,
        vol_levels,
        selected_index=vol_levels.index(SETTINGS.get("master_volume", "Medium")) if SETTINGS.get("master_volume", "Medium") in vol_levels else 2,
        row_height=38,
    )

    dd_gamemode = Dropdown(
        "Gamemode",
        (panel_x + panel_w // 2, panel_y + 290),
        360,
        gamemodes,
        selected_index=gamemodes.index(SETTINGS.get("gamemode", "Air")) if SETTINGS.get("gamemode", "Air") in gamemodes else 1,
        row_height=38,
    )

    dd_difficulty = Dropdown(
        "Difficulty",
        (panel_x + panel_w // 2, panel_y + 380),
        360,
        difficulties,
        selected_index=difficulties.index(SETTINGS.get("difficulty", "Normal")) if SETTINGS.get("difficulty", "Normal") in difficulties else 1,
        row_height=38,
    )

    dd_airports = Dropdown(
        "Airport",
        (panel_x + panel_w // 2, panel_y + 480),
        360,
        Airport,
        selected_index=Airport.index(SETTINGS.get("Airport", "London Heathrow")) if SETTINGS.get("Airport", "London Heathrow") in Airport else 1,
        row_height=38,
    )

    back_btn = Button("Back", (80, WINDOW_SIZE[1] - 40), lambda: change_scene("menu"))
    apply_btn = Button("Apply", (panel_x + panel_w - 140, panel_y + panel_h - 40), lambda: None, width=200, height=50)
    reset_btn = Button("Reset", (panel_x + 140, panel_y + panel_h - 40), lambda: None, width=200, height=50)

    def apply_changes():
        SETTINGS["master_volume"] = dd_master_vol.value
        SETTINGS["difficulty"] = dd_difficulty.value
        SETTINGS["gamemode"] = dd_gamemode.value
        SETTINGS["Airport"] = dd_airports.value
        change_scene("menu")

    def reset_defaults():
        dd_master_vol.index = vol_levels.index("Medium")
        dd_difficulty.index = difficulties.index("Normal")
        dd_gamemode.index = gamemodes.index("Air")
        dd_airports.index = Airport.index("London Heathrow")
        SETTINGS["master_volume"] = "Medium"
        SETTINGS["difficulty"] = "Normal"
        SETTINGS["gamemode"] = "Air"
        SETTINGS["Airport"] = "London Heathrow"

    apply_btn.action = apply_changes
    reset_btn.action = reset_defaults

    while current_scene == "settings":
        screen.blit(background_generic, (0, 0))

        # Dimmed panel
        s = pygame.Surface((panel_w, panel_h))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        screen.blit(s, (panel_x, panel_y))

        # Title
        draw_text("Game Settings", font_title, (255, 255, 255), screen, panel_x + panel_w // 2, panel_y + 80)

        # Draw controls
        dd_master_vol.draw(screen)
        dd_gamemode.draw(screen)
        dd_difficulty.draw(screen)
        dd_airports.draw(screen)

        # Draw buttons
        reset_btn.draw(screen)
        apply_btn.draw(screen)
        back_btn.draw(screen)

        # Re-draw open dropdowns last so their menus are on top
        for dd in (dd_master_vol, dd_gamemode, dd_difficulty, dd_airports):
            if dd.open:
                dd.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Delegate to controls
            dd_master_vol.handle_event(event)
            dd_gamemode.handle_event(event)
            dd_difficulty.handle_event(event)
            dd_airports.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.is_clicked(event.pos):
                    back_btn.activate()
                elif reset_btn.is_clicked(event.pos):
                    reset_btn.activate()
                elif apply_btn.is_clicked(event.pos):
                    apply_btn.activate()

        pygame.display.flip()
        clock.tick(60)

# Tutorial Screen

def tutorial_screen():


    WHITE = (255,255,255)
    GREEN = (0,255,0)
    pages = [
        ["Welcome to the Air Traffic Controller Simulator", "Your Ultimate goal is to guide aircraft to and from the Airport.", "Ensuring maximum aircraft safety at all times.","You will be able to do this by using the dedicated commands"],
        ["To contact an aircraft you must follow these steps","You must first call upon a specific aircraft by using their unique identifer (Callsign)", [("An example of this may be:" ,WHITE),("BA0342" ,GREEN)],"You must then let the aircraft know what direction to head (Heading (0 to 360 degrees))", [("Something like this:" ,WHITE),("HDG180" ,GREEN)],"You must then let the aircraft know what speed to travel at", [("e.g" ,WHITE),("SPD250" ,GREEN)]],
        ["Finally you must tell them the altitude they need to be at", [("As shown:" ,WHITE),("FL360" ,GREEN)], "You can then combine these 4 into one statement as shown", ("BA0342 HDG180 SPD250 FL360",GREEN),"If your statement is correct the aircraft will follow your instructions ASAP"],
        ["All aircraft need to be directed into the intended entry point for each runway", "To see an example of what this can look like press the button below", "The red arrow on the left pointing to the right shows exactly where aircraft must be to land", " The departure path is also shown on the right of the runway using the red arrow", "This is the landing/take-off procedure at Heathrow Airport Runway 09L,", " every Airport and runway will have a unique document to follow."],
        ["Once the aircraft have arrived at the entry point, the user must command them to land", [("This can be done like this:", WHITE), ("BA0342 CLEARED TO LAND RWY09L",GREEN)],"Note aircraft must be at the suitable landing altitude stated in the document","Aircraft must also be at a suitable distance from each other (5nm)", [("Similarly, to take off an aircraft simply type: ", WHITE),("BA0342 CLEARED FOR TAKEOFF RWY09L", GREEN)]],
        ["The other gamemode, which the user can also play is ground control", "The user must guide aircraft between the gates and runways", "An example of what the Airport might look like can be seen by pressing the button below.", [("The user can guide aircraft to gates like this:",WHITE), ("BA0342 TAXI TO GATE 45 VIA A B F", GREEN)], "With A B and F being specific taxi-ways"],
    ]

    page_index = 0

    def acknowledge():
        nonlocal page_index
        if page_index < len(pages) - 1:
            page_index += 1
        else:
            change_scene("menu")  # Finish returns to menu

    def open_pdf(pdf_path: str):
        abs_path = os.path.abspath(pdf_path)
        if not os.path.exists(abs_path):
            print(f"PDF not found: {abs_path}")
            return
        webbrowser.open_new(Path(abs_path).as_uri())  # opens in default viewer

    back_btn = Button("Back", (80, WINDOW_SIZE[1]-40), lambda: change_scene("menu"))

    while current_scene == "tutorial":
        screen.blit(background_generic, (0, 0))

        # Darkened background box
        box_width, box_height = 1100, 600
        box_x = (WINDOW_SIZE[0] - box_width) // 2
        box_y = (WINDOW_SIZE[1] - box_height) // 2

        s = pygame.Surface((box_width, box_height))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        screen.blit(s, (box_x, box_y))

        # Title
        draw_text("Tutorial", font_title, (255, 255, 255), screen,
                  WINDOW_SIZE[0]//2, box_y + 40)

        # Draw current page lines supporting strings, (text,color) tuples, and lists of segments
        y = box_y + 120
        for item in pages[page_index]:
            if isinstance(item, str):
                draw_text(item, font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, y)
            elif isinstance(item, tuple) and len(item) == 2:
                text, color = item
                draw_text(text, font_button, color, screen, WINDOW_SIZE[0]//2, y)
            else:
                # list of (text, color) segments
                draw_text_multi_color(item, font_button, screen, WINDOW_SIZE[0]//2, y)
            y += 50

        # Page indicator
        draw_text(f"Page {page_index + 1} / {len(pages)}", font_button, (200, 200, 200), screen,
                  WINDOW_SIZE[0]//2, box_y + box_height - 90)

        # Buttons
        ack_text = "Acknowledge" if page_index < len(pages) - 1 else "Finish"
        ack_btn = Button(ack_text, (box_x + box_width - 180, box_y + box_height - 40),
                         acknowledge, width=220, height=50)

        # PDF button appears only on the 5th page (index 4)
        pdf_btn = None
        if page_index == 3:
            pdf_btn = Button(
                "Open PDF",
                (box_x + 180, box_y + box_height - 40),
                lambda: open_pdf("Runway09L.pdf"),
                width=220,
                height=50,
            )

        back_btn.draw(screen)
        if pdf_btn:
            pdf_btn.draw(screen)
        ack_btn.draw(screen)


        # PDF button appears only on the 5th page (index 4)
        pdf_btn = None
        if page_index == 5:
            pdf_btn = Button(
                "Open PDF",
                (box_x + 180, box_y + box_height - 40),
                lambda: open_pdf("Groundmap.pdf"),
                width=220,
                height=50,
            )


        back_btn.draw(screen)
        if pdf_btn:
            pdf_btn.draw(screen)
        ack_btn.draw(screen)
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.is_clicked(event.pos):
                    back_btn.activate()
                elif pdf_btn and pdf_btn.is_clicked(event.pos):
                    pdf_btn.activate()
                elif ack_btn.is_clicked(event.pos):
                    ack_btn.activate()

        pygame.display.flip()
        clock.tick(60)


def confirm_tutorial():
    # Panel dimensions similar to credits/tutorial screens
    box_width, box_height = 600, 300
    box_x = (WINDOW_SIZE[0] - box_width) // 2
    box_y = (WINDOW_SIZE[1] - box_height) // 2

    # Buttons centered relative to the box
    buttons = [
        Button("Yes", (box_x + box_width//2 - 80, box_y + box_height - 60),
               lambda: change_scene("tutorial"), width=150, height=50),
        Button("No",  (box_x + box_width//2 + 80, box_y + box_height - 60),
               lambda: change_scene("start"), width=150, height=50),
    ]

    while current_scene == "confirm_tutorial":
        screen.blit(background_generic, (0, 0))

        # Draw semi-transparent dark rectangle
        s = pygame.Surface((box_width, box_height))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        screen.blit(s, (box_x, box_y))

        # Draw prompt text centered in box
        draw_text(
            "Visit tutorial first?",
            font_title,
            (255, 255, 255),
            screen,
            box_x + box_width // 2,
            box_y + 80
        )

        # Draw the buttons
        for b in buttons:
            b.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b.is_clicked(event.pos):
                        b.action()

        pygame.display.flip()
        clock.tick(60)

# Main loop
while True:
    if current_scene == "menu":
        main_menu()
    elif current_scene == "confirm_tutorial":
        confirm_tutorial()
    elif current_scene == "settings":
        settings_screen()
    elif current_scene == "tutorial":
        tutorial_screen()
    elif current_scene == "credits":
        credits_screen()
    elif current_scene == "start":
        simulation_screen()
