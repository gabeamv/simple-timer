import time
import tkinter as tk
from tkinter import ttk


class TimerApp:
    TICK_MS = 100  # display refresh rate, not a measurement unit

    def __init__(self, root):
        self.root = root
        self.root.title("Simple Timer")

        self.mode = tk.StringVar(value="countdown")
        self.running = False
        self.after_id = None

        # Elapsed/remaining time is derived from timestamps, not accumulated
        # per-tick, so after() scheduling jitter never causes drift.
        self.accumulated_ms = 0.0   # time banked before the current run
        self.run_start = None       # time.monotonic() when current run began
        self.countdown_target_ms = 0.0

        self._build_widgets()
        self._on_mode_change()

    # ---- UI ----

    def _build_widgets(self):
        mode_frame = ttk.Frame(self.root)
        mode_frame.pack(pady=5)
        ttk.Radiobutton(mode_frame, text="Countdown", variable=self.mode,
                        value="countdown", command=self._on_mode_change).pack(side="left")
        ttk.Radiobutton(mode_frame, text="Stopwatch", variable=self.mode,
                        value="stopwatch", command=self._on_mode_change).pack(side="left")

        self.input_frame = ttk.Frame(self.root)
        self.input_frame.pack(pady=5)
        ttk.Label(self.input_frame, text="MM:SS").pack(side="left")
        self.time_entry = ttk.Entry(self.input_frame, width=8)
        self.time_entry.insert(0, "05:00")
        self.time_entry.pack(side="left")

        self.display_var = tk.StringVar(value="00:00.0")
        ttk.Label(self.root, textvariable=self.display_var,
                  font=("Consolas", 32)).pack(pady=15)

        self.start_pause_btn = ttk.Button(self.root, text="Start",
                                           command=self._toggle_start_pause)
        self.start_pause_btn.pack(pady=5)

    def _on_mode_change(self):
        self._stop_ticking()
        self.running = False
        self.accumulated_ms = 0.0
        self.run_start = None
        self.start_pause_btn.config(text="Start")
        self.time_entry.config(state="normal")

        if self.mode.get() == "countdown":
            self.input_frame.pack(pady=5)
            self.display_var.set(self.time_entry.get() + ".0")
        else:
            self.input_frame.pack_forget()
            self.display_var.set("00:00.0")

    # ---- control ----

    def _toggle_start_pause(self):
        self._pause() if self.running else self._start()

    def _start(self):
        if self.mode.get() == "countdown" and self.accumulated_ms == 0.0 and self.run_start is None:
            self.countdown_target_ms = self._parse_mmss(self.time_entry.get())
            if self.countdown_target_ms <= 0:
                return
            self.time_entry.config(state="disabled")

        self.running = True
        self.run_start = time.monotonic()
        self.start_pause_btn.config(text="Pause")
        self._tick()

    def _pause(self):
        self._bank_elapsed()
        self.running = False
        self.run_start = None
        self.start_pause_btn.config(text="Start")
        self._stop_ticking()

    def _bank_elapsed(self):
        if self.run_start is not None:
            self.accumulated_ms += (time.monotonic() - self.run_start) * 1000
            self.run_start = time.monotonic()

    # ---- ticking ----

    def _tick(self):
        if not self.running:
            return

        self._bank_elapsed()

        if self.mode.get() == "countdown":
            remaining = max(0.0, self.countdown_target_ms - self.accumulated_ms)
            self._update_display(remaining)
            if remaining <= 0:
                self.running = False
                self.run_start = None
                self.start_pause_btn.config(text="Start")
                self.time_entry.config(state="normal")
                self.root.bell()
                return
        else:
            self._update_display(self.accumulated_ms)

        self.after_id = self.root.after(self.TICK_MS, self._tick)

    def _stop_ticking(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _update_display(self, total_ms):
        total_ms = int(total_ms)
        minutes, rem_ms = divmod(total_ms, 60000)
        seconds, tenths_ms = divmod(rem_ms, 1000)
        self.display_var.set(f"{minutes:02d}:{seconds:02d}.{tenths_ms // 100}")

    @staticmethod
    def _parse_mmss(text):
        try:
            mm, ss = text.strip().split(":")
            return (int(mm) * 60 + int(ss)) * 1000
        except ValueError:
            return 0.0


if __name__ == "__main__":
    root = tk.Tk()
    TimerApp(root)
    root.mainloop()
