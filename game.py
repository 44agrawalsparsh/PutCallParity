import numpy as np
import signal
import curses

def wait_for_char(stdscr, char):
    """
    Description: hacky solution to wait for user to type a character for a given curses window
    """
    while True:
        try:
            if (chr(stdscr.getch()) == char):
                return
        except:
            pass

class PutCallGame():
    """
    Class object for put call parity. Similar to the website with 5 modes:

    1. Basic Put Call Parity: C - P = S - K + r/c solve for C/P given other values

    2. Combo: combo = S - K + r/c given values other than S back out S

    3. Straddle: straddle = combo + 2P, straddle = 2C - combo. Given S,K,r/c and straddle value back out C or P

    4. B/W: B/W = P + r/c, B/W = C - parity, given S, K, r/c and B/W back out C or P

    5. P&S: P&S = C - r/c, P&S = P + parity. Similar to B/W

    """

    def __init__(self, modes_allowed:int, time_length:int, stdscr):
        """
        Description:

        sets up the game object. Can call play function to start a game.

        Arguments:

        modes_allowed(int): 5 bits to convey which modes are allowed

        time_length(int): number of seconds the game should last

        stdscr(curses library obj): needed for interacting with the terminal

        Raises:

        ValueError: invalid number for modes allowed or time_length is negative
        """

        if ((not isinstance(modes_allowed, int)) or (modes_allowed < 1) or (modes_allowed > 0x1F)):
            raise ValueError("Invald modes_allowed")

        if ((not isinstance(time_length, int)) or (time_length <= 0)):
            raise ValueError("invalid time_length")

        self.stdscr = stdscr

        self.allowed_modes = []
        if (modes_allowed & 0b00001):
            self.allowed_modes.append("ONE")

        if (modes_allowed & 0b00010):
            self.allowed_modes.append("TWO")

        if (modes_allowed & 0b00100):
            self.allowed_modes.append("THREE")

        if (modes_allowed & 0b01000):
            self.allowed_modes.append("FOUR")

        if (modes_allowed & 0b10000):
            self.allowed_modes.append("FIVE")

        self.score = -1

        self.starting_time = time_length
        self.timer = [-1] #what the signal alarm will affect

        self.rng = np.random.default_rng()

        self.is_playing = False

    def alarm_handler(self, signum, frame):
        """signal handler used to update the time left in the game"""

        if (self.timer[0] >= 0):
            self.timer[0] -= 1

    def reset(self):
        """
        Description: resets the game until play is called again
        """
        self.timer[0] = -1
        self.score = -1

        # Stop the interval timer
        signal.setitimer(signal.ITIMER_REAL, 0)
        # Reset the signal handler for SIGALRM to default
        signal.signal(signal.SIGALRM, signal.SIG_DFL)

        self.is_playing = False

    def play(self):
        """
        Description: Executes a round of the game

        """

        self.stdscr.clear()
        self.stdscr.refresh()

        self.score = 0
        self.timer[0] = self.starting_time
        self.is_playing = True


        # Set up the signal handler for SIGALRM
        signal.signal(signal.SIGALRM, self.alarm_handler)

        # Start the interval timer (decrements every second)
        signal.setitimer(signal.ITIMER_REAL, 1, 1)

        # Disable cursor
        curses.curs_set(0)

        # Clear screen
        self.stdscr.clear()
        self.stdscr.refresh()

        import time

        while (self.is_playing):
            self.play_question();

        self.stdscr.clear()

        self.stdscr.addstr(1,0, "GAME OVER")
        self.stdscr.addstr(2,0, f"Final score: {self.score}")
        self.stdscr.addstr(5,0, "Press r to return to menu")
        self.stdscr.refresh()

        wait_for_char(self.stdscr, "r")
        self.reset()


    def generate_prices(self):
        """
        Description: generates C,P,S,K,r/c values that adhere to put call parity

        Process is as follows:

        All random numbers are generated such that they are at most two decimal places.

        K is a random multiple of 5 between 5 and 100
        S is K plus a random number between -10 and 10
        r/c is a random value between 0 and 1

        If S > K, then we set C = random number between 0-10 plus the intrinsic value and derive P from put call parity
        If S < K, then we set P = random number between 0-10 plus the intrinsic value and derive C from put call parity

        Returns:

        market_values(dict): A dictionary of C,P,S,K,r/c values
        """

        output = {}

        K = self.rng.integers(2,21) * 5

        S = 20*self.rng.random() - 10 + K
        S = np.round(S, 2)
        carry = np.round(self.rng.random(), 2)

        option_premium = 10*self.rng.random() + 0.01
        option_premium = np.round(option_premium, 2)

        if (S + carry >= K):
            C = S - K + carry + option_premium
            P = C - S + K - carry
        else:
            P = K - S - carry + option_premium
            C = P + S - K + carry

        C = np.round(C, 2)
        P = np.round(P, 2)

        output["K"] = K
        output["S"] = S
        output["r/c"] = carry
        output["C"] = C
        output["P"] = P

        #assert ((C - P) - (S - K + carry)) < 0.00001
        #assert C > 0
        #assert P > 0

        #print(output)


        return output



    def generate_problem(self):
        """
        Description: Generates a set of valid prices, then based on allowed types of questions generates a question.

        Returns:

        problem(tuple): first element is a string to show the player - this includes market values of some fields and a ? besides the value being solved for -, the second element is the answer
        """

        prices = self.generate_prices()
        problem_type = self.rng.choice(self.allowed_modes)

        market_values = ""
        answer = ""

        if (problem_type == "ONE"):
            #determine whether C or P should be solved for
            if (self.rng.random() > 0.5):
                #hide C
                market_values = f'C = ?\nP = {prices["P"]}\nS = {prices["S"]}\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
                answer = prices["C"]

            else:
                #hide P
                market_values = f'C = {prices["C"]}\nP = ?\nS = {prices["S"]}\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
                answer = prices["P"]

        elif (problem_type == "TWO"):

            combo = prices["S"] - prices["K"] + prices["r/c"]
            combo = np.round(combo, 2)
            market_values = f'Combo = {combo}\nS = ?\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
            answer = prices["S"]

        elif (problem_type == "THREE"):
            straddle = prices["C"] + prices["P"]
            straddle = np.round(straddle, 2)

            #decide whether C or P will be hidden
            if (self.rng.random() > 0.5):
                market_values = f'C = ?\nStraddle = {straddle}\nS = {prices["S"]}\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
                answer = prices["C"]
            else:
                market_values = f'P = ?\nStraddle = {straddle}\nS = {prices["S"]}\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
                answer = prices["P"]

        elif (problem_type == "FOUR"):
            b_w = prices["C"] + prices["K"] - prices["S"]
            b_w = np.round(b_w, 2)

            if (self.rng.random() > 0.5):
                #C
                market_values = f'C = ?\nB/W = {b_w}\nS = {prices["S"]}\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
                answer = prices["C"]
            else:
                #P
                market_values = f'P = ?\nB/W = {b_w}\nS = {prices["S"]}\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
                answer = prices["P"]
        elif (problem_type == "FIVE"):
            p_s = prices["P"] + prices["S"] - prices["K"]
            p_s = np.round(p_s, 2)

            if (self.rng.random() > 0.5):
                #C
                market_values = f'C = ?\nP&S = {p_s}\nS = {prices["S"]}\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
                answer = prices["C"]
            else:
                #P
                market_values = f'P = ?\nP&S = {p_s}\nS = {prices["S"]}\nK = {prices["K"]}\nr/c = {prices["r/c"]}'
                answer = prices["P"]

        return market_values, answer

    def play_question(self):
        """
        Description: Presents a question to the user and only proceeds once they enter the correct answer

        """

        question, answer = self.generate_problem()

        target = str(answer).strip()

        self.stdscr.clear()
        self.stdscr.refresh()

        user_input = ""
        cursor_pos = 0

        while (self.is_playing):
            #self.stdscr.erase()
            self.stdscr.addstr(0,0,f"{self.timer[0]} seconds left")
            self.stdscr.clrtoeol()
            self.stdscr.addstr(1,0, f"Score: {self.score}")
            self.stdscr.clrtoeol()

            self.stdscr.addstr(5,0, question)
            self.stdscr.clrtoeol()

            self.stdscr.addstr(12,0, "Answer:")
            self.stdscr.clrtoeol()

            self.stdscr.addstr(14, 0, user_input)
            self.stdscr.clrtoeol()

            self.stdscr.refresh()

            if (self.timer[0] <= 0):
                self.is_playing = False

            ch = self.stdscr.getch()

            if ch == curses.KEY_BACKSPACE or ch == 127:  # Handle backspace (127 is for some terminals)
                if cursor_pos > 0:
                    user_input = user_input[:cursor_pos - 1] + user_input[cursor_pos:]
                    cursor_pos -= 1
            elif 0 < ch < 256 and chr(ch).isprintable():  # Handle printable characters
                user_input = user_input[:cursor_pos] + chr(ch) + user_input[cursor_pos:]
                cursor_pos += 1

            if (user_input == target):

                self.stdscr.addstr(14, 0, user_input)
                self.stdscr.clrtoeol()
                self.stdscr.refresh()
                self.score += 1

                return

