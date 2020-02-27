import threading
import tkinter as tk
import tkinter.ttk
import tkinter.messagebox
import tkinter.font
import queue as q
import enum
from typing import NamedTuple, Optional, List
import time
import subprocess as sp
import platform

def look_at_root_dir() -> str:
    if platform.system() == 'Windows':
        cp = sp.run(['DIR', 'C:\\'], shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
    else:
        cp = sp.run(['ls', '/'], text=True, stdout=sp.PIPE, stderr=sp.PIPE)

    return cp.stdout

class QueueState(enum.Enum):
    READY = enum.auto()
    RUNNING = enum.auto()
    DONE = enum.auto()
    FAILED = enum.auto()


class QueueElement(NamedTuple):
    queue_state: QueueState
    message: Optional[str]


class Backend(threading.Thread):

    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    def run(self):
        self.queue.put(QueueElement(QueueState.READY, 'Process is starting.\n'))

        append_queue = lambda message: self.queue.put(QueueElement(QueueState.RUNNING, message))
        for i in range(5):
            append_queue(f'Running process... {i}\n')
            time.sleep(1)
        append_queue(look_at_root_dir())

        self.queue.put(QueueElement(QueueState.DONE, 'Process Completed.\n'))


class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Text Status Widget
        self.frame_1 = tk.Frame(self, padx=20, pady=20)
        self.frame_1.pack()
        font_times_18 = tk.font.Font(family='Times New Roman', size=18)
        self.status = tk.StringVar(self, value='Ready to run.')
        tk.Label(self.frame_1, textvariable=self.status, font=font_times_18).pack()

        # Button Widget
        self.frame_2 = tk.Frame(self, padx=20)
        self.frame_2.pack()
        self.button = tk.Button(self.frame_2, text='Click Me', command=self.go)
        self.button.pack()

        # Textbox Frame
        self.frame_3 = tk.Frame(self, padx=20, pady=20)
        self.frame_3.pack()
        self.textbox = TextBoxOutput(self.frame_3)
        self.textbox.pack()

    def go(self) -> None:
        """
        This function will start the background process class, Backend, which is a child of the Thread Class. The
        Backend class will run in its own thread, thus not making the Tkinter GUI freeze. The two threads will
        communicate with a queue. This communication is one way though, as the GUI will simply print out messages
        the Backend sends, and not put anything to the queue.
        """
        queue = q.Queue()
        process = Backend(queue)
        process.start()
        self.after(0, self.check_queue, queue)

    def check_queue(self, queue) -> None:
        """
        This function checks the queue every 100 milliseconds. It also pops the queue if there is an element. The queue
        is expected to be homogeneous of the type, named tuple: QueueElement. This function will keep calling itself
        every 100 milliseconds until it gets QueueElement.queue_state that is QueueState.DONE or QueueState.Failed.
        This function does use the QueueElement.message string to print output to the GUI.
        """
        if not queue.empty():
            element = queue.get()

            if element.queue_state is QueueState.READY or element.queue_state is QueueState.RUNNING:
                self.textbox.print_message(element.message)
                self.status.set('Background Process is Running')

            if element.queue_state is QueueState.DONE or element.queue_state is QueueState.FAILED:
                self.textbox.print_message(element.message)

                if element.queue_state is QueueState.DONE:
                    self.status.set('Background Process Completed')
                elif element.queue_state is QueueState.FAILED:
                    self.status.set('Background Process Failed')

                return

        self.after(100, self.check_queue, queue)


class TextBoxOutput(tk.Frame):
    """
    This widget is based on the tk.Text widget. It acts as a sort of pseudo-terminal that only prints output, but
    doesn't accept user input. It will in the state of tk.DISABLED so that the user can't use it, but switch to
    tk.Normal, when the program wants to print something out to the screen.
    """

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.text = tk.Text(self, state=tk.DISABLED)
        self.vsb = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side=tk.RIGHT, fill="y")
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def print_message(self, message: str) -> None:
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, message)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)


if __name__ == "__main__":
    app = App()
    app.title('Tkinter Template.')
    app.mainloop()
