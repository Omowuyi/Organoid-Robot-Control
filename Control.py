import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

###############################################################################
##  CONFIGURATION
###############################################################################
CSV_DATA_PATH = r"C:/Users/xxxx/rgo_spike_list.csv"  # <-- Update path
TIME_STEP = 0.5       # Normal speed: each loop increments sim_time by 0.5 s
POLL_INTERVAL = 500   # 500 ms between updates
SIM_DURATION = 1000.0
WINDOW_DURATION = SIM_DURATION

START_DELAY_MS = 40000  # 40-second real-time delay
MIN_TIMESTAMP = 48      # Only use spikes with Time >= 55
SHIFT_SECONDS = 48      # Subtract 55 when plotting so earliest spike is at 0

# Full B2 electrode list for display (including B2_12).
ELECTRODES_ALL = [
    "B2_11", "B2_12", "B2_13", "B2_14",
    "B2_21", "B2_22", "B2_23", "B2_24",
    "B2_31", "B2_32", "B2_33", "B2_34",
    "B2_41", "B2_42", "B2_43", "B2_44"
]
# For spike data, exclude B2_12
ELECTRODES_DATA = [
    "B2_11", "B2_13", "B2_14",
    "B2_21", "B2_22", "B2_23", "B2_24",
    "B2_31", "B2_32", "B2_33", "B2_34",
    "B2_41", "B2_42", "B2_43"
]