def main(stdscr):
    """
    Description: main menu interacting with the game

    Asks you to choose game length as well as which questions are permitted before starting a game
    """
    while True:

        curses.curs_set(0)

        stdscr.clear()
        stdscr.addstr(0,0, "Welcome to Put-Call-Parity! Press b to begin!")
        stdscr.clrtoeol()
        stdscr.refresh()
        wait_for_char(stdscr, "b")

        stdscr.clear()
        stdscr.addstr(0,0, "How many seconds would you like the game to last?")
        stdscr.clrtoeol()
        stdscr.refresh()

        ch = -1

        user_input = ""
        cursor_pos = 0

        while (ch not in [10,13, curses.KEY_ENTER]):

            ch = stdscr.getch()

            if ch == curses.KEY_BACKSPACE or ch == 127:  # Handle backspace (127 is for some terminals)
                if cursor_pos > 0:
                    user_input = user_input[:cursor_pos - 1] + user_input[cursor_pos:]
                    cursor_pos -= 1
            elif 48 <= ch <= 57 and chr(ch).isprintable():  # Handle printable characters
                user_input = user_input[:cursor_pos] + chr(ch) + user_input[cursor_pos:]
                cursor_pos += 1

            stdscr.addstr(1,0, user_input)
            stdscr.clrtoeol()
            stdscr.refresh()

        seconds = int(user_input)

        stdscr.clear()
        stdscr.refresh()

        stdscr.addstr(1,0, "Simple Put-Call Parity Questions: Enabled (Press 1 to toggle)")
        stdscr.clrtoeol()
        stdscr.addstr(2,0, "Combo Questions: Enabled (Press 2 to toggle)")
        stdscr.clrtoeol()
        stdscr.addstr(3,0, "Straddle Questions: Enabled (Press 3 to toggle)")
        stdscr.clrtoeol()
        stdscr.addstr(4,0, "B/W Questions: Enabled (Press 4 to toggle)")
        stdscr.clrtoeol()
        stdscr.addstr(5,0, "P&S Questions: Enabled (Press 5 to toggle)")
        stdscr.clrtoeol()
        stdscr.addstr(6,0, "Press r when ready")
        stdscr.clrtoeol()

        game_modes = 0x1F

        ch = -1
        while (0 >= ch or 256 <= ch or chr(ch) != 'r'):
            ch = stdscr.getch()

            if (chr(ch) == '1'):
                game_modes = game_modes ^ 0b00001
                if (game_modes & 0b00001):
                    stdscr.addstr(1,0, "Simple Put-Call Parity Questions: Enabled (Press 1 to toggle)")
                else:
                    stdscr.addstr(1,0, "Simple Put-Call Parity Questions: Disabled (Press 1 to toggle)")

            elif (chr(ch) == '2'):
                game_modes = game_modes ^ 0b00010
                if (game_modes & 0b00010):
                    stdscr.addstr(2,0, "Combo Questions: Enabled (Press 2 to toggle)")
                else:
                    stdscr.addstr(2,0, "Combo Questions: Disabled (Press 2 to toggle)")

            elif (chr(ch) == '3'):
                game_modes = game_modes ^ 0b00100
                if (game_modes & 0b00100):
                    stdscr.addstr(3,0, "Straddle Questions: Enabled (Press 3 to toggle)")
                else:
                    stdscr.addstr(3,0, "Straddle Questions: Disabled (Press 3 to toggle)")
            elif (chr(ch) == '4'):
                game_modes = game_modes ^ 0b01000
                if (game_modes & 0b01000):
                    stdscr.addstr(4,0, "B/W Questions: Enabled (Press 4 to toggle)")
                else:
                    stdscr.addstr(4,0, "B/W Questions: Disabled (Press 4 to toggle)")
            elif (chr(ch) == '5'):
                game_modes = game_modes ^ 0b10000
                if (game_modes & 0b10000):
                    stdscr.addstr(5,0, "P&S Questions: Enabled (Press 5 to toggle)")
                else:
                    stdscr.addstr(5,0, "P&S Questions: Disabled (Press 5 to toggle)")

            stdscr.clrtoeol()
            stdscr.refresh()

        obj = PutCallGame(game_modes, seconds, stdscr)
        obj.play()


if (__name__ == "__main__"):
  curses.wrapper(main)

