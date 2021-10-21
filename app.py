import csv
import _csv
import io
import time
import threading
from datetime import datetime
from pprint import pprint
from typing import Callable, List

import numpy as np
from serial import Serial
from pykalman import KalmanFilter

import tkinter as tk
from tkinter.filedialog import asksaveasfile

import matplotlib
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class NatsuCsvWriter():
  file: io.TextIOWrapper = None
  writer: '_csv._writer' = None

  def __init__(self, file_path: str) -> None:
    # open file for writing and CSV writer
    self.file = open(file_path, "w", newline='')
    self.writer = csv.writer(self.file, delimiter=',',
                             quotechar='"', quoting=csv.QUOTE_MINIMAL)

    self.writer.writerow(['timestamp', 'y', 'y_noise', 'yhat'])

  def write(self, timestamp: datetime, measured: str, measured_with_noise: str, estimated: str) -> None:
    self.writer.writerow([timestamp.isoformat(), measured,
                         measured_with_noise, estimated])

  def close(self) -> None:
    # close opened file
    if self.file:
      self.file.close()


class NatsuSerialReader():
  thread: threading.Thread = None
  thread_stop_signal: bool = False
  serial_port: Serial = None
  serial_data: str = ""
  data_received_callback: Callable[[float], None] = None

  def __init__(self, port: str, baudrate: int, callback: Callable[[float], None]) -> None:
    self.serial_port = Serial()
    self.serial_port.port = port
    self.serial_port.baudrate = baudrate
    self.serial_port.timeout = 1

    self.data_received_callback = callback

  def start(self) -> None:
    print("Opening serial...")
    self.serial_port.open()

    # start new thread to prevent UI-blocking
    self.thread = threading.Thread(target=self.receive_serial)
    self.thread.daemon = True
    self.thread.start()

  def receive_serial(self) -> None:
    print("Start serial reading...")
    while (not self.thread_stop_signal):
      try:
        # read single line from serial
        self.serial_data = self.serial_port.readline().decode('ascii')

        # check null or whitespace
        if not self.serial_data or self.serial_data.isspace():
          continue

        # got valid data, execute the callback
        if self.data_received_callback:
          parsed_value = float(self.serial_data)
          self.data_received_callback(parsed_value)
      except:
        pass

  def close(self) -> None:
    self.thread_stop_signal = True
    time.sleep(0.1)

    if self.serial_port:
      self.serial_port.close()


