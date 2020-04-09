class ImageDimensions:

    def __init__(self, minX, minY, maxX, maxY, pixelX, pixelY):
        self.minX, self.minY, self.maxX, self.maxY, self.pixelX, self.pixelY = minX, minY, maxX, maxY, pixelX, pixelY

    def toString(self):
        return ' '.join(map(lambda prop: str(prop), (self.minX, self.minY, self.maxX, self.maxY, ' ', self.pixelX, self.pixelY)))
