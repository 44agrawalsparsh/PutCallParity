import numpy as np
import signal
import curses

class PutCallGame():
    """
    Class object for put call parity. Similar to the website with 5 modes:

    1. Basic Put Call Parity: C - P = S - K + r/c solve for C/P given other values

    2. Combo: combo = S - K + r/c given three of these values back out the missing value

    3. Straddle: straddle = combo + 2P, straddle = 2C - combo. Always given the values of S, K, r/c then two of C, P, Straddle are selected. One is missing one is shown and need to back out the missing one.

    4. B/W: B/W = P + r/c, B/W = C - parity, given S, K, r/c and one of B/W and C/P. Whichever one is not shown's value must be identified.

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

        if ((not is_instance(modes_allowed, int)) or (modes_allowed < 1) or (modes_allowed > 0x1F)):
            raise ValueError("Invald modes_allowed")

        if ((not is_instance(time_length, int)) or (time_length <= 0)):
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
        self.timer = [-1] #what the signal alarm will affect

        self.rng = np.random.default_rng()

    def signal_handler(self, signum, frame):
        """signal handler used to update the time left in the game"""
        #TODO
        if (self.timer[0] >= 0):
            self.timer[0] -= 1

    def play(self):
        """
        Description: Executes a round of the game

        """

        #TODO
        pass

    def generate_prices(self):
        """
        Description: generates C,P,S,K,r/c values that adhere to put call parity

        Process is as follows:

        All random numbers are generated such that they are at most two decimal places.

        K is a random multiple of 5 between 5 and 100
        S is K plus a random number between -10 and 10
        r/c is a random value between 0 and 1

        C is a random number between 0 and 15
        P is derived from C,K,S,r/c so that put call parity applies

        Returns:

        market_values(dict): A dictionary of C,P,S,K,r/c values
        """

        output = {}

        K = self.rng.integers(2,21) * 5
        S = 20*self.rng.random() - 10 + K
        S = np.round(S, 2)
        carry = np.round(self.rng.random(), 2)

        C = 5 + 10*self.rng.random()
        C = np.round(C, 2)
        P = C - S + K - carry

        output["K"] = K
        output["S"] = S
        output["r/c"] = carry
        output["C"] = C
        output["P"] = P

        return output



    def gen_problem(self):
        """
        Description: Generates a set of valid prices, then based on allowed types of questions generates a question.

        Returns:

        problem(tuple): first element is a list of market values to show the player, the second element is the answer
        """

        #TODO
        pass

    def get_response(self, target_answer):
        """
        Description: Has the user attempt to type in the correct answer. Once the correct answer is typed, score is updated.

        Arguments:

        target_answer(int): the target number - will be converted to a string locally

        """
        #TODO
        pass


if (__name__ == "__main__"):
    obj = PutCallParity(0x1F, 120, None)
    print(obj.generate_prices())

