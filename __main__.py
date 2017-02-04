"""
Run the completion server.
"""

from os import path
import sys

sys.path.append(path.join(path.dirname(__file__), 'jedi'))

import completion

if __name__ == '__main__':
    completion.JediCompletion().watch()