class NatsuPyApp(tk.Frame):
  # --- to store plot data
  data_time: List[float] = None
  data_measured: List[float] = None
  data_measured_with_noise: List[float] = None
  data_estimated: List[float] = None

  # --- kalman filter implementation
  kf: KalmanFilter = KalmanFilter(initial_state_mean=0, n_dim_obs=1)
  kf_initialized: bool = False
  kf_last_means = None
  kf_last_covariances = None
  prng: np.random.Generator = None

  # --- to read data from serial and writing to csv
  csv_writer: NatsuCsvWriter = None
  serial_reader: NatsuSerialReader = None

  # --- to plot things
  fig: Figure = None
  ax: Axes = None
  sc_measured = None
  sc_measured_with_noise = None
  line_estimated = None

  # --- tkinter widgets
  tkPortInputText: tk.StringVar = None
  tkBaudInputText: tk.StringVar = None
  tkFileInputText: tk.StringVar = None

  tkPortInput: tk.Entry = None
  tkBaudInput: tk.Entry = None
  tkFileInput: tk.Entry = None
  tkBrowseButton: tk.Button = None
  tkConnectButton: tk.Button = None
  tkCanvas: FigureCanvasTkAgg = None

  # --- constructor
  def __init__(self, parent: tk.Tk, *args, **kwargs) -> None:
    tk.Frame.__init__(self, parent, *args, **kwargs)
    self.parent = parent

    self.prng = np.random.default_rng(0)
    self.initialize_controls()
    self.initialize_plot()

  def initialize_controls(self) -> None:
    # set background to white
    self.tk_setPalette(background="white")
    self.pack(side="top", fill="both", expand=True)

    # to hold inputs
    input_frame = tk.Frame(self)

    # add port input
    self.tkPortInputText = tk.StringVar(value="COM3")
    tk.Label(input_frame, text="COM port:").grid(row=0, column=0)
    self.tkPortInput = tk.Entry(input_frame, textvariable=self.tkPortInputText)
    self.tkPortInput.grid(row=0, column=1)

    # add baud rate input
    self.tkBaudInputText = tk.StringVar(value="9000")
    tk.Label(input_frame, text="Baud rate:").grid(row=0, column=2)
    self.tkBaudInput = tk.Entry(input_frame, textvariable=self.tkBaudInputText)
    self.tkBaudInput.grid(row=0, column=3)

    # add connect button
    self.tkConnectButton = tk.Button(
        input_frame, text="Connect", width=10, background="white smoke", command=self.connect)
    self.tkConnectButton.grid(row=0, column=4, padx=10, pady=10)

    # add save file input
    self.tkFileInputText = tk.StringVar(value="data.csv")
    tk.Label(input_frame, text="Save path:").grid(row=1, column=0)
    self.tkFileInput = tk.Entry(input_frame, textvariable=self.tkFileInputText)
    self.tkFileInput.grid(row=1, column=1, columnspan=3, sticky='we')

    # add connect button
    self.tkBrowseButton = tk.Button(
        input_frame, text="Browse", width=10, background="white smoke", command=self.browse_file)
    self.tkBrowseButton.grid(row=1, column=4, padx=10, pady=10)

    input_frame.pack(padx=20, pady=(20, 0))

  def initialize_plot(self) -> None:
    # fill initial data with zeros
    self.data_time = np.arange(10).tolist()
    self.data_measured = np.zeros(10).tolist()
    self.data_measured_with_noise = np.zeros(10).tolist()
    self.data_estimated = np.zeros(10).tolist()

    # create figure and axes
    self.fig = Figure(figsize=(6, 6))
    self.ax = self.fig.add_subplot(111)
    self.sc_measured = self.ax.scatter(
        self.data_time, self.data_measured, label="Measured", c="orange")
    self.sc_measured_with_noise = self.ax.scatter(
        self.data_time, self.data_measured_with_noise, label="Measured with Noise", c="red")
    self.line_estimated, = self.ax.plot(
        self.data_time, self.data_estimated, label="Estimated", c="blue")

    # add title and legends
    self.ax.set_ylabel("Temperature")
    self.ax.set_xlabel("Time")
    self.ax.set_ylim(10, 50)
    self.ax.legend()

    # add to window
    self.tkCanvas = FigureCanvasTkAgg(self.fig, master=self.parent)
    self.tkCanvas.get_tk_widget().pack()
    self.tkCanvas.draw()

  def connect(self):
    # disable UI interaction
    self.tkPortInput["state"] = "disabled"
    self.tkBaudInput["state"] = "disabled"
    self.tkFileInput["state"] = "disabled"
    self.tkBrowseButton["state"] = "disabled"
    self.tkConnectButton["state"] = "disabled"

    # inistiate reader and writer
    self.serial_reader = NatsuSerialReader(
        self.tkPortInputText.get(), int(self.tkBaudInputText.get()), self.update_plot)
    self.csv_writer = NatsuCsvWriter(self.tkFileInputText.get())

    # start serial reading
    self.serial_reader.start()

  def browse_file(self):
    # open file save dialog
    file_types = [("CSV file", "*.csv")]
    asked_path = asksaveasfile(
        mode="w", filetypes=file_types, defaultextension=file_types)

    # if file is selected, set the file value
    if asked_path:
      self.tkFileInputText.set(asked_path.name)
    pass

  def update_plot(self, measured) -> None:
    estimated = 0.0
    measured_with_noise = measured + self.prng.uniform(-2, 2)

    # based on the data we have,
    if self.data_measured[0] == 0:
      # no prior data, buffer the data to estimate kalman parameters
      estimated = measured_with_noise
    elif self.data_measured[0] != 0 and not self.kf_initialized:
      # initial data has been collected, run EM algorithm
      print('Estimating Kalman parameters...')
      current_observations = self.data_measured.copy() + [measured_with_noise]
      self.kf = self.kf.em(np.array(current_observations))
      self.kf_initialized = True

      # print parameters
      pprint(vars(self.kf))

      # estimate using Kalman filter
      means, covariances = self.kf.filter(np.array(current_observations))
      estimated = means[-1]
      self.kf_last_means = means
      self.kf_last_covariances = covariances
    else:
      # estimate using Kalman filter
      means, covariances = self.kf.filter_update(
          self.kf_last_means[-1], self.kf_last_covariances[-1], np.array([measured_with_noise]))
      estimated = means.item(0)
      self.kf_last_means = means
      self.kf_last_covariances = covariances

    # print current measurement
    print("{} - measured: {:.2f}, measured with noise: {:.2f}, estimated: {:.2f}".format(
        datetime.now().strftime("%H:%M:%S"), measured, measured_with_noise, estimated))

    # write to file
    self.csv_writer.write(datetime.now(), measured,
                          measured_with_noise, estimated)

    # update plot data
    self.data_time.pop(0)
    self.data_measured.pop(0)
    self.data_measured_with_noise.pop(0)
    self.data_estimated.pop(0)

    self.data_time.append(self.data_time[-1] + 1)
    self.data_measured.append(measured)
    self.data_measured_with_noise.append(measured_with_noise)
    self.data_estimated.append(estimated)

    # update plot
    self.sc_measured.set_offsets(np.c_[self.data_time, self.data_measured])
    self.sc_measured_with_noise.set_offsets(
        np.c_[self.data_time, self.data_measured_with_noise])
    self.line_estimated.set_data(self.data_time, self.data_estimated)

    self.ax.set_xlim(self.data_time[0], self.data_time[-1])
    self.tkCanvas.draw()

  def close(self) -> None:
    print("Closing serial port and CSV writer...")
    if self.serial_reader:
      self.serial_reader.close()

    if self.csv_writer:
      self.csv_writer.close()


# boostrap application
if __name__ == "__main__":
  matplotlib.use('TkAgg')

  root = tk.Tk()
  root.geometry("600x600")
  root.title("NatsuPy Demo App")

  app = NatsuPyApp(root)

  # gracefully close open serial/file
  def on_close():
    app.close()
    root.destroy()

  # begin main message loop
  root.protocol('WM_DELETE_WINDOW', on_close)
  root.mainloop()