###############################################################################
# Main GUI Class
###############################################################################
class PuppyPiGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Control Software")
        # Set a portrait window size
        self.master.geometry("450x700")
        self.master.minsize(450, 700)

        # Start the internal simulation clock at 0
        self.sim_time = 0.0
        self.all_data = pd.DataFrame()
        self.max_time = 0.0
        self.raster_data = pd.DataFrame(columns=["Time (s)", "Electrode"])
        self.color_window = 1.0
        self.well_items = {}

        # Setup styles for AXIOM (blue) and Temperature/Spikes (gray)
        self.setup_styles()

        # Build the GUI layout
        self.setup_gui()

        # Load CSV data
        self.load_and_prepare_csv()

        # Key fix: set self.sim_time = 55 immediately so we see spikes at once after 40s
        self.sim_time = 48

        # After a 40-second delay, start the simulation
        self.master.after(START_DELAY_MS, self.update_loop)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Axiom.TButton",
            foreground="white",
            background="dodgerblue",
            padding=5,
            font=("Arial", 10, "bold")
        )
        style.configure(
            "Neutral.TButton",
            foreground="black",
            background="#e0e0e0",
            padding=5,
            font=("Arial", 10, "bold")
        )

    def setup_gui(self):
        # Top frame
        self.top_frame = ttk.Frame(self.master)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.left_subframe = ttk.Frame(self.top_frame)
        self.left_subframe.pack(side=tk.LEFT, padx=5, pady=5)

        self.right_subframe = ttk.Frame(self.top_frame)
        self.right_subframe.pack(side=tk.RIGHT, padx=5, pady=5)

        # B2 well canvas
        self.well_canvas_width = 240
        self.well_canvas_height = 240
        self.well_canvas = tk.Canvas(
            self.left_subframe,
            width=self.well_canvas_width,
            height=self.well_canvas_height,
            bg="white"
        )
        self.well_canvas.pack()

        self.draw_rounded_box(
            self.well_canvas, 5, 5,
            self.well_canvas_width - 5,
            self.well_canvas_height - 5,
            radius=20
        )

        # Create circles for the 16 electrodes
        margin = 20
        grid_size = 4
        cell_w = (self.well_canvas_width - 2*margin) / grid_size
        cell_h = (self.well_canvas_height - 2*margin) / grid_size
        circle_r = min(cell_w, cell_h) * 0.3
        for idx, elec_label in enumerate(ELECTRODES_ALL):
            row = idx // 4
            col = idx % 4
            cx = margin + cell_w*col + cell_w/2
            cy = margin + cell_h*row + cell_h/2
            x0 = cx - circle_r
            y0 = cy - circle_r
            x1 = cx + circle_r
            y1 = cy + circle_r
            item = self.well_canvas.create_oval(x0, y0, x1, y1, fill="black", outline="black")
            self.well_items[elec_label] = item

        # AXIOM–ROBOT button
        self.axiom_button = ttk.Button(
            self.right_subframe,
            text="AXIOM\n⇄ ROBOT",
            style="Axiom.TButton",
            command=self.on_axiom_button_clicked
        )
        self.axiom_button.pack(pady=5)

        # Temperature button
        self.temp_button = ttk.Button(
            self.right_subframe,
            text="Temperature\n37°C",
            style="Neutral.TButton"
        )
        self.temp_button.pack(pady=5)

        # Spikes button
        self.spikes_button = ttk.Button(
            self.right_subframe,
            text="Spikes\n0",
            style="Neutral.TButton"
        )
        self.spikes_button.pack(pady=5)

        # Bottom frame for raster plot
        self.bottom_frame = ttk.Frame(self.master)
        self.bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        # Adjust margins so "Electrodes" label is visible
        self.fig.subplots_adjust(left=0.30, right=0.95, top=0.90, bottom=0.15)
        self.ax_raster = self.fig.add_subplot(111)
        self.ax_raster.set_title("Raster Plot (Well B2)")
        self.ax_raster.set_xlabel("Time (s)")
        self.ax_raster.set_ylabel("Electrodes", labelpad=15)
        self.ax_raster.grid(True)

        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=self.bottom_frame)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def draw_rounded_box(self, canvas, x1, y1, x2, y2, radius=25):
        canvas.create_arc(x1, y1, x1+2*radius, y1+2*radius,
                          start=90, extent=90, style=tk.ARC, width=2)
        canvas.create_arc(x2-2*radius, y1, x2, y1+2*radius,
                          start=0, extent=90, style=tk.ARC, width=2)
        canvas.create_arc(x1, y2-2*radius, x1+2*radius, y2,
                          start=180, extent=90, style=tk.ARC, width=2)
        canvas.create_arc(x2-2*radius, y2-2*radius, x2, y2,
                          start=270, extent=90, style=tk.ARC, width=2)
        canvas.create_line(x1+radius, y1, x2-radius, y1, width=2)
        canvas.create_line(x2, y1+radius, x2, y2-radius, width=2)
        canvas.create_line(x2-radius, y2, x1+radius, y2, width=2)
        canvas.create_line(x1, y2-radius, x1, y1+radius, width=2)

    def on_axiom_button_clicked(self):
        print("AXIOM ⇄ ROBOT button clicked!")

    def load_and_prepare_csv(self):
        if not os.path.exists(CSV_DATA_PATH):
            print(f"CSV file not found: {CSV_DATA_PATH}")
            return
        try:
            df = pd.read_csv(CSV_DATA_PATH)
            df["Time (s)"] = pd.to_numeric(df["Time (s)"], errors="coerce")
            df.dropna(subset=["Time (s)"], inplace=True)
            df["Electrode"] = df["Electrode"].astype(str)
            # Keep B2 electrodes, exclude B2_12
            df = df[df["Electrode"].str.startswith("B2_")]
            df = df[df["Electrode"] != "B2_12"]
            df.sort_values("Time (s)", inplace=True)
            self.all_data = df
            if not df.empty:
                self.max_time = df["Time (s)"].max()
            print(f"Loaded CSV ignoring B2_12: {len(df)} rows, max_time={self.max_time}")
        except Exception as e:
            print(f"Error loading CSV: {e}")

    def update_loop(self):
        # Normal speed: each update increments sim_time by 0.5 s
        self.sim_time += TIME_STEP

        
        df_window = self.all_data[
            (self.all_data["Time (s)"] >= MIN_TIMESTAMP) &
            (self.all_data["Time (s)"] <= self.sim_time)
        ]
        self.raster_data = df_window.copy()

        self.update_raster_plot()
        self.update_well_display()

        # Update the Spikes button
        total_spikes = len(self.raster_data)
        self.spikes_button.config(text=f"Spikes\n{total_spikes}")

        if self.sim_time < self.max_time:
            self.master.after(POLL_INTERVAL, self.update_loop)
        else:
            print("Reached end of simulation or CSV data limit.")

    def update_raster_plot(self):
        self.ax_raster.clear()
        self.ax_raster.set_title("Raster Plot (Well B2)")
        self.ax_raster.set_xlabel("Time (s)")
        self.ax_raster.set_ylabel("Electrodes", labelpad=15)
        self.ax_raster.grid(True)

        # Always show all electrodes on the y-axis
        self.ax_raster.set_yticks(range(len(ELECTRODES_ALL)))
        self.ax_raster.set_yticklabels(ELECTRODES_ALL)

        if not self.raster_data.empty:
            # shift by SHIFT_SECONDS => earliest spike at x=0
            elec_to_y = {elec: i for i, elec in enumerate(ELECTRODES_ALL)}
            for _, row in self.raster_data.iterrows():
                real_t = row["Time (s)"]
                shifted_t = real_t - MIN_TIMESTAMP
                elec = row["Electrode"]
                if elec in elec_to_y:
                    y_val = elec_to_y[elec]
                    self.ax_raster.plot(shifted_t, y_val, marker='|', color='black', markersize=8)

        self.canvas_plot.draw()

    def update_well_display(self):
        
        if self.raster_data.empty:
            for elec in ELECTRODES_ALL:
                self.well_canvas.itemconfig(self.well_items[elec], fill="black", outline="black")
            return

        for elec in ELECTRODES_ALL:
            sub_df = self.raster_data[self.raster_data["Electrode"] == elec]
            if sub_df.empty:
                color = "black"
            else:
                last_spike = sub_df["Time (s)"].max()
                # If the last spike is within 1 second of current sim_time => color = blue
                if (self.sim_time - last_spike) <= self.color_window:
                    color = "blue"
                else:
                    color = "black"
            self.well_canvas.itemconfig(self.well_items[elec], fill=color, outline=color)

def main():
    root = tk.Tk()
    app = PuppyPiGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
