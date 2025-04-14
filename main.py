import tkinter as tk
from PIL import Image, ImageTk
import math

# === CONFIG ===
MAT_IMAGE = "fll_mat.png"     # Update to your image path
PIXELS_PER_INCH = 16        # Scale of your mat image (Dimensions of image in px / field size in inches)
# Robot length and width are from the farthest points of your robot, you can choose to ignore this but then your
# paths might be ever so slightly different.
# How to calculate offset, find the distance to the center of your 2 drive wheels, find the offset from your overall center to your drive center.

class PathPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("FLL Path Planner")
        self.frame = tk.Frame(root)
        self.frame.pack(side=tk.LEFT, fill=tk.Y)

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.LEFT)

        self.image = Image.open(MAT_IMAGE)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas = tk.Canvas(self.canvas_frame, width=self.image.width, height=self.image.height)
        self.canvas.pack()
        self.canvas.create_image(0, self.image.height, anchor=tk.SW, image=self.tk_image)

        self.textbox = tk.Text(self.frame, width=30, height=20, bg="white", fg="black", font=("Courier", 10))
        self.textbox.pack(padx=5, pady=5)

        self.robot_length_var = tk.DoubleVar(value=2.0)
        self.robot_width_var = tk.DoubleVar(value=1.5)
        self.robot_offset_x_var = tk.DoubleVar(value=0.0)
        self.robot_offset_y_var = tk.DoubleVar(value=0.0)

        tk.Label(self.frame, text="Robot Length (in)").pack()
        tk.Entry(self.frame, textvariable=self.robot_length_var).pack(pady=2)

        tk.Label(self.frame, text="Robot Width (in)").pack()
        tk.Entry(self.frame, textvariable=self.robot_width_var).pack(pady=2)

        tk.Label(self.frame, text="Offset X (in)").pack()
        tk.Entry(self.frame, textvariable=self.robot_offset_x_var).pack(pady=2)

        tk.Label(self.frame, text="Offset Y (in)").pack()
        tk.Entry(self.frame, textvariable=self.robot_offset_y_var).pack(pady=2)

        tk.Label(self.frame, text="Start X (in)").pack()
        self.start_x_entry = tk.Entry(self.frame)
        self.start_x_entry.insert(0, "5")
        self.start_x_entry.pack(pady=2)

        tk.Label(self.frame, text="Start Y (in)").pack()
        self.start_y_entry = tk.Entry(self.frame)
        self.start_y_entry.insert(0, "5")
        self.start_y_entry.pack(pady=2)

        tk.Label(self.frame, text="Start Angle (\u00b0)").pack()
        self.start_angle_entry = tk.Entry(self.frame)
        self.start_angle_entry.insert(0, "0")
        self.start_angle_entry.pack(pady=2)

        self.set_pose_button = tk.Button(self.frame, text="Set Start Pose", command=self.update_start_pose)
        self.set_pose_button.pack(pady=5)

        self.turn_button = tk.Button(self.frame, text="Add Turn Step", command=self.add_turn_step)
        self.turn_button.pack(pady=5)

        self.marker_button = tk.Button(self.frame, text="Add Marker", command=self.add_marker)
        self.marker_button.pack(pady=5)

        self.clear_button = tk.Button(self.frame, text="Reset", command=self.reset)
        self.clear_button.pack(pady=5)

        self.undo_button = tk.Button(self.frame, text="Undo", command=self.undo)
        self.undo_button.pack(pady=5, side=tk.BOTTOM)  # Ensures the button is at the bottom

        self.points = []
        self.robot_angle = 0
        self.turn_mode = False
        self.robot_box = None
        self.robot_position = None
        self.marker_count = 1
        self.history = []  # Store actions for undo

        self.canvas.bind("<Button-1>", self.add_point)
        self.update_start_pose()

    def resize_image(self, img):
        # Resize the image to fit within the canvas size
        canvas_width = 800  # Specify the desired width for the canvas
        canvas_height = 600  # Specify the desired height for the canvas
        img_width, img_height = img.size

        # Calculate the scaling factor to maintain the aspect ratio
        scale_factor = min(canvas_width / img_width, canvas_height / img_height)

        # Calculate new dimensions for the image
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)

        # Resize the image
        return img.resize((new_width, new_height), Image.ANTIALIAS)
    def update_start_pose(self):
        try:
            self.robot_length = self.robot_length_var.get() * PIXELS_PER_INCH
            self.robot_width = self.robot_width_var.get() * PIXELS_PER_INCH
            self.robot_offset = (
                self.robot_offset_x_var.get() * PIXELS_PER_INCH,
                self.robot_offset_y_var.get() * PIXELS_PER_INCH
            )

            x_in = float(self.start_x_entry.get())
            y_in = float(self.start_y_entry.get())
            angle = float(self.start_angle_entry.get()) * -1 +90
            x_px = x_in * PIXELS_PER_INCH
            y_px = y_in * PIXELS_PER_INCH
            self.set_start_pose(x_px, y_px, angle)
        except ValueError:
            pass

    def set_start_pose(self, x, y, angle):
        self.robot_position = (x, y)
        self.robot_angle = angle
        self.canvas.delete("all")
        self.canvas.create_image(0, self.image.height, anchor=tk.SW, image=self.tk_image)
        self.points.clear()
        self.textbox.delete("1.0", tk.END)
        self.draw_robot(x, y, angle)

    def reset(self):
        self.update_start_pose()

    def add_turn_step(self):
        self.turn_mode = True

    def add_marker(self):
        if self.robot_position:
            # Get the current position of the robot to place the marker visually
            x, y = self.robot_position

            # Draw a small circle to represent the marker on the canvas
            marker_radius = 10
            self.canvas.create_oval(x - marker_radius, self.image.height - y - marker_radius,
                                    x + marker_radius, self.image.height - y + marker_radius,
                                    outline="green", width=2, tags=f"marker_{self.marker_count}")

            # Add marker text to the textbox
            self.textbox.insert(tk.END, f"MARKER {self.marker_count} at ({x / PIXELS_PER_INCH:.2f}, {y / PIXELS_PER_INCH:.2f})\n")
            self.history.append(('marker', x, y))  # Track this action
            self.marker_count += 1

    def undo(self):
        if self.history:
            last_action = self.history.pop()
            self.canvas.delete("all")
            self.canvas.create_image(0, self.image.height, anchor=tk.SW, image=self.tk_image)
            self.points.clear()
            self.textbox.delete("1.0", tk.END)
            self.robot_position = (0, 0)
            self.robot_angle = 0

            # Replay all actions except the last one
            for action in self.history:
                if action[0] == 'marker':
                    x, y = action[1], action[2]
                    marker_radius = 10
                    self.canvas.create_oval(x - marker_radius, self.image.height - y - marker_radius,
                                            x + marker_radius, self.image.height - y + marker_radius,
                                            outline="green", width=2)
                    self.textbox.insert(tk.END, f"MARKER {self.marker_count} at ({x / PIXELS_PER_INCH:.2f}, {y / PIXELS_PER_INCH:.2f})\n")

            self.draw_robot(self.robot_position[0], self.robot_position[1], self.robot_angle)

    def add_point(self, event):
        x, y = event.x, self.image.height - event.y

        if self.turn_mode and self.robot_position:
            rx, ry = self.robot_position
            dx = x - rx
            dy = y - ry
            desired_angle = math.degrees(math.atan2(dy, dx))
            turn_angle = (desired_angle - self.robot_angle + 360) % 360
            if turn_angle > 180:
                turn_angle -= 360

            self.robot_angle = (self.robot_angle + turn_angle) % 360
            self.points.append(("TURN", turn_angle))

            size = 10
            tip_x = rx + size * math.cos(math.radians(self.robot_angle))
            tip_y = ry + size * math.sin(math.radians(self.robot_angle))
            left_x = rx + size * math.cos(math.radians(self.robot_angle + 140))
            left_y = ry + size * math.sin(math.radians(self.robot_angle + 140))
            right_x = rx + size * math.cos(math.radians(self.robot_angle - 140))
            right_y = ry + size * math.sin(math.radians(self.robot_angle - 140))

            self.canvas.create_polygon(
                [tip_x, self.image.height - tip_y,
                 left_x, self.image.height - left_y,
                 right_x, self.image.height - right_y],
                fill="purple",
                tags="turn_arrow"
            )

            self.textbox.insert(tk.END, f"rotate_{turn_angle:.1f}\n")
            self.turn_mode = False
            self.history.append(('turn', turn_angle))  # Track the turn action
            self.draw_robot(rx, ry, self.robot_angle)
        else:
            self.points.append((x, y))
            self.canvas.create_oval(x - 4, self.image.height - y - 4, x + 4, self.image.height - y + 4, fill='red')

            if self.robot_position:
                x1, y1 = self.robot_position
                x2, y2 = x, y
                dx = x2 - x1
                dy = y2 - y1
                distance_px = math.sqrt(dx ** 2 + dy ** 2)
                distance_in = distance_px / PIXELS_PER_INCH

                desired_angle = math.degrees(math.atan2(dy, dx))
                turn_angle = (desired_angle - self.robot_angle + 360) % 360
                if turn_angle > 180:
                    turn_angle -= 360
                turn_angle = turn_angle*-1
                self.robot_angle = desired_angle % 360
                self.canvas.create_line(x1, self.image.height - y1, x2, self.image.height - y2, fill='blue', width=2)
                self.textbox.insert(tk.END, f"r{turn_angle:.1f}_")
                self.textbox.insert(tk.END, f"d{distance_in:.2f}_")

            self.robot_position = (x, y)
            self.history.append(('move', x, y, self.robot_angle))  # Track movement action
            self.draw_robot(x, y, self.robot_angle)

    def draw_robot(self, x, y, angle):
        if self.robot_box:
            self.canvas.delete(self.robot_box)

        offset_x, offset_y = self.robot_offset
        length = self.robot_length
        width = self.robot_width

        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        ox = x + offset_x * cos_a - offset_y * sin_a
        oy = y + offset_x * sin_a + offset_y * cos_a

        corners = [(-length/2, -width/2), (length/2, -width/2),
                   (length/2, width/2), (-length/2, width/2)]

        rotated = []
        for dx, dy in corners:
            rx = ox + dx * cos_a - dy * sin_a
            ry = oy + dx * sin_a + dy * cos_a
            rotated.append((rx, self.image.height - ry))

        self.robot_box = self.canvas.create_polygon(rotated, outline='black', fill='cyan', width=2, tags="robot_box")

        # Draw front direction arrow (pose indicator)
        arrow_size = 10
        tip_x = x + arrow_size * math.cos(rad)
        tip_y = y + arrow_size * math.sin(rad)
        left_x = x + arrow_size * math.cos(rad + math.radians(140))
        left_y = y + arrow_size * math.sin(rad + math.radians(140))
        right_x = x + arrow_size * math.cos(rad - math.radians(140))
        right_y = y + arrow_size * math.sin(rad - math.radians(140))

        self.canvas.create_polygon(
            [tip_x, self.image.height - tip_y,
             left_x, self.image.height - left_y,
             right_x, self.image.height - right_y],
            fill="orange",
            tags="pose_arrow"
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = PathPlanner(root)
    root.mainloop()
