import time
import humanize
import threading

from clint.textui import puts, colored
from clint.textui.progress import Bar, ETA_INTERVAL, ETA_SMA_WINDOW, STREAM
from progress.spinner import Spinner

BAR_TEMPLATE = '%s[%s%s] %i%% - %s/%s - %s\r'


class ProgressBar(Bar):
    def show(self, progress, count=None):
        if count is not None:
            self.expected_size = count
        if self.expected_size is None:
            raise Exception("expected_size not initialized")
        self.last_progress = progress
        if (time.time() - self.etadelta) > ETA_INTERVAL:
            self.etadelta = time.time()
            self.ittimes = \
                self.ittimes[-ETA_SMA_WINDOW:] + \
                [-(self.start - time.time()) / (progress + 1)]
            self.eta = \
                sum(self.ittimes) / float(len(self.ittimes)) * \
                (self.expected_size - progress)
            self.etadisp = self.format_time(self.eta)
        x = int(self.width * progress / self.expected_size)
        if not self.hide:
            if (progress % self.every) == 0 or (progress == self.expected_size):
                STREAM.write(BAR_TEMPLATE % (
                    self.label, self.filled_char * x,
                    self.empty_char * (self.width - x),
                    progress * 100 / self.expected_size,
                    humanize.naturalsize(progress),
                    humanize.naturalsize(self.expected_size), self.etadisp))
                STREAM.flush()


class AsyncSpinner(threading.Thread):
    def __init__(self, text):
        threading.Thread.__init__(self)
        self._stop = False
        self._spinner = Spinner(text)
    
    def run(self):
        while not self._stop:
            time.sleep(0.1)
            self._spinner.next()
        print("") # Newline
    
    def stop(self):
        self._stop = True
        time.sleep(0.5) # Wait 0.5 seconds for thread to terminate


def input_yn(question, default=True):
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default:
        prompt = " [Y/n] "
    else:
        prompt = " [y/N] "

    while True:
        print(question + prompt, end='')
        choice = input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")


def print_error(msg, newline, exit_after):
    puts(colored.red("ERROR: {}".format(msg)), newline=newline)

    if exit_after:
        exit(1)


def print_warning(msg, newline):
    puts(colored.yellow("Warning: {}".format(msg)), newline=newline)
