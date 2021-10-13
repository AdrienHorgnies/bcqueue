class Block:
    def __init__(self, size, selection, mining=None):
        self.size = size
        self.selection = selection
        self.mining = mining

    def mined(self, mining):
        self.mining = mining
